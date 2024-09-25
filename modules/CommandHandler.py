import os
import sys
from prompt_toolkit import prompt
from modules.InAppHelp import IN_APP_HELP

class CommandHandler:
    def __init__(self, chat_interface):
        self.chat_interface = chat_interface

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
            self.chat_interface.history.clear_history()
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
        elif command == '/config':
            self.chat_interface.show_config()
        elif command == '/exit' or command == '/e' or command == '/q':
            sys.exit(0)
        else:
            print("Unknown command. Type /h for a list of commands.")
