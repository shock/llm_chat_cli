import os
import sys
import time
import pyperclip
import signal
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
from modules.word_list_manager import WordListManager
from modules.spell_check_word_completer import SpellCheckWordCompleter
from prompt_toolkit.completion import merge_completers

from modules.InAppHelp import IN_APP_HELP

class SigTermException(Exception):
    pass

class ChatInterface:
    """Class to provide a chat interface."""

    def __init__(self, config):
        self.config = config
        if not self.config.get('api_key') or self.config.get('api_key') == '':
            raise ValueError("API Key is required")
        """Initialize the chat interface with optional chat history."""
        model = self.config.get('model')
        system_prompt = self.config.get('system_prompt')
        api_key = self.config.get('api_key')
        base_api_url = self.config.get('base_api_url')
        self.api = OpenAIApi(api_key, model, system_prompt, base_api_url)
        home_dir = os.path.expanduser('~')
        self.chat_history = CustomFileHistory(f'{home_dir}/.llm_api_chat_history', skip_prefixes=[])
        self.word_list_manager = WordListManager( [], save_file = config.get('data_directory') + "/word_list.txt" )
        self.spell_check_completer = SpellCheckWordCompleter(self.word_list_manager)
        self.merged_completer = merge_completers([self.spell_check_completer])
        self.session = PromptSession(
            history=self.chat_history,
            key_bindings=KeyBindingsHandler(self).create_key_bindings(),
            completer=self.merged_completer,
            complete_while_typing=True,
        )
        self.history = MessageHistory(system_prompt=system_prompt)
        self.command_handler = CommandHandler(self)
        # Register the signal handler for SIGTERM
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, sig, frame):
        raise SigTermException()

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
                    if user_input is None or user_input.strip() == '':
                        continue
                    if user_input.startswith('/'):
                        self.command_handler.handle_command(user_input)
                    else:
                        self.word_list_manager.add_words_from_text(user_input)
                        if self.history.in_seek_user():
                            self.history.update_user_message(user_input)
                        else:
                            self.history.add_message("user", user_input)
                        try:
                            if self.config.get('stream'):
                                ai_response = self.api.stream_chat_completion(self.history.get_history())
                                self.history.add_message("assistant", ai_response)
                                self.word_list_manager.add_words_from_text(ai_response)
                                self.print_history()
                            else:
                                response = self.api.get_chat_completion(self.history.get_history())
                                if response.get('error'):
                                    print(f"ERROR: {response['error']['message']}")
                                else:
                                    ai_response = response['choices'][0]['message']['content']
                                    self.word_list_manager.add_words_from_text(ai_response)
                                    self.print_assistant_message(ai_response)
                                    self.history.add_message("assistant", ai_response)
                        except KeyboardInterrupt:
                            print("\nKeyboard interrupt.")
                            self.history.remove_last_user_message()
                        except Exception as e:
                            print(f"ERROR: {e}")
                except EOFError:
                    break
        except KeyboardInterrupt:
            pass
        except SigTermException:
            pass
        self.word_list_manager.stop()

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

    def show_config(self):
        config = self.config
        print()
        print(f"API Key       : {'*' * 8}{config.get('api_key')[-4:]}")
        print(f"Model         : {config.get('model')}")
        print(f"Base API URL  : {config.get('base_api_url')}")
        print(f"Sassy Mode    : {'Enabled' if config.get('sassy') else 'Disabled'}")
        print(f"Stream Mode   : {'Enabled' if config.get('stream') else 'Disabled'}")
        print(f"Data Dir      : {config.get('data_directory')}")
        print(f"System Prompt :\n\n{config.get('system_prompt')}")
        print()

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
            return response['error']['message']
        else:
            ai_response = response['choices'][0]['message']['content']
            self.print_assistant_message(ai_response)
            return ai_response
