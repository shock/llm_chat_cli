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

## **Introduction** to _Markdown_ ***Formatting***

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

#### Unordered List with ~~strikethrough~~ in the header

- Item 1
  - Subitem 1.1 has **bold text**
    - Sub-sub-item 1.1.1 with `inline code`
  - Subitem 1.2 has *italic text*
- Item 2 is ~~strikethrough~~
- Item 3

#### Ordered List

1. First
2. Second
3. Third
   1. Subthird 1
   2. __Bold Subthird 2__

#### Task List

- [x] Completed task
- [ ] Incomplete task
- [ ] ***Another bold task***

---

### Blockquote

> This is a blockquote _with italic text_.
    > It can have indentation and span multiple lines and contain **bold text**.

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

    print("The formatted output above is still valid markdown that can be")
    print("copied and used with other markdown processing tools.")

if __name__ == "__main__":
    demo_markdown_formatting()