import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from modules.MarkdownFormatter import MarkdownFormatter


def test_formatting_characters_preserved():
    """Test that formatting characters like #, *, ** are preserved in the output."""
    message = """# Heading 1

This is a paragraph with **bold text** and *italic text*.

## Heading 2

- List item 1
- List item 2

### Heading 3

Here's some `inline code` and a code block:

```python
def hello_world():
    print("Hello, World!")
```

> This is a blockquote

And some more **bold** and *italic* text.
"""

    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # Formatting characters must be preserved - remove permissive OR clauses
    assert "# Heading 1" in formatted_output
    assert "**bold text**" in formatted_output
    assert "*italic text*" in formatted_output
    assert "## Heading 2" in formatted_output
    assert "### Heading 3" in formatted_output
    assert "`inline code`" in formatted_output
    assert "```python" in formatted_output
    assert "> This is a blockquote" in formatted_output


def test_headings_preserve_hashtags():
    """Test that heading hashtags are preserved."""
    message = """# H1 Heading
## H2 Heading
### H3 Heading
#### H4 Heading
##### H5 Heading
###### H6 Heading"""

    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # Headings must preserve their hashtags
    assert "# H1 Heading" in formatted_output
    assert "## H2 Heading" in formatted_output
    assert "### H3 Heading" in formatted_output


def test_bold_and_italic_preserve_asterisks():
    """Test that bold and italic formatting preserves asterisks."""
    message = """This has **bold text** and *italic text* and ***bold italic***.

Also __bold with underscores__ and _italic with underscores_."""

    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # Bold and italic markers must be preserved
    assert "**bold text**" in formatted_output
    assert "*italic text*" in formatted_output
    assert "***bold italic***" in formatted_output


def test_bold_italic_ansi_formatting():
    """Test that bold+italic text gets proper ANSI formatting."""
    message = "This has ***bold italic text*** and regular text."

    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # Check that bold+italic text gets the proper ANSI codes
    bold_italic_ansi = '\033[1;3;33m'
    reset_ansi = '\033[0m'

    # The formatted output should contain ANSI codes around the bold+italic text
    assert bold_italic_ansi in formatted_output
    assert reset_ansi in formatted_output
    assert "***bold italic text***" in formatted_output

    # Verify the ANSI codes are properly placed around the bold+italic content
    expected_pattern = f"{bold_italic_ansi}***bold italic text***{reset_ansi}"
    assert expected_pattern in formatted_output


def test_bold_italic_precedence():
    """Test that bold+italic takes precedence over bold and italic."""
    message = "***bold italic*** **bold only** *italic only*"

    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # All formatting should be preserved
    assert "***bold italic***" in formatted_output
    assert "**bold only**" in formatted_output
    assert "*italic only*" in formatted_output

    # Verify no conflicts between different formatting types
    bold_italic_ansi = '\033[1;3;33m'
    bold_ansi = '\033[1;33m'
    italic_ansi = '\033[3;33m'
    reset_ansi = '\033[0m'

    # Each formatting type should have its own ANSI codes
    assert formatted_output.count(bold_italic_ansi) == 1
    assert formatted_output.count(bold_ansi) == 1
    assert formatted_output.count(italic_ansi) == 1
    assert formatted_output.count(reset_ansi) == 3  # One reset for each formatting block


def test_code_blocks_preserve_backticks():
    """Test that code blocks preserve backticks."""
    message = """Here's some inline `code` and a block:

```python
def function():
    return "hello"
```"""

    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # Code formatting must preserve backticks
    assert "`code`" in formatted_output
    assert "```python" in formatted_output


def test_lists_preserve_markers():
    """Test that list markers are preserved."""
    message = """- Unordered item 1
- Unordered item 2

1. Ordered item 1
2. Ordered item 2"""

    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # List markers must be preserved
    assert "- Unordered item 1" in formatted_output
    assert "1. Ordered item 1" in formatted_output


def test_blockquotes_preserve_gt_sign():
    """Test that blockquotes preserve the > character."""
    message = """> This is a blockquote
> With multiple lines
> And more content"""

    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # Blockquote markers must be preserved
    assert "> This is a blockquote" in formatted_output


def test_links_and_images_preserve_syntax():
    """Test that link and image syntax is preserved."""
    message = """[Link text](https://example.com)
![Alt text](image.jpg)"""

    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # Link and image syntax must be preserved
    assert "[Link text](https://example.com)" in formatted_output
    assert "![Alt text](image.jpg)" in formatted_output


def test_escape_sequences_preserved():
    """Test that escape sequences and special characters are preserved."""
    message = """\\*escaped asterisk\\*
\\#escaped hashtag
\\`escaped backtick\\`"""

    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # Escape sequences must be preserved
    assert "\\*escaped asterisk\\*" in formatted_output
    assert "\\#escaped hashtag" in formatted_output


def test_mixed_formatting_preserved():
    """Test complex mixed formatting preserves all markers."""
    message = """# Heading with **bold** and *italic*

- List item with `code`
- Another item with **bold**

> Blockquote with *italic*

```python
# Code comment
print("Hello")
```"""

    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # All formatting must be preserved
    assert "# Heading" in formatted_output
    assert "**bold**" in formatted_output
    assert "*italic*" in formatted_output
    assert "`code`" in formatted_output
    assert "> Blockquote" in formatted_output
    assert "```python" in formatted_output


def test_code_block_extraction_still_works():
    """Test that code block extraction functionality still works."""
    message = """Some text

```python
def hello():
    print("hello")
```

More text"""

    formatter = MarkdownFormatter(message)
    code_blocks = formatter._extract_code_blocks()

    assert len(code_blocks) == 1
    assert code_blocks[0][0] == 'python'
    assert 'def hello():' in code_blocks[0][1]


def test_format_message_returns_string():
    """Test that formatted_messageeturns a string."""
    message = "Simple text message"
    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    assert isinstance(formatted_output, str)
    assert len(formatted_output) > 0

encoded_def_hello = '\x1b[34mdef\x1b[39;49;00m \x1b[32mhello_world\x1b[39;49;00m():\x1b[37m\x1b[39;49;00m'

def test_extract_code_blocks():
    message = """
    Here is some text with a code block:
    ```python
    def hello_world():
        print("Hello, World!")
    ```
    """
    helper = MarkdownFormatter(message)
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
    helper = MarkdownFormatter(message)
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
    helper = MarkdownFormatter(message)
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
    helper = MarkdownFormatter(message)
    helper.list_code_blocks()
    captured = capsys.readouterr()
    assert '1 :' in captured.out
    assert encoded_def_hello in captured.out

def test_select_code_block(monkeypatch):
    message = """
    Here is some text with a code block:
    ```python
    def goodbye_world():
        print("Goodbye, World!")
    ```
    ```python
    def hello_world():
        print("Hello, World!")
    ```
    """
    helper = MarkdownFormatter(message)
    monkeypatch.setattr('builtins.input', lambda _: "2")
    selected_code = helper.select_code_block()
    assert selected_code == '    def hello_world():\n        print("Hello, World!")\n'
