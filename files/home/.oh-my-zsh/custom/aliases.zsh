alias x=trash-put
alias e=nvim
alias s=gsb
alias d='gd ":(exclude)poetry.lock"'
alias di='gdca ":(exclude)poetry.lock"'
alias lo=glods
alias amend=gc!

a ()
{
    if [ $# -eq 0 ]; then
        git add .
    else
        git add "$@"
    fi
}

t ()
{
	level=${1:-3}
	clear; tree -a -L $level -I '.git|__pycache__|ipython_log\.py\.*~|zz*' --gitignore
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
