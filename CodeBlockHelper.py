import re
from pygments.formatters import TerminalFormatter
from CodeHighlighter import CodeHighlighter

class CodeBlockHelper:
    def __init__(self, message, style=TerminalFormatter):
        self.message = message
        self.code_blocks = self._extract_code_blocks()
        self.code_block_highlighter = CodeHighlighter(style=style)
        self.highlighted_code_blocks = self._highlighted_code_blocks()
        self.highlighted_message = self._highlighted_message()

    def _extract_code_blocks(self):
        """Extract all code blocks from the message."""
        code_block_pattern = re.compile(r'```\s*(?P<language>\w+)?\n(?P<code>.*?\n)[ ]*```', re.DOTALL)
        return code_block_pattern.findall(self.message)

    def _highlighted_code_blocks(self):
        """Return a list of highlighted code blocks."""
        return [self.code_block_highlighter.highlight_code(code, language) for language, code in self.code_blocks]

    def _highlighted_message(self):
        """Return a message replacing original code blocks with highlighted code blocks."""
        highlighted_message = self.message
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
