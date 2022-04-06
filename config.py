#!/usr/bin/python3

import os
import subprocess

from base import (
    Path,
    apt_install,
    download,
    download_and_install_deb,
    get_return_code,
    install_from_github_release,
    is_not_dpkg_installed,
    lineinfile,
    pip_install,
    run,
    snap_install,
    splitlines,
    symlink,
    temporary_ownership_of,
)

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# basic
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
apt_install("git etckeeper")
if not Path("/etc/.git").exists():
    run("etckeeper commit 'first commit'")

apt_install(
    """
    software-properties-common python3-pip
    tree trash-cli xclip curl smbclient htop ncdu silversearcher-ag

    docker.io docker-compose
    """
)

# BUG https://bugs.launchpad.net/ubuntu/+source/libwebcam/+bug/811604
#     webcam related log file grows without boundaries
# workaround: purge the package uvcdynctrl
# see https://bugs.launchpad.net/ubuntu/+source/libwebcam/+bug/811604/comments/48
uvcdynctrl_log = Path("/var/log/uvcdynctrl-udev.log")
if uvcdynctrl_log.exists() or get_return_code("dpkg -s uvcdynctrl") == 0:
    run(f"sudo rm -f {uvcdynctrl_log}")
    # purge the offending package as a workaround
    run("sudo apt purge uvcdynctrl --yes --quiet --quiet")


# Remove unnecessary hunspell english dicts
for dic in Path("/usr/share/hunspell").glob("en_*"):
    if "en_US" != dic.stem:
        run(f"sudo rm {dic}")

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# link home config files recursively
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
HOME = Path("~")
FILES = Path("files").absolute()

files_home_dir = Path(FILES, "home")
for here in files_home_dir.rglob("*"):
    athome = Path(HOME, here.relative_to(files_home_dir))  # path relative to home
    if here.is_dir() and not here.is_symlink():
        athome.mkdir(exist_ok=True)
    else:
        if here.name != ".gitkeep":  # skip directory holders
            symlink(athome, here)

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# python
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
python_versions = [9, 10]
python_packages = " ".join(f"python3.{v} python3.{v}-dev" for v in python_versions)
if any(is_not_dpkg_installed(p) for p in python_packages.split()):
    run("sudo apt-get update")
    apt_install(python_packages)

pip_install("virtualenvwrapper")

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# bash customizations
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
pip_install("cdiff")  # used in ~/.bash_customizations
# color promt, infinite history size and run .bash_customizations
BASHRC_FILE = Path(HOME, ".bashrc")
for line in splitlines(
    """
        force_color_prompt=yes
        HISTSIZE=-1
        HISTFILESIZE=-1
        test -f ~/.bash_customizations && source ~/.bash_customizations
    """
):
    lineinfile(BASHRC_FILE, line)

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# development tools
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
LOCAL_BIN_DIR = Path(HOME, ".local/bin")

# neovim
NVIM_AUTOLOAD_DIR = "~/.local/share/nvim/site/autoload"
if not Path(NVIM_AUTOLOAD_DIR, "plug.vim").exists():
    apt_install(
        """
        neovim
        universal-ctags         # for majutsushi/tagbar
        """
    )
    run(f"mkdir -p {NVIM_AUTOLOAD_DIR}")
    download(
        "https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim",
        NVIM_AUTOLOAD_DIR,
    )
    pip_install("black isort")  # used on save python files

apt_install(
    """
    postgresql
    sqlite3
    python3-tk                  # for %paste in IPython
    libpq-dev                   # for psycopg

    graphviz libgraphviz-dev
    """
)

# django
DJANGO_BASH_COMPLETION_FILE = Path(LOCAL_BIN_DIR, "django_bash_completion")
if not DJANGO_BASH_COMPLETION_FILE.exists():
    download(
        "https://raw.githubusercontent.com/django/django/master/extras/django_bash_completion",
        LOCAL_BIN_DIR,
    )
    lineinfile(BASHRC_FILE, f". {DJANGO_BASH_COMPLETION_FILE}")

