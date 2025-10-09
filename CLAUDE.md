# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a command-line interface (CLI) for interacting with OpenAI and OpenAI-compatible LLM models. The tool provides both interactive chat sessions and single-prompt modes with features like chat history management, code highlighting, and session management.

## Development Commands

### Building
- `make debug` - Build debug version using python-inliner
- `make release` - Build release version
- `make clean` - Clean build artifacts
- `make install` - Install executable to target directory (default: /opt/local/bin)

### Testing
- `make test` or `pytest` - Run all tests
- Tests are located in `tests/` directory, organized by module
- Test files follow naming convention: `test_<module_name>.py`

### Dependencies
- Uses uv for dependency management (pyproject.toml + uv.lock)
- Dependencies include: prompt-toolkit, pydantic, pygments, pyperclip, requests, toml, PyYAML
- Custom dependency: `string-space-completer` (editable path dependency)

## Architecture

### Core Components
- **main.py**: Entry point with CLI argument parsing and initialization
- **modules/**: Modular architecture with focused responsibilities
  - `ChatInterface`: Main interactive chat interface
  - `Config`: Configuration management with TOML files
  - `OpenAIChatCompletionApi`: API communication layer
  - `MessageHistory`: Chat session management
  - `CommandHandler`: In-chat command processing
  - `CodeHighlighter`: Syntax highlighting for code blocks
  - Various utility modules for specific functionality

### Key Design Patterns
- Configuration uses Pydantic models with TOML file storage
- Session management with JSON file persistence
- Provider-agnostic API design supporting multiple LLM providers
- Modular architecture with clear separation of concerns

## Configuration

- Default data directory: `~/.llm_chat_cli/`
- Configuration file: `config.toml` in data directory
- Environment variables override config: `OPENAI_API_KEY`, `LLMC_DEFAULT_MODEL`, `LLMC_SYSTEM_PROMPT`
- Supports multiple providers through provider-specific API keys

## Code Style Guidelines

- Prefer verbose variable names for readability
- Write tests for all new functionality using pytest
- Use descriptive function and variable names
- Follow existing module-based architecture patterns
- Tests should import modules using sys.path.append to handle relative imports

## Testing Requirements

- **ALWAYS run tests after completing any code editing task** using `make test` or `pytest`
- Ensure all tests pass before considering a task complete
- If tests fail, address the failures before marking the task as completed
- New functionality must include corresponding tests

## Session Management

- Sessions are managed as JSON files with metadata
- Default session: "default.json" in data directory
- Session files include name, creation date, and message history
- Session management commands available via `/session` in chat interface