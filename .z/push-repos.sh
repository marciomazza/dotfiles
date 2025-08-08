#!/bin/bash

echo "Pushing .z repository..."
git push

echo "Pushing nvim config repository..."
git -C /home/mazza/.config/nvim push

echo "Done!"