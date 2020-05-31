import pathlib
import re
import subprocess
from contextlib import contextmanager
from os import getuid
from textwrap import dedent
from urllib.request import Request, urlopen, urlretrieve


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


def install(tool, packages, cmd, test_cmd):
    for name in strip_comments(packages).split():
        if get_return_code(f"{test_cmd} {name}"):
            print(f"{tool}: installing {name}...")
            run(cmd.format(name), capture_output=True)


def apt_install(packages):
    install("apt", packages, "sudo apt-get install {} --yes --quiet --quiet", "dpkg -s")


def pip_install(packages):
    install("pip", packages, "pip install {}", "pip show")


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


def get_url_headers(url):
    return urlopen(Request(url, method="HEAD")).info()


def download(url, dest_dir="/tmp"):
    print(f"Downloading {url}... ", end="", flush=True)
    tmp_dest = Path(dest_dir, Path(url).name)

    def is_downloaded(headers):
        lenght = int(headers["Content-Length"])
        return tmp_dest.exists() and tmp_dest.stat().st_size == lenght

    if is_downloaded(get_url_headers(url)):
        print("already downloaded")
    else:
        _, headers = urlretrieve(url, tmp_dest)
        assert is_downloaded(headers)
        print("done")
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
    install("snap", packages, "sudo snap install {}", "snap list")


@contextmanager
def temporary_ownership_of(path):
    "Temporarily change onwnership of path to the current user"
    path = Path(path)
    original_uid = path.stat().st_uid
    run(f"sudo chown {getuid()} {path}")
    yield path
    run(f"sudo chown {original_uid} {path}")
