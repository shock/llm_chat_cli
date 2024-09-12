import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import MagicMock, patch
from modules.ChatInterface import ChatInterface
from modules.CommandHandler import CommandHandler

@pytest.fixture
def chat_interface():
    api_key = "test_api_key"
    model = "test_model"
    system_prompt = "test_system_prompt"
    return ChatInterface(api_key, model, system_prompt)

def test_init(chat_interface):
    assert chat_interface.api.api_key == "test_api_key"
    assert chat_interface.api.model == "test_model"
    assert chat_interface.history.system_prompt() == "test_system_prompt"

def test_run(chat_interface):
    mock_prompt = MagicMock()
    mock_prompt.prompt.side_effect = ["test input", KeyboardInterrupt()]
    chat_interface.session = mock_prompt

    chat_interface.command_handler.handle_command = MagicMock()
    chat_interface.api.get_chat_completion = MagicMock(return_value={
        'choices': [{'message': {'content': 'AI response'}}]
    })

    with pytest.raises(SystemExit):
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
