# LLM API Chat

NOTE: This document was revised by an LLM and I'm lazy, so please forgive the cheese and hyperbole.

## Overview

LLM API Chat is a command-line interface designed for seamless interaction with OpenAI's models, or any provider's models that adhere to the OpenAI API. This tool provides a streamlined environment for engaging with advanced AI language functionalities directly within a terminal. In an age where graphical interfaces dominate, this script emphasizes simplicity, efficiency, and accessibility, allowing users to leverage the power of AI within the terminal.

## Philosophy

For developers.  For researchers.  For tinkerers.  As a developer, I want to be able to interact with AI in a way that is both versatile and respectful of my time.  I wanted a quick and easy way to ask an LLM a question and get an answer, without have to open a web browser or download a separate app.  I always have a terminal open when I'm developing, so it seemed logical to enable LLM access with a simple command. This script does that.

## Features

- Intuitive command-line interaction with OpenAI and OpenAI-compatible models (OpenAI, DeepSeek, Hyperbolic)
- Lightweight design that emphasizes speed and efficiency
- Support for managing chat histories, enabling users to maintain context over numerous interactions
- Code highlighting capabilities, ideal for developers looking to showcase or test snippets of code
- A user-friendly command set for manipulating the chat environment without overwhelming complexity
- Single prompt mode for getting a response from the model and exiting - useful for scripting and prompt testing
- Configurable system prompt for different use cases, both in chat mode and single prompt mode
- Session management with persistent chat history
- Multiple provider support with automatic model detection
- Sassy mode for a more entertaining chat experience

## Installation

### Prerequisites
- Python 3.12 or higher
- `uv` for dependency management (https://docs.astral.sh/uv/)
- `python-inliner` for building the executable (https://github.com/llm-api/python-inliner)
- `string-space` for autocompletion (https://github.com/shock/string_space)

### Building
```bash
uv sync
make debug    # Build single-file debug version (./build/llm_api_chat.py)
make release  # Build single-file release version (./build/llm_api_chat.py)
make install  # Build and install release version to /opt/local/bin (default)
```

### Development Setup
```bash
uv sync       # Install dependencies
make test     # Run tests
```

## Usage

### Command Line Options
```bash
./main.py [options]

Options:
  -p, --prompt TEXT         Pass a prompt directly to the model, show response and exit
  -s, --system-prompt TEXT  System prompt for the chat
  -f, --history-file FILE   File to restore chat history from
  -m, --model TEXT          Model to use for the chat (default: gpt-4.1-mini)
  -v, --version             Show version and exit
  -c, --clear               Clear terminal screen at startup
  -e, --echo                Echo mode - don't send prompt to model, just print
  --sassy                   Enable sassy mode (default is nice mode)
  -d, --data-directory DIR  Data directory for configuration and sessions
  -h, --help                Show help message
  --create-config           Create a default configuration file
```

### Environment Variables

```
OPENAI_API_KEY          Your OpenAI API key (required if not set in config files)
LLMC_DEFAULT_MODEL      Overrides the default model if specified (default: gpt-4.1-mini)
LLMC_SYSTEM_PROMPT      Overrides the default system prompt if specified
```

### Supported Models

**OpenAI:**
- gpt-4o-2024-08-06 (4o)
- gpt-4o-mini-2024-07-18 (4o-mini)
- gpt-4.1-2024-04-14 (4.1)
- gpt-4.1-mini-2025-04-14 (4.1-mini)
- gpt-5-mini (5-mini) - experimental

**DeepSeek:**
- deepseek-chat (dschat)
- deepseek-reasoner (r1)

**Hyperbolic:**
- Qwen/QwQ-32B-Preview (qdub)
- Qwen/Qwen2.5-72B-Instruct (qinstruct)

Additional models can be added to the `~/.llm_chat_cli/config.toml` file or the `~/.llm_chat_cli/openaicompat-providers.yaml` file, if present.

## Chat Commands

### Basic Controls
- `/help` (`/h`) - Show help message with these commands
- `/clear` (`/c`) - Clear terminal screen
- `/exit` (`/e`, `/q`) - Exit chat interface

### Chat History
- `/reset` (`/r`) - Clear chat history and start fresh
- `/print` (`/p`) - Show entire chat history
- `/save` (`/s`) [FILENAME] - Save chat history to file
- `/load` (`/l`) [FILENAME] - Load chat history from file
- `/clear_history` (`/ch`) - Clear saved chat history

### Model Configuration
- `/mod` [MODEL] - Switch to specified model
- `/dm` - Reset to default model
- `/config` (`/con`) - Show current configuration

### Content Management
- `/sp` - Edit system prompt
- `/cb` - Work with code blocks in last response
- `/md` - Export chat to Markdown

### Keyboard Shortcuts
- `shift-up/down` - Navigate previous/next user input message
- `ctrl-shift-up/down` - Navigate previous/next assistant response
- `alt-enter/ctrl-o` - Submit current input buffer
- `enter` - Newline in input
- `ctrl-b` - Copy current input buffer to clipboard
- `ctrl-l` - Copy last assistant response to clipboard

## Configuration

### Data Directory

The default data directory is `~/.llm_chat_cli`. You can specify a different data directory using the `-d` or `--data-directory` option.  The data directory directory is used to store configuration files and session files.

### Configuration File

Configuration is stored in `<data-directory>/config.toml`. You can create a default configuration file in the default data directory using the `--create-config` command line option.

### Example Configuration File
```toml
[openai]
api_key = "your-api-key-here"
base_api_url = "https://api.openai.com/v1"

[deepseek]
api_key = "your-deepseek-key-here"
base_api_url = "https://api.deepseek.com/v1"

[hyperbolic]
api_key = "your-hyperbolic-key-here"
base_api_url = "https://api.hyperbolic.xyz/v1"

[default]
model = "gpt-4.1-mini"
system_prompt = "You're name is Lemmy. You are a helpful assistant..."
sassy = false
stream = true
```

## Development

### Project Structure
```
main.py              # Entry point with CLI argument parsing
modules/             # Modular architecture
├── ChatInterface.py        # Main interactive chat interface
├── Config.py              # Configuration management
├── OpenAIChatCompletionApi.py # API communication layer
├── MessageHistory.py      # Chat session management
├── CommandHandler.py      # In-chat command processing
├── CodeHighlighter.py    # Syntax highlighting
└── ... (various utility modules)
```

### Testing
```bash
make test    # Run all tests
pytest       # Alternative test command
```

Tests are located in the `tests/` directory and follow the naming convention `test_<module_name>.py`.

### Code Style
- Prefer verbose variable names for readability
- Write tests for all new functionality using pytest
- Follow existing module-based architecture patterns
- Use descriptive function and variable names

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run `make test` to ensure all tests pass
6. Submit a pull request

## License

This project is open source and available under the MIT License.
