import IPython
from IPython import get_ipython
from prompt_toolkit.buffer import indent, unindent

if int(IPython.__version__.split(".")[0]) > 5:
    ip = get_ipython()
    kb = ip.pt_app.key_bindings

    def _register(func, key):
        @kb.add("escape", key)
        def _indent_unindent(event):
            buffer = event.current_buffer
            func(buffer, 0, buffer.document.line_count)

    def _do_register():
        for func, key in ((indent, ">"), (unindent, "<")):
            _register(func, key)

    # run like this to avoid binding variables here
    _do_register()
