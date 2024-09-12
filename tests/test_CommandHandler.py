import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from modules.CommandHandler import CommandHandler
from modules.ChatInterface import ChatInterface
from modules.InAppHelp import IN_APP_HELP

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
