#!/bin/bash

sudo pacman -S --noconfirm zsh
sudo chsh -s /usr/bin/zsh

# https://github.com/ohmyzsh/ohmyzsh?tab=readme-ov-file#manual-installation

unset GIT_DIR
unset GIT_WORK_TREE

OHMYZSH_DIR="$HOME/.oh-my-zsh"

if [ ! -d "$OHMYZSH_DIR" ]; then
    git clone https://github.com/ohmyzsh/ohmyzsh.git "$OHMYZSH_DIR"
else
    echo "oh-my-zsh already exists at $OHMYZSH_DIR, skipping installation"
fi

# Plugin remotes list
plugin_remotes=(
    "https://github.com/z-shell/F-Sy-H.git"
    "https://github.com/bobthecow/git-flow-completion"
    "https://github.com/paulirish/git-open.git"
    "https://github.com/zsh-users/zsh-autosuggestions"
    "https://github.com/zsh-users/zsh-completions"
)

# Clone plugins to custom plugins directory
echo "Cloning oh-my-zsh plugins..."
PLUGINS_DIR="$HOME/.oh-my-zsh/custom/plugins"

for url in "${plugin_remotes[@]}"; do
    plugin_name=$(basename "$url" .git)
    plugin_path="$PLUGINS_DIR/$plugin_name"
    if [ ! -d "$plugin_path" ]; then
        echo "Cloning $plugin_name from $url..."
        git clone "$url" "$plugin_path"
    else
        echo "$plugin_name already exists at $plugin_path, skipping clone"
    fi
done

echo "Plugin installation complete!"
