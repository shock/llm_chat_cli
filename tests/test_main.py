import sys
import os
import pytest
from unittest.mock import patch, MagicMock
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.Config import Config
from modules.ChatInterface import ChatInterface
import main

@pytest.fixture
def mock_chat_interface():
    with patch('main.ChatInterface') as mock:
        yield mock

@pytest.fixture
def mock_config():
    with patch('main.Config') as mock:
        mock.return_value.get.return_value = "mocked_value"
        mock.return_value.is_sassy.return_value = False
        yield mock

def test_version():
    assert main.VERSION == "1.7.1 - beta"

@pytest.mark.parametrize("env_var, expected", [
    ("OPENAI_API_KEY", "test_api_key"),
    ("LLMC_DEFAULT_MODEL", "test_model"),
    ("LLMC_SYSTEM_PROMPT", "test_system_prompt"),
])
def test_environment_variables(monkeypatch, env_var, expected):
    monkeypatch.setenv(env_var, expected)
    assert os.getenv(env_var) == expected

@patch('argparse.ArgumentParser.parse_args')
@patch('os.system')
def test_clear_option(mock_system, mock_parse_args, mock_chat_interface, mock_config):
    mock_parse_args.return_value = MagicMock(clear=True, help=False, prompt=None, create_config=False, data_directory=None)

    main.main()

    mock_system.assert_called_once_with('cls' if os.name == 'nt' else 'clear')

@patch('argparse.ArgumentParser.parse_args')
@patch('argparse.ArgumentParser.print_help')
def test_help_option(mock_print_help, mock_parse_args, mock_chat_interface, mock_config):
    mock_parse_args.return_value = MagicMock(help=True, create_config=False, data_directory=None)

    main.main()

    mock_print_help.assert_called_once()

@patch('argparse.ArgumentParser.parse_args')
def test_chat_interface_creation(mock_parse_args, monkeypatch, mock_chat_interface, mock_config):
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None, system_prompt=None,
        history_file=None, model=None, sassy=False, config="~/.llm_chat_cli.toml",
        create_config=False, data_directory=None
    )
    monkeypatch.setenv("OPENAI_API_KEY", "test_api_key")

    main.main()

    mock_chat_interface.assert_called_once()
    mock_config.assert_called_once()

    # Test sassy mode
    mock_parse_args.return_value.sassy = True
    mock_config.return_value.is_sassy.return_value = True
    main.main()

    mock_chat_interface.assert_called()
    mock_config.assert_called()

    # Test with custom system prompt
    custom_prompt = "Custom system prompt"
    mock_parse_args.return_value.system_prompt = custom_prompt
    main.main()

    mock_chat_interface.assert_called()
    mock_config.assert_called()

@patch('argparse.ArgumentParser.parse_args')
@patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key"})
def test_one_shot_prompt(mock_parse_args, mock_chat_interface, mock_config):
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt="Test prompt",
        system_prompt=None, history_file=None, model=None,
        create_config=False, data_directory=None
    )

    with patch.object(sys, 'exit') as mock_exit:
        main.main()

    mock_chat_interface.return_value.one_shot_prompt.assert_called_once_with("Test prompt")
    mock_exit.assert_called_once_with(0)

@patch('argparse.ArgumentParser.parse_args')
def test_create_config_option(mock_parse_args, mock_config):
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None, system_prompt=None,
        history_file=None, model=None, sassy=False, config="~/.llm_chat_cli.toml",
        create_config=True, data_directory=None
    )

    main.main()

    mock_config.assert_called_once()
    assert mock_config.call_args[1]['create_config'] == True

@patch.dict(os.environ, {"OPENAI_API_KEY": "other_test_api_key"})
@patch('argparse.ArgumentParser.parse_args')
def test_override_option(mock_parse_args, mock_config):
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None, system_prompt=None,
        history_file=None, model=None, sassy=False, config=None,
        create_config=False, data_directory=None, override=True
    )

    def mock_run():
        print("Mock run")

    ChatInterface = MagicMock()
    ChatInterface.return_value.run = mock_run
    main.main()

    mock_config.assert_called_once()
    assert mock_config.return_value.config.api_key == "other_test_api_key"

if __name__ == "__main__":
    pytest.main()
