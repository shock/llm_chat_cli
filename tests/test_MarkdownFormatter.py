import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from modules.MarkdownFormatter import MarkdownFormatter, RESET, BOLD_ENABLE, BOLD_DISABLE, ITALIC_ENABLE, ITALIC_DISABLE, STRIKETHROUGH_ENABLE, STRIKETHROUGH_DISABLE, HEADING_COLOR, LIST_COLOR, BLOCKQUOTE_COLOR

def strip_ansi_codes(s):
    """Utility function to strip ANSI codes from a string for easier testing."""
    import re
    ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', s)

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

    # Formatting characters must be preserved with ANSI codes
    assert "# Heading 1" in formatted_output
    assert f"{BOLD_ENABLE}**bold text**{BOLD_DISABLE}" in formatted_output
    assert f"{ITALIC_ENABLE}*italic text*{ITALIC_DISABLE}" in formatted_output
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
    assert "#### H4 Heading" in formatted_output
    assert "##### H5 Heading" in formatted_output
    assert "###### H6 Heading" in formatted_output


def test_bold_and_italic_preserve_asterisks():
    """Test that bold and italic formatting preserves asterisks."""
    message = """This has **bold text** and *italic text* and ***bold italic***.

Also __bold with underscores__ and _italic with underscores_."""

    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # Bold and italic markers must be preserved with ANSI codes
    assert f"{BOLD_ENABLE}**bold text**{BOLD_DISABLE}" in formatted_output
    assert f"{ITALIC_ENABLE}*italic text*{ITALIC_DISABLE}" in formatted_output
    assert f"{BOLD_ENABLE}{ITALIC_ENABLE}***bold italic***{ITALIC_DISABLE}{BOLD_DISABLE}" in formatted_output
    assert f"{BOLD_ENABLE}__bold with underscores__{BOLD_DISABLE}" in formatted_output
    assert f"{ITALIC_ENABLE}_italic with underscores_{ITALIC_DISABLE}" in formatted_output


def test_bold_italic_ansi_formatting():
    """Test that bold+italic text gets proper ANSI formatting."""
    message = """This has ***bold italic text*** and regular text.
Also ___bold italic with underscores___."""

    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # The formatted output should contain ANSI codes around the bold+italic text
    assert "***bold italic text***" in formatted_output

    # Verify the ANSI codes are properly placed around the bold+italic content
    expected_pattern = f"{BOLD_ENABLE}{ITALIC_ENABLE}***bold italic text***{ITALIC_DISABLE}{BOLD_DISABLE}"
    assert expected_pattern in formatted_output

    # Check that bold italic with underscores gets the proper ANSI codes
    assert "___bold italic with underscores___" in formatted_output

    # Verify the ANSI codes are properly placed around the bold+italic content
    expected_pattern = f"{BOLD_ENABLE}{ITALIC_ENABLE}___bold italic with underscores___{ITALIC_DISABLE}{BOLD_DISABLE}"
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
    bold_italic_ansi = f"{BOLD_ENABLE}{ITALIC_ENABLE}"
    bold_ansi = BOLD_ENABLE
    italic_ansi = ITALIC_ENABLE

    # Each formatting type should have its own ANSI codes
    assert formatted_output.count(bold_italic_ansi) == 1
    assert formatted_output.count(bold_ansi) == 2  # bold only + bold+italic
    assert formatted_output.count(italic_ansi) == 2  # italic only + bold+italic
    assert formatted_output.count(RESET) == 0  # No resets because all are closed properly


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


def test_strikethrough_basic():
    """Test basic strikethrough functionality."""
    message = "This has ~~strikethrough text~~ and regular text."
    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # Strikethrough markers must be preserved
    assert "~~strikethrough text~~" in formatted_output

    # Should contain strikethrough ANSI codes
    assert STRIKETHROUGH_ENABLE in formatted_output
    assert STRIKETHROUGH_DISABLE in formatted_output


def test_strikethrough_with_bold():
    """Test strikethrough combined with bold formatting."""
    message = "~~**bold strikethrough**~~ **~~bold strikethrough~~** and **bold only**"
    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # All formatting markers must be preserved
    assert f"{STRIKETHROUGH_ENABLE}~~{BOLD_ENABLE}**bold strikethrough**{BOLD_DISABLE}~~{STRIKETHROUGH_DISABLE}" in formatted_output
    assert f"{BOLD_ENABLE}**{STRIKETHROUGH_ENABLE}~~bold strikethrough~~{STRIKETHROUGH_DISABLE}**{BOLD_DISABLE}" in formatted_output
    assert f"**bold only**" in formatted_output

    # Should contain appropriate ANSI codes
    assert formatted_output.count(STRIKETHROUGH_ENABLE) == 2
    assert formatted_output.count(BOLD_ENABLE) == 3
    assert formatted_output.count(STRIKETHROUGH_DISABLE) == 2
    assert formatted_output.count(BOLD_DISABLE) == 3

