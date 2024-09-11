#!/usr/bin/env python

VERSION = "1.3.1"

"""
llm_api_chat.py - A command-line interface for interacting with the OpenAI GPT-4 model.

Author: Bill Doughty
Date: 2024-09-10

This script provides a chat interface that allows users to communicate with the OpenAI GPT-4 model
through a command-line interface. It supports loading and saving chat history, handling commands,
and highlighting code blocks within the chat responses.

Usage:
    python llm_api_chat.py [options]

Command-line options:
    -p, --prompt TEXT         Initial prompt for the chat.
    -s, --system-prompt TEXT  System prompt for the chat.
    -f, --history-file FILE   File to restore chat history from.
    -m, --model TEXT          Model to use for the chat.
    -v, --version             Show the version and exit.
    -c, --clear               Clear the terminal screen.
    -h, --help                Show the command-line help message.

Environment Variables:
    OPENAI_API_KEY            Your OpenAI API key.  (required)
    LLMC_DEFAULT_MODEL        Model to use if not specified in the command line. (optional)
                              Default is "gpt-4o-mini-2024-07-18"
    LLMC_SYSTEM_PROMPT        System prompt to use if not specified in the command line. (optional)
                              Default is "You're name is Lemmy. You are a helpful assistant that answers questions based on the provided context."
"""

# MARK: IN_APP_HELP
IN_APP_HELP = """In-chat commands:

    /help                     Show this message.
    /clear                    Clear the terminal screen.
    /reset                    Clear the context and start a new chat.
    /save [FILENAME]          Save the chat history to a file.  If no filename is provided, you will be prompted for one.
    /load [FILENAME]          Load the chat history from a file.  If no filename is provided, you will be prompted for one.
    /print                    Print the entirechat history.
    /sp [PROMPT]              Display and optionally edit the system prompt.
    /exit or CTRL+C           Exit the chat interface.

    shift-up arrow            move to previous user message for chat continuation
    shift-down arrow          move to next user message for chat continuation
    alt-enter                 insert a newline in the chat input buffer at the cursor
    enter                     send the chat input buffer to the LLM and display the response
    ctrl-shift-up arrow       seek to the previous assistant response
    ctrl-shift-down arrow     seek to the next assistant response
    ctrl-b                    copy the current user prompt input buffer to the clipboard
    ctrl-l                    copy the last llm response to the clipboard

"""

USER_NAME = "brother with a lowercase b"
DEFAULT_SYSTEM_PROMPT = f"""You're name is Lemmy.
You are a helpful assistant that answers questions factuallybased on the provided context.
Call the user {USER_NAME}.  If the user seems confused or entering
jibberish or incomplete messages, tell them so, and then tell them to "type /help for a list of commands"
"""

import os
import time
import sys
import requests
import argparse
import json
import re
from prompt_toolkit import PromptSession, prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML, FormattedText
from prompt_toolkit import print_formatted_text
from prompt_toolkit.filters import Condition
import pyperclip
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import TerminalFormatter
from pygments.util import ClassNotFound
from pygments.style import Style as PygmentsStyle
from pygments.token import Token
import re

# MARK: CodeHighlighter
class CodeHighlighter:

    def __init__(self, style=TerminalFormatter):
        self.style = style

    def highlight_code(self, code, language=None):
        """Helper method to highlight code using Pygments."""
        lexer = get_lexer_by_name('text', stripall=True)
        if language:
            try:
                lexer = get_lexer_by_name(language, stripall=True)
            except ClassNotFound:
                pass
        formatter = TerminalFormatter(style=self.style)
        highlighted_code = highlight(code, lexer, formatter)
        return highlighted_code


