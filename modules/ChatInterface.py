import os
import sys
import time
import pyperclip
import signal
import copy
from prompt_toolkit import PromptSession, prompt
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit import print_formatted_text
from modules.CodeBlockHelper import CodeBlockHelper
from modules.CustomFileHistory import CustomFileHistory
from modules.MessageHistory import MessageHistory
from modules.OpenAIChatCompletionApi import OpenAIChatCompletionApi
from modules.CommandHandler import CommandHandler
from modules.KeyBindingsHandler import KeyBindingsHandler
from modules.MarkdownExporter import MarkdownExporter
from modules.Version import VERSION
# from modules.word_list_manager import WordListManager
# from modules.spell_check_word_completer import SpellCheckWordCompleter
from string_space_completer import StringSpaceCompleter
from prompt_toolkit.completion import merge_completers

from modules.InAppHelp import IN_APP_HELP

class SigTermException(Exception):
    pass

class ChatInterface:
    """Class to provide a chat interface."""

    def __init__(self, config):
        self.config = config

        providers = self.config.providers
        if not providers:
            raise ValueError("Providers are required")
        if isinstance(providers, str):
            raise ValueError("Providers must be a dictionary")
        for provider in providers.keys():
            api_key = providers[provider].api_key
            if not api_key or api_key == '':
                raise ValueError(f"API Key is required for {provider}")

        """Initialize the chat interface with optional chat history."""
        model = self.config.get('model')
        system_prompt = self.config.get('system_prompt')
        self.api = OpenAIChatCompletionApi.get_api_for_model_string(model)
        home_dir = os.path.expanduser('~')
        chat_history_file = config.get('data_directory') + "/chat_history.txt"
        self.chat_history = CustomFileHistory(chat_history_file, max_history=100, skip_prefixes=[])
        # self.word_list_manager = WordListManager( [], save_file = config.get('data_directory') + "/word_list.txt" )
        # self.spell_check_completer = SpellCheckWordCompleter(self.word_list_manager)
        self.spell_check_completer = StringSpaceCompleter(host='127.0.0.1', port=7878)
        self.merged_completer = merge_completers([self.spell_check_completer])
        self.session = PromptSession(
            history=self.chat_history,
            key_bindings=KeyBindingsHandler(self).create_key_bindings(),
            completer=self.merged_completer,
            complete_while_typing=True,
        )
        self.session.app.ttimeoutlen = 0.001  # Set to 1 millisecond
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
                    self.spell_check_completer.stop() # Shouldn't be necessary, but it is
                    model = self.api.brief_model()

                    prompt_symbol = f'{model} *>' if self.history.session_active() else f'{model} >'
                    user_input = self.session.prompt(
                        HTML(f'<style fg="white">{prompt_symbol}</style> '),
                        style=Style.from_dict({'': 'white'}),
                        multiline=True
                    )
                    if user_input is None or user_input.strip() == '':
                        continue
                    # strip leading and trailing whitespace
                    user_input = user_input.strip()
                    if user_input.startswith('/'):
                        self.command_handler.handle_command(user_input)
                    else:
                        self.spell_check_completer.add_words_from_text(user_input)
                        if self.history.in_seek_user():
                            self.history.update_user_message(user_input)
                        else:
                            self.history.add_message("user", user_input)
                        try:
                            if self.config.echo_mode:
                                print(user_input)
                            elif self.config.get('stream'):
                                ai_response = self.api.stream_chat_completion(self.history.get_history())
                                self.history.add_message("assistant", ai_response)
                                self.spell_check_completer.add_words_from_text(ai_response)
                                self.print_history()
                            else:
                                response = self.api.get_chat_completion(self.history.get_history())
                                if response.get('error'):
                                    print(f"ERROR: {response['error']['message']}")
                                else:
                                    ai_response = response['choices'][0]['message']['content']
                                    self.spell_check_completer.add_words_from_text(ai_response)
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
        except KeyboardInterrupt:
            pass
        except SigTermException:
            pass
        self.spell_check_completer.stop()

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
                # print_formatted_text(HTML(f'<style fg="white">{prompt}{msg['content']}</style>'))
                bright_white = "\033[1;37m"
                reset = "\033[0m"
                formatted_string = f"{bright_white}{prompt}{msg['content']}{reset}"
                print(formatted_string)
            elif msg['role'] == 'assistant':
                self.print_assistant_message(msg['content'])
            i+=1

    def show_config(self):
        config = self.config
        print()
        print(f"Version       : {VERSION}")
        print(f"API Key       : {'*' * 8}{config.get('api_key')[-4:]}")
        print(f"Model         : {self.api.model}")
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

    def set_model(self, model):
        """Set the model to be used."""
        # make sure the model is valid
        try:
            self.api = self.api.set_model(model)
        except ValueError as e:
            print(e)
        print(f"Model set to {self.api.model}.")

    def set_default_model(self):
        """Set the default model to be used."""
        self.api.set_model(self.config.get('model'))
        print(f"Model set to {self.api.model}.")

    def export_markdown(self, titleize=True):
        """Export the chat history to Markdown and copy it to the clipboard."""
        title = None
        if titleize:
            system_prompt = """
You are an export note taking assistant.  Your current task is to process the following conversation
and create a short title for it that captures the subject in 3 to 8 words.  The title should be
a single line of title-case text that is no longer than 50 characters.  Your output should be just the title
and nothing else.  Here is the conversation:

###

"""
            history = copy.deepcopy(self.history.get_history())
            # history = self.history.get_history().copy()
            # change the role to user fo all messages so the bot doesn't get confused
            for msg in history:
                msg['role'] = 'user'
            history[0] = {"role": "system", "content": system_prompt}
            title = self.api.get_chat_completion(history)['choices'][0]['message']['content']
            title = title.strip().replace('\n', ' ').replace('\r', '')
        file = None
        system_prompt = """
You are a computer file system manager.  Your task is to create a succinct file name for a document
with the supplied title.  The file name should be continous string of alphanumeric characters that
are human-readable and not too long.  The file name should be no longer than 30 characters.  Do not
include any file extensions.  Your output should be just the file name and nothing else.
"""
        history = []
        history.append({"role": "system", "content": system_prompt})
        history.append({"role": "user", "content": f"Title: {title}"})
        file = self.api.get_chat_completion(history)['choices'][0]['message']['content']
        file = file.strip().replace('\n', ' ').replace('\r', '')
        exporter = MarkdownExporter(self.config.get('model'), self.history, title=title, file=file)
        markdown = exporter.markdown()
        pyperclip.copy(markdown)
        print(f"Markdown exported to clipboard.")