import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tempfile
import pytest
from modules.CustomFileHistory import CustomFileHistory
def test_initialization():
    """Test the initialization of CustomFileHistory."""
    with tempfile.NamedTemporaryFile() as temp_file:
        history = CustomFileHistory(temp_file.name)
        assert history.max_history is None
        assert history.skip_prefixes == []

        history = CustomFileHistory(temp_file.name, max_history=10, skip_prefixes=["#", "//"])
        assert history.max_history == 10
        assert history.skip_prefixes == ["#", "//"]
def test_append_string():
    """Test appending strings to the history."""
    with tempfile.NamedTemporaryFile() as temp_file:
        history = CustomFileHistory(temp_file.name, skip_prefixes=["#"])
        history.append_string("Hello")
        assert history._loaded_strings[0] == "Hello"
        history.append_string("#Skip this")
        assert history._loaded_strings[0] == "Hello"
        history.append_string("World\nWide")
        history.append_string("Again")
        assert history._loaded_strings[0] == "Again"
def test_truncate_file():
    """Test truncating the file when the history exceeds the maximum limit."""
    with tempfile.NamedTemporaryFile() as temp_file:
        history = CustomFileHistory(temp_file.name, max_history=2)
        history.append_string("Hello")
        history.append_string("World\nWide")
        history.append_string("Again")
        history._truncate_file()
        assert len(history._loaded_strings) == 2
        history = CustomFileHistory(temp_file.name, max_history=2)
        history.load()
        strings = list(history.load_history_strings())
        assert len(strings) == 2
        assert strings[0] == "Again"
        assert strings[1] == "World\nWide"
def test_clear_history():
    """Test clearing the history file."""
    with tempfile.NamedTemporaryFile() as temp_file:
        history = CustomFileHistory(temp_file.name)
        history.append_string("Hello")
        history.append_string("World")
        history.clear_history()

        with open(temp_file.name, "r") as f:
            lines = f.readlines()
            assert len(lines) == 0
