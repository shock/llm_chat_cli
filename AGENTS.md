# AGENTS.md

This file provides guidance for AI coding agents working with this repository. It contains the technical context needed to quickly get up to speed and work effectively with this codebase.

## Project Overview

LLM API Chat is a Python-based command-line interface for interacting with OpenAI and OpenAI-compatible LLM models (OpenAI, DeepSeek, Hyperbolic, etc.). The tool provides both interactive chat sessions and single-prompt modes with features like chat history management, code highlighting, session management, and provider-agnostic API design.

**Key characteristics:**
- Python 3.12+ required
- Uses `uv` for dependency management
- Modular architecture with clear separation of concerns
- Supports multiple LLM providers through a unified API interface
- Single-file executable capability via `python-inliner`

## Development Environment

### Prerequisites
- Python 3.12 or higher
- `uv` for dependency management (https://docs.astral.sh/uv/)
- `python-inliner` for building single-file executables (https://github.com/shock/python-inliner)

### Setup
```bash
# Install dependencies
uv sync

# Activate the virtual environment
source .venv/bin/activate

# Run the application from source
./main.py
```

### Build Commands
```bash
make debug    # Build single-file debug version using python-inliner (./build/llm_api_chat.py)
make release  # Build single-file release version (runs tests first)
make clean    # Remove build artifacts
make install  # Build and install release version to /opt/local/bin (default)
```

### Testing
```bash
# Run all tests
make test
# or
pytest

# Run with specific timeout (configured in Makefile as 3 seconds)
pytest --timeout=3

# Run specific test file
pytest tests/test_Config.py
```

**Critical:** Always run `make test` or `pytest` after completing any code changes. Ensure all tests pass before considering a task complete.

## Project Architecture

### Directory Structure
```
llm_chat_cli/
├── main.py                    # Entry point with CLI argument parsing
├── pyproject.toml             # Project dependencies and metadata (single source of truth for version)
├── Makefile                   # Build and test commands
├── AGENTS.md                  # This file - guidance for AI agents
├── README.md                  # Human-facing documentation
├── ENGINEERING_GUIDELINES.md  # Engineering standards and practices
├── CLAUDE.md                  # Specific guidance for Claude Code
├── modules/                   # Modular architecture
│   ├── ChatInterface.py       # Main interactive chat interface
│   ├── Config.py              # Configuration management with TOML/YAML
│   ├── OpenAIChatCompletionApi.py  # API communication layer
│   ├── MessageHistory.py      # Chat session management
│   ├── CommandHandler.py      # In-chat command processing
│   ├── CodeHighlighter.py     # Syntax highlighting for code blocks
│   ├── MarkdownFormatter.py  # Markdown formatting for responses
│   ├── MarkdownExporter.py    # Export chats to Markdown files
│   ├── ModelCommandCompleter.py  # Intelligent model name autocomplete
│   ├── DelegatingCompleter.py  # Context-aware completion routing
│   ├── ProviderManager.py     # Multi-provider management
│   ├── ProviderConfig.py      # Provider configuration models
│   ├── ModelDiscoveryService.py  # Automatic model discovery from APIs
│   ├── CustomFileHistory.py   # Input history management
│   ├── Types.py               # Type definitions and constants
│   └── ... (various utility modules)
├── tests/                     # Test suite (pytest)
│   ├── conftest.py           # pytest fixtures
│   └── test_*.py             # Tests organized by module
├── data/                     # Example configurations
│   └── openaicompat-providers.yaml
└── build/                    # Build output directory
```

### Core Module Responsibilities

**main.py**
- Entry point with argparse CLI parsing
- Version management (reads from pyproject.toml via `get_version()`)
- Instantiates ChatInterface with configuration

**ChatInterface.py**
- Main interactive chat loop
- User input handling with prompt_toolkit
- Command routing and execution
- Session management
- Display formatting

**Config.py**
- Configuration file management (TOML format in `<data-dir>/config.toml`)
- Environment variable overrides: `OPENAI_API_KEY`, `LLMC_DEFAULT_MODEL`, `LLMC_SYSTEM_PROMPT`
- Multi-provider configuration from YAML
- Default data directory: `~/.llm_chat_cli/`

**OpenAIChatCompletionApi.py**
- Provider-agnostic API communication
- Request/response handling
- Error handling and retries
- Model validation

**ProviderManager.py**
- Manages multiple provider configurations
- API key validation per provider
- Provider-specific model lists
- Model discovery from provider APIs

**ModelCommandCompleter.py**
- Intelligent model name autocomplete for `/mod` command
- Jaro-Winkler similarity matching
- Supports provider prefixes (`openai/`, `deepseek/`, etc.)
- Short names and long names matching

**CommandHandler.py**
- In-chat command processing
- Commands: `/help`, `/clear`, `/exit`, `/reset`, `/print`, `/save`, `/load`, `/mod`, `/list`, `/dm`, `/config`, `/sp`, `/cb`, `/md`

**MessageHistory.py**
- Chat session message management
- JSON serialization/deserialization
- History persistence

## Configuration

### Version Management
**CRITICAL:** The `pyproject.toml` file is the single source of truth for the project version. Version is read dynamically at runtime using the `get_version()` function in `main.py`. Do not use a separate `VERSION` constant file.

### Configuration Files
- **Primary config:** `<data-dir>/config.toml` (TOML format)
- **Providers config:** `<data-dir>/openaicompat-providers.yaml` (YAML format)
- **Data directory:** Default `~/.llm_chat_cli/`, override with `-d/--data-directory`

### Environment Variables
```
OPENAI_API_KEY          # API key for OpenAI provider (can be overridden per provider)
LLMC_DEFAULT_MODEL      # Default model selection
LLMC_SYSTEM_PROMPT      # Default system prompt
```

### Supported Providers
- OpenAI (default)
- DeepSeek
- Hyperbolic
- Any OpenAI-compatible API

## Code Style Guidelines

### Python Conventions
- Prefer verbose variable names for readability
- Write descriptive function and variable names
- Use comments to explain complex logic
- Follow existing module-based architecture patterns

### Testing Requirements
1. **Always add tests** for new functionality using pytest
2. Test files must be named `test_<module_name>.py`
3. Tests should be placed in the `tests/` directory, one file per module
4. Tests importing from `modules` must include this at the top:
   ```python
   import sys
   import os
   sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
   ```
5. All tests must pass before considering changes complete

### Test Organization
- Tests are organized by module: `test_ChatInterface.py`, `test_Config.py`, etc.
- Integration tests are in `test_integration_phase1.py`
- Use pytest fixtures defined in `conftest.py`
- Test timeout is set to 3 seconds via `pytest-timeout`

## Key Development Patterns

### Configuration Loading
The Config class handles:
1. Load config from `<data-dir>/config.toml` if it exists
2. Load provider config from `<data-dir>/openaicompat-providers.yaml`
3. Apply environment variable overrides
4. Use defaults if config doesn't exist
5. Validate provider API keys and models

### Provider Selection
Models can be specified with provider prefixes:
- `openai/gpt-4o` - Explicit provider selection
- `deepseek/deepseek-chat` - Explicit provider selection
- `gpt-4o` - Defaults to OpenAI provider (backward compatible)

### Model Discovery
The `--update-valid-models` flag enables automatic discovery:
1. Query each provider's API for available models
2. Validate each discovered model
3. Update `openaicompat-providers.yaml` with results

## Single-File Executable

The project supports building a single-file executable using `python-inliner`:

```bash
make debug    # Debug build with verbose output
make release  # Release build (includes test execution)
make install  # Install to /opt/local/bin
```

To run the single-file script:
```bash
uv run /opt/local/bin/llm_api_chat.py
```

The executable includes all modules and dependencies, allowing it to run from anywhere with `uv`.

## Important Implementation Notes

### Version Bumping
When bumping version:
1. Update version in `pyproject.toml` (single source of truth)
2. Test with `./main.py --version`
3. No separate version file needed

### Adding New Providers
1. Add provider configuration to `openaicompat-providers.yaml`
2. Ensure `ProviderManager.py` can handle the provider
3. Add tests for the new provider
4. Update documentation

### Autocomplete System
The project uses two autocomplete systems:
1. **ModelCommandCompleter** - Intelligent model name matching for `/mod` command
2. **StringSpaceCompleter** - Word prediction from conversation history (external dependency)

### Session Management
- Sessions are JSON files with metadata (name, creation_date, last_update_date)
- Default session: `default.json` in data directory
- Sessions are saved in realtime during chat
- Resetting creates a new default session

## Troubleshooting Common Issues

### Import Errors in Tests
If you get import errors when running tests:
1. Ensure tests include the sys.path.append pattern shown above
2. Verify you're running from the project root directory
3. Activate the virtual environment: `source .venv/bin/activate`

### Build Failures
If `python-inliner` build fails:
1. Ensure `python-inliner` is installed: `pip install python-inliner`
2. Check that all modules are listed in INLINE_MODULES in Makefile
3. Verify dependencies are installed: `uv sync`

### Configuration Issues
If configuration isn't loading:
1. Check the data directory is correct (`~/.llm_chat_cli/` by default)
2. Verify `config.toml` exists in the data directory
3. Check environment variables are set correctly
4. Ensure TOML/YAML syntax is valid

## Documentation Files Reference

- `README.md` - User-facing documentation, features, usage instructions
- `ENGINEERING_GUIDELINES.md` - Code standards and engineering practices
- `CLAUDE.md` - Specific guidance for Claude Code agent
- `TODO.md` - Planned features and refactoring tasks
- `CURRENT_FEATURE.md` - Current development focus
- `AGENTS.md` - This file, guidance for AI coding agents

## Running the Application

### Development Mode
```bash
./main.py                    # Start interactive chat
./main.py --version          # Show version
./main.py --help             # Show CLI help
./main.py -p "your prompt"   # Single prompt mode
```

### Test Commands
```bash
make test                    # Run all tests
pytest                       # Run all tests
pytest tests/test_Config.py  # Run specific test
pytest -v                    # Verbose output
```

### Build Commands
```bash
make debug                   # Build debug version
make release                 # Build release version
make install                 # Install to system
```

## Quick Reference for Common Tasks

### Adding a new module
1. Create file in `modules/` directory
2. Follow existing module patterns
3. Create corresponding test file in `tests/` with `test_<module>.py`
4. Include sys.path.append pattern in test file
5. Add tests for all functionality
6. Run `make test` to verify

### Modifying existing module
1. Make changes to module file
2. Update corresponding tests in `tests/test_<module>.py`
3. Run `make test` to ensure all tests pass
4. If adding new functionality, add corresponding tests

### Adding new provider
1. Add provider to `openaicompat-providers.yaml`
2. Ensure ProviderManager can handle it
3. Add tests for provider-specific behavior
4. Update README.md with provider information
5. Test with `./main.py --update-valid-models`

### Bumping version
1. Update version string in `pyproject.toml`
2. Test with `./main.py --version`
3. No other files need updating (version is read dynamically)
