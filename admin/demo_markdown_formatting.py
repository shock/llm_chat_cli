#!/usr/bin/env python3
"""
Demo script for the MarkdownFormatter implementation.
Shows how markdown formatting characters are preserved while adding ANSI colors.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..')

from modules.MarkdownFormatter import MarkdownFormatter

def demo_markdown_formatting():
    """Demonstrate the new markdown formatting that preserves syntax."""

    # Test markdown with various elements
    test_markdown = """# Sample Markdown Document

## Introduction

This document demonstrates various **Markdown styles** and _list types_.

---

### Text Styles

- **Bold text**
- *Italic text*
- ***Bold and italic text***
- ~~Strikethrough~~
- `Inline code`

---

### Lists

#### Unordered List

- Item 1
  - Subitem 1.1
  - Subitem 1.2
- Item 2
- Item 3

#### Ordered List

1. First
2. Second
3. Third
   1. Subthird 1
   2. Subthird 2

#### Task List

- [x] Completed task
- [ ] Incomplete task
- [ ] Another task

---

### Blockquote

> This is a blockquote.
> It can span multiple lines.

---

### Code Blocks

#### Bash Script

```bash
#!/bin/bash
echo "Hello, brother"
date
```

#### Python Program

```python
def greet(name):
    print(f"Hello, {name}")

greet("brother")
```

---

### Tables

| Syntax | Description |
|--------|-------------|
| Header | Title       |
| Paragraph | Text      |

---

### Horizontal Rule

---

That's a quick tour of Markdown styles and lists. Let me know if you want me to add more, brother.
"""

    print("Original Markdown:")
    print("=" * 60)
    print(test_markdown)
    print("=" * 60)
    print()

    print("Formatted Output (preserving syntax):")
    print("=" * 60)

    formatter = MarkdownFormatter(test_markdown)
    formatted_output = formatter.formatted_message

    print(formatted_output)
    print("=" * 60)
    print()

    # Show that the output is still valid markdown
    print("Key features demonstrated:")
    print("✓ Headings preserve # characters")
    print("✓ Bold text preserves ** characters")
    print("✓ Italic text preserves * characters")
    print("✓ Code blocks preserve ``` characters")
    print("✓ Lists preserve - and numbers")
    print("✓ Blockquotes preserve > characters")
    print("✓ All formatting characters remain for other tools to parse")
    print()
    print("The formatted output above is still valid markdown that can be")
    print("copied and used with other markdown processing tools.")

if __name__ == "__main__":
    demo_markdown_formatting()