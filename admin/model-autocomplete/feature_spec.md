# Model Autocomplete Feature - Master Plan

## Objective

Implement a `prompt_toolkit` Completer that provides autocomplete suggestions for model names when users type the `/mod` command. The completer should:

- Detect when the input buffer starts with `/mod`
- Provide autocomplete suggestions for valid model names (both long and short names)
- Source model names from all configured providers via the ProviderManager
- Integrate seamlessly with the existing completer architecture in `ChatInterface.py`

## Current Architecture Analysis

### Existing Completer Setup (ChatInterface.py:61-66)

The `ChatInterface` class currently uses:
- A `StringSpaceCompleter` (custom dependency, connects to external service on port 7878)
- `merge_completers([self.spell_check_completer])` to combine multiple completers
- Completer is attached to the `PromptSession` with `complete_while_typing=True`

**CORRECTION**: The variable name `self.spell_check_completer` actually refers to a `StringSpaceCompleter` instance, not a spell check completer. The spell check completer is commented out and replaced by the external StringSpaceCompleter service.

Key observation: The architecture already supports multiple merged completers, making integration straightforward.

### Provider Manager Model Access (ProviderManager.py)

The `ProviderManager` class provides several methods for retrieving model information:

1. **`merged_models()`** (line 92-106):
   - Returns: `List[Tuple[str, Tuple[str, str]]]`
   - Format: `[(provider_name, (long_model_name, short_model_name)), ...]`
   - Combines models from all configured providers
   - This is the primary source for autocomplete data

2. **`valid_scoped_models()`** (line 108-116):
   - Returns: `List[str]`
   - Format: `["provider/long_name (short_name)", ...]`
   - Pre-formatted display strings

3. **`get_available_models()`** (line 240-249):
   - Returns: `List[str]`
   - Can filter by provider

### /mod Command Implementation (CommandHandler.py:85-89)

- Command: `/mod` (lines 85-89)
- Takes a single argument: the model name
- Calls `chat_interface.set_model(args[0])`
- Model string can be:
  - Provider-prefixed: `openai/gpt-4o`
  - Unprefixed (searches all providers): `gpt-4o`
  - Short name: `4o`

## High-Level Approach

### 1. Create a Custom Completer Class

Create a new module: `modules/ModelCommandCompleter.py`

The completer should:
- Inherit from `prompt_toolkit.completion.Completer`
- Accept a `ProviderManager` instance in its constructor
- Implement the `get_completions()` method to:
  - Check if the input starts with `/mod`
  - Extract the partial model name being typed
  - Generate completion suggestions from `ProviderManager.merged_models()`

### 2. Completion Strategy

For each model in `merged_models()`, generate multiple completion entries:
- Full scoped format: `provider/long_name`
- Short name only: `short_name`
- Long name only (unprefixed): `long_name`

This allows users to type any of these formats and get matches:
- `/mod open` → matches `openai/gpt-4o`
- `/mod 4o` → matches `4o` (short name)
- `/mod gpt-4o` → matches both `openai/gpt-4o` and unprefixed `gpt-4o`

**Implementation Details:**
- Sort completions by string length (shortest first) to prioritize quick selections
- Use `display_meta` to distinguish completion types: `"Provider: OpenAI"`
- Generate all three formats for maximum flexibility

### 3. Integration into ChatInterface

Modify `ChatInterface.__init__()` (around line 61-62):
- Instantiate the new `ModelCommandCompleter` with access to `self.config.config.providers` (which is already a ProviderManager instance)
- Add it to the `merge_completers()` list alongside the existing `StringSpaceCompleter`

Example:
```python
self.model_completer = ModelCommandCompleter(self.config.config.providers)
self.merged_completer = merge_completers([
    self.spell_check_completer,  # This is actually StringSpaceCompleter
    self.model_completer
])
```

### 4. Filtering Logic

The completer should only activate when:
- Input buffer matches regex `r/^\s*\/mod\s+/` (exactly `/mod` followed by space)
- There's text after `/mod ` (the partial model name)

Use `prompt_toolkit`'s document state to:
- Get the current line text using `Document.text_before_cursor`
- Check prefix with regex pattern
- Extract the word being completed using `Document.get_word_before_cursor()`
- Filter models based on the partial input using case-insensitive matching
- Return empty list when not in `/mod` context to avoid interfering with StringSpaceCompleter

### 5. Display Formatting

Completion suggestions should show:
- The completion text (what gets inserted)
- Optional display text (what the user sees in the dropdown)
- Use `display_meta` for provider context: `"Provider: OpenAI"`
- Keep main completion text clean while providing context in metadata

## Technical Considerations

### Prompt Toolkit Integration Points

- Use `Document.text_before_cursor` to get current input
- Use `Document.get_word_before_cursor(WORD=True)` for proper word boundary detection (following spell_check_word_completer.py:11 pattern)
- Calculate `start_position` based on length of partial word after `/mod ` prefix
- Return `Completion` objects with:
  - `text`: The completion string
  - `start_position`: How many characters back to replace (length of partial word)
  - `display`: Optional display text (for rich formatting)
  - `display_meta`: Optional metadata (e.g., provider name)
- **Required import**: `from prompt_toolkit.completion import Completion`

### Performance