def test_strikethrough_with_italic():
    """Test strikethrough combined with italic formatting."""
    message = "~~*italic strikethrough*~~ and *~~italic strikethrough~~* and *italic only*"
    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # All formatting markers must be preserved
    assert f"{STRIKETHROUGH_ENABLE}~~{ITALIC_ENABLE}*italic strikethrough*{ITALIC_DISABLE}~~{STRIKETHROUGH_DISABLE}" in formatted_output
    assert f"{ITALIC_ENABLE}*{STRIKETHROUGH_ENABLE}~~italic strikethrough~~{STRIKETHROUGH_DISABLE}*{ITALIC_DISABLE}" in formatted_output
    assert f"{ITALIC_ENABLE}*italic only*{ITALIC_DISABLE}" in formatted_output

    # Should contain appropriate ANSI codes
    # assert strikethrough_enable occures in formatted_output twice
    assert formatted_output.count(STRIKETHROUGH_ENABLE) == 2
    assert formatted_output.count(STRIKETHROUGH_DISABLE) == 2
    assert formatted_output.count(ITALIC_ENABLE) == 3
    assert formatted_output.count(ITALIC_DISABLE) == 3


def test_strikethrough_with_bold_italic():
    """Test strikethrough combined with bold+italic formatting."""
    message = "~~***bold italic strikethrough***~~ and ***~~bold italic strikethrough~~*** and ***bold italic only***"
    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # All formatting markers must be preserved
    assert f"{STRIKETHROUGH_ENABLE}~~{BOLD_ENABLE}{ITALIC_ENABLE}***bold italic strikethrough***{ITALIC_DISABLE}{BOLD_DISABLE}~~{STRIKETHROUGH_DISABLE}" in formatted_output
    assert f"{BOLD_ENABLE}{ITALIC_ENABLE}***{STRIKETHROUGH_ENABLE}~~bold italic strikethrough~~{STRIKETHROUGH_DISABLE}***{ITALIC_DISABLE}{BOLD_DISABLE}" in formatted_output
    assert f"{BOLD_ENABLE}{ITALIC_ENABLE}***bold italic only***{ITALIC_DISABLE}{BOLD_DISABLE}" in formatted_output

    # Should contain appropriate ANSI codes
    assert formatted_output.count(STRIKETHROUGH_ENABLE) == 2
    assert formatted_output.count(STRIKETHROUGH_DISABLE) == 2
    assert formatted_output.count(BOLD_ENABLE) == 3
    assert formatted_output.count(BOLD_DISABLE) == 3
    assert formatted_output.count(ITALIC_ENABLE) == 3
    assert formatted_output.count(ITALIC_DISABLE) == 3

def test_strikethrough_precedence_1():
    """Test that strikethrough has highest precedence."""
    message = "~~***text***~~"
    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # Formatting markers must be preserved
    assert f"{STRIKETHROUGH_ENABLE}~~{BOLD_ENABLE}{ITALIC_ENABLE}***text***{ITALIC_DISABLE}{BOLD_DISABLE}~~{STRIKETHROUGH_DISABLE}" in formatted_output

    # Should contain strikethrough ANSI code first
    # Find positions of ANSI codes
    strikethrough_pos = formatted_output.find(STRIKETHROUGH_ENABLE)
    bold_pos = formatted_output.find(BOLD_ENABLE)
    italic_pos = formatted_output.find(ITALIC_ENABLE)

    # Strikethrough should come before bold and italic
    assert strikethrough_pos < bold_pos
    assert strikethrough_pos < italic_pos


def test_strikethrough_precedence_2():
    """Test that strikethrough has highest precedence."""
    message = "***~~text~~***"
    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # Formatting markers must be preserved
    assert f"{BOLD_ENABLE}{ITALIC_ENABLE}***{STRIKETHROUGH_ENABLE}~~text~~{STRIKETHROUGH_DISABLE}***" in formatted_output

    # Should contain strikethrough ANSI code first
    # Find positions of ANSI codes
    strikethrough_pos = formatted_output.find(STRIKETHROUGH_ENABLE)
    bold_pos = formatted_output.find(BOLD_ENABLE)
    italic_pos = formatted_output.find(ITALIC_ENABLE)

    # Strikethrough should come before bold and italic
    assert strikethrough_pos > bold_pos
    assert strikethrough_pos > italic_pos
    assert bold_pos < italic_pos


