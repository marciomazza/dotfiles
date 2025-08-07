#!/bin/bash

# https://ohmyz.sh/#install

if [ ! -d "$HOME/.oh-my-zsh" ]; then
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
else
    echo "oh-my-zsh already exists at $HOME/.oh-my-zsh, skipping installation"
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
