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
    --sassy                   Sassy mode (default is nice mode)
    -h, --help                Show the command-line help message.

Environment Variables:
    OPENAI_API_KEY            Your OpenAI API key.  (required)
    LLMC_DEFAULT_MODEL        Model to use if not specified in the command line. (optional)
                              Default is "gpt-4o-mini-2024-07-18"
    LLMC_SYSTEM_PROMPT        System prompt to use if not specified in the command line. (optional)
                              Default is "You're name is Lemmy. You are a helpful assistant that answers questions based on the provided context."
"""

USER_NAME = "brother (with a lowercase b)"

SASSY_SYSTEM_PROMPT = """You're name is Lemmy. You are a rude, ugly, contrary, argumentative, complainer
that begrudgingly does what you're told and answers questions with a sassy, elitest attiude."""

DEFAULT_SYSTEM_PROMPT = f"""You're name is Lemmy.
You are a helpful assistant that answers questions factuallybased on the provided context.
Call the user {USER_NAME}.  If the user seems confused or entering
jibberish or incomplete messages, tell them so, and then tell them to "type /help for a list of commands"
"""

import os
import sys
import argparse

from modules.ChatInterface import ChatInterface

def main():
    parser = argparse.ArgumentParser(description="Command-line chat interface for OpenAI models", add_help=False)
    parser.add_argument("-p", "--prompt", type=str, help="Initial prompt for the chat")
    parser.add_argument("-s", "--system-prompt", type=str, help="System prompt for the chat")
    parser.add_argument("-f", "--history-file", type=str, help="File to restore chat history from")
    parser.add_argument("-m", "--model", type=str, help="Model to use for the chat (default is gpt-4o-mini-2024-07-18)")
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument("-c", "--clear", action="store_true", help="Clear the terminal screen")
    parser.add_argument("--sassy", action="store_true", help="Sassy mode (default is nice mode)")
    parser.add_argument("-h", "--help", action="store_true", help="Show this help message and exit")
    args = parser.parse_args()

    if args.clear:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Welcome to LLM Chat\n")

    if args.help:
        parser.print_help()
        print("\nType /help at the prompt for in-chat command help.\n")
        return  # Use return instead of sys.exit(0)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set.")
        sys.exit(1)

    default_model = os.getenv("LLMC_DEFAULT_MODEL", args.model)
    if not default_model:
        default_model = "gpt-4o-mini-2024-07-18"

    system_prompt = args.system_prompt if args.system_prompt else os.getenv("LLMC_SYSTEM_PROMPT", SASSY_SYSTEM_PROMPT if args.sassy else DEFAULT_SYSTEM_PROMPT)
    chat_interface = ChatInterface(api_key, model=default_model, system_prompt=system_prompt)

    if args.history_file:
        if os.path.exists(args.history_file):
            chat_interface.history.load_history(args.history_file)
            chat_interface.print_history()
        else:
            print(f"Warning: History file {args.history_file} does not exist.  No history will be loaded.")

    if args.prompt:
        chat_interface.one_shot_prompt(args.prompt)
        sys.exit(0)

    chat_interface.run()

if __name__ == "__main__":
    main()
