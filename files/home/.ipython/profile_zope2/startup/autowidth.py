import shutil
import sys
import types

import IPython

try:
    import numpy as np
except ImportError:
    pass


def update_terminal_width(*ignored):
    """Resize the IPython and numpy printing width to match the terminal.
    (based on https://stackoverflow.com/a/40623958/1877490)
    """
    w, h = shutil.get_terminal_size()
    config = IPython.get_ipython().config
    config.PlainTextFormatter.max_width = w - 1
    shell = IPython.core.interactiveshell.InteractiveShell.instance()
    shell.init_display_formatter()

    if 'numpy' in sys.modules:
        import numpy as np
        np.set_printoptions(linewidth=w - 5)


# do update at startup
update_terminal_width()

# monkey patch prompt toolkit event loop to run the update on terminal resize
eventloop = IPython.get_ipython().pt_cli.eventloop
eventloop._original_received_winch = eventloop.received_winch


def received_winch_patch(self):
    self.call_from_executor(update_terminal_width)
    self._original_received_winch()


eventloop.received_winch = types.MethodType(received_winch_patch, eventloop)
