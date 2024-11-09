export PATH="/home/mazza/.cargo/bin:$PATH"

# Path to your oh-my-zsh installation.
export ZSH="$HOME/.oh-my-zsh"

# Set name of the theme to load --- if set to "random", it will
# load a random theme each time oh-my-zsh is loaded, in which case,
# to know which specific one was loaded, run: echo $RANDOM_THEME
# See https://github.com/ohmyzsh/ohmyzsh/wiki/Themes
ZSH_THEME="bira"

# Set list of themes to pick from when loading at random
# Setting this variable when ZSH_THEME=random will cause zsh to load
# a theme from this variable instead of looking in $ZSH/themes/
# If set to an empty array, this variable will have no effect.
# ZSH_THEME_RANDOM_CANDIDATES=( "robbyrussell" "agnoster" )

# Uncomment the following line to use case-sensitive completion.
# CASE_SENSITIVE="true"

# Uncomment the following line to use hyphen-insensitive completion.
# Case-sensitive completion must be off. _ and - will be interchangeable.
# HYPHEN_INSENSITIVE="true"

# Uncomment one of the following lines to change the auto-update behavior
# zstyle ':omz:update' mode disabled  # disable automatic updates
# zstyle ':omz:update' mode auto      # update automatically without asking
# zstyle ':omz:update' mode reminder  # just remind me to update when it's time

# Uncomment the following line to change how often to auto-update (in days).
# zstyle ':omz:update' frequency 13

# Uncomment the following line if pasting URLs and other text is messed up.
# DISABLE_MAGIC_FUNCTIONS="true"

# Uncomment the following line to disable colors in ls.
# DISABLE_LS_COLORS="true"

# Uncomment the following line to disable auto-setting terminal title.
# DISABLE_AUTO_TITLE="true"

# Uncomment the following line to enable command auto-correction.
# ENABLE_CORRECTION="true"

# Uncomment the following line to display red dots whilst waiting for completion.
# You can also set it to another string to have that shown instead of the default red dots.
# e.g. COMPLETION_WAITING_DOTS="%F{yellow}waiting...%f"
# Caution: this setting can cause issues with multiline prompts in zsh < 5.7.1 (see #5765)
# COMPLETION_WAITING_DOTS="true"

# Uncomment the following line if you want to disable marking untracked files
# under VCS as dirty. This makes repository status check for large repositories
# much, much faster.
# DISABLE_UNTRACKED_FILES_DIRTY="true"

# Uncomment the following line if you want to change the command execution time
# stamp shown in the history command output.
# You can set one of the optional three formats:
# "mm/dd/yyyy"|"dd.mm.yyyy"|"yyyy-mm-dd"
# or set a custom format using the strftime function format specifications,
# see 'man strftime' for details.
# HIST_STAMPS="mm/dd/yyyy"

# Would you like to use another custom folder than $ZSH/custom?
# ZSH_CUSTOM=/path/to/new-custom-folder

# Which plugins would you like to load?
# Standard plugins can be found in $ZSH/plugins/
# Custom plugins may be added to $ZSH_CUSTOM/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
# Add wisely, as too many plugins slow down shell startup.
DISABLE_VENV_CD=1
plugins=(git autojump virtualenv git-open poetry asdf F-Sy-H zsh-autosuggestions)
export _Z_DATA="$HOME/.data/z"

fpath+=${ZSH_CUSTOM:-${ZSH:-~/.oh-my-zsh}/custom}/plugins/zsh-completions/src
source $ZSH/oh-my-zsh.sh

# Theme customization
ZSH_THEME_VIRTUALENV_PREFIX="%F{red}"
ZSH_THEME_VIRTUALENV_SUFFIX="%f"
ZSH_AUTOSUGGEST_STRATEGY=(history completion)

# User configuration

# export MANPATH="/usr/local/man:$MANPATH"

# You may need to manually set your language environment
# export LANG=en_US.UTF-8

export EDITOR='vim'
export LESS="-SRXF"

[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh
# https://github.com/junegunn/fzf#respecting-gitignore
export FZF_DEFAULT_COMMAND='fdfind --type f --strip-cwd-prefix --hidden --follow --exclude .git'

# for plone
export RELOAD_PATH=src  # for sauna.reload
export PYCHARM_JDK=/usr/lib/jvm/java-11-openjdk-amd64  # for pycharm

# debug with ipdb
export PYTHONBREAKPOINT='IPython.terminal.debugger.set_trace'

function uv_venv_create() {
    # Create a unique venv name based on the initials of parent directories
    # and the current directory name
    local ancestors_initials=""
    for dir in $(pwd | sed "s|^$HOME/||" | tr '/' ' '); do
        ancestors_initials+="${dir:0:1}"
    done
    local venv_name="${ancestors_initials}-$(basename $(pwd))"
    # Create the venv if it doesn't exist
    local venv_dir="$HOME/.venvs/$venv_name"
    [[ ! -d "$venv_dir" ]] && uv venv "$venv_dir"
    # make a symlink .venv pointing to the actual one to satisfy uv
    # see https://github.com/astral-sh/uv/issues/1495
    ln -sfn "$venv_dir" .venv
    # finally activate
    source .venv/bin/activate
}
alias u=uv_venv_create
