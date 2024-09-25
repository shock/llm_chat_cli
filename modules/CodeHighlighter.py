from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import TerminalFormatter
from pygments.util import ClassNotFound

class CodeHighlighter:

    def __init__(self, style=TerminalFormatter):
        self.style = style

    def highlight_code(self, code, language=None):
        """Helper method to highlight code using Pygments."""
        lexer = get_lexer_by_name('text', stripall=False)
        if language:
            try:
                lexer = get_lexer_by_name(language, stripall=False)
            except ClassNotFound:
                pass
        formatter = TerminalFormatter(style=self.style)
        highlighted_code = highlight(code, lexer, formatter)
        return highlighted_code
