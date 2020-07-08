#!/usr/bin/python3

import os
import re
import subprocess
import tarfile
from urllib.request import urljoin, urlopen

from base import (Path,
                  apt_install,
                  download,
                  download_and_install_deb,
                  is_not_dpkg_installed,
                  lineinfile,
                  pip_install,
                  run,
                  snap_install,
                  splitlines,
                  symlink,
                  temporary_ownership_of,)

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
        symlink(athome, here)

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# bash customizations
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
pip_install("cdiff")  # used in ~/.bash_customizations
# color promt, infinite history size and run .bash_customizations
for line in splitlines(
    """
        force_color_prompt=yes
        HISTSIZE=-1
        HISTFILESIZE=-1
        test -f ~/.bash_customizations && source ~/.bash_customizations
    """
):
    lineinfile("~/.bashrc", line)

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# development tools
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# neovim
NVIM_AUTOLOAD_DIR = "~/.local/share/nvim/site/autoload"
if not Path(NVIM_AUTOLOAD_DIR, "plug.vim").exists():
    apt_install(
        """
        neovim
        universal-ctags         # for majutsushi/tagbar
        """
    )
    download(
        "https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim",
        NVIM_AUTOLOAD_DIR,
    )

apt_install(
    """
    mysql-server mysql-client
    libmysqlclient-dev          # for MySQL-python
    postgresql
    python3-tk                  # for %paste in IPython
    libpq-dev                   # for psycopg

    graphviz libgraphviz-dev
    """
)

# add pt_BR locale
if "pt_BR.utf8" not in run("locale -a", capture_output=True).stdout.splitlines():
    run("sudo locale-gen pt_BR.UTF-8")

# install python versions 3.6 to 3.8
python_versions = " ".join(f"python3.{v} python3.{v}-dev" for v in [6, 7, 8])
if any(is_not_dpkg_installed(p) for p in python_versions.split()):
    run("sudo add-apt-repository ppa:deadsnakes/ppa --yes")
    run("sudo apt-get update")
    apt_install(python_versions)

pip_install("virtualenvwrapper")


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# desktop
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def install_spotify():
    snap_install("spotify")
    template = Path(FILES, "spotify_spotify.desktop.template").read_text()
    [icon] = Path("/snap/spotify").rglob("icons/spotify-linux-128.png")
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


def fix_cedilla_on_us_keyboard():
    with temporary_ownership_of(
        "/usr/lib/x86_64-linux-gnu/gtk-3.0/3.0.0/immodules.cache"
    ) as path:
        lineinfile(
            path,
            '"cedilla" "Cedilla" "gtk30" "/usr/share/locale" "az:ca:co:fr:gv:oc:pt:sq:tr:wa:en"',  # noqa
            '"cedilla" "Cedilla" "gtk30"',
        )
    with temporary_ownership_of("/usr/share/X11/locale/en_US.UTF-8/Compose") as path:
        path.write_text(path.read_text().replace("ć", "ç").replace("Ć", "Ç"))

    with temporary_ownership_of("/etc/environment") as path:
        for line in splitlines(
            """
            GTK_IM_MODULE=cedilla
            QT_IM_MODULE=cedilla
            """
        ):
            lineinfile(path, line)


def install_geckodriver():
    if Path("~/.local/bin/geckodriver").exists():
        return
    res = urlopen("https://github.com/mozilla/geckodriver/releases/latest")
    page_content = res.read().decode("utf-8")
    [download_path] = re.findall(
        "/mozilla/geckodriver/releases/download/.*/geckodriver-.*-linux64.tar.gz",
        page_content,
    )
    path = download(urljoin("https://github.com/", download_path), "~/.local/bin")
    tarfile.open(path).extractall(Path(HOME, ".local/bin"))


if "XDG_CURRENT_DESKTOP" in os.environ:
    apt_install(
        """
        terminator
        gnome-tweak-tool gnome-shell-extensions gnome-shell-pomodoro
        dconf-editor

        gimp imagemagick
        vlc mplayer audacity ffmpeg
        xournal
        libreoffice
        """
    )

    # custom firefox appearance
    [firefox_profile] = Path("~/.mozilla/firefox").glob("*.default-release")
    symlink(Path(firefox_profile, "user.js"), Path(FILES, "firefox/user.js"))

    # install google chrome
    download_and_install_deb(
        "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb",
        "google-chrome-stable",
    )

    install_spotify()
    adjust_desktop()
    fix_cedilla_on_us_keyboard()
    download_and_install_deb("https://zoom.us/client/latest/zoom_amd64.deb", "zoom")

    # banco do brasil
    download_and_install_deb(
        "https://cloud.gastecnologia.com.br/bb/downloads/ws/warsaw_setup64.deb",
        "warsaw",
    )

    # more desktop dev tools
    apt_install("gitg meld pgadmin3")
    install_geckodriver()
