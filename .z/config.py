#!/usr/bin/python3
import os
from base import (
    Path,
    apt_install,
    cmd_output,
    cmd_works,
    download_and_install_deb,
    install,
    install_from_github_release,
    lineinfile,
    npm_install,
    print_message_and_done,
    run,
)

# avoid conflicts with git operations and still use as a repo for dotfiles
os.environ.pop("GIT_DIR", None)
os.environ.pop("GIT_WORK_TREE", None)

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# basic
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
apt_install(Path("apt_packages").read_text())

# zsh
if cmd_output("echo $SHELL") != "/usr/bin/zsh":
    run("sudo chsh -s /bin/zsh")


# install some stuf with bash scripts
for script in Path("install").glob("*.sh"):
    match script.stem.split(":"):
        case [command_name]:
            is_installed = cmd_works(f"which {command_name}")
        case [command_name, test]:
            is_installed = cmd_works(test)
    if not is_installed:
        with print_message_and_done(f"Installing {command_name}"):
            # work on /tmp for downloads not to polute this dir
            run(str(script.absolute()), cwd="/tmp", capture_output=True)


npm_install("@bitwarden/cli")


# https://github.com/foriequal0/git-trim
install_from_github_release(
    "foriequal0/git-trim", ".*linux.*tgz$", Path.home() / ".local/bin", "git-trim"
)

# python
if install("basic", "uv", "curl -LsSf https://astral.sh/uv/install.sh | env UV_NO_MODIFY_PATH=1 sh"):
    install(
        "uv",
        "ruff isort ipython djlint",
        "uv tool install --force {}",
        lambda _: False,
    )

# google chrome
download_and_install_deb(
    "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb",
    "google-chrome-stable",
)

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# tweaks
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# enable some Linux Magic System Request Keys
# see https://www.kernel.org/doc/html/latest/admin-guide/sysrq.html
lineinfile("/etc/sysctl.conf", f"kernel.sysrq={0b11110000}")

# limit the total size of /var/log/journal/ to 100M
lineinfile("/etc/systemd/journald.conf", "SystemMaxUse=100M")

# Remove unnecessary hunspell english dicts
for dic in Path("/usr/share/hunspell").glob("en_*"):
    if "en_US" != dic.stem:
        run(f"sudo rm {dic}")

# add pt_BR locale
if "pt_BR.utf8" not in run("locale -a", capture_output=True).stdout.splitlines():
    run("sudo locale-gen pt_BR.UTF-8")


# FOR FUTURE USE, MAYBE ...

# zoom
# download_and_install_deb("https://zoom.us/client/latest/zoom_amd64.deb", "zoom")

# banco do brasil
# download_and_install_deb(
#     "https://cloud.gastecnologia.com.br/bb/downloads/ws/warsaw_setup64.deb",
#     "warsaw",
# )
