import os
import sys
import time
import pyperclip
from prompt_toolkit import PromptSession, prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit import print_formatted_text
from prompt_toolkit.filters import Condition
from modules.CodeBlockHelper import CodeBlockHelper
from modules.CustomFileHistory import CustomFileHistory
from modules.MessageHistory import MessageHistory
from modules.OpenAIApi import OpenAIApi

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

class ChatInterface:
    """Class to provide a chat interface."""

    def __init__(self, api_key, model="gpt-4o-mini-2024-07-18", system_prompt="You are a helpful assistant that answers questions factually based on the provided context.", chat_history=[]):
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
    def one_shot_prompt(self, prompt):
        """Handle a one-shot prompt."""
        self.history.add_message("user", prompt)
        response = self.api.get_chat_completion(self.history.get_history())
        style = Style.from_dict({'error': 'red'})
        if response.get('error'):
            print_formatted_text(HTML(f"<error>API ERROR:{response['error']['message']}</error>"), style=style)
        else:
            ai_response = response['choices'][0]['message']['content']
            self.print_assistant_message(ai_response)
