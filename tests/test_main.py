import sys
import os
import pytest
from unittest.mock import patch, MagicMock
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.Config import Config
import main

@pytest.fixture
def mock_chat_interface():
    with patch('main.ChatInterface') as mock:
        yield mock

def test_version():
    assert main.VERSION == "1.4"

def test_default_system_prompt():
    assert "You're name is Lemmy." in main.DEFAULT_SYSTEM_PROMPT
    assert "Call the user brother (with a lowercase b)" in main.DEFAULT_SYSTEM_PROMPT

@pytest.mark.parametrize("env_var, expected", [
    ("OPENAI_API_KEY", "test_api_key"),
    ("LLMC_DEFAULT_MODEL", "test_model"),
    ("LLMC_SYSTEM_PROMPT", "test_system_prompt"),
])
def test_environment_variables(monkeypatch, env_var, expected):
    # monkeypatch is a fixture provided by pytest that allows you to set environment variables during testing.
    monkeypatch.setenv(env_var, expected)  # Sets the environment variable to the expected value for the test.
    assert os.getenv(env_var) == expected

@patch('argparse.ArgumentParser.parse_args')
@patch('os.system')
def test_clear_option(mock_system, mock_parse_args, mock_chat_interface):
    mock_parse_args.return_value = MagicMock(clear=True, help=False, prompt=None, create_config=False)

    with patch.object(sys, 'exit') as mock_exit:
        main.main()

    mock_system.assert_called_once_with('cls' if os.name == 'nt' else 'clear')

@patch('argparse.ArgumentParser.parse_args')
@patch('argparse.ArgumentParser.print_help')
def test_help_option(mock_print_help, mock_parse_args, mock_chat_interface):
    mock_parse_args.return_value = MagicMock(help=True, create_config=False)

    main.main()

    mock_print_help.assert_called_once()

@patch('argparse.ArgumentParser.parse_args')
def test_chat_interface_creation(mock_parse_args, monkeypatch, mock_chat_interface):
    # Test default mode (non-sassy)
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None, system_prompt=None,
        history_file=None, model=None, sassy=False, config="~/.llm_chat_cli.toml",
        create_config=False
    )
    monkeypatch.setenv("OPENAI_API_KEY", "test_api_key")

    main.main()

    mock_chat_interface.assert_called_once()
    config = mock_chat_interface.call_args[0][0]
    assert isinstance(config, Config)
    assert config.get('api_key') == "test_api_key"
    assert config.get('model') == "gpt-4o-mini-2024-07-18"
    assert config.get('system_prompt') == main.DEFAULT_SYSTEM_PROMPT

    # Test sassy mode
    mock_parse_args.return_value.sassy = True
    main.main()

    mock_chat_interface.assert_called()
    config = mock_chat_interface.call_args[0][0]
    assert isinstance(config, Config)
    assert config.get('api_key') == "test_api_key"
    assert config.get('model') == "gpt-4o-mini-2024-07-18"
    assert config.get('system_prompt') == main.SASSY_SYSTEM_PROMPT

    # Test with custom system prompt (overrides sassy mode)
    custom_prompt = "Custom system prompt"
    mock_parse_args.return_value.system_prompt = custom_prompt
    main.main()

    mock_chat_interface.assert_called()
    config = mock_chat_interface.call_args[0][0]
    assert isinstance(config, Config)
    assert config.get('api_key') == "test_api_key"
    assert config.get('model') == "gpt-4o-mini-2024-07-18"
    assert config.get('system_prompt') == custom_prompt

@patch('argparse.ArgumentParser.parse_args')
@patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key"})
def test_one_shot_prompt(mock_parse_args, mock_chat_interface):
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt="Test prompt",
        system_prompt=None, history_file=None, model=None,
        create_config=False
    )

    with patch.object(sys, 'exit') as mock_exit:
        main.main()

    mock_chat_interface.return_value.one_shot_prompt.assert_called_once_with("Test prompt")
    mock_exit.assert_called_once_with(0)

@patch('argparse.ArgumentParser.parse_args')
@patch('modules.Config.Config.create_default_config')
def test_create_config_option(mock_create_default_config, mock_parse_args):
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None, system_prompt=None,
        history_file=None, model=None, sassy=False, config="~/.llm_chat_cli.toml",
        create_config=True
    )
    mock_create_default_config.return_value = True

    main.main()

    mock_create_default_config.assert_called_once()

if __name__ == "__main__":
    pytest.main()
