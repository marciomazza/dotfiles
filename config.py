import os

from base import (Path,
                  download_and_install_deb,
                  install,
                  lineinfile,
                  pip_install,
                  run,
                  splitlines,
                  symlink,)

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# basic
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
install("git etckeeper")
if not Path("/etc/.git").exists():
    run("etckeeper commit 'first commit'")

install(
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
if "XDG_CURRENT_DESKTOP" in os.environ:
    install(
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
