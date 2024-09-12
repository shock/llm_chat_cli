import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from modules.CommandHandler import CommandHandler
from modules.ChatInterface import ChatInterface
from modules.InAppHelp import IN_APP_HELP
import tempfile

class MockChatInterface:
    def __init__(self):
        self.chat_history = MockMessageHistory()
        self.history = MockMessageHistory()

    def print_history(self):
        print("Mock history printed")

    def edit_system_prompt(self):
        pass

    def handle_code_block_command(self):
        pass

class MockMessageHistory:
    def clear_history(self):
        pass

    def save_history(self, filename):
        pass

    def load_history(self, filename):
        return True

@pytest.fixture
def command_handler():
    chat_interface = MockChatInterface()
    return CommandHandler(chat_interface)

def test_handle_command_help(capsys, command_handler):
    command_handler.handle_command('/help')
    captured = capsys.readouterr()
    assert IN_APP_HELP in captured.out  # Use actual expected output

def test_handle_command_clear_history(command_handler):
    command_handler.handle_command('/clear_history')
    # Add assertions to verify history is cleared

def test_handle_command_clear(capsys, command_handler):
    command_handler.handle_command('/clear')
    captured = capsys.readouterr()
    # Remove assertion for "Terminal cleared"

def test_handle_command_reset(command_handler):
    command_handler.handle_command('/reset')
    # Add assertions to verify history is reset

def test_handle_command_save(monkeypatch, command_handler):
    monkeypatch.setattr('builtins.input', lambda _: 'test_history.txt')
    command_handler.handle_command('/save')
    # Add assertions to verify history is saved

def test_handle_command_load(monkeypatch, command_handler):
    monkeypatch.setattr('builtins.input', lambda _: 'test_history.txt')
    command_handler.handle_command('/load')
    # Add assertions to verify history is loaded

def test_handle_command_print(capsys, command_handler):
    command_handler.handle_command('/print')
    captured = capsys.readouterr()
    assert "Mock history printed" in captured.out  # Use actual expected output

def test_handle_command_sp(command_handler):
    command_handler.handle_command('/sp')
    # Add assertions to verify system prompt is edited

def test_handle_command_cb(command_handler):
    command_handler.handle_command('/cb')
    # Add assertions to verify code block command is handled

def test_handle_command_exit(command_handler):
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        command_handler.handle_command('/exit')
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from unittest.mock import MagicMock, patch
from modules.CommandHandler import CommandHandler

class MockChatInterface:
    def __init__(self):
        self.chat_history = MagicMock()
        self.history = MagicMock()
        self.print_history = MagicMock()
        self.edit_system_prompt = MagicMock()
        self.handle_code_block_command = MagicMock()

@pytest.fixture
def command_handler():
    return CommandHandler(MockChatInterface())

def test_help_command(command_handler, capsys):
    command_handler.handle_command('/help')
    captured = capsys.readouterr()
    assert "Available commands:" in captured.out

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
    command_handler.chat_interface.history.clear_history.assert_called_once()
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

@patch('os.system')
def test_print_command(mock_system, command_handler):
    command_handler.handle_command('/print')
    mock_system.assert_called_once()
    command_handler.chat_interface.print_history.assert_called_once()

def test_sp_command(command_handler):
    command_handler.handle_command('/sp')
    command_handler.chat_interface.edit_system_prompt.assert_called_once()

def test_cb_command(command_handler):
    command_handler.handle_command('/cb')
    command_handler.chat_interface.handle_code_block_command.assert_called_once()

def test_unknown_command(command_handler, capsys):
    command_handler.handle_command('/unknown')
    captured = capsys.readouterr()
    assert "Unknown command. Type /h for a list of commands." in captured.out

@pytest.mark.parametrize("exit_command", ['/exit', '/e', '/q'])
def test_exit_command(exit_command, command_handler):
    with pytest.raises(SystemExit):
        command_handler.handle_command(exit_command)
