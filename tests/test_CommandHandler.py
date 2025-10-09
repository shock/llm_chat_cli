import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import MagicMock, patch
from modules.CommandHandler import CommandHandler
from modules.InAppHelp import IN_APP_HELP

class MockChatInterface:
    def __init__(self):
        self.chat_history = MagicMock()
        self.history = MagicMock()
        self.print_history = MagicMock()
        self.edit_system_prompt = MagicMock()
        self.show_config = MagicMock()
        self.config = {
            'api_key': 'sk-1234567890abcdef',
            'model': 'gpt-4o-mini-2024-07-18',
            'system_prompt': 'You are a helpful assistant.',
            'sassy': False,
            'stream': True
        }
        self.handle_code_block_command = MagicMock()
        self.export_markdown = MagicMock()
        self.set_model = MagicMock()
        self.set_default_model = MagicMock()
        self.clear_history = MagicMock()

@pytest.fixture
def command_handler():
    return CommandHandler(MockChatInterface())

def test_help_command(command_handler, capsys):
    command_handler.handle_command('/help')
    captured = capsys.readouterr()
    assert IN_APP_HELP in captured.out

def test_clear_history_command(command_handler, capsys):
    command_handler.handle_command('/clear_history')
    command_handler.chat_interface.chat_history.clear_history.assert_called_once()
    captured = capsys.readouterr()
    assert "Chat file history cleared." in captured.out

@patch('os.system')
def test_clear_command(mock_system, command_handler):
    command_handler.handle_command('/clear')
    mock_system.assert_called_once()

def test_reset_command(command_handler, capsys):
    command_handler.handle_command('/reset')
    command_handler.chat_interface.clear_history.assert_called_once()
    captured = capsys.readouterr()
    assert "Chat history reset." in captured.out

@patch('builtins.input', return_value='test.json')
def test_save_command(mock_input, command_handler):
    command_handler.handle_command('/save')
    command_handler.chat_interface.history.save_history.assert_called_once_with('test.json')

@patch('builtins.input', return_value='test.json')
def test_load_command(mock_input, command_handler):
    command_handler.chat_interface.history.load_history.return_value = True
    command_handler.handle_command('/load')
    command_handler.chat_interface.history.load_history.assert_called_once_with('test.json')
    command_handler.chat_interface.print_history.assert_called_once()

def test_sp_command(command_handler):
    command_handler.handle_command('/sp')
    command_handler.chat_interface.edit_system_prompt.assert_called_once()

def test_cb_command(command_handler):
    command_handler.handle_command('/cb')
    command_handler.chat_interface.handle_code_block_command.assert_called_once()

def test_md_command(command_handler):
    command_handler.handle_command('/md')
    command_handler.chat_interface.export_markdown.assert_called_once()

def test_unknown_command(command_handler, capsys):
    command_handler.handle_command('/unknown')
    captured = capsys.readouterr()
    assert "Unknown command. Type /h for a list of commands." in captured.out

@pytest.mark.parametrize("exit_command", ['/exit', '/e', '/q'])
def test_exit_command(exit_command, command_handler):
    with pytest.raises(SystemExit):
        command_handler.handle_command(exit_command)
