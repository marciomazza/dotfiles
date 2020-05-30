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
                  symlink,)

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
    [icon] = Path("/snap/spotify").rglob("icons/spotify-linux-128.png")
    template = Path(files_dir, "spotify_spotify.desktop.template")
    desktop_file = Path("/tmp/spotify_spotify.desktop")
    desktop_file.write_text(template.read_text().format(icon=icon))
    desktop_file.chmod(0o555)  # read and write for all
    desktop_final_path = "/var/lib/snapd/desktop/applications/spotify_spotify.desktop"
    run(f"sudo mv {desktop_file} {desktop_final_path}")
    run(f"sudo chown root: {desktop_final_path}")


def adjust_desktop():
    gsettings = [
        line.split(maxsplit=2) for line in splitlines(Path("gsettings").read_text())
    ]
    for schema, key, value in gsettings:
        subprocess.check_call(["gsettings", "set", schema, key, value])


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
