BASE_DIR=$HOME/.z
mkdir -p $BASE_DIR
git clone --bare git@github.com:marciomazza/dotfiles.git $BASE_DIR/.dotfiles.git
export GIT_DIR=$BASE_DIR/.dotfiles.git GIT_WORK_TREE=$HOME
git checkout -f
git config --local include.path ../.gitconfig
./config.py
if [ ! -d $HOME/.config/nvim ]; then
    git clone git@github.com:marciomazza/neovim_config.git $HOME/.config/nvim
fi
