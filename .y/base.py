import cgi
import json
import re
import shutil
import subprocess
import tarfile
import tempfile
import time
import zipfile
from contextlib import contextmanager
from os import getuid
from pathlib import Path
from urllib.request import Request, urlopen, urlretrieve


def run(cmd, **kwargs):
    """
    Tweaks subprocess.run to receive cmd as a single string.
    Raises exception by default when unsuccessful.
    """
    kwargs.setdefault("check", True)
    kwargs.setdefault("shell", True)
    res = subprocess.run(cmd, **kwargs)
    res.stdout, res.stderr = [b.decode() if b else b for b in (res.stdout, res.stderr)]
    return res


def get_return_code(cmd):
    return run(cmd, capture_output=True, check=False).returncode


def cmd_output(cmd):
    return run(cmd, capture_output=True, check=False).stdout.strip()


def cmd_works(cmd):
    return get_return_code(cmd) == 0


def wait_for_condition(test, timeout=2):
    start = time.time()
    while time.time() < start + timeout:
        if res := test():
            return res
        time.sleep(0.1)
    return False


def strip_comments(text):
    return re.sub(" *#.*", "", text)


def install(tool, packages, cmd, cmd_check_is_installed="which"):
    """
    Returns the list of packages actually installed for the first time
    """
    names = strip_comments(packages).split()

    def already_installed(name):
        if callable(cmd_check_is_installed):
            return cmd_check_is_installed(name)
        return get_return_code(f"{cmd_check_is_installed} {name}") == 0

    def install_all():
        for name in names:
            if not already_installed(name):
                print(f"{tool}: Installing {name}...")
                run(cmd.format(name), capture_output=True)
                yield name

    # returns the list of packages installed for the first time
    return list(install_all())


def apt_install(packages, extra_args=""):
    return install(
        "apt", packages, f"sudo apt install {extra_args} {{}} --yes --quiet", "dpkg -s"
    )


def apt_add_ppa(name):
    if "/" not in name:
        name = f"{name}/ppa"
    # skip if ppa was already added
    if [
        line
        for line in run("apt-cache policy", capture_output=True).stdout.splitlines()
        if name in line
    ]:
        return
    run(f"sudo add-apt-repository ppa:{name} --yes")
    run("sudo apt-get update")


def npm_install(packages):
    return install(
        "global npm", packages, "sudo npm install --global {}", "npm list -g"
    )


def really_exists(path):
    return path.is_symlink() or path.exists()


def symlink(link, target):
    if really_exists(link):
        link.unlink()
    link.symlink_to(target)


def lineinfile(path, line, start=None):
    path = Path(path)
    # start defaults to the start of the line up to "="
    #   for example, the start of "abc=123" is "abc="
    start = start or re.sub(r"(?<==).*", "", line)
    # normalize line
    line = line.rstrip() + "\n"

    original_text = path.read_text()

    def gen_text_lines_with_replaced_line():
        replaced = 0
        for current in original_text.splitlines(keepends=True):
            if current.startswith(start):
                yield line
                replaced += 1
            else:
                yield current
        if not replaced:
            # if not replaced yield as last line
            newline_if_needed = "" if original_text.endswith("\n") else "\n"
            yield newline_if_needed + line

        assert replaced <= 1, f"Line replaced more than once in {path}: {line}"

    new_text = "".join(gen_text_lines_with_replaced_line())
    if original_text != new_text:
        # try first without temporary ownership to avoid an unnecessary sudo
        try:
            path.write_text(new_text)
        except PermissionError:
            with temporary_ownership_of(path):
                path.write_text(new_text)


def get_file_info_for_download(url):
    headers = urlopen(Request(url, method="HEAD")).info()
    if content_disposition := headers.get("Content-Disposition"):
        match cgi.parse_header(content_disposition):
            case ("attachment", {"filename": filename}):
                return filename, headers
    return None, headers


@contextmanager
def print_message_and_done(message, oneline=True):
    if oneline:
        message, done_message = f"{message}... ", "done"
    else:
        message, done_message = f"#### {message} ####\n", "\n---- done ----"

    def done(msg):
        nonlocal done_message
        done_message = msg

    print(message, end="", flush=True)
    yield done
    print(done_message)


def download(url, dest_dir="/tmp", quick=False):
    basename = Path(url).name
    if quick and (dest_basename := Path(dest_dir, basename)).exists():
        return dest_basename

    print(f"Downloading {url}")
    filename, pre_headers = get_file_info_for_download(url)
    dest = Path(dest_dir, filename or basename)

    with print_message_and_done(f"  filename: {dest}") as done:

        def is_downloaded(headers):
            lenght = int(headers["Content-Length"])
            return dest.exists() and dest.stat().st_size == lenght

        if is_downloaded(pre_headers):
            done("already downloaded")
        else:
            _, final_headers = urlretrieve(url, dest)
            assert is_downloaded(final_headers)
    return dest


def is_not_dpkg_installed(package_name):
    return get_return_code(f"dpkg -s {package_name}")


def download_and_install_deb(url, package_name):
    if is_not_dpkg_installed(package_name):
        apt_install("gdebi")
        tmp_dest = download(url)
        print(f"Installing {package_name}...")
        run(f"sudo gdebi {tmp_dest} --non-interactive")


@contextmanager
def temporary_ownership_of(path):
    "Temporarily change onwnership of path to the current user"
    path = Path(path)
    original_uid = path.stat().st_uid
    run(f"sudo chown {getuid()} {path}")
    yield path
    run(f"sudo chown {original_uid} {path}")


def install_from_github_release(
    repo_path, download_url_regex, dest_dir, target_glob, update=False
):
    some_target_exists = any(Path(dest_dir).glob(f"**/{target_glob}"))
    if not (update) and some_target_exists:
        # shortcut and signal that the install was already done before
        return False

    # download compressed file from github
    url = f"https://api.github.com/repos/{repo_path}/releases/latest"
    res = json.load(urlopen(url))
    urls = (a["browser_download_url"] for a in res["assets"])
    [download_url] = (u for u in urls if re.match(download_url_regex, u))
    path_compressed_file = download(download_url)

    match path_compressed_file.suffixes:
        case (*_, ".tar", ".gz") | (*_, ".tgz"):
            open_fn = tarfile.open
        case (*_, ".zip"):
            open_fn = zipfile.ZipFile
        case _:
            raise Exception(
                f"Release from github repo {repo_path} is not a recognized compressed file."
            )

    # extract, pick the target file and move it to dest_dir
    with tempfile.TemporaryDirectory() as temp_dir:
        open_fn(path_compressed_file).extractall(temp_dir)
        for path in Path(temp_dir).glob(f"**/{target_glob}"):
            if path.is_file():
                if (dest_path := dest_dir / path.name).exists():
                    dest_path.unlink()
                shutil.move(str(path), dest_dir)
                print(f"{path} installed in {dest_dir}")

    # signal that the install or update was done
    return True


def mkdir(*path_parts):
    path = Path(*path_parts)
    path.mkdir(parents=True, exist_ok=True)
    return path
