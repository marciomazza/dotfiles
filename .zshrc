export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/opt/nvim-linux-x86_64/bin:$PATH"
export SHELL=$(which zsh)
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="bira"
DISABLE_VENV_CD=1
plugins=(git virtualenv git-open F-Sy-H zsh-autosuggestions git-flow-completion)
export _Z_DATA="$HOME/.data/z"
fpath+=${ZSH_CUSTOM:-${ZSH:-~/.oh-my-zsh}/custom}/plugins/zsh-completions/src

source $ZSH/oh-my-zsh.sh

# Theme customization
ZSH_THEME_VIRTUALENV_PREFIX="%F{red}"
ZSH_THEME_VIRTUALENV_SUFFIX="%f"
ZSH_AUTOSUGGEST_STRATEGY=(history completion)

# User configuration
source ~/.zsh/aliases.zsh
export EDITOR='nvim'
export LESS="-SRXF"

[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh
# https://github.com/junegunn/fzf#respecting-gitignore
export FZF_DEFAULT_COMMAND='fdfind --type f --strip-cwd-prefix --hidden --follow --exclude .git'

# for plone
export RELOAD_PATH=src  # for sauna.reload
export PYCHARM_JDK=/usr/lib/jvm/java-11-openjdk-amd64  # for pycharm

# debug with IPython
export PYTHONBREAKPOINT='IPython.terminal.debugger.set_trace'
export PYTEST_ADDOPTS="--pdbcls=IPython.terminal.debugger:Pdb"

function uv_venv_create() {
    # Create a unique venv name based on the initials of parent directories
    # and the current directory name
    local ancestors_initials=""
    for dir in $(dirname `pwd` | sed "s|^$HOME/||" | tr '/' ' '); do
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

function bwcopy() {
  export NODE_NO_WARNINGS=1
  if ! bw sync --session "$BW_SESSION" --quiet >/dev/null 2>&1; then
    export BW_SESSION=$(bw unlock --raw)
  fi
  bw get password "$1" --session "$BW_SESSION" | xclip -selection clipboard
}

eval "$(mise activate zsh)"
eval "$(zoxide init --cmd=j zsh)"

# SSH key management - load on demand
alias loadkey='eval $(keychain --eval --quiet ~/.ssh/id_rsa)'
