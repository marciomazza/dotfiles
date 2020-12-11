from IPython import get_ipython
from prompt_toolkit.buffer import indent, unindent

ip = get_ipython()
kb = ip.pt_app.key_bindings


def _(func, key):
    @kb.add("escape", key)
    def _indent_unindent(event):
        buffer = event.current_buffer
        func(buffer, 0, buffer.document.line_count)


for func, key in ((indent, ">"), (unindent, "<")):
    _(func, key)
