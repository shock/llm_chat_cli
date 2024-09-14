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

    def __init__(self, config, chat_history=[]):
        self.config = config
        """Initialize the chat interface with optional chat history."""
        model = self.config.get('model')
        system_prompt = self.config.get('system_prompt')
        api_key = self.config.get('api_key')
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
                        try:
                            if self.config.get('stream'):
                                ai_response = self.api.stream_chat_completion(self.history.get_history())
                                self.history.add_message("assistant", ai_response)
                                self.print_history()
                            else:
                                response = self.api.get_chat_completion(self.history.get_history())
                                if response.get('error'):
                                    print(f"ERROR: {response['error']['message']}")
                                else:
                                    ai_response = response['choices'][0]['message']['content']
                                    self.print_assistant_message(ai_response)
                                    self.history.add_message("assistant", ai_response)
                        except KeyboardInterrupt:
                            print("\nKeyboard interrupt.")
                            self.history.remove_last_user_message()
                        except Exception as e:
                            print(f"ERROR: {e}")
                except EOFError:
                    sys.exit(0)
        except KeyboardInterrupt:
            sys.exit(0)

    def print_assistant_message(self, message):
        cb_helper = CodeBlockHelper(message)
        highlighted_response = cb_helper.highlighted_message
        print(highlighted_response)

    def print_history(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        i=0
        for msg in self.history.history:
            prompt = "> " if i==1 else "*> "
            if msg['role'] == 'user':
                # print_formatted_text(HTML(f'<style fg="white">{prompt}{msg["content"]}</style>'))
                bright_white = "\033[1;37m"
                reset = "\033[0m"
                formatted_string = f"{bright_white}{prompt}{msg["content"]}{reset}"
                print(formatted_string)
            elif msg['role'] == 'assistant':
                self.print_assistant_message(msg['content'])
            i+=1

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
        return ai_response
