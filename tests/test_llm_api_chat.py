import sys
import os
import pytest
from unittest.mock import patch, MagicMock
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import llm_api_chat

@pytest.fixture
def mock_chat_interface():
    with patch('llm_api_chat.ChatInterface') as mock:
        yield mock

def test_version():
    assert llm_api_chat.VERSION == "1.3.1"

def test_default_system_prompt():
    assert "You're name is Lemmy." in llm_api_chat.DEFAULT_SYSTEM_PROMPT
    assert "Call the user brother (with a lowercase b)" in llm_api_chat.DEFAULT_SYSTEM_PROMPT

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
def test_clear_option(mock_system, mock_parse_args, mock_chat_interface):
    mock_parse_args.return_value = MagicMock(clear=True, help=False, prompt=None)
    
    with patch.object(sys, 'exit') as mock_exit:
        llm_api_chat.main()
    
    mock_system.assert_called_once_with('cls' if os.name == 'nt' else 'clear')

@patch('argparse.ArgumentParser.parse_args')
@patch('argparse.ArgumentParser.print_help')
def test_help_option(mock_print_help, mock_parse_args, mock_chat_interface):
    mock_parse_args.return_value = MagicMock(help=True)
    
    llm_api_chat.main()
    
    mock_print_help.assert_called_once()

@patch('argparse.ArgumentParser.parse_args')
@patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key"})
def test_chat_interface_creation(mock_parse_args, mock_chat_interface):
    # Test default mode (non-sassy)
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt=None, system_prompt=None, 
        history_file=None, model=None, sassy=False
    )
    
    llm_api_chat.main()
    
    mock_chat_interface.assert_called_with(
        "test_api_key", 
        model="gpt-4o-mini-2024-07-18", 
        system_prompt=llm_api_chat.DEFAULT_SYSTEM_PROMPT
    )

    # Test sassy mode
    mock_parse_args.return_value.sassy = True
    llm_api_chat.main()
    
    mock_chat_interface.assert_called_with(
        "test_api_key", 
        model="gpt-4o-mini-2024-07-18", 
        system_prompt=llm_api_chat.SASSY_SYSTEM_PROMPT
    )

    # Test with custom system prompt (overrides sassy mode)
    mock_parse_args.return_value.system_prompt = "Custom system prompt"
    llm_api_chat.main()
    
    mock_chat_interface.assert_called_with(
        "test_api_key", 
        model="gpt-4o-mini-2024-07-18", 
        system_prompt="Custom system prompt"
    )

@patch('argparse.ArgumentParser.parse_args')
@patch.dict(os.environ, {"OPENAI_API_KEY": "test_api_key"})
def test_one_shot_prompt(mock_parse_args, mock_chat_interface):
    mock_parse_args.return_value = MagicMock(
        clear=False, help=False, prompt="Test prompt", 
        system_prompt=None, history_file=None, model=None
    )
    
    with patch.object(sys, 'exit') as mock_exit:
        llm_api_chat.main()
    
    mock_chat_interface.return_value.one_shot_prompt.assert_called_once_with("Test prompt")
    mock_exit.assert_called_once_with(0)

if __name__ == "__main__":
    pytest.main()
