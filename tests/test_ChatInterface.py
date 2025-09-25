import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import MagicMock, patch
from modules.ChatInterface import ChatInterface, SigTermException
from modules.Config import Config
from modules.OpenAIChatCompletionApi import PROVIDER_DATA

@pytest.fixture
def mock_config():
    with patch('main.Config') as mock:
        mock.return_value.get.return_value = "mocked_value"
        mock.return_value.is_sassy.return_value = False
        yield mock

@pytest.fixture
def chat_interface():
    providers = {}
    for provider in PROVIDER_DATA.keys():
        providers[provider] = {} if not providers.get(provider) else providers[provider]
        providers[provider]["api_key"] = "test_api_key"
    config = Config(data_directory="/tmp", overrides={"providers": providers, "model": "4o-mini"})
    # Don't override the model since we need a valid one for tests
    config.config.system_prompt = "test_system_prompt"
    config.config.stream = False
    return ChatInterface(config)

def test_init(chat_interface):
    assert chat_interface.api.api_key == "test_api_key"
    assert chat_interface.api.model == "gpt-4o-mini-2024-07-18"
    assert chat_interface.history.system_prompt() == "test_system_prompt"
    assert isinstance(chat_interface.config, Config)

def test_init_no_api_key(mock_config):
    config = Config(data_directory="/tmp", overrides={"providers": {"openai": {"api_key": ""}}, "model": "4o-mini"})
    with pytest.raises(ValueError):
        ChatInterface(config)
    config = Config(data_directory="/tmp")
    with pytest.raises(ValueError):
        ChatInterface(config)

def test_run(chat_interface):
    mock_prompt = MagicMock()
    mock_prompt.prompt.side_effect = ["test input", KeyboardInterrupt(), SigTermException()]
    chat_interface.session = mock_prompt

    chat_interface.command_handler.handle_command = MagicMock()
    chat_interface.api.get_chat_completion = MagicMock(return_value={
        'choices': [{'message': {'content': 'AI response'}}]
    })

    chat_interface.run()

    chat_interface.api.get_chat_completion.assert_called_once()
    assert chat_interface.history.get_history()[-1]['content'] == 'AI response'

def test_print_assistant_message(capsys, chat_interface):
    chat_interface.print_assistant_message("Test message")
    captured = capsys.readouterr()
    assert "Test message" in captured.out

def test_print_history(capsys, chat_interface):
    chat_interface.history.add_message("user", "User message")
    chat_interface.history.add_message("assistant", "Assistant message")
    chat_interface.print_history()
    captured = capsys.readouterr()
    assert "User message" in captured.out
    assert "Assistant message" in captured.out

@patch('modules.ChatInterface.pyperclip')
@patch('builtins.input', return_value='1')
def test_handle_code_block_command(mock_input, mock_pyperclip, chat_interface):
    chat_interface.history.add_message("assistant", "```python\nprint('Hello')\n```")
    chat_interface.handle_code_block_command()
    mock_pyperclip.copy.assert_called_once_with("print('Hello')\n")

def test_edit_system_prompt(chat_interface):
    with patch('modules.ChatInterface.prompt', return_value="New system prompt"):
        chat_interface.edit_system_prompt()
    assert chat_interface.history.system_prompt() == "New system prompt"

@patch('modules.ChatInterface.pyperclip')
def test_copy_last_response(mock_pyperclip, chat_interface):
    chat_interface.history.add_message("assistant", "Last response")
    chat_interface.copy_last_response()
    mock_pyperclip.copy.assert_called_once_with("Last response")

def test_one_shot_prompt(capsys, chat_interface):
    chat_interface.api.get_chat_completion = MagicMock(return_value={
        'choices': [{'message': {'content': 'One-shot response'}}]
    })
    response = chat_interface.one_shot_prompt("One-shot prompt")
    captured = capsys.readouterr()
    assert "One-shot response" in captured.out
    assert response == "One-shot response"

def test_show_config(capsys, chat_interface):
    # Update provider config

    chat_interface.show_config()
    captured = capsys.readouterr()

    assert "API Key       : ********_key" in captured.out
    assert "Model         : gpt-4" in captured.out
    assert "System Prompt :\n\ntest_system_prompt" in captured.out
    assert "Sassy Mode    : Disabled" in captured.out
    assert "Stream Mode   : Disabled" in captured.out

