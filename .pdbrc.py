import pdb


class Config(pdb.DefaultConfig):
    sticky_by_default = True


def _pdbrc_init():
    # Save history across sessions
    import readline
    from pathlib import Path

    histfile = Path("~/.pdb-pyhist").expanduser()
    try:
        readline.read_history_file(histfile)
    except IOError:
        pass
    import atexit

    atexit.register(readline.write_history_file, histfile)
    readline.set_history_length(1000)


_pdbrc_init()
del _pdbrc_init
