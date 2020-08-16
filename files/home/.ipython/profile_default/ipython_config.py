c = get_config()  # noqa
c.InteractiveShell.autocall = 2
c.InteractiveShell.logstart = True
c.InteractiveShellApp.extensions = ["autoreload"]
c.InteractiveShellApp.exec_lines = ["%autoreload 2"]
c.PlainTextFormatter.max_width = 110
