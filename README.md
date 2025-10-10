# LLM API Chat

## Overview

LLM API Chat is a command-line interface designed for seamless interaction with OpenAI's models, or any provider's models that adhere to the OpenAI API. This tool provides a streamlined environment for engaging with advanced AI language functionalities directly within a terminal. In an age where graphical interfaces dominate, this script emphasizes simplicity, efficiency, and accessibility, allowing users to leverage the power of AI within the terminal.

## Philosophy

For developers.  For researchers.  For tinkerers.  As a developer, I want to be able to interact with AI in a way that is both versatile and respectful of my time.  I wanted a quick and easy way to ask an LLM a question and get an answer, without having to open a web browser or download a separate app.  I always have a terminal open when I'm developing, so it seemed logical to enable LLM access with a simple command. This script does that.

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

## Quick Start

- Ensure [uv is installed](https://docs.astral.sh/uv/)
- Clone [https://github.com/shock/llm_chat_cli.git](https://github.com/shock/llm_chat_cli) and change directory into it
- Run `uv sync`
- Set the OPENAI_API_KEY environment variable to your OpenAI API key
- execute `./main.py`
- enter '/help' for a list of commands
- Enter the prompt: "generate a sample markdown demonstrating various styles and a python code block"
- Submit the prompt with one of these options:
  - **macOS**: `option-enter` or `ctrl-o`
  - **Windows**: `alt-enter` or `ctrl-o`
  - **Linux**: `alt-enter` or `ctrl-o`
  - Use `ENTER` with no modifier for multiline prompts
  - **Note**: Some terminals may require configuring the alt/option key as the meta key

## Single-File Installation

Single file installation allows you to create a single-file executable python script that utilizes `uv` to manage its dependencies independently of the current python environment.

### Prerequisites
- Python 3.12 or higher
- `uv` for dependency management (https://docs.astral.sh/uv/)
- `python-inliner` for building the executable (https://github.com/shock/python-inliner)
- `string-space` for autocompletion (https://github.com/shock/string_space)

### Building Single-File Script
```bash
uv sync
source .venv/bin/activate
make debug    # Build single-file debug version using `python-inliner` (./build/llm_api_chat.py)
make release  # Build single-file release version using `python-inliner` (./build/llm_api_chat.py)
# Create /opt/local/bin and add to PATH, if needed
curl -sSL https://raw.githubusercontent.com/shock/string_space/refs/heads/master/setup_opt_local_bin.sh | /bin/bash
make install  # Build and install release version to /opt/local/bin (default)
```

To run the single-file script, use `uv run /opt/local/bin/llm_api_chat.py`.  This will enable uv to parse the inline dependencies and run the script in its own independent virtual environment from anywhere.  (https://docs.astral.sh/uv/guides/scripts/#declaring-script-dependencies)

eg.
```bash
alias llm=`uv run /opt/local/bin/llm_api_chat.py`
llm
```

### Auto-Completion

You need to install StringSpaceServer (https://github.com/shock/string_space) to enable autocompletion.  Auto-completion with string-space learns words over time from your conversations and ranks them by frequency.  It attempts to predict the most likely word completions as you type.  The more you converse, the better it becomes.  Auto-completion using string-space is a work in progress and does not always predict correctly.

### Development Setup
```bash
uv sync       # Install dependencies and create uv virtual environment
source .venv/bin/activate
make test     # Run tests
./main.py     # Run LLM API Chat from local repo source
```

## Usage

### Command Line Options
```
  -p, --prompt TEXT          Pass a prompt directly to the model, show response and exit
  -s, --system-prompt TEXT   System prompt for the chat
  -f, --history-file FILE    File to restore chat history from
  -m, --model TEXT           Model to use for the chat (default: gpt-4.1-mini)
  -v, --version              Show version and exit
  -c, --clear                Clear terminal screen at startup
  -e, --echo                 Echo mode - don't send prompt to model, just print
  --sassy                    Enable sassy mode (default is nice mode)
  -d, --data-directory DIR   Data directory for configuration and sessions
  -h, --help                 Show help message
  --create-config            Create a default configuration file
  -uvm, --update-valid-models Update valid models by discovering from configured providers
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

Additional models can be added to the `~/.llm_chat_cli/config.toml` file or the `~/.llm_chat_cli/openaicompat-providers.yaml` file, if present.  See `data/openaicompat-providers.yaml` for an example.

### Model Discovery

The `--update-valid-models` (or `-uvm`) flag enables automatic discovery and validation of available models from configured providers. When invoked, the tool will:

1. Query each configured provider's API for available models
2. Validate each discovered model to ensure it's compatible
3. Update the list of valid and invalid models for each provider
4. Persist the results to `~/.llm_chat_cli/openaicompat-providers.yaml`

This feature is useful when:
- Setting up the tool for the first time
- A provider adds new models
- You want to refresh the list of available models

**Usage:**
```bash
./main.py --update-valid-models
# or using the short alias
./main.py -uvm
```

**Note:** Model discovery requires valid API keys for each provider you want to query. Providers without valid API keys will be skipped during discovery.

You can also list available models from within the chat interface using the `/list` command. See the Chat Commands section for more details.

## Chat Commands

### Basic Controls
- `/help` (`/h`) - Show help message with these commands
- `/clear` (`/c`) - Clear terminal screen
- `/exit` (`/e`, `/q`) - Exit chat interface

### Chat History
- `/reset` (`/r`) - Clear chat history and start fresh
- `/print` (`/p`) - Show entire chat history
- `/save` (`/s`) [FILENAME] - Save chat history file to data directory (unless full path is specified). Appends .json to FILENAME by default if no extension is specified
- `/load` (`/l`) [FILENAME] - Load chat history file from data directory (unless full path is specified).  Appends .json to FILENAME by default if no extension is specified
- `/clear_history` (`/ch`) - Clear saved input history

### Model Configuration
- `/mod` [MODEL] - Switch to specified model.  Leave MODEL blank to list available models.
- `/dm` - Reset to default model
- `/config` (`/con`) - Show current configuration

### Content Management
- `/sp` - Edit system prompt
- `/cb` - utility to copy code/doc blocks from last assistant response
- `/md` - Export chat to Markdown

### Keyboard Shortcuts

#### macOS (Terminal, iTerm2)
- `up/down` - Navigate previous/next user input from history across all chats
- `shift-up/down` - Navigate previous/next user input message in the current chat
- `ctrl-shift-up/down` - Navigate previous/next assistant response, let's you rewind through the chat history
- `shift-option-n` - Clear chat history and start fresh (same as /r)
- `option-enter` or `ctrl-o` - Submit current input buffer
- `enter` - Newline in multiline input
- `ctrl-b` - Copy current input buffer to clipboard
- `ctrl-l` - Copy last assistant response to clipboard

#### Windows / Linux
- `up/down` - Navigate previous/next user input from history across all chats
- `shift-up/down` - Navigate previous/next user input message in the current chat
- `ctrl-shift-up/down` - Navigate previous/next assistant response
- `shift-alt-n` - Clear chat history and start fresh (same as /r)
- `alt-enter` or `ctrl-o` - Submit current input buffer
- `enter` - Newline in input
- `ctrl-b` - Copy current input buffer to clipboard
- `ctrl-l` - Copy last assistant response to clipboard

**Note**: The `alt/option` key behavior may vary depending on your terminal emulator configuration. Some terminals may require you to configure the alt/option key as the meta key for these shortcuts to work properly.

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
system_prompt = "Your name is Lemmy. You are a helpful assistant..."
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
