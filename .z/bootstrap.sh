mkdir -p ~/.z
git clone --bare git@github.com:marciomazza/dotfiles.git ~/.z/.dotfiles.git
export GIT_DIR=/home/mazza/.z/.dotfiles.git GIT_WORK_TREE=/home/mazza
git config --local include.path ../.gitconfig
git checkout -f
./config.py
if [ ! -d ~/.config/nvim ]; then
    git clone git@github.com:marciomazza/neovim_config.git ~/.config/nvim
fi