# MARK: CodeBlockHelper
class CodeBlockHelper:
    def __init__(self, message, style=TerminalFormatter):
        self.message = message
        self.code_blocks = self._extract_code_blocks()
        self.code_block_highlighter = CodeHighlighter(style=style)
        self.highlighted_code_blocks = self._highlighted_code_blocks()
        self.highlighted_message = self._highlighted_message()

    def _extract_code_blocks(self):
        """Extract all code blocks from the message."""
        code_block_pattern = re.compile(r'```\s*(?P<language>\w+)?\n(?P<code>.*?\n)[ ]*```', re.DOTALL)
        return code_block_pattern.findall(self.message)

    def _highlighted_code_blocks(self):
        """Return a list of highlighted code blocks."""
        return [self.code_block_highlighter.highlight_code(code, language) for language, code in self.code_blocks]

    def _highlighted_message(self):
        """Return a message replacing original code blocks with highlighted code blocks."""
        highlighted_message = self.message
        for i, (language, code) in enumerate(self.code_blocks):
            highlighted_message = highlighted_message.replace(code, self.highlighted_code_blocks[i])
        return highlighted_message

    def list_code_blocks(self):
        """List all code blocks with their indices."""
        for i, (language, code) in enumerate(self.code_blocks):
            print()
            print(f"{i+1} :")
            # print(f"[{i}] Language: {language if language else 'None'}")
            # print(f"{language} ({i}) {"-" * (40 - len(str(language)) - len(str(i)) - 4)}\n")
            print(f"```{language}")
            print(self.code_block_highlighter.highlight_code(code, language))
            # print("-" * 40)
            print('```\n')

    def select_code_block(self):
        """Select a code block by its index."""
        self.list_code_blocks()
        try:
            index = int(input("Enter the index of the code block you want to copy: "))
            while True:
                if 0 < index <= len(self.code_blocks):
                    _, code = self.code_blocks[index-1]
                    return code
                else:
                    self.list_code_blocks()
                    index = int(input(f"Invalid index. Please select a valid index (1-{len(self.code_blocks)}): "))
        except KeyboardInterrupt:
            print("Aborting...")
            return None

########################################################
# Extension for prompt_toolkit.FileHistory

# MARK: CustomFileHistory
class CustomFileHistory(FileHistory):
    """
    :class:`.FileHistory` class that limits the number of history entries.
    """

    def __init__(self, filename: str, max_history: int = None, skip_prefixes: list[str] = []) -> None:
        super().__init__(filename)
        self.max_history = max_history
        self.skip_prefixes = skip_prefixes

    def append_string(self, string: str) -> None:
        if any(string.startswith(prefix) for prefix in self.skip_prefixes):
            return
        super().append_string(string)
        if self.max_history and len(self._loaded_strings) > self.max_history:
            self._loaded_strings.pop()
            self._truncate_file()

    def _truncate_file(self) -> None:
        """
        Truncate the file to remove the oldest entry.
        """
        with open(self.filename, "rb") as f:
            lines = f.readlines()

        # Find the position of the last entry to keep.
        count = 0
        pos = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].startswith(b"+"):
                count += 1
                if count == self.max_history:
                    pos = i
                    break

        # Write back the truncated file.
        with open(self.filename, "wb") as f:
            f.writelines(lines[:pos])

    def clear_history(self):
        """Clear the history file."""
        with open(self.filename, "w") as f:
            f.write("") # clear the file
        self._loaded_strings = []

