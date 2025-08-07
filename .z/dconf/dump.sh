#!/bin/bash
dconf dump /org/gnome/settings-daemon/plugins/media-keys/ > "data/media-keys.dconf"
dconf dump /org/gnome/desktop/input-sources/ > "data/input-sources.dconf"
dconf dump /org/gnome/desktop/wm/ > "data/wm.dconf"
dconf dump /org/gnome/shell/ > "data/shell.dconf"
dconf dump /org/gnome/mutter/ > "data/mutter.dconf"
