import cgi
import json
import pathlib
import re
import shutil
import subprocess
import tarfile
import tempfile
import time
import zipfile
from contextlib import contextmanager
from os import getuid
from textwrap import dedent
from urllib.request import Request, urlopen, urlretrieve

import pkg_resources


def run(cmd, **kwargs):
    """
    Tweaks subprocess.run to receive cmd as a single string.
    Raises exception by default when unsuccessful.
    """
    if "check" not in kwargs:
        kwargs["check"] = True
    res = subprocess.run(cmd.split(), **kwargs)
    res.stdout, res.stderr = [b.decode() if b else b for b in (res.stdout, res.stderr)]
    return res


def get_return_code(cmd):
    return run(cmd, capture_output=True, check=False).returncode


def is_success(cmd):
    return not get_return_code(cmd)


def wait_for_condition(test, timeout=2):
    start = time.time()
    while time.time() < start + timeout:
        if res := test():
            return res
        time.sleep(0.1)
    return False


def strip_comments(text):
    return re.sub(" *#.*", "", text)


def install(tool, packages, cmd, test_cmd="which"):
    names = strip_comments(packages).split()
    test = (
        test_cmd
        if callable(test_cmd)
        else lambda name: get_return_code(f"{test_cmd} {name}")
    )

    def install_all():
        for name in names:
            if test(name):
                print(f"{tool}: installing {name}...")
                run(cmd.format(name), capture_output=True)
                yield name

    return list(install_all())


def apt_install(packages, extra_args=""):
    return install(
        "apt", packages, f"sudo apt install {extra_args} {{}} --yes --quiet", "dpkg -s"
    )


def apt_add_ppa(name):
    # check if ppa was already added
    if [
        line
        for line in run("apt-cache policy", capture_output=True).stdout.splitlines()
        if f"{name}/ppa" in line
    ]:
        return
    run(f"sudo add-apt-repository ppa:{name}/ppa --yes")
    run("sudo apt-get update")


def test_python_package_installed(name):
    # return False if installed to go allong with linux return code for success
    return name not in {i.key for i in pkg_resources.working_set}


def pip_install(packages):
    return install("pip", packages, "pip install {}", test_python_package_installed)


def npm_install(packages):
    return install(
        "global npm", packages, "sudo npm install --global {}", "npm list -g"
    )


def splitlines(text):
    return [
        line
        for line in dedent(text).strip().splitlines()
        if line and not line.strip().startswith("#")
    ]


def Path(*args, **kwargs):
    return pathlib.Path(*args, **kwargs).expanduser()


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
def print_message_and_done(message):
    done_message = "done"

    def done(msg):
        nonlocal done_message
        done_message = msg

    print(f"{message}... ", end="", flush=True)
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


def snap_install(packages):
    return install("snap", packages, "sudo snap install {}", "snap list")


@contextmanager
def temporary_ownership_of(path):
    "Temporarily change onwnership of path to the current user"
    path = Path(path)
    original_uid = path.stat().st_uid
    run(f"sudo chown {getuid()} {path}")
    yield path
    run(f"sudo chown {original_uid} {path}")


def install_from_github_release(repo_path, download_url_regex, dest_dir, target_file):
    # stop if this is already installed
    if Path(dest_dir, target_file).exists():
        return

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
        [binary] = [
            path for path in Path(temp_dir).glob(f"**/{target_file}") if path.is_file()
        ]
        shutil.move(str(binary), dest_dir)
        print(f"{target_file} installed in {dest_dir}")

    return True  # signal that the install was done for the first time


def mkdir(*path_parts):
    Path(*path_parts).mkdir(parents=True, exist_ok=True)
