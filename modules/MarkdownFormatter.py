import re
from pygments.formatters import TerminalFormatter
from modules.CodeHighlighter import CodeHighlighter

# ANSI code constants for individual attributes
RESET = '\033[0m'
BOLD_ENABLE = '\033[1m'
BOLD_DISABLE = '\033[22m'
ITALIC_ENABLE = '\033[3m'
ITALIC_DISABLE = '\033[23m'
STRIKETHROUGH_ENABLE = '\033[9m'
STRIKETHROUGH_DISABLE = '\033[29m'

# Colors for whole-line formatting (headings, lists, blockquotes)
HEADING_COLOR = '\033[36m'  # Cyan for headings
CODE_COLOR = '\033[36m'       # Cyan for code
LIST_COLOR = '\033[32m'     # Green for list markers
BLOCKQUOTE_COLOR = '\033[35m'  # Magenta for blockquotes
RESET_COLOR = '\033[39;49m'  # Reset foreground and background colors

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
        Uses selective formatting with line-based reset and independent attribute tracking.
        """


        # Process the text line by line
        lines = text.split('\n')
        result_lines = []

        in_code_block = False
        for line in lines:
            # Consume code block lines as-is, but format the ``` lines
            if line.strip().startswith('```'):
                result_lines.append(f'{CODE_COLOR}{line}{RESET}')
                in_code_block = not in_code_block
                continue
            if in_code_block:
                result_lines.append(line)
                continue

            # Phase 1: Word-group formatting (strikethrough, bold, italics)
            # Process with selective ANSI codes and independent attribute tracking
            current_formats = set()  # Track active formatting attributes
            result_line = ""
            i = 0

            while i < len(line):
                # Check for strikethrough (highest precedence)
                if line[i:i+2] == "~~" and (i == 0 or line[i-1] != "\\"):
                    # Toggle strikethrough
                    if "strikethrough" in current_formats:
                        result_line += "~~"
                        # Exit strikethrough
                        result_line += STRIKETHROUGH_DISABLE
                        current_formats.remove("strikethrough")
                    else:
                        # Enter strikethrough
                        result_line += STRIKETHROUGH_ENABLE
                        current_formats.add("strikethrough")
                        result_line += "~~"
                    i += 2
                    continue

                # Check for bold+italic (*** or ___)
                if (line[i:i+3] == "***" or line[i:i+3] == "___") and (i == 0 or line[i-1] != "\\"):
                    # Toggle bold+italic
                    if "bold" in current_formats and "italic" in current_formats:
                        result_line += line[i:i+3]
                        # Exit bold+italic
                        result_line += ITALIC_DISABLE + BOLD_DISABLE
                        current_formats.remove("bold")
                        current_formats.remove("italic")
                    else:
                        # Enter bold+italic
                        result_line += BOLD_ENABLE + ITALIC_ENABLE
                        current_formats.add("bold")
                        current_formats.add("italic")
                        result_line += line[i:i+3]
                    i += 3
                    continue

                # Check for bold (** or __)
                if (line[i:i+2] == "**" or line[i:i+2] == "__") and (i == 0 or line[i-1] != "\\"):
                    # Toggle bold
                    if "bold" in current_formats:
                        result_line += line[i:i+2]
                        # Exit bold
                        result_line += BOLD_DISABLE
                        current_formats.remove("bold")
                    else:
                        # Enter bold
                        result_line += BOLD_ENABLE
                        current_formats.add("bold")
                        result_line += line[i:i+2]
                    i += 2
                    continue

                # Check for italic (* or _)
                if (line[i] == "*" or line[i] == "_") and (i == 0 or line[i-1] != "\\"):
                    # Toggle italic
                    if "italic" in current_formats:
                        result_line += line[i]
                        # Exit italic
                        result_line += ITALIC_DISABLE
                        current_formats.remove("italic")
                    else:
                        # Enter italic
                        result_line += ITALIC_ENABLE
                        current_formats.add("italic")
                        result_line += line[i]
                    i += 1
                    continue

                # Process inline code (preserve ` characters)
                if line[i] == "`" and (i == 0 or line[i-1] != "\\"):
                    # Find the matching backtick
                    j = i + 1
                    while j < len(line) and line[j] != "`":
                        j += 1
                    if j < len(line):
                        # Found matching backtick
                        code_content = line[i:j+1]
                        result_line += f'{CODE_COLOR}{code_content}{RESET_COLOR}'
                        i = j + 1
                        continue

                # Regular character - apply current formatting
                result_line += line[i]
                i += 1

            # Add full reset at line end if any formatting is still active
            if current_formats:
                result_line += RESET

            # Phase 2: Whole-line formatting (headings, lists, blockquotes)
            formatted_line = result_line

            # Process headings (preserve # characters)
            formatted_line = re.sub(r'^(#{1,6})\s+(.+)$',
                                  rf'{HEADING_COLOR}\1 \2{RESET}',
                                  formatted_line)

            # Process unordered lists (preserve - characters)
            if not formatted_line.startswith(HEADING_COLOR):
                formatted_line = re.sub(r'^(\s*-\s+.+)$',
                                      rf'{LIST_COLOR}\1{RESET}',
                                      formatted_line)

            # Process ordered lists (preserve numbers)
            if not formatted_line.startswith(HEADING_COLOR) and not formatted_line.startswith(LIST_COLOR):
                formatted_line = re.sub(r'^(\s*\d+\.\s+.+)$',
                                      rf'{LIST_COLOR}\1{RESET}',
                                      formatted_line)

            # Process blockquotes (preserve > characters)
            if not (formatted_line.startswith(HEADING_COLOR) or
                    formatted_line.startswith(LIST_COLOR)):
                formatted_line = re.sub(r'^(\s*>\s+.+)$',
                                      rf'{BLOCKQUOTE_COLOR}\1{RESET}',
                                      formatted_line)

            result_lines.append(formatted_line)

        text = '\n'.join(result_lines)

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
