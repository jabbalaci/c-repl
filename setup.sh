#!/usr/bin/env bash

# tested under Linux Mint
# it should also work on Debian-based distros

sudo apt install pipx
pipx install uv
# pipx upgrade-all

export PATH=$PATH:$HOME/.local/bin

sudo apt install gcc
sudo apt install clang-format
sudo apt install bat
sudo apt install micro
sudo apt install valgrind

echo "Done. Start the C REPL with ./start.sh"
