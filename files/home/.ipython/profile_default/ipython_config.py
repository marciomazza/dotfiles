c = get_config()  # noqa
c.InteractiveShell.autocall = 2
c.InteractiveShell.logstart = True
c.InteractiveShellApp.extensions = ["autoreload"]
c.InteractiveShellApp.exec_lines = ["%autoreload 2"]
c.PlainTextFormatter.max_width = 110

# workaround for tab not working with autocall
#   ex.: len so<TAB> => len sorted
#   https://github.com/ipython/ipython/issues/11530
#   https://github.com/ipython/ipython/issues/10926
c.Completer.use_jedi = False
