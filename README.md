# dotfiles

My personal laptop configuration based on Ubuntu 20.04 in hacky and simple `python`.

The main parts are:

**config.py**<br/>
My specific installation.

**base.py**<br/>
A set of reusable installation primitives.

**files/home**<br/>
A tree structure that mirrors the relevant config files in home

**nvim**<br/>
A submodule with my neovim configuration that lives in https://github.com/marciomazza/neovim

That's basically it.

## Installation

Beware this is a very specific and personal configuration.
Use it as an example if you wish.

```bash
git checkout git@github.com:marciomazza/dotfiles.git
cd dotfiles
python3 config.py
```