def test_strikethrough_in_heading():
    """Test strikethrough within a heading."""
    message = "# Heading with ~~strikethrough~~ text"
    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # Heading marker must be preserved
    assert "# Heading with " in formatted_output

    # Should contain both heading and strikethrough ANSI codes
    heading_ansi = HEADING_COLOR
    assert heading_ansi in formatted_output
    assert STRIKETHROUGH_ENABLE in formatted_output
    assert STRIKETHROUGH_DISABLE in formatted_output
    assert RESET in formatted_output

def test_strikethrough_in_list():
    """Test strikethrough within a list item."""
    message = "- List item with ~~strikethrough~~ text"
    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # List marker must be preserved
    assert "- List item with " in formatted_output

    # Should contain both list and strikethrough ANSI codes
    list_ansi = LIST_COLOR
    assert list_ansi in formatted_output
    assert STRIKETHROUGH_ENABLE in formatted_output
    assert STRIKETHROUGH_DISABLE in formatted_output
    assert RESET in formatted_output

def test_strikethrough_in_blockquote():
    """Test strikethrough within a blockquote."""
    message = "> Blockquote with ~~strikethrough~~ text"
    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # Blockquote marker marker must be preserved
    assert "> Blockquote with " in formatted_output

    # Should contain both blockquote and strikethrough ANSI codes
    blockquote_ansi = BLOCKQUOTE_COLOR
    assert blockquote_ansi in formatted_output
    assert STRIKETHROUGH_ENABLE in formatted_output
    assert STRIKETHROUGH_DISABLE in formatted_output
    assert RESET in formatted_output

def test_strikethrough_multiline():
    """Test strikethrough across multiple lines."""
    message = """First line with ~~strikethrough
Second line with ~~strikethrough~~
Third line without"""
    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # Each line should be processed independently
    lines = formatted_output.split('\n')
    assert len(lines) == 3

    # Each line should have its own reset code
    assert formatted_output.count(RESET) == 1 # One reset because of unclosed strikethrough


def test_strikethrough_escaped():
    """Test that escaped tildes are not treated as strikethrough."""
    message = "This has \\~~not strikethrough\\~~ text"
    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # Escape tildes must be preserved as literal text.  No ANSI codes should be added.
    assert "\\~~not strikethrough\\~~" in formatted_output

    # Should not contain strikethrough ANSI codes
    assert STRIKETHROUGH_ENABLE not in formatted_output
    assert STRIKETHROUGH_DISABLE not in formatted_output


def test_escape_sequences_preserved():
    """Test that escape sequences and special characters are preserved."""
    message = """\\*escaped asterisk\\*
\\#escaped hashtag
\\`escaped backtick\\`"""

    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # Escape sequences must be preserved as literal text.  No ANSI codes should be added.
    assert "\\*escaped asterisk\\*" in formatted_output
    assert "\\#escaped hashtag" in formatted_output


def test_strikethrough_nested_formatting():
    """Test strikethrough with nested formatting."""
    message = "~~**bold** and *italic*~~"
    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # All formatting markers must be preserved
    assert "~~**bold** and *italic*~~" in strip_ansi_codes(formatted_output)

    # Should contain appropriate ANSI codes
    assert STRIKETHROUGH_ENABLE in formatted_output
    assert STRIKETHROUGH_DISABLE in formatted_output
    assert BOLD_ENABLE in formatted_output
    assert BOLD_DISABLE in formatted_output
    assert ITALIC_ENABLE in formatted_output
    assert ITALIC_DISABLE in formatted_output


def test_strikethrough_mixed_combinations():
    """Test various strikethrough combinations."""
    message = """~~strikethrough~~ **bold** ~~*strikethrough italic*~~ ***bold italic***
# ~~strikethrough heading~~
- ~~strikethrough item~~
> ~~strikethrough quote~~"""

    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    stripped_output = strip_ansi_codes(formatted_output)
    # All formatting markers must be preserved
    assert "~~strikethrough~~" in stripped_output
    assert "**bold**" in stripped_output
    assert "~~*strikethrough italic*~~" in stripped_output
    assert "***bold italic***" in stripped_output
    assert "# ~~strikethrough heading~~" in stripped_output
    assert "- ~~strikethrough item~~" in stripped_output
    assert "> ~~strikethrough quote~~" in stripped_output

    # Should contain appropriate ANSI codes
    assert formatted_output.count(STRIKETHROUGH_ENABLE) == 5  # Multiple strikethrough instances
    assert formatted_output.count(STRIKETHROUGH_DISABLE) == 5


