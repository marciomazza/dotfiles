from IPython import get_ipython

ip = get_ipython()
kb = ip.pt_app.key_bindings


MATCHING_PAIRS = (("'", "'"), ('"', '"'), ("(", ")"), ("[", "]"), ("{", "}"))


def just_inserted_matching_pair(document):
    return (document.char_before_cursor, document.current_char) in MATCHING_PAIRS


def register_autopair(ini, end):
    @kb.add(ini)
    def _(event):
        buffer = event.current_buffer
        buffer.insert_text(ini)
        buffer.insert_text(end, move_cursor=False)

    if ini != end:
        # for different opening and closing characters,
        #
        # if we just typed the opening character and yet type the closing one
        # since the closing one was just auto inserted
        # do not insert it again
        @kb.add(end)
        def _(event):
            buffer = event.current_buffer
            if not just_inserted_matching_pair(buffer.document):
                buffer.insert_text(end)


for ini, end in MATCHING_PAIRS:
    register_autopair(ini, end)


# if we just typed the opening character and hit backspace
# then both characters are deleted
@kb.add("c-h")
def _(event):
    buffer = event.current_buffer
    if just_inserted_matching_pair(buffer.document):
        buffer.delete()  # delete current character: the closing one
    buffer.delete_before_cursor()
