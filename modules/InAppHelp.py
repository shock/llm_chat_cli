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
    /clear_history (/ch)      Clear saved input history

Model Configuration:
    /mod [MODEL]              Switch to specified model.  Leave [MODEL] blank to list available models
    /dm                       Reset to default model
    /config (/con)            Show current configuration

Content Management:
    /sp                       Edit system prompt
    /cb                       Work with code blocks in last response
    /md                       Export chat to Markdown

Keyboard Shortcuts:
    up/down                   Navigate previous/next user input from history across all chats
    shift-up/down             Navigate previous/next user input message in current chat
    ctrl-shift-up/down        Navigate previous/next assistant response
    shift-alt-n               Clear chat history and start fresh (same as /r)
    alt-enter or ctrl-o       Submit current input buffer
    enter                     Newline in input
    ctrl-b                    Copy current input buffer to clipboard
    ctrl-l                    Copy last assistant response to clipboard
    ctrl-d                    Exit the chat interface
"""
