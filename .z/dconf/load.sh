#!/bin/bash
[ -f "data/media-keys.dconf" ] && dconf load /org/gnome/settings-daemon/plugins/media-keys/ < "data/media-keys.dconf"
[ -f "data/input-sources.dconf" ] && dconf load /org/gnome/desktop/input-sources/ < "data/input-sources.dconf"
[ -f "data/wm.dconf" ] && dconf load /org/gnome/desktop/wm/ < "data/wm.dconf"
[ -f "data/shell.dconf" ] && dconf load /org/gnome/shell/ < "data/shell.dconf"
[ -f "data/mutter.dconf" ] && dconf load /org/gnome/mutter/ < "data/mutter.dconf"
