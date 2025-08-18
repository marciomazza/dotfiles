#!/bin/bash

yay -S --noconfirm $(cat "$(dirname "$0")/packages")
