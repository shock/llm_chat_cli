import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from modules.MessageHistory import MessageHistory

def test_initialization():
    """Test the initialization of MessageHistory."""
    with pytest.raises(ValueError):
        MessageHistory()
    history = MessageHistory(system_prompt="Test System Prompt")
    assert history.get_history()[0]['role'] == 'system'
    assert history.get_history()[0]['content'] == 'Test System Prompt'

def test_system_prompt():
    """Test setting and getting the system prompt."""
    history = MessageHistory(system_prompt="Initial Prompt")
    assert history.system_prompt() == "Initial Prompt"
    history.system_prompt("Updated Prompt")
    assert history.system_prompt() == "Updated Prompt"

def test_add_message():
    """Test adding messages to the history."""
    history = MessageHistory(system_prompt="Test System Prompt")
    history.add_message("user", "Hello")
    history.add_message("assistant", "Hi there!")
    assert len(history.get_history()) == 3
    assert history.get_history()[1]['role'] == 'user'
    assert history.get_history()[1]['content'] == 'Hello'
    assert history.get_history()[2]['role'] == 'assistant'
    assert history.get_history()[2]['content'] == 'Hi there!'

def test_clear_history():
    """Test clearing the message history."""
    history = MessageHistory(system_prompt="Test System Prompt")
    history.add_message("user", "Hello")
    history.clear_history()
    assert len(history.get_history()) == 1
    assert history.get_history()[0]['role'] == 'system'

def test_seek_messages():
    """Test seeking previous and next messages."""
    history = MessageHistory(system_prompt="Test System Prompt")
    history.add_message("user", "Hello")
    history.add_message("assistant", "Hi there!")
    history.add_message("user", "How are you?")
    history.add_message("assistant", "I'm good, thanks!")

    assert history.seek_previous_user_message()['content'] == "How are you?"
    assert history.seek_previous_user_message()['content'] == "Hello"
    assert history.seek_next_user_message()['content'] == "How are you?"
    assert history.seek_next_user_message() == None

    assert history.seek_previous_assistant_message()['content'] == "Hi there!"
    assert history.seek_next_assistant_message() == None

def test_update_user_message():
    """Test updating the user message at the current seek index."""
    history = MessageHistory(system_prompt="Test System Prompt")
    history.add_message("user", "Hello")
    history.add_message("assistant", "Hi there!")
    history.add_message("user", "How are you?")
    history.add_message("assistant", "I'm good, thanks!")

    history.seek_previous_user_message()
    assert history.seek_previous_user_message()['content'] == "Hello"
    history.update_user_message("Hello, how are you?")
    assert history.get_history()[1]['content'] == "Hello, how are you?"
    assert len(history.get_history()) == 2

def test_save_and_load_history(tmp_path):
    """Test saving and loading the message history."""
    history = MessageHistory(system_prompt="Test System Prompt")
    history.add_message("user", "Hello")
    history.add_message("assistant", "Hi there!")

    file_path = tmp_path / "test_history.json"
    history.save_history(file_path)

    new_history = MessageHistory(system_prompt="Test System Prompt")
    new_history.load_history(file_path)
    assert new_history.get_history() == history.get_history()
