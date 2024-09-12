import os
import sys
import time
import pyperclip
from prompt_toolkit import PromptSession, prompt
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit import print_formatted_text
from modules.CodeBlockHelper import CodeBlockHelper
from modules.CustomFileHistory import CustomFileHistory
from modules.MessageHistory import MessageHistory
from modules.OpenAIApi import OpenAIApi
from modules.CommandHandler import CommandHandler
from modules.KeyBindingsHandler import KeyBindingsHandler

from modules.InAppHelp import IN_APP_HELP

class ChatInterface:
    """Class to provide a chat interface."""

    def __init__(self, api_key, model="gpt-4o-mini-2024-07-18", system_prompt="You are a helpful assistant that answers questions factually based on the provided context.", chat_history=[]):
        """Initialize the chat interface with an API key, model, system prompt, and optional chat history."""
        self.api = OpenAIApi(api_key, model, system_prompt)
        home_dir = os.path.expanduser('~')
        self.chat_history = CustomFileHistory(f'{home_dir}/.llm_api_chat_history', skip_prefixes=['/'])
        self.session = PromptSession(history=self.chat_history, key_bindings=KeyBindingsHandler(self).create_key_bindings())
        self.history = MessageHistory(system_prompt=system_prompt)
        self.command_handler = CommandHandler(self)

    def run(self):
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
                        self.command_handler.handle_command(user_input)
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

    def print_assistant_message(self, message):
        cb_helper = CodeBlockHelper(message)
        highlighted_response = cb_helper.highlighted_message
        print(highlighted_response)

    def print_history(self):
        for msg in self.history.history:
            if msg['role'] == 'user':
                print(f"> {msg['content']}\n")
            elif msg['role'] == 'assistant':
                self.print_assistant_message(msg['content'])

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
        try:
            current_prompt = self.history.system_prompt()
            kb = KeyBindings()

            @kb.add('escape','enter')
            def _(event):
                event.current_buffer.insert_text('\n')

            @kb.add('enter')
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
        message = self.history.get_last_assistant_message()
        if message:
            pyperclip.copy(message['content'])
            print("Last assistant response copied to clipboard.")
            return
        print("No assistant response found to copy.")

    def one_shot_prompt(self, prompt):
        self.history.add_message("user", prompt)
        response = self.api.get_chat_completion(self.history.get_history())
        style = Style.from_dict({'error': 'red'})
        if response.get('error'):
            print_formatted_text(HTML(f"<error>API ERROR:{response['error']['message']}</error>"), style=style)
        else:
            ai_response = response['choices'][0]['message']['content']
            self.print_assistant_message(ai_response)
