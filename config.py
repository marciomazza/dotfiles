import os
import subprocess

from base import (Path,
                  apt_install,
                  download_and_install_deb,
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
    tree trash-cli xclip curl smbclient htop ncdu silversearcher-ag
    python3-pip terminator neovim

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
home = Path("~")
files_dir = Path("files").absolute()
files_home_dir = Path(files_dir, "home")
for here in files_home_dir.rglob("*"):
    athome = Path(home, here.relative_to(files_home_dir))  # path relative to home
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
# desktop
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def install_spotify():
    snap_install("spotify")
    template = Path(files_dir, "spotify_spotify.desktop.template").read_text()
    [icon] = Path("/snap/spotify").rglob("icons/spotify-linux-128.png")
    with temporary_ownership_of(
        "/var/lib/snapd/desktop/applications/spotify_spotify.desktop"
    ) as desktop_file:
        desktop_file.write_text(template.format(icon=icon))


def adjust_desktop():
    gsettings = [
        line.split(maxsplit=2) for line in splitlines(Path("gsettings").read_text())
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


if "XDG_CURRENT_DESKTOP" in os.environ:
    apt_install(
        """
        gnome-tweak-tool gnome-shell-extensions gnome-shell-pomodoro
        dconf-editor

        gimp imagemagick
        vlc mplayer audacity
        xournal

        gitg meld pgadmin3
        """
    )
    # custom firefox appearance
    [firefox_profile] = Path("~/.mozilla/firefox").glob("*.default-release")
    symlink(Path(firefox_profile, "user.js"), Path(files_dir, "firefox/user.js"))

    # install google chrome
    download_and_install_deb(
        "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb",
        "google-chrome-stable",
    )

    install_spotify()
    adjust_desktop()
    fix_cedilla_on_us_keyboard()
