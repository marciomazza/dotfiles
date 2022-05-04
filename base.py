import cgi
import json
import os
import pathlib
import re
import shutil
import subprocess
import tarfile
import tempfile
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
    res.stdout, res.stderr = [
        b.decode("utf-8") if b else b for b in (res.stdout, res.stderr)
    ]
    return res


def get_return_code(cmd):
    return run(cmd, capture_output=True, check=False).returncode


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


def apt_install(packages):
    return install(
        "apt", packages, "sudo apt install {} --yes --quiet --quiet", "dpkg -s"
    )


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

    def text_with_line():
        replaced = 0
        text = path.read_text()
        for current in text.splitlines(keepends=True):
            if current.startswith(start):
                yield line
                replaced += 1
            else:
                yield current
        if not replaced:
            # if not replaced yield at last
            newline_if_needed = "" if text.endswith("\n") else "\n"
            yield newline_if_needed + line

        assert replaced <= 1, f"Line replaced more than once in {path}: {line}"

    path.write_text("".join(text_with_line()))


def get_filename_for_download(url, headers):
    if content_disposition := headers.get("Content-Disposition"):
        match cgi.parse_header(content_disposition):
            case ("attachment", {"filename": filename}):
                return filename
    return Path(url).name


@contextmanager
def print_message_and_done(message):
    done_message = "done"

    def done(msg):
        nonlocal done_message
        done_message = msg

    print(f"{message}... ", end="", flush=True)
    yield done
    print(done_message)


def download(url, dest_dir="/tmp"):
    print(f"Downloading {url}")
    pre_headers = urlopen(Request(url, method="HEAD")).info()
    tmp_dest = Path(dest_dir, get_filename_for_download(url, pre_headers))
    with print_message_and_done(f"  filename: {tmp_dest}") as done:

        def is_downloaded(headers):
            lenght = int(headers["Content-Length"])
            return tmp_dest.exists() and tmp_dest.stat().st_size == lenght

        if is_downloaded(pre_headers):
            done("already downloaded")
        else:
            _, final_headers = urlretrieve(url, tmp_dest)
            assert is_downloaded(final_headers)
    return tmp_dest


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
