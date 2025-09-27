import re
from pygments.formatters import TerminalFormatter
from modules.CodeHighlighter import CodeHighlighter

class MarkdownFormatter:
    """Enhanced markdown formatter that preserves original markdown syntax while adding ANSI formatting."""

    def __init__(self, message, style=TerminalFormatter):
        self.message = message
        self.formatted_message = message
        # Create console with terminal-friendly settings
        self.code_block_highlighter = CodeHighlighter(style=style)
        self.code_blocks = self._extract_code_blocks()
        self.highlighted_code_blocks = self._highlighted_code_blocks()
        self.formatted_message = self._format_message()
        self.formatted_message = self._highlighted_message()

    def _format_message(self):
        """
        Format the message while preserving all original markdown syntax.
        This approach adds ANSI color codes around the formatting characters
        instead of removing them.
        """
        # Process the message to add ANSI formatting while preserving syntax
        formatted_message = self._format_markdown_preserving_syntax(self.message)

        return formatted_message

    def _format_markdown_preserving_syntax(self, text):
        """
        Add ANSI formatting to markdown while preserving the original syntax.
        This is a custom implementation that doesn't use Rich's Markdown class.
        """
        # Define ANSI color codes
        RESET = '\033[0m'
        HEADING_COLOR = '\033[1;36m'  # Bold cyan for headings
        CODE_COLOR = '\033[36m'       # Cyan for code
        BOLD_COLOR = '\033[1;33m'     # Bold yellow for bold text
        ITALIC_COLOR = '\033[3;33m'   # Italic yellow for italic text
        BOLD_ITALIC_COLOR = '\033[1;3;33m'  # Bold italic yellow for bold+italic text
        LIST_COLOR = '\033[1;32m'     # Bold green for list markers
        BLOCKQUOTE_COLOR = '\033[1;35m'  # Bold magenta for blockquotes

        # First, protect escape sequences by replacing them with placeholders
        escape_placeholders = {}
        escape_pattern = r'(\\[\\*#`])'

        def escape_replacer(match):
            placeholder = f'__ESCAPE_{len(escape_placeholders)}__'
            escape_placeholders[placeholder] = match.group(1)
            return placeholder

        text = re.sub(escape_pattern, escape_replacer, text)

        # Process headings (preserve # characters)
        text = re.sub(r'^(#{1,6})\s+(.+)$',
                     rf'{HEADING_COLOR}\1 \2{RESET}',
                     text, flags=re.MULTILINE)

        # Process bold+italic text (preserve *** characters) - must come before bold/italic
        text = re.sub(r'(?<!\*)\*\*\*(?!\*)(.+?)(?<!\*)\*\*\*(?!\*)',
                     rf'{BOLD_ITALIC_COLOR}***\1***{RESET}',
                     text)

        # Process bold text (preserve ** characters) - use lookaround to avoid conflicts
        text = re.sub(r'(?<!\*)\*\*(?!\*)(.+?)(?<!\*)\*\*(?!\*)',
                     rf'{BOLD_COLOR}**\1**{RESET}',
                     text)

        # Process italic text (preserve * characters)
        text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)',
                     rf'{ITALIC_COLOR}*\1*{RESET}',
                     text)

        # Process inline code (preserve ` characters)
        text = re.sub(r'`([^`\n]+?)`',
                     rf'{CODE_COLOR}`\1`{RESET}',
                     text)

        # Process code blocks (preserve ``` characters)
        # This is more complex - we need to handle multi-line code blocks
        lines = text.split('\n')
        in_code_block = False
        code_block_lines = []
        result_lines = []

        for line in lines:
            if line.strip().startswith('```') and not in_code_block:
                # Start of code block
                in_code_block = True
                code_block_lines = [f'{CODE_COLOR}{line}{RESET}']
            elif line.strip().startswith('```') and in_code_block:
                # End of code block
                in_code_block = False
                # Color the entire code block
                code_block = '\n'.join(code_block_lines)
                result_lines.append(code_block)
                result_lines.append(f'{CODE_COLOR}{line}{RESET}')
            elif in_code_block:
                # Inside code block
                code_block_lines.append(line)
            else:
                # Regular line
                result_lines.append(line)

        text = '\n'.join(result_lines)

        # Process unordered lists (preserve - characters)
        text = re.sub(r'^-(\s+.+)$',
                     rf'{LIST_COLOR}-\1{RESET}',
                     text, flags=re.MULTILINE)

        # Process ordered lists (preserve numbers)
        text = re.sub(r'^(\d+\.\s+.+)$',
                     rf'{LIST_COLOR}\1{RESET}',
                     text, flags=re.MULTILINE)

        # Process blockquotes (preserve > characters)
        text = re.sub(r'^>(\s+.+)$',
                     rf'{BLOCKQUOTE_COLOR}>\1{RESET}',
                     text, flags=re.MULTILINE)

        # Restore escape sequences
        for placeholder, original_escape in escape_placeholders.items():
            text = text.replace(placeholder, original_escape)

        return text

    def _extract_code_blocks(self):
        """Extract all code blocks from the message."""
        code_block_pattern = re.compile(r'```[\t ]*(?P<language>\w+)?\n(?P<code>.*?\n)[ ]*```', re.DOTALL)
        return code_block_pattern.findall(self.message)

    def _highlighted_code_blocks(self):
        """Return a list of highlighted code blocks."""
        return [self.code_block_highlighter.highlight_code(code, language) for language, code in self.code_blocks]

    def _highlighted_message(self):
        """Return a message replacing original code blocks with highlighted code blocks."""
        highlighted_message = self.formatted_message
        for i, (language, code) in enumerate(self.code_blocks):
            highlighted_message = highlighted_message.replace(code, self.highlighted_code_blocks[i])
        return highlighted_message

    def list_code_blocks(self):
        """List all code blocks with their indices."""
        for i, (language, code) in enumerate(self.code_blocks):
            print()
            print(f"{i+1} :")
            print(f"```{language}")
            print(self.code_block_highlighter.highlight_code(code, language))
            print('```\n')

    def select_code_block(self):
        """Select a code block by its index."""
        self.list_code_blocks()
        try:
            index = int(input("Enter the index of the code block you want to copy: "))
            while True:
                if 0 < index <= len(self.code_blocks):
                    _, code = self.code_blocks[index-1]
                    return code
                else:
                    self.list_code_blocks()
                    index = int(input(f"Invalid index. Please select a valid index (1-{len(self.code_blocks)}): "))
        except KeyboardInterrupt:
            print("Aborting...")
            return None