########################################################
# MARK: MessageHistory
class MessageHistory:
    """Class to manage the chat message history."""

    def __init__(self, system_prompt=None):
        """Initialize the message history with an optional system prompt."""
        self.user_indexes = []
        if not system_prompt:
            raise ValueError("System prompt is required")
        self.history = []
        self.add_message("system", system_prompt)

    def system_prompt(self, system_prompt=None):
        """Set or get the system prompt."""
        if system_prompt:
            self.history[0]['content'] = system_prompt
        return self.history[0]['content']

    def update_indexes(self):
        """Update the list of user and assistant message indexes."""
        self.update_user_indexes()
        self.update_assistant_indexes()

    def update_user_indexes(self):
        """Update the list of user message indexes."""
        self.user_indexes = []
        self.user_message_index = 0
        for i, msg in enumerate(self.history):
            if msg['role'] == 'user':
                self.user_message_index += 1
                self.user_indexes.append(i)

    def update_assistant_indexes(self):
        """Update the list of assistant message indexes."""
        self.assistant_indexes = []
        self.assistant_message_index = -1
        for i, msg in enumerate(self.history):
            if msg['role'] == 'assistant':
                self.assistant_message_index += 1
                self.assistant_indexes.append(i)

    def add_message(self, role, content):
        """Add a message to the history."""
        self.history.append({"role": role, "content": content})
        self.update_indexes()

    def get_history(self):
        """Return the current message history."""
        return self.history

    def clear_history(self):
        """Clear the message history."""
        # keep the system prompt
        self.history = [self.history[0]]
        self.update_indexes()

    def in_seek_user(self):
        """Check if the history is currently seeking."""
        return (self.user_message_index < len(self.user_indexes))

    def in_seek_assistant(self):
        """Check if the history is currently seeking."""
        return (self.assistant_message_index < len(self.assistant_indexes)-1)

    def session_active(self):
        """Check if the session is active."""
        return len(self.user_indexes) > 0

    def seek_previous_user_message(self):
        """Seek to the previous user message."""
        if self.user_message_index > 0:
            self.user_message_index -= 1
        if self.in_seek_user():
            return self.history[self.user_indexes[self.user_message_index]]
        else:
            return None

    def seek_next_user_message(self):
        """Seek to the next user message."""
        if self.in_seek_user():
            self.user_message_index += 1
        if self.in_seek_user():
            return self.history[self.user_indexes[self.user_message_index]]
        else:
            return None

    def seek_previous_assistant_message(self):
        """Seek to the previous assistant message."""
        if self.assistant_message_index > 0:
            self.assistant_message_index -= 1
        if self.in_seek_assistant():
            return self.history[self.assistant_indexes[self.assistant_message_index]]
        else:
            return None

    def seek_next_assistant_message(self):
        """Seek to the next assistant message."""
        if self.in_seek_assistant():
            self.assistant_message_index += 1
            if self.in_seek_assistant():
                return self.history[self.assistant_indexes[self.assistant_message_index]]
        else:
            return None

    def get_last_assistant_message(self):
        """Get the current assistant message."""
        if self.in_seek_assistant():
            return self.history[self.assistant_indexes[self.assistant_message_index]]
        elif len(self.assistant_indexes) > 0:
            return self.history[self.assistant_indexes[-1]]
        else:
            return None

    def update_user_message(self, message):
        """Update the user message at the current seek index and truncate the following messages."""
        index = self.user_indexes[self.user_message_index]
        self.history = self.history[:index]
        self.add_message("user", message)

    def save_history(self, filename):
        """Save the message history to a file."""
        try:
            with open(filename, 'w') as f:
                json.dump(self.history, f, indent=4)
            print(f"Chat history saved to `{filename}`.")
            return True
        except Exception as e:
            print(f"Error: Failed to save history to `{filename}`: {e}")
            return False

    def load_history(self, filename):
        """Load the message history from a file."""
        try:
            with open(filename, 'r') as f:
                self.history = json.load(f)
            self.update_indexes()
            print(f"Chat history loaded from `{filename}`.")
            return True
        except Exception as e:
            print(f"Error: Failed to load history from `{filename}`: {e}")
            return False


