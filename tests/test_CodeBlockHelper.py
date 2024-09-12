import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from modules.CodeBlockHelper import CodeBlockHelper

encoded_def_hello = '\x1b[34mdef\x1b[39;49;00m \x1b[32mhello_world\x1b[39;49;00m():\x1b[37m\x1b[39;49;00m'

def test_extract_code_blocks():
    message = """
    Here is some text with a code block:
    ```python
    def hello_world():
        print("Hello, World!")
    ```
    """
    helper = CodeBlockHelper(message)
    assert len(helper.code_blocks) == 1
    assert helper.code_blocks[0] == ('python', '    def hello_world():\n        print("Hello, World!")\n')

def test_highlighted_code_blocks():
    message = """
    Here is some text with a code block:
    ```python
    def hello_world():
        print("Hello, World!")
    ```
    """
    helper = CodeBlockHelper(message)
    highlighted_blocks = helper._highlighted_code_blocks()
    assert len(highlighted_blocks) == 1
    assert encoded_def_hello in highlighted_blocks[0]

def test_highlighted_message():
    message = """
    Here is some text with a code block:
    ```python
    def hello_world():
        print("Hello, World!")
    ```
    """
    helper = CodeBlockHelper(message)
    highlighted_message = helper._highlighted_message()
    assert encoded_def_hello in highlighted_message
    assert '```python' in highlighted_message

def test_list_code_blocks(capsys):
    message = """
    Here is some text with a code block:
    ```python
    def hello_world():
        print("Hello, World!")
    ```
    """
    helper = CodeBlockHelper(message)
    helper.list_code_blocks()
    captured = capsys.readouterr()
    assert '1 :' in captured.out
    assert encoded_def_hello in captured.out

def test_select_code_block(monkeypatch):
    message = """
    Here is some text with a code block:
    ```python
    def hello_world():
        print("Hello, World!")
    ```
    """
    helper = CodeBlockHelper(message)
    monkeypatch.setattr('builtins.input', lambda _: "1")
    selected_code = helper.select_code_block()
    assert selected_code == '    def hello_world():\n        print("Hello, World!")\n'
