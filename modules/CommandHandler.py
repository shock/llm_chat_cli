import os
import sys
from prompt_toolkit import prompt
from modules.InAppHelp import IN_APP_HELP

class CommandHandler:
    def __init__(self, chat_interface):
        self.chat_interface = chat_interface

    def handle_models_command(self, args: list) -> str:
        """Handle /models command to list available models."""
        from modules.OpenAIChatCompletionApi import OpenAIChatCompletionApi

        # Parse provider filter if provided
        provider_filter = args[0] if args else None

        # Get configured providers
        providers_to_query = []
        if provider_filter:
            if provider_filter in self.chat_interface.config.config.providers:
                providers_to_query = [provider_filter]
            else:
                return f"Error: Provider '{provider_filter}' not found"
        else:
            providers_to_query = list(self.chat_interface.config.config.providers.keys())

        result_lines = []

        for provider_name in providers_to_query:
            provider_config = self.chat_interface.config.config.providers[provider_name]

            # Create API instance using factory method
            api = OpenAIChatCompletionApi.create_for_model_querying(
                provider=provider_name,
                api_key=provider_config.api_key,
                base_api_url=provider_config.base_api_url
            )

            # Always try dynamic query when user explicitly requests model listing
            dynamic_models = api.get_available_models()

            if dynamic_models:
                result_lines.append(f"\n**{provider_name.upper()} - Dynamic Models:**")
                for model in dynamic_models:
                    model_id = model.get('id', 'Unknown')
                    result_lines.append(f"• {provider_name}/{model_id}")  # Dynamic models show full name only
            else:
                # Fallback to static models
                result_lines.append(f"\n**{provider_name.upper()} - Static Models:**")
                static_models = provider_config.valid_models if hasattr(provider_config, 'valid_models') else {}
                for model_name, short_name in static_models.items():
                    result_lines.append(f"• {model_name} ({short_name})")  # Static models show both full name and shorthand

                if not static_models:
                    result_lines.append("No models configured")

        return "\n".join(result_lines) if result_lines else "No providers configured"

    def handle_command(self, command):
        args = command.strip().split(' ', 1)
        command = args[0]
        args = args[1:] if len(args) > 1 else []
        if command == '/help' or command == '/h':
            print(IN_APP_HELP)
        elif command == '/clear_history' or command == '/ch':
            self.chat_interface.chat_history.clear_history()
            print("Chat file history cleared.")
        elif command == '/clear' or command == '/c':
            os.system('cls' if os.name == 'nt' else 'clear')
        elif command == '/reset' or command == '/r':
            self.chat_interface.clear_history()
            print("Chat history reset.")
        elif command == '/save' or command == '/s':
            filename = input("Enter filename to save history: ") if args == [] else args[0]
            self.chat_interface.history.save_history(filename)
        elif command == '/load' or command == '/l':
            filename = input("Enter filename to load history: ") if args == [] else args[0]
            if self.chat_interface.history.load_history(filename):
                self.chat_interface.print_history()
        elif command == '/print' or command == '/p':
            self.chat_interface.print_history()
        elif command == '/sp':
            self.chat_interface.edit_system_prompt()
        elif command == '/cb':
            self.chat_interface.handle_code_block_command()
        elif command == '/md':
            self.chat_interface.export_markdown()
        elif command.startswith('/con'):
            self.chat_interface.show_config()
        elif command.startswith('/mod'):
            if len(args) == 0:
                print("Please specify a model name. Type /list to see available models.")
                return
            self.chat_interface.set_model(args[0])
        elif command == '/dm':
            self.chat_interface.set_default_model()
        elif command.startswith('/list'):
            print(self.handle_models_command(args))
        elif command == '/exit' or command == '/e' or command == '/q':
            sys.exit(0)
        else:
            print("Unknown command. Type /h for a list of commands.")