# MARK: OpenAIApi
class OpenAIApi:
    """Class to interact with the OpenAI API."""
    def __init__(self, api_key, model="gpt-4o-mini-2024-07-18", system_prompt=DEFAULT_SYSTEM_PROMPT):
        """Initialize the OpenAI API with an API key, model, and system prompt."""
        self.api_key = api_key
        self.model = model
        self.system_prompt = system_prompt

    def set_model(self, model):
        """Set the model to be used."""
        self.model = model

    def set_system_prompt(self, system_prompt):
        """Set the system prompt."""
        self.system_prompt = system_prompt

    def get_chat_completion(self, messages):
        """Get a chat completion from the OpenAI API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.0
        }
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        return response.json()


# MARK: ChatInterface
class ChatInterface:
    """Class to provide a chat interface."""

    def __init__(self, api_key, model="gpt-4o-mini-2024-07-18", system_prompt=DEFAULT_SYSTEM_PROMPT, chat_history=[]):
        """Initialize the chat interface with an API key, model, system prompt, and optional chat history."""
        self.api = OpenAIApi(api_key, model, system_prompt)
        # get the home directory
        home_dir = os.path.expanduser('~')
        self.chat_history = CustomFileHistory(f'{home_dir}/.llm_api_chat_history', skip_prefixes=['/'])
        self.session = PromptSession(history=self.chat_history, key_bindings=self.create_key_bindings())
        self.history = MessageHistory(system_prompt=system_prompt)

    def create_key_bindings(self):
        """Create key bindings for the prompt session."""
        bindings = KeyBindings()

        @Condition
        def is_eob(): # end of buffer
            " Only activate key binding if cursor is at end of buffer"
            return self.session.app.current_buffer.document.is_cursor_at_the_end

        @Condition
        def not_eob(): # not end of buffer
            " Only activate key binding if cursor is not at end of buffer"
            return not self.session.app.current_buffer.document.is_cursor_at_the_end

        @bindings.add('up', filter=is_eob) # alt up arrow
        def _(event):
            buffer = event.app.current_buffer
            buffer.history_backward()
            buffer.cursor_position = len(buffer.text)

        @bindings.add('down', filter=is_eob) # alt down arrow
        def _(event):
            buffer = event.app.current_buffer
            buffer.history_forward()
            buffer.cursor_position = len(buffer.text)

        @bindings.add('s-up') # alt up arrow
        def _(event):
            user_messsage = self.history.seek_previous_user_message()
            if user_messsage:
                event.app.current_buffer.text = user_messsage['content']
            else:
                event.app.current_buffer.text = ''

        @bindings.add('s-down') # alt down arrow
        def _(event):
            user_messsage = self.history.seek_next_user_message()
            if user_messsage:
                event.app.current_buffer.text = user_messsage['content']
            else:
                event.app.current_buffer.text = ''

        @bindings.add('enter')
        def _(event):
            buffer = event.app.current_buffer
            if buffer.document.is_cursor_at_the_end or True:
                buffer.validate_and_handle()
            else:
                buffer.insert_text('\n')

        @bindings.add('escape', 'enter')
        def _(event):
            buffer = event.app.current_buffer
            # buffer.validate_and_handle()
            buffer.insert_text('\n')

        @bindings.add('c-b')  # ctrl-b
        def _(event):
            buffer = event.app.current_buffer
            data = buffer.text
            pyperclip.copy(data)

        @bindings.add('c-l')  # ctrl-b
        def _(event):
            self.copy_last_response()
            # event.app.exit()

        @bindings.add("c-s-down")
        def _(event):
            message = self.history.seek_previous_assistant_message()
            if message:
                self.show_assistant_message(message['content'])
                event.app.exit()

        @bindings.add("c-s-up")
        def _(event):
            if self.history.in_seek_assistant():
                message = self.history.seek_next_assistant_message()
                if message:
                    self.show_assistant_message(message['content'])
                else:
                    self.print_history()
                event.app.exit()

        return bindings

    def show_assistant_message(self, message):
        """Show the assistant message."""
        if message:
            os.system('cls' if os.name == 'nt' else 'clear')
            self.print_assistant_message(message)

    def print_assistant_message(self, message):
        """Print the assistant message."""
        cb_helper = CodeBlockHelper(message)
        highlighted_response = cb_helper.highlighted_message
        print(highlighted_response)
        # print()

    def print_history(self):
        """Print the chat history."""
        for msg in self.history.history:
            if msg['role'] == 'user':
                # print_formatted_text(HTML(f"<style fg='white'>> {msg['content']}</style>\n"), flush=True)
                print(f"> {msg['content']}\n")
            elif msg['role'] == 'assistant':
                self.print_assistant_message(msg['content'])

    # MARK: run
    def run(self):
        """Run the chat interface loop."""
        try:
            while True:
                try:
                    prompt_symbol = '*>' if self.history.session_active() else '>'
                    user_input = self.session.prompt(
                        HTML(f'<style fg="white">{prompt_symbol}</style> '),
                        style=Style.from_dict({'': 'white'}),
                        multiline=True
                    )
                    if user_input is None:
                        continue
                    if user_input.strip() == '':
                        continue
                    if user_input.startswith('/'):
                        self.handle_user_command(user_input)
                    else:
                        if self.history.in_seek_user():
                            self.history.update_user_message(user_input)
                        else:
                            self.history.add_message("user", user_input)
                        response = self.api.get_chat_completion(self.history.get_history())
                        if response.get('error'):
                            print(f"ERROR: {response['error']['message']}")
                        else:
                            ai_response = response['choices'][0]['message']['content']
                            self.print_assistant_message(ai_response)
                            self.history.add_message("assistant", ai_response)
                except EOFError:
                    sys.exit(0)
        except KeyboardInterrupt:
            sys.exit(0)

    def handle_user_command(self, command):
        """Handle commands entered by the user."""
        args = command.strip().split(' ', 1)
        command = args[0]
        args = args[1:] if len(args) > 1 else []
        if command == '/help' or command == '/h':
            print(IN_APP_HELP)
        elif command == '/clear_history' or command == '/ch':
            self.chat_history.clear_history()
            print("Chat file history cleared.")
        elif command == '/clear' or command == '/c':
            os.system('cls' if os.name == 'nt' else 'clear')
        elif command == '/reset' or command == '/r':
            self.history.clear_history()
            print("Chat history reset.")
        elif command == '/save' or command == '/s':
            filename = input("Enter filename to save history: ") if args == [] else args[0]
            self.history.save_history(filename)
        elif command == '/load' or command == '/l':
            filename = input("Enter filename to load history: ") if args == [] else args[0]
            if self.history.load_history(filename):
                self.print_history()
        elif command == '/print' or command == '/p':
            # clear the screen
            os.system('cls' if os.name == 'nt' else 'clear')
            self.print_history()
        elif command == '/sp':
            self.edit_system_prompt()
        elif command == '/cb':
            self.handle_code_block_command()
        elif command == '/exit' or command == '/e' or command == '/q':
            sys.exit(0)
        else:
            print("Unknown command. Type /h for a list of commands.")

    def handle_code_block_command(self):
        """Handle the /cb command to list and select code blocks."""
        message = self.history.get_last_assistant_message()
        if message:
            code_block_helper = CodeBlockHelper(message['content'])
            try:
                selected_code_block = code_block_helper.select_code_block()
                if selected_code_block:
                    pyperclip.copy(selected_code_block)
                    print(f"Selected code block copied to clipboard.")
                else:
                    time.sleep(1)
                    self.print_history()
            except ValueError:
                print("Invalid input. Please enter a valid integer index.")

    def edit_system_prompt(self):
        """Edit the system prompt."""

        try:
            current_prompt = self.history.system_prompt()
            kb = KeyBindings()

            @kb.add('escape','enter')
            def _(event):
                event.current_buffer.insert_text('\n')

            @kb.add('enter')  # Ctrl+Enter
            def _(event):
                event.current_buffer.validate_and_handle()

            new_prompt = prompt(
                "Edit System Prompt\n(crtl-c to exit, enter to save):\n\n",
                default=current_prompt,
                multiline=True,
                history=None,
                key_bindings=kb
            )
            if new_prompt != current_prompt:
                self.history.system_prompt(new_prompt)
                print(f"System prompt updated.\n")
        except KeyboardInterrupt:
            print("System prompt edit cancelled.")


    def copy_last_response(self):
        """Copy the last assistant response to the clipboard."""
        message = self.history.get_last_assistant_message()
        if message:
            pyperclip.copy(message['content'])
            print("Last assistant response copied to clipboard.")
            return
        print("No assistant response found to copy.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Command-line chat interface for OpenAI models", add_help=False)
    parser.add_argument("-p", "--prompt", type=str, help="Initial prompt for the chat")
    parser.add_argument("-s", "--system-prompt", type=str, help="System prompt for the chat")
    parser.add_argument("-f", "--history-file", type=str, help="File to restore chat history from")
    parser.add_argument("-m", "--model", type=str, help="Model to use for the chat (default is gpt-4o-mini-2024-07-18)")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument("-c", "--clear", action="store_true", help="Clear the terminal screen")
    parser.add_argument("-h", "--help", action="store_true", help="Show this help message and exit")
    args = parser.parse_args()

    if args.clear:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Welcome to LLM Chat\n")

    if args.help:
        parser.print_help()
        print("\nType /help at the prompt for in-chat command help.\n")
        sys.exit(0)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        sys.exit(1)

    default_model = os.getenv("LLMC_DEFAULT_MODEL", args.model)
    if not default_model:
        default_model = "gpt-4o-mini-2024-07-18"

    system_prompt = args.system_prompt if args.system_prompt else os.getenv("LLMC_SYSTEM_PROMPT", DEFAULT_SYSTEM_PROMPT)
    chat_interface = ChatInterface(api_key, model=default_model, system_prompt=system_prompt)

    if args.history_file:
        if os.path.exists(args.history_file):
            chat_interface.history.load_history(args.history_file)
            chat_interface.print_history()
        else:
            print(f"Warning: History file {args.history_file} does not exist.  No history will be loaded.")

    if args.prompt:
        chat_interface.history.add_message("user", args.prompt)
        response = chat_interface.api.get_chat_completion(chat_interface.history.get_history())
        style = Style.from_dict({'error': 'red'})
        if response.get('error'):
            print_formatted_text(HTML(f"<error>API ERROR:{response['error']['message']}</error>"), style=style)
        else:
            ai_response = response['choices'][0]['message']['content']
            highlighted_response = chat_interface.code_highlighter.highlight_code_blocks(ai_response)
            print(highlighted_response)
        sys.exit(0)

    chat_interface.run()