# add pt_BR locale
if "pt_BR.utf8" not in run("locale -a", capture_output=True).stdout.splitlines():
    run("sudo locale-gen pt_BR.UTF-8")

# nodejs
# https://github.com/nodesource/distributions/blob/master/README.md#debinstall
def install_node(version):
    added_to_sources = Path("/etc/apt/sources.list.d/nodesource.list").exists()

    def get_node_version():
        version = run("node --version", capture_output=True).stdout
        return int(version.lstrip("v").split(".")[0])

    if not added_to_sources or get_node_version() < version:
        node_setup_script = download(f"https://deb.nodesource.com/setup_{version}.x")
        run(f"sudo -E bash {node_setup_script}")
        apt_install("")


install_node(14)


def install_git_trim():
    # https://github.com/foriequal0/git-trim
    install_from_github_release(
        "foriequal0/git-trim", ".*linux.*tgz$", LOCAL_BIN_DIR, "git-trim"
    )
    run("git config --global trim.bases develop,master")


install_git_trim()

# TODO...
# docker compose V2
# https://docs.docker.com/compose/cli-command/
#
# sudo mkdir -p /usr/local/lib/docker/cli-plugins
# sudo curl -SL https://github.com/docker/compose/releases/download/v2.0.1/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# desktop
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def install_spotify():
    snap_install("spotify")
    template = Path(FILES, "spotify_spotify.desktop.template").read_text()
    # there can be multiple versions of the snap
    # the paths start with /snap/spotify/<version>,
    # so the last one should be the installed version
    *_, icon = sorted(Path("/snap/spotify").rglob("icons/spotify-linux-128.png"))
    with temporary_ownership_of(
        "/var/lib/snapd/desktop/applications/spotify_spotify.desktop"
    ) as desktop_file:
        desktop_file.write_text(template.format(icon=icon))


def adjust_desktop():
    gsettings = [
        line.split(maxsplit=2)
        for line in splitlines(Path(FILES, "gsettings").read_text())
    ]
    for schema, key, value in gsettings:
        subprocess.check_call(["gsettings", "set", schema, key, value])


def install_geckodriver():
    install_from_github_release(
        "mozilla/geckodriver", ".*linux64.*tar\.gz$", LOCAL_BIN_DIR, "geckodriver"
    )


if "XDG_CURRENT_DESKTOP" in os.environ:
    apt_install(
        """
        terminator fonts-hack-ttf
        gnome-tweaks gnome-shell-extensions
        dconf-editor
        gnome-shell-extension-autohidetopbar

        gimp imagemagick
        vlc mplayer audacity ffmpeg
        xournal
        libreoffice
        """
    )

    # custom firefox appearance
    [firefox_profile] = Path("~/snap/firefox/common/.mozilla/firefox").glob("*.default")
    symlink(Path(firefox_profile, "user.js"), Path(FILES, "firefox/user.js"))

    # install google chrome
    download_and_install_deb(
        "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb",
        "google-chrome-stable",
    )

    install_spotify()
    adjust_desktop()
    download_and_install_deb("https://zoom.us/client/latest/zoom_amd64.deb", "zoom")

    # banco do brasil
    download_and_install_deb(
        "https://cloud.gastecnologia.com.br/bb/downloads/ws/warsaw_setup64.deb",
        "warsaw",
    )

    # more desktop dev tools
    apt_install("gitg meld pgadmin3")
    install_geckodriver()
    install_git_trim()

    # TODO
    # disable faulty lenovo webcam
    # based on https://superuser.com/a/982292
    #
    # add disable to the startup using cron
    # based on https://karlcode.owtelse.com/blog/2017/01/09/disabling-usb-ports-on-linux/
    #
    # ... > sudo crontab -e
    #
    # disable builtin webcam
    # @reboot echo 0 > /sys/bus/usb/devices/2-8/bConfigurationValue