def test_indented_unordered_list_items():
    """Test that indented unordered list items are properly formatted."""
    message = """- This is a top level item
  - This is an indented sub-item
    - This is a deeply indented sub-item
- Back to top level"""

    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # All list markers should be formatted with LIST_COLOR
    assert f"{LIST_COLOR}- This is a top level item{RESET}" in formatted_output
    assert f"{LIST_COLOR}  - This is an indented sub-item{RESET}" in formatted_output
    assert f"{LIST_COLOR}    - This is a deeply indented sub-item{RESET}" in formatted_output
    assert f"{LIST_COLOR}- Back to top level{RESET}" in formatted_output


def test_indented_ordered_list_items():
    """Test that indented ordered list items are properly formatted."""
    message = """1. This is a top level item
   1. This is an indented sub-item
      1. This is a deeply indented sub-item
2. Back to top level"""

    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # All list markers should be formatted with LIST_COLOR
    assert f"{LIST_COLOR}1. This is a top level item{RESET}" in formatted_output
    assert f"{LIST_COLOR}   1. This is an indented sub-item{RESET}" in formatted_output
    assert f"{LIST_COLOR}      1. This is a deeply indented sub-item{RESET}" in formatted_output
    assert f"{LIST_COLOR}2. Back to top level{RESET}" in formatted_output


def test_indented_blockquotes():
    """Test that indented blockquotes are properly formatted."""
    message = """> This is a top level blockquote
  > This is an indented blockquote
    > This is a deeply indented blockquote"""

    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # All blockquote markers should be formatted with BLOCKQUOTE_COLOR
    assert f"{BLOCKQUOTE_COLOR}> This is a top level blockquote{RESET}" in formatted_output
    assert f"{BLOCKQUOTE_COLOR}  > This is an indented blockquote{RESET}" in formatted_output
    assert f"{BLOCKQUOTE_COLOR}    > This is a deeply indented blockquote{RESET}" in formatted_output


def test_mixed_indented_lists():
    """Test mixed indented lists with various formatting."""
    message = """- Top level unordered item
  - Indented unordered sub-item
    1. Ordered sub-item within unordered
       - Unordered sub-sub-item
2. Top level ordered item
   - Unordered sub-item within ordered
     2. Ordered sub-sub-item"""

    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # All list markers should be formatted with LIST_COLOR
    assert f"{LIST_COLOR}- Top level unordered item{RESET}" in formatted_output
    assert f"{LIST_COLOR}  - Indented unordered sub-item{RESET}" in formatted_output
    assert f"{LIST_COLOR}    1. Ordered sub-item within unordered{RESET}" in formatted_output
    assert f"{LIST_COLOR}       - Unordered sub-sub-item{RESET}" in formatted_output
    assert f"{LIST_COLOR}2. Top level ordered item{RESET}" in formatted_output
    assert f"{LIST_COLOR}   - Unordered sub-item within ordered{RESET}" in formatted_output
    assert f"{LIST_COLOR}     2. Ordered sub-sub-item{RESET}" in formatted_output


def test_list_formatting_with_example_from_issue():
    """Test the specific example from the issue description."""
    message = """- This is a top level item that is currently being formatted correctly
  - This is an indented sub-item, but it's currently not being formatted at all."""

    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message

    # Both items should be formatted with LIST_COLOR
    assert f"{LIST_COLOR}- This is a top level item that is currently being formatted correctly{RESET}" in formatted_output
    assert f"{LIST_COLOR}  - This is an indented sub-item, but it's currently not being formatted at all.{RESET}" in formatted_output


def test_list_formatting_preserves_original_text():
    """Test that list formatting preserves the original text content."""
    message = """- Item 1
  - Sub-item 1.1
    - Sub-sub-item 1.1.1
  - Sub-item 1.2
- Item 2"""

    formatter = MarkdownFormatter(message)
    formatted_output = formatter.formatted_message
    stripped_output = strip_ansi_codes(formatted_output)

    # The original text content should be preserved (ignore exact whitespace differences)
    # Check that all list items are present
    assert "- Item 1" in stripped_output
    assert "- Sub-item 1.1" in stripped_output
    assert "- Sub-sub-item 1.1.1" in stripped_output
    assert "- Sub-item 1.2" in stripped_output
    assert "- Item 2" in stripped_output
