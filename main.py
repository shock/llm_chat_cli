#!/usr/bin/env python
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "prompt-toolkit>=3.0.47",
#     "pydantic>=2.9.1",
#     "pygments>=2.18.0",
#     "pyperclip>=1.9.0",
#     "requests>=2.32.3",
#     "toml>=0.10.2",
#     "PyYAML>=6.0.2",
# ]
# ///

"""
llm_api_chat.py - A command-line interface for interacting with LLM models compatible with the OpenAI API.

Author: Bill Doughty
Github: https://github.com/shock/llm_chat_cli

This script provides a terminal-based chat interface to LLM models compatible with the
OpenAI API. It supports loading and saving chat history, markdown syntax highlighting, and
custom system prompts.

Usage:
    python llm_api_chat.py [options]

Command-line options:
    -p, --prompt TEXT         One-shot prompt the model and exit.
    -s, --system-prompt TEXT  System prompt for the chat.
    -f, --history-file NAME   File to restore chat history from.
    -m, --model MODEL         Model to use.  Use --list-models to see available models.
    -l, --list-models         List available models (dynamically queries APIs when possible) and exit.
    --provider PROVIDER       Filter models by specific provider when using --list-models.
    -v, --version             Show the version and exit.
    -c, --clear               Clear the terminal screen at startup.
    -e, --echo                Echo mode.  Don't send the prompt to the model, just print it.
    -d, --data-directory DIR  Directory to store configuration and session files. (default is ~/.llm_chat_cli)
    --sassy                   Sassy mode (default is nice mode)
    --create-config           Create a default configuration file if one does not exist.
    -h, --help                Show the command-line help message.

Environment Variables:
    OPENAI_API_KEY            A valid OpenAI API key.  (only used if config file key is not set)
    LLMC_DEFAULT_MODEL        Model to use if not specified in the command line. (optional)
                              Default is "openai/4.1-mini"
    LLMC_SYSTEM_PROMPT        System prompt to use if not specified in the command line. (optional)
                              Otherwise, the default or configured system prompt is used.
"""

import os
import sys
import argparse

from modules.ChatInterface import ChatInterface
from modules.Config import Config
from modules.Version import VERSION
from modules.Types import DEFAULT_MODEL, PROVIDER_DATA

def main():
    parser = argparse.ArgumentParser(description="Command-line chat interface for OpenAI models", add_help=False)
    parser.add_argument("-p", "--prompt", type=str, help="Initial prompt for the chat")
    parser.add_argument("-s", "--system-prompt", type=str, help="System prompt for the chat")
    parser.add_argument("-f", "--history-file", type=str, help="File to restore chat history from")
    parser.add_argument("-m", "--model", type=str, help="Model to use for the chat (default is openai/4.1-mini)")
    parser.add_argument("-l", "--list-models", action="store_true", help="List available models (dynamically queries APIs when possible)")
    parser.add_argument(
        "--provider",
        type=str,
        help="Filter models by specific provider (e.g., openai, deepseek)"
    )
    parser.add_argument("-v", "--version", action="version", version=f"%(prog)s {VERSION}")
    parser.add_argument("-c", "--clear", action="store_true", help="Clear the terminal screen")
    parser.add_argument("-e", "--echo", action="store_true", help="Echo mode.  Don't send the prompt to the model, just print it.")
    parser.add_argument("--sassy", action="store_true", help="Sassy mode (default is nice mode)")
    parser.add_argument("-h", "--help", action="store_true", help="Show this help message and exit")
    parser.add_argument("-d", "--data-directory", type=str, help="Data directory for configuration and session files")
    parser.add_argument("--create-config", action="store_true", help="Create a default configuration file")
    args = parser.parse_args()

    if args.clear:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Welcome to LLM Chat\n")

    if args.help:
        parser.print_help()
        print("\nType /help at the prompt for in-chat command help.\n")
        return  # Use return instead of sys.exit(0)

    config_overrides = {}

    default_model = os.getenv("LLMC_DEFAULT_MODEL", args.model)

    # make sure the model is valid
    if not default_model or default_model == DEFAULT_MODEL:
        default_model = DEFAULT_MODEL

    config_overrides["model"] = default_model or None
    config_overrides["sassy"] = args.sassy or None
    env_system_prompt = os.getenv("LLMC_SYSTEM_PROMPT")
    config_overrides["system_prompt"] = args.system_prompt if args.system_prompt else env_system_prompt if env_system_prompt else None
    config = Config(data_directory=args.data_directory, overrides=config_overrides, create_config=args.create_config)

    if args.create_config:
        return  # Exit after creating the config file

    if args.list_models:
        from modules.ModelDiscoveryService import ModelDiscoveryService

        # Determine which providers to query
        providers_to_query = []
        if args.provider:
            # Query specific provider
            if config.config.providers.get_provider_config(args.provider):
                providers_to_query = [args.provider]
            else:
                print(f"Error: Provider '{args.provider}' not found in configuration")
                sys.exit(1)
        else:
            # Query all configured providers
            providers_to_query = config.config.providers.get_all_provider_names()

        # Query and display models for each provider
        for provider_name in providers_to_query:
            provider_config = config.config.providers.get_provider_config(provider_name)

            # Use ModelDiscoveryService for model discovery
            discovery_service = ModelDiscoveryService()
            dynamic_models = discovery_service.discover_models(provider_config)

            if dynamic_models:
                print(f"\n{provider_name.upper()} - Dynamic Models:")
                for model in dynamic_models:
                    model_id = model.get('id', 'Unknown')
                    print(f"  - {provider_name}/{model_id}")  # Dynamic models show full name only
            else:
                # Fallback to static models
                print(f"\n{provider_name.upper()} - Static Models:")
                static_models = provider_config.valid_models if hasattr(provider_config, 'valid_models') else {}
                for model_name, short_name in static_models.items():
                    print(f"  - {model_name} ({short_name})")  # Static models show both full name and shorthand

                if not static_models:
                    print("  No models configured")

        return  # Use return instead of sys.exit(0)

    config.echo_mode = args.echo

    chat_interface = ChatInterface(config)

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
