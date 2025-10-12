import os
import time
import pyperclip
import signal
import copy
import re
from prompt_toolkit import PromptSession, prompt
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit import print_formatted_text
from modules.MarkdownFormatter import MarkdownFormatter
from modules.CustomFileHistory import CustomFileHistory
from modules.MessageHistory import MessageHistory
from modules.OpenAIChatCompletionApi import OpenAIChatCompletionApi
from modules.ModelDiscoveryService import ModelDiscoveryService
from modules.CommandHandler import CommandHandler
from modules.KeyBindingsHandler import KeyBindingsHandler
from modules.MarkdownExporter import MarkdownExporter
from modules.Config import Config
from modules.Version import VERSION
from modules.ModelCommandCompleter import ModelCommandCompleter
from modules.DelegatingCompleter import DelegatingCompleter
from string_space_completer import StringSpaceCompleter
from prompt_toolkit.completion import merge_completers


class SigTermException(Exception):
    pass

class ChatInterface:
    """Class to provide a chat interface."""

    def __init__(self, config: Config):
        self.config = config

        providers = self.config.config.providers
        if not providers:
            raise ValueError("Providers are required")
        if isinstance(providers, str):
            raise ValueError("Providers must be a ProviderManager instance")
        for provider_name in providers.get_all_provider_names():
            provider_config = providers.get_provider_config(provider_name)
            api_key = provider_config.api_key
            if not api_key or api_key == '':
                raise ValueError(f"API Key is required for {provider_name}")

        """Initialize the chat interface with optional chat history."""
        model = self.config.get('model')
        system_prompt = self.config.get('system_prompt')

        # Use ModelDiscoveryService to parse model string and validate
        model_discovery = ModelDiscoveryService()
        provider, model_name = model_discovery.parse_model_string(model)

        self.api = OpenAIChatCompletionApi.create_api_instance(providers, provider, model_name)
        chat_history_file = config.get('data_directory') + "/chat_history.txt"
        self.chat_history = CustomFileHistory(chat_history_file, max_history=100, skip_prefixes=[])
        self.spell_check_completer = StringSpaceCompleter(host='127.0.0.1', port=7878)
        self.merged_completer = merge_completers([self.spell_check_completer])

        # Create ModelCommandCompleter instance
        self.model_completer = ModelCommandCompleter(
            self.config.config.providers,
            MOD_COMMAND_PATTERN
        )

        # Create DelegatingCompleter to route between completers
        self.top_level_completer = DelegatingCompleter(
            self.model_completer,           # completer_a - for /mod commands
            self.merged_completer,          # completer_b - for all other commands
            is_mod_command                  # decision function
        )

        self.session = PromptSession(
            history=self.chat_history,
            key_bindings=KeyBindingsHandler(self).create_key_bindings(),
            completer=self.top_level_completer,
            complete_while_typing=True,
        )
        self.session.app.ttimeoutlen = 0.001  # Set to 1 millisecond
        self.history = MessageHistory(system_prompt=system_prompt)
        self.command_handler = CommandHandler(self)
        # Register the signal handler for SIGTERM
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, _sig, _frame):  # parameters are required by signal handler signature but not used
        raise SigTermException()

    def clear_history(self):
        self.history.clear_history()

    def run(self):
        try:
            while True:
                try:
                    self.spell_check_completer.stop() # Shouldn't be necessary, but it is
                    # Use model name directly for prompt
                    model_name = self.api.model_short_name()

                    prompt_symbol = f'{model_name} *>' if self.history.session_active() else f'{model_name} >'
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
                                if isinstance(response, dict) and response.get('error'):
                                    print(f"ERROR: {response['error']['message']}")
                                elif isinstance(response, dict):
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
        formatter = MarkdownFormatter(message)
        formatted_response = formatter.formatted_message
        print(formatted_response)

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
        print(f"API Key       : {'*' * 8}{self.api.api_key[-4:]}")
        print(f"Model         : {self.api.model}")
        print(f"Base API URL  : {self.api.base_api_url}")
        print(f"Sassy Mode    : {'Enabled' if config.get('sassy') else 'Disabled'}")
        print(f"Stream Mode   : {'Enabled' if config.get('stream') else 'Disabled'}")
        print(f"Data Dir      : {config.get('data_directory')}")
        print(f"System Prompt :\n\n{config.get('system_prompt')}")
        print()

    def handle_code_block_command(self):
        """Handle the /cb command to list and select code blocks."""
        message = self.history.get_last_assistant_message()
        if message:
            formatter = MarkdownFormatter(message['content'])
            try:
                selected_code_block = formatter.select_code_block()
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
        if isinstance(response, dict) and response.get('error'):
            print_formatted_text(HTML(f"<error>API ERROR:{response['error']['message']}</error>"), style=style)
            return response['error']['message']
        elif isinstance(response, dict):
            ai_response = response['choices'][0]['message']['content']
            self.print_assistant_message(ai_response)
            return ai_response

    def set_model(self, model):
        """Set the model to be used."""
        # Parse the model string to get provider and model name
        model_discovery = ModelDiscoveryService()
        try:
            provider, model_name = model_discovery.parse_model_string(model)
            # Create a new API instance with the new model
            providers = self.config.config.providers
            self.api = OpenAIChatCompletionApi.create_api_instance(providers, provider, model_name)
            print(f"Model set to {self.api.model}.")
        except ValueError as e:
            print(str(e))

    def set_default_model(self):
        """Set the default model to be used."""
        model = self.config.get('model')
        model_discovery = ModelDiscoveryService()
        try:
            provider, model_name = model_discovery.parse_model_string(model)
            # Create a new API instance with the default model
            providers = self.config.config.providers
            self.api = OpenAIChatCompletionApi.create_api_instance(providers, provider, model_name)
            print(f"Model set to {self.api.model}.")
        except ValueError as e:
            print(e)

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
            title_response = self.api.get_chat_completion(history)
            if isinstance(title_response, dict):
                title = title_response['choices'][0]['message']['content']
                title = title.strip().replace('\n', ' ').replace('\r', '')
            else:
                title = "Untitled"
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
        file_response = self.api.get_chat_completion(history)
        if isinstance(file_response, dict):
            file = file_response['choices'][0]['message']['content']
            file = file.strip().replace('\n', ' ').replace('\r', '')
        else:
            file = "untitled"
        exporter = MarkdownExporter(self.config.get('model'), self.history, title=title, file=file)
        markdown = exporter.markdown()
        pyperclip.copy(markdown)
        print(f"Markdown exported to clipboard.")


MOD_COMMAND_PATTERN = re.compile(r'^\s*\/mod[^\s]*\s+([^\s]*)')

def is_mod_command(document) -> bool:
    text = document.text_before_cursor
    match = re.match(MOD_COMMAND_PATTERN, text)
    if match:
        return True
    return False