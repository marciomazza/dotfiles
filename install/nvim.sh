# https://github.com/neovim/neovim/blob/master/INSTALL.md#linux

curl -LO https://github.com/neovim/neovim/releases/latest/download/nvim-linux64.tar.gz
sudo rm -rf /opt/nvim
sudo tar -C /opt -xzf nvim-linux64.tar.gz

# for preservim/tagbar
sudo apt install universal-ctags
