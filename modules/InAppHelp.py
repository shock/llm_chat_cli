IN_APP_HELP = """Available commands:

    /help                     Show this message.
    /clear                    Clear the terminal screen.
    /reset                    Clear the context and start a new chat.
    /save [FILENAME]          Save the chat history to a file.  If no filename is provided, you will be prompted for one.
    /load [FILENAME]          Load the chat history from a file.  If no filename is provided, you will be prompted for one.
    /print                    Print the entire chat history.
    /sp [PROMPT]              Display and optionally edit the system prompt.
    /config                   Display the current configuration.
    /exit or CTRL+C           Exit the chat interface.
    /md                       Export the chat history to a Markdown file and copy it to the clipboard.
    /cb                       List and select code blocks in the last assistant response.

    shift-up arrow            move to previous user message for chat continuation
    shift-down arrow          move to next user message for chat continuation
    alt-enter                 insert a newline in the chat input buffer at the cursor
    enter                     send the chat input buffer to the LLM and display the response
    ctrl-shift-up arrow       seek to the previous assistant response
    ctrl-shift-down arrow     seek to the next assistant response
    ctrl-b                    copy the current user prompt input buffer to the clipboard
    ctrl-l                    copy the last llm response to the clipboard

"""