# @patch('modules.ChatInterface.pyperclip')
# @patch('builtins.print')
# @patch('modules.ChatInterface.pyperclip')
# def test_handle_code_block_command_no_code_blocks(mock_input, mock_print, mock_pyperclip, chat_interface):
#     chat_interface.history.add_message("assistant", "No code blocks here")
#     chat_interface.handle_code_block_command()
#     mock_print.assert_called_with("No code blocks found in the last assistant message.")
#     mock_pyperclip.copy.assert_not_called()

@patch('modules.ChatInterface.prompt')
def test_edit_system_prompt_cancelled(mock_prompt, chat_interface):
    mock_prompt.side_effect = KeyboardInterrupt()
    chat_interface.edit_system_prompt()
    assert chat_interface.history.system_prompt() == "test_system_prompt"  # Original prompt unchanged

@patch('modules.ChatInterface.pyperclip')
def test_copy_last_response_no_response(mock_pyperclip, capsys, chat_interface):
    chat_interface.history.get_last_assistant_message = MagicMock(return_value=None)
    chat_interface.copy_last_response()
    captured = capsys.readouterr()
    assert "No assistant response found to copy." in captured.out
    mock_pyperclip.copy.assert_not_called()

def test_one_shot_prompt_api_error(capsys, chat_interface):
    chat_interface.api.get_chat_completion = MagicMock(return_value={
        'error': {'message': 'API Error'}
    })
    result = chat_interface.one_shot_prompt("One-shot prompt")
    assert result == "API Error"
    captured = capsys.readouterr()
    # assert "API ERROR:API Error" in captured.out

def test_get_api_for_model_string_openai():
    from modules.OpenAIChatCompletionApi import OpenAIChatCompletionApi
    api = OpenAIChatCompletionApi.get_api_for_model_string( model_string="openai/gpt-4o-2024-08-06" )
    assert api.__class__.__name__ == "OpenAIChatCompletionApi"
    assert api.model == "gpt-4o-2024-08-06"
    assert api.api_key == "test_api_key"
    assert api.base_api_url == "https://api.openai.com/v1"

def test_get_api_for_model_string_deepseek():
    from modules.OpenAIChatCompletionApi import OpenAIChatCompletionApi
    api = OpenAIChatCompletionApi.get_api_for_model_string( model_string="deepseek/deepseek-chat" )
    assert api.__class__.__name__ == "OpenAIChatCompletionApi"
    assert api.model == "deepseek-chat"
    assert api.api_key == "ds-test_api_key"  # Changed from test_key to test_api_key
    assert api.base_api_url == "https://api.deepseek.com/v1"

def test_get_api_for_model_string_default_openai():
    from modules.OpenAIChatCompletionApi import OpenAIChatCompletionApi
    api = OpenAIChatCompletionApi.get_api_for_model_string( model_string="gpt-4o-2024-08-06" )  # No provider prefix
    assert api.__class__.__name__ == "OpenAIChatCompletionApi"
    assert api.model == "gpt-4o-2024-08-06"

def test_get_api_for_model_string_unsupported_provider():
    from modules.OpenAIChatCompletionApi import OpenAIChatCompletionApi
    with pytest.raises(ValueError, match="Invalid provider prefix: unsupported"):
        OpenAIChatCompletionApi.get_api_for_model_string( model_string="unsupported/chat" )

# Test the export_markdown method
# Mock the OpenAIApi class to return a mock response
# @patch('modules.OpenAIApi')  # Patch the OpenAIApi class
@patch('modules.ChatInterface.pyperclip')
def test_export_markdown(mock_pyperclip, chat_interface):
    chat_interface.api.get_chat_completion = MagicMock(return_value={
        'choices': [{'message': {'content': 'API RESPONSE'}}]
    })
    history = [
        {"role": "system", "content": "System message"},
        {"role": "user", "content": "User message"},
        {"role": "assistant", "content": "Assistant message"},
        {"role": "user", "content": "Second user message"},
        {"role": "assistant", "content": "Second assistant message"},
    ]
    chat_interface.history.history = history
    chat_interface.export_markdown()
    # be sure it doesn't change the original history
    assert history[0]['role'] == 'system'
    assert history[0]['content'] == 'System message'
    assert history[1]['role'] == 'user'
    assert history[1]['content'] == 'User message'
    assert history[2]['role'] == 'assistant'
    assert history[2]['content'] == 'Assistant message'
    mock_pyperclip.copy.assert_called()