- Cache model list at initialization in completer's `__init__` method
- Completer runs on every keystroke, so keep filtering logic lightweight
- `merged_models()` returns a list, not a generator, so it's safe to iterate
- For future dynamic updates, consider adding a `refresh()` method

### Edge Cases

- Empty provider list: Should gracefully handle no completions
- Invalid provider in config: ProviderManager already validates
- Models with special characters: Test with actual model names
- Case sensitivity: Implement case-insensitive matching for better UX
- No models available: Return empty list rather than raising errors
- **Model parsing default behavior**: ModelDiscoveryService.parse_model_string() defaults to 'openai' provider when no provider prefix is specified (ModelDiscoveryService.py:32-37)
- **Error handling**: Gracefully handle ProviderManager exceptions during completion by returning empty list

## Testing Strategy

### Unit Tests

Create `tests/test_ModelCommandCompleter.py`:
- Test detection of `/mod` prefix
- Test completion generation from mock ProviderManager
- Test filtering logic with partial input
- Test both long and short name matching
- Test provider-prefixed completions
- Test case-insensitive matching
- Test word boundary detection with `WORD=True`
- Test error handling when ProviderManager raises exceptions
- Test default provider behavior (openai fallback)
- Test with empty provider list
- Test with no models available

### Integration Tests

Extend `tests/test_ChatInterface.py`:
- Test that completer is properly merged
- Test interaction with existing StringSpaceCompleter
- Mock Document objects to test completion generation without interactive input

### Manual Testing

- Test with live chat interface
- Verify completions appear while typing
- Test tab completion behavior
- Test with multiple providers configured
- Test with no providers configured

## Implementation Phases

### Phase 1: Core Completer
- Create `ModelCommandCompleter` class
- Implement basic `/mod` detection
- Implement completion generation from ProviderManager

### Phase 2: Integration
- Integrate into `ChatInterface`
- Test with existing completer
- Verify no conflicts with StringSpaceCompleter

### Phase 3: Enhancement
- Add display metadata (provider names)
- Refine filtering logic
- Add case-insensitive matching

### Phase 4: Testing & Validation
- Write comprehensive unit tests
- Perform integration testing
- Manual QA with various scenarios
- Run `make test` to ensure no regressions

## Dependencies

- `prompt_toolkit`: Already in dependencies
- `ProviderManager`: Already implemented
- No new external dependencies required

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Conflicts with StringSpaceCompleter | Use `merge_completers()` properly; test both completers |
| Performance degradation | Cache model list; keep filtering lightweight |
| Breaking existing tests | Run full test suite after each phase |
| Model list not updating | Consider refresh mechanism or accept static list per session |

## Success Criteria

- [ ] Completer activates only for `/mod` commands
- [ ] Suggestions include long names, short names, and provider-prefixed names
- [ ] Tab completion works correctly
- [ ] No interference with existing StringSpaceCompleter
- [ ] All existing tests pass
- [ ] New unit tests achieve >90% coverage of ModelCommandCompleter functionality
- [ ] Manual testing confirms expected behavior with various input scenarios
- [ ] Case-insensitive matching works correctly
- [ ] Error handling gracefully manages ProviderManager exceptions

## Next Steps

1. Review issues to be addressed and approve this plan
2. Begin Phase 1 implementation
3. Iterate based on testing feedback

## Issues Resolved in Plan Updates

The following issues identified in the original plan have been addressed and resolved in the updated plan above:

### 1. Completer Architecture Discrepancy ✅ RESOLVED
- **Issue**: The plan referenced `self.spell_check_completer` but the current implementation uses `StringSpaceCompleter`
- **Resolution**: Updated plan to clarify that `self.spell_check_completer` is actually a `StringSpaceCompleter` instance

### 2. ProviderManager Access Pattern ✅ RESOLVED
- **Issue**: The plan suggested accessing `self.config.config.providers` but this is already a ProviderManager instance
- **Resolution**: Updated plan to clarify that ProviderManager can be used directly without conversion

### 3. Model Parsing Default Behavior ✅ RESOLVED
- **Issue**: ModelDiscoveryService.parse_model_string() defaults to 'openai' provider when no provider prefix is specified
- **Resolution**: Added this behavior to Edge Cases section and test coverage requirements

### 4. Missing Import for Completion Class ✅ RESOLVED
- **Issue**: The plan mentioned `Completion` objects but didn't specify the import
- **Resolution**: Added required import to Prompt Toolkit Integration Points section

### 5. Word Boundary Detection Logic ✅ RESOLVED
- **Issue**: The plan used `Document.get_word_before_cursor()` without `WORD=True` parameter
- **Resolution**: Updated to specify `WORD=True` following spell_check_word_completer.py:11 pattern

### 6. Test Coverage Requirements ✅ RESOLVED
- **Issue**: The plan mentioned >90% coverage but didn't specify what should be tested
- **Resolution**: Added comprehensive list of specific test scenarios in Unit Tests section

### 7. Performance Considerations ✅ RESOLVED
- **Issue**: The plan mentioned caching but didn't address potential memory usage
- **Resolution**: Acknowledged that generating 3 formats per model is acceptable given typical model counts

### 8. Error Handling Strategy ✅ RESOLVED
- **Issue**: The plan didn't specify how to handle ProviderManager exceptions
- **Resolution**: Added graceful fallback strategy to Edge Cases section and test coverage