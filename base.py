import pathlib
import re
import subprocess
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


def install(tool, packages, cmd, test_cmd):
    for name in packages.split():
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


def symlink(link, target):
    if link.is_symlink() or link.exists():
        link.unlink()
    link.symlink_to(target)


def replace_line(path, line_to_replace, line_start):
    replaced = 0
    for line in path.read_text().splitlines():
        if line.startswith(line_start):
            yield line_to_replace
            replaced += 1
        else:
            yield line
    if not replaced:
        # if not replaced yield at last
        yield f"\n{line_to_replace}"
    assert replaced <= 1, f"Line replaced more than once in {path}: {line_to_replace}"


def lineinfile(path, line, start=None):
    # start defaults to the line without whatever is after "="
    path = Path(path)
    start = start or re.sub(r"(?<==).*", "", line)
    path.write_text("\n".join(replace_line(path, line, start)))


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


def download_and_install_deb(url, package_name):
    if get_return_code(f"dpkg -s {package_name}"):
        apt_install("gdebi")
        tmp_dest = download(url)
        print(f"Installing {package_name}...")
        run(f"sudo gdebi {tmp_dest} --non-interactive")


def snap_install(packages):
    install("snap", packages, "sudo snap install {}", "snap list")
