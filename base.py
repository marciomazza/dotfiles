import pathlib
import re
import subprocess
from textwrap import dedent


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


def install(packages):
    for name in packages.split():
        if run(f"dpkg -s {name}", capture_output=True, check=False).returncode:
            print(f"apt: installing {name}...")
            run(
                f"sudo apt-get install {name} --yes --quiet --quiet",
                capture_output=True,
            )


def pip_install(packages):
    for name in packages.split():
        print(f"pip: installing {name}...")
        run(f"pip install {name}")


def splitlines(text):
    return dedent(text).strip().splitlines()


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
