c = get_config()  # noqa
c.InteractiveShell.autocall = 2
c.InteractiveShell.logstart = True
c.InteractiveShellApp.extensions = ["autoreload"]
c.PlainTextFormatter.max_width = 160
c.InteractiveShellApp.exec_lines = [
    "%autoreload 2",
    # load extensions ignoring absent ones
    """
for ext in ["ipython_autoimport", "pprintpp"]:
    try:
        get_ipython().run_line_magic("load_ext", ext)
    except ImportError: pass
""",
]
# c.TerminalInteractiveShell.editing_mode = "vi"

# FIXME would like to use the black autoformatter, but it bugs autocall
c.InteractiveShell.autoformatter = None
