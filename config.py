#!/usr/bin/python3

import grp
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
    npm_install,
    pip_install,
    print_message_and_done,
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
    openfortivpn
    """
)

# FIXME is this still relevant after ubuntu 22.04?
#
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
USERNAME = os.getlogin()
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
python_versions = [10]
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
PROFILE_FILE = Path(HOME, ".profile")
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


def install_nerd_font(base_font_name, font_filename):
    # install patched Hack nerd font (https://www.nerdfonts.com)
    # we install only
    custom_fonts_dir = "/usr/local/share/fonts/truetype/custom"
    run(f"sudo mkdir -p {custom_fonts_dir}")

    with temporary_ownership_of(custom_fonts_dir):
        done_for_the_first_time = install_from_github_release(
            "ryanoasis/nerd-fonts",
            f".*{base_font_name}.zip",
            custom_fonts_dir,
            font_filename,
        )
    if done_for_the_first_time:
        with print_message_and_done(f"Updating fonts"):
            run("sudo fc-cache -rsv", capture_output=True)


def install_neovim():
    NVIM_AUTOLOAD_DIR = Path("~/.local/share/nvim/site/autoload")
    if Path(NVIM_AUTOLOAD_DIR, "plug.vim").exists():
        return
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

    # install patched Hack font for ryanoasis/vim-devicons
    install_nerd_font("Hack", "Hack Regular Nerd Font Complete Mono.ttf")


install_neovim()

apt_install(
    """
    postgresql
    sqlite3
    libpq-dev                   # for psycopg

    graphviz libgraphviz-dev
    """
)


def install_ipython():
    pip_install("ipython")
    apt_install("python3-tk")  # for %paste in IPython


install_ipython()

# poetry
def install_poetry():
    poetry_home = f"{HOME}/.local/share/poetry"
    poetry_final = Path(poetry_home, "bin/poetry")
    if poetry_final.exists():
        return
    print("Installing poetry...")
    get_poetry = download(
        "https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py"
    )
    env = os.environ | {"POETRY_HOME": poetry_home}
    run(f"python3 {get_poetry} --yes", env=env, capture_output=True)
    symlink(Path(LOCAL_BIN_DIR, "poetry"), poetry_final)


install_poetry()

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
        if get_return_code("which node"):
            return 0  # not installed
        version = run("node --version", capture_output=True).stdout
        return int(version.lstrip("v").split(".")[0])

    if not added_to_sources or get_node_version() < version:
        node_setup_script = download(f"https://deb.nodesource.com/setup_{version}.x")
        run(f"sudo -E bash {node_setup_script}")
        apt_install("nodejs")


install_node(16)
npm_install("yarn")

# bitwarden cli
npm_install("@bitwarden/cli")


def install_git_trim():
    # https://github.com/foriequal0/git-trim
    install_from_github_release(
        "foriequal0/git-trim", ".*linux.*tgz$", LOCAL_BIN_DIR, "git-trim"
    )
    run("git config --global trim.bases develop,master")


install_git_trim()


def get_user_groups(username):
    return {g.gr_name for g in grp.getgrall() if username in g.gr_mem}


# TODO...
# docker compose V2
# https://docs.docker.com/compose/cli-command/
#
# sudo mkdir -p /usr/local/lib/docker/cli-plugins
# sudo curl -SL https://github.com/docker/compose/releases/download/v2.0.1/docker-compose-linux-x86_64 -o /usr/local/lib/docker/cli-plugins/docker-compose
# run docker without sudo


if "docker" not in get_user_groups(USERNAME):
    run(f"sudo adduser --quiet {USERNAME} docker")


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# desktop
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def install_spotify():
    if snap_install("spotify"):
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


VSCODE_EXTENSIONS = """
    vscodevim.vim
    dbaeumer.vscode-eslint
    esbenp.prettier-vscode
    EditorConfig.EditorConfig
"""


def install_vscode():
    download_and_install_deb(
        "https://code.visualstudio.com/sha/download?build=stable&os=linux-deb-x64",
        "code",
    )
    out = run("code --list-extensions", capture_output=True)
    installed_extensions = set(out.stdout.splitlines())
    extensions = set(splitlines(VSCODE_EXTENSIONS))
    for extension in extensions - installed_extensions:
        run(f"code --install-extension {extension}")


if "XDG_CURRENT_DESKTOP" in os.environ:
    apt_install(
        """
        terminator
        gnome-tweaks gnome-shell-extensions
        dconf-editor

        gimp imagemagick
        vlc mplayer audacity ffmpeg
        xournal pdfarranger
        libreoffice
        qbittorrent
        """
    )
    # XXX reenable extension when available for ubuntu 22.04
    # gnome-shell-extension-autohidetopbar

    # custom firefox appearance
    # FIXME firefox is ignoring this, as it seems from ubuntu 22.04 snap firefox
    [firefox_profile] = Path("~/snap/firefox/common/.mozilla/firefox").glob("*.default")
    symlink(Path(firefox_profile, "user.js"), Path(FILES, "firefox/user.js"))

    # make firefox the default browser on X
    run("xdg-settings set default-web-browser firefox_firefox.desktop")

    # install google chrome
    download_and_install_deb(
        "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb",
        "google-chrome-stable",
    )

    install_spotify()
    download_and_install_deb("https://zoom.us/client/latest/zoom_amd64.deb", "zoom")

    # banco do brasil
    download_and_install_deb(
        "https://cloud.gastecnologia.com.br/bb/downloads/ws/warsaw_setup64.deb",
        "warsaw",
    )

    # more desktop dev tools
    apt_install("gitk gitg meld")
    install_geckodriver()
    install_git_trim()
    snap_install("teams")
    install_vscode()

    # must come last (actually after all installs referred in gsettings)
    adjust_desktop()

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
