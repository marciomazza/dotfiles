#!/bin/bash

# https://nodejs.org/en/download

if [ ! -d "$HOME/.nvm" ]; then
  git clone https://github.com/nvm-sh/nvm.git "$HOME/.nvm"
fi
\. "$HOME/.nvm/nvm.sh"
nvm install 22
corepack enable yarn
