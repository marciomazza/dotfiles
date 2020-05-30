from pathlib import Path

from base import install, lineinfile, pip_install, run, splitlines

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

    gitg meld
    """
)

# Remove unnecessary hunspell english dicts
for dic in Path("/usr/share/hunspell").glob("en_*"):
    if "en_US" != dic.stem:
        run(f"sudo rm {dic}")

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# link home config files recursively
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
home = Path("~").expanduser()
base = Path("files/home").absolute()
for here in base.rglob("*"):
    athome = Path(home, here.relative_to(base))  # path relative to home
    if here.is_dir() and not here.is_symlink():
        athome.mkdir(exist_ok=True)
    else:
        if athome.is_symlink() or athome.exists():
            athome.unlink()
        athome.symlink_to(here)

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
