#!/usr/bin/python3

import subprocess

from base import (
    Path,
    apt_add_ppa,
    apt_install,
    cmd_output,
    cmd_works,
    download_and_install_deb,
    install,
    install_from_github_release,
    lineinfile,
    mkdir,
    npm_install,
    print_message_and_done,
    run,
    symlink,
    wait_for_condition,
)

# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# link home config files recursively
# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
files_home_dir = Path("files/home").absolute()
for here in files_home_dir.rglob("*"):
    athome = Path.home() / here.relative_to(files_home_dir)  # path relative to home
    if here.is_dir() and not here.is_symlink():
        mkdir(athome)
    else:
        if here.name != ".gitkeep":  # skip directory holders
            symlink(athome, here)


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# basic
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
apt_install(Path("apt_packages").read_text())

# zsh
if cmd_output("echo $SHELL") != "/usr/bin/zsh":
    run("sudo chsh -s /bin/zsh")


def command_not_available(name):
    return not cmd_works(f"which {command_name}")


# install some stuf with bash scripts
for script in Path("install").glob("*.sh"):
    command_name = script.stem
    if command_not_available(command_name):
        with print_message_and_done(f"Installing {command_name}"):
            # work on /tmp for downloads not to polute this dir
            run(str(script.absolute()), cwd="/tmp", capture_output=True)


# nodejs
def install_node():
    # install nvm more or less like
    # https://nodejs.org/en/download/package-manager
    nvm_repo = "https://github.com/nvm-sh/nvm.git"
    nvm_dir = Path.home() / ".nvm"
    if nvm_dir.exists():
        run("git pull", cwd=nvm_dir)
    else:
        run(f"git clone {nvm_repo} /tmp/{nvm_dir}")
    run("nvm install node", executable="/bin/zsh")


if command_not_available("node"):
    install_node()

npm_install("yarn")
npm_install("@bitwarden/cli")  # bitwarden cli


# https://github.com/foriequal0/git-trim
install_from_github_release(
    "foriequal0/git-trim", ".*linux.*tgz$", Path.home() / ".local/bin", "git-trim"
)

# python
if install("basic", "uv", "curl -LsSf https://astral.sh/uv/install.sh | sh"):
    install(
        "uv",
        "ruff isort ipython djlint poetry",
        "uv tool install --force {}",
        lambda _: False,
    )


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# extra development tools
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def install_nerd_font(base_font_name):
    # install patched Hack nerd font (https://www.nerdfonts.com)
    custom_fonts_dir = mkdir(Path.home() / ".local/share/fonts")
    done_for_the_first_time = install_from_github_release(
        "ryanoasis/nerd-fonts",
        f".*{base_font_name}.zip",
        custom_fonts_dir,
        "*.ttf",
        update=True,
    )
    if done_for_the_first_time:
        with print_message_and_done("Updating fonts"):
            run("sudo fc-cache -rsv", capture_output=True)


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


# <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# desktop
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


FILES = Path("files").absolute()


def sudo_cp(origin_dir, dest_dir):
    files = [p for p in origin_dir.glob("**/*") if p.is_file()]
    if not all(
        cmd_works(f"diff {p} {dest_dir}/{p.relative_to(origin_dir.parent)}")
        for p in files
    ):
        run(f"sudo cp -rf {FILES}/firefox/apt /etc")


def install_firefox():
    # remove snap that is the default on ubuntu 22.04
    # based on https://www.omgubuntu.co.uk/2022/04/how-to-install-firefox-deb-apt-ubuntu-22-04

    if cmd_works("snap list firefox"):
        run("sudo snap remove --purge firefox")
    apt_add_ppa("mozillateam")
    # configure apt to prioritize PPA and do automatic updates
    sudo_cp(FILES / "firefox/apt", "/etc")
    apt_install("firefox")

    config_dir = Path.home() / ".mozilla/firefox"

    # trigger the the creation the initial config that includes the default profile
    process = subprocess.Popen(["firefox", "--headless"])
    wait_for_condition(config_dir.exists)
    process.terminate()

    # custom firefox appearance
    [firefox_profile] = config_dir.glob("*.default-release")
    symlink(firefox_profile / "user.js", FILES / "firefox/user.js")

    # make firefox the default browser on X
    run("xdg-settings set default-web-browser firefox.desktop")


# if "XDG_CURRENT_DESKTOP" in os.environ:
def temp_not_using_______________________________():
    install_firefox()

    # install google chrome
    download_and_install_deb(
        "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb",
        "google-chrome-stable",
    )

    download_and_install_deb("https://zoom.us/client/latest/zoom_amd64.deb", "zoom")

    # banco do brasil
    download_and_install_deb(
        "https://cloud.gastecnologia.com.br/bb/downloads/ws/warsaw_setup64.deb",
        "warsaw",
    )

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
