IN_APP_HELP = """Chat Commands:

Basic Controls:
    /help (/h)                Show this help message
    /clear (/c)               Clear the terminal screen
    /exit (/e, /q)            Exit the chat interface

Chat History:
    /reset (/r)               Clear chat history and start fresh
    /print (/p)               Show entire chat history
    /save (/s) [FILENAME]     Save chat history to file
    /load (/l) [FILENAME]     Load chat history from file
    /clear_history (/ch)      Clear saved chat history

Model Configuration:
    /mod [MODEL]              Switch to specified model
    /dm                       Reset to default model
    /config (/con)            Show current configuration

Content Management:
    /sp                       Edit system prompt
    /cb                       Work with code blocks in last response
    /md                       Export chat to Markdown

Keyboard Shortcuts:
    shift-up/down             Navigate previous/next user message
    ctrl-shift-up/down        Navigate previous/next assistant response
    alt-enter                 Insert newline in input
    ctrl-b                    Copy current input to clipboard
    ctrl-l                    Copy last response to clipboard
"""
