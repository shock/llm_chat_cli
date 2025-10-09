# Revised Markdown Support Implementation Plan

## Goal
Implement strikethrough text support (`~~text~~`) in the MarkdownFormatter using a selective formatting approach that handles complex combinations with existing formatting (bold, italic, bold+italic) and works within other markdown elements like headings, lists, and blockquotes.

## Core Strategy: Selective Formatting with Line-Based Reset

### Key Design Decisions
1. **Line-based processing**: Formatting state resets at every newline character
2. **Selective ANSI codes**: Apply individual formatting attributes (bold, italic, strikethrough) independently
3. **State tracking**: Maintain active formatting states during line processing
4. **Two-phase processing**: Handle word-group formatting first, then whole-line formatting

### Processing Order
1. **Phase 1: Word-group formatting** (strikethrough, bold, italics)
   - Process within each line, tracking formatting state
   - Apply selective ANSI codes for individual attributes
   - Reset formatting at line boundaries

2. **Phase 2: Whole-line formatting** (headings, lists, blockquotes, etc.)
   - Apply existing formatting approach after word-group processing
   - Maintains current behavior for these elements

## Implementation Details

### Formatting State Management
- **Initial state per line**: No formatting (regular text)
- **Formatting attributes tracked independently**: bold, italic, strikethrough
- **ANSI codes applied selectively** when formatting state changes
- **No RESET codes between formats** - only enable/disable individual attributes

### ANSI Code Strategy
- **Bold**: `\033[1m` (enable), `\033[22m` (disable)
- **Italic**: `\033[3m` (enable), `\033[23m` (disable)
- **Strikethrough**: `\033[9m` (enable), `\033[29m` (disable)
- **Combined formats**: Stack codes (e.g., `\033[1;3;9m` for bold+italic+strikethrough)
- **Full reset**: `\033[0m` at line end

### Processing Algorithm
```python
for each line in text:
    current_formatting = set()  # Track active formatting attributes
    result_line = ""

    # Process markdown patterns in precedence order
    for pattern in patterns:
        # Apply formatting selectively based on pattern matches
        # Update current_formatting set
        # Apply appropriate ANSI codes when formatting state changes

    # Add full reset at line end
    result_line += "\033[0m"
```

### Formatting Precedence
1. **Strikethrough** (highest precedence)
2. **Bold+Italic** (`***text***`)
3. **Bold** (`**text**`)
4. **Italic** (`*text*`)

### Benefits of This Approach
- **Handles any combination**: `# ~~*Heading*~~`, `> ~~blockquote~~`, `- ~~list item~~`
- **No combinatorial explosion**: Don't need separate patterns for each permutation
- **Cleaner output**: No redundant ANSI codes
- **More flexible**: Works within any markdown context
- **Simplified logic**: Line-based reset eliminates complex nested state management

### Additional Considerations
 - Color changes for strikethrough, bold, and italic will no longer be supported.
 - Color for line-based formatting (heading, list, blockquote) will be preserved.
 - Code blocks will be processed as-is, no changes required.

### Example Processing Flow
Input: `~~*bold italic strikethrough*~~ and **bold**`

Processing:
1. Enter strikethrough: `\033[9m`
2. Enter bold+italic: `\033[1;3m`
3. Text: `bold italic strikethrough`
4. Exit bold+italic: `\033[22;23m` (disable bold/italic, keep strikethrough)
5. Exit strikethrough: `\033[29m`
6. Regular text: ` and `
7. Enter bold: `\033[1m`
8. Text: `bold`
9. Exit bold: `\033[22m`
10. Line end: `\033[0m` (full reset)

## Files to Modify

1. **modules/MarkdownFormatter.py**:
   - Replace current formatting approach with selective state management
   - Add strikethrough support
   - Implement line-based processing

2. **tests/test_MarkdownFormatter.py**:
   - Add comprehensive tests for strikethrough and combinations
   - Test strikethrough within headings, lists, blockquotes
   - Test edge cases and formatting precedence

## Testing Strategy

### Core Functionality
- Individual strikethrough: `~~text~~`
- Combinations: `~~*text*~~`, `*~~text~~*`, `~~**text**~~`, `**~~text~~**`, `~~***text***~~`, `***~~text~~***`
- Precedence: strikethrough should apply first

### Integration Testing
- Strikethrough in headings: `# ~~strikethrough heading~~`
- Strikethrough in lists: `- ~~strikethrough item~~`
- Strikethrough in blockquotes: `> ~~strikethrough quote~~`
- Mixed formatting: `# ~~*bold italic strikethrough heading*~~`

### Edge Cases
- Escaped tildes: `\~~not strikethrough\~~`
- Nested formatting: `~~**bold** and *italic*~~`
- Line boundaries: formatting reset at newlines

## Logical Integrity Check

This approach maintains:
- **Consistency**: Works with existing markdown elements
- **Simplicity**: Line-based reset eliminates complex state tracking
- **Flexibility**: Handles any formatting combination
- **Performance**: Processes lines independently, no global state
- **Maintainability**: Clear separation between word-group and whole-line formatting

The two-phase processing ensures that strikethrough (and other word-group formatting) can be applied within any markdown context, while preserving the existing behavior for headings, lists, and other whole-line elements.