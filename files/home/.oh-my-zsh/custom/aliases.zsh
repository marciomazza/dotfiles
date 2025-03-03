# aliases and helper functions

alias x=trash-put
alias vim=nvim
alias e=nvim
alias s=gsb

DIFF_EXCLUDES='":(exclude)**/uv.lock" ":(exclude)**/package-lock.json"'
alias d="git diff -w $DIFF_EXCLUDES"
alias di="git diff -w --cached $DIFF_EXCLUDES"
alias dd="git difftool --no-prompt -- $DIFF_EXCLUDES"
alias ddi="git difftool --no-prompt --cached -- $DIFF_EXCLUDES"

alias lo=glods
alias lol=glola
alias amend=gc!
alias w=workon
alias pz="pwd | tr -d '[:space:]' | xclip -selection c"
alias cp='cp -a -v'
alias fd=fdfind
alias vd="nvim -d"
alias gh="git open"
alias z='cd ..'
alias zz='cd ../..'
alias zzz='cd ../../..'
alias zzzz='cd ../../../..'
alias zzzzz='cd ../../../../..'
alias ls="eza --icons --git --ignore-glob='.git|node_modules|__pycache__|*.pyc|*.pyo|*.o|*.swp|*.swo|*.swx|*.swpx'" # list
alias ll="ls -l"
alias t="ls --tree"
alias p=pytest


a ()
{
    if [ $# -eq 0 ]; then
        git add .
    else
        git add "$@"
    fi
}

c ()
{
    if [ $# -eq 0 ]; then
        git commit
    else
        msg=$(echo "$*" | sed 's/.*/\u&/')
        len_line_1=$(echo "$*" | sed -n 1p | tr -d '\n' | wc -m)
        len_line_2=$(echo "$*" | sed -n 2p | tr -d '\n' | wc -m)
        max_len=$(echo "$*" | wc --max-line-length)
        if [ $len_line_1 -gt 50 -o $len_line_2 -gt 0 -o $max_len -gt 72 ]; then
            git commit -m "$msg" -e
        else
            git commit -m "$msg"
        fi
    fi
}

i ()
# use either IPython or django extensions shell_plus
{
    if test -f "manage.py"; then
        ./manage.py shell_plus
    else
        ipython
    fi
}

fz ()
{
    readlink -f "$*" | tr -d '[:space:]' | xclip -selection c
}
