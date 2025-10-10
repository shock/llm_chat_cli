# Phase 1 Execution Plan: Enhanced ProviderConfig and ModelDiscoveryService

## Introduction

This execution plan details the implementation of Phase 1 of the provider refactoring project. Phase 1 focuses on creating the foundational classes (`ProviderConfig` and `ModelDiscoveryService`) that will form the basis for the new architecture.

**CRITICAL**: If any step cannot be completed as specified, **STOP IMMEDIATELY**, update the status document (`admin/refactor-providers/status/phase_1_execution_status.md`), and notify the user. Do not proceed with incomplete or incorrect implementations.

## Pre-Implementation Steps

### Step 1: Read Master Plan
Read the complete master plan document at `admin/refactor-providers/master_plan.md` to understand the full context and architectural vision for this refactoring.

### Step 2: Check Execution Status
Scan the `/admin/refactor-providers/status` directory to determine if a status document for Phase 1 already exists. If `phase_1_execution_status.md` exists:
- Read its contents carefully
- Use the status information to determine which steps have been completed
- Resume execution from the first incomplete step
- Do not repeat completed steps unless explicitly required

### Step 3: Run Test Suite
Run the full test suite using `make test` or `pytest` to establish a baseline. All tests must pass before proceeding. If any tests fail:
- **STOP** execution immediately
- Update the status document to reflect "NOT STARTED" status
- Notify the user of the test failures
- Do not proceed until the user resolves the test failures

### Step 4: Review Existing Codebase
Review and understand the current state of the following files and modules:
- `modules/Types.py` - Current location of ProviderConfig class
- `modules/OpenAIChatCompletionApi.py` - Contains model discovery logic to be extracted
- `modules/Config.py` - Configuration loading and management
- `tests/test_Config.py` - Existing configuration tests
- `data/openaicompat-providers.yaml` - Example provider configuration file

Focus on understanding:
- Current ProviderConfig structure and fields
- Model discovery implementation in OpenAIChatCompletionApi
- Error handling patterns in model discovery (lines 273-283)
- Configuration loading sequence in Config.py
- Existing test coverage and patterns

## Implementation Steps

### Step 1: Create ProviderConfig.py Module

Create a new file at `modules/ProviderConfig.py` with the enhanced ProviderConfig class.

**Requirements:**
- Import required dependencies: `from pydantic import BaseModel, Field, PrivateAttr`, `List`, `Any`, `Dict`, `Optional`
- Move the `ProviderConfig` class definition from `modules/Types.py` to this new file
- Enhance the class with new fields and methods as specified below

**Field Structure:**

Implement two categories of fields:

**Persisted Fields** (saved to YAML):
- `name: str` - Provider display name (default: "Test Provider")
- `base_api_url: str` - Base API endpoint URL (default: "https://test.openai.com/v1")
- `api_key: str` - API authentication key (default: "")
- `valid_models: dict[str, str]` - Dictionary mapping long model names to short names (default: empty dict)
- `invalid_models: List[str]` - List of incompatible model names (default: empty list) **[NEW FIELD]**

**Runtime-Only Fields** (not saved to YAML):
- `_cached_models: List[Any]` - Cached model data from API (PrivateAttr, default: empty list)
- `_cache_timestamp: float` - Timestamp of last cache update (PrivateAttr, default: 0.0)
- `cache_duration: int` - Cache validity duration in seconds (PrivateAttr, default: 300)

**Initialization:**
```python
def model_post_init(self, __context: Any) -> None:
    self._cached_models = []
    self._cache_timestamp = 0.0
    self.cache_duration = 300
```

**Backward Compatibility:**
- Existing YAML files without `invalid_models` field must load without errors
- The `invalid_models` field defaults to an empty list
- All other fields maintain their current structure and defaults

**Helper Methods to Implement:**

1. `get_valid_models() -> List[str]`
   - Return list of valid model long names (keys from valid_models dict)

2. `get_invalid_models() -> List[str]`
   - Return copy of invalid_models list

3. `find_model(name: str) -> Optional[str]`
   - Search for model by name in valid_models
   - Search order:
     1. Exact match on long name (dict key)
     2. Exact match on short name (dict value)
     3. Substring match on long name
     4. Substring match on short name
   - Return matched long name or None if not found

4. `merge_valid_models(models: List[str]) -> None`
   - Merge new model long names with existing valid_models
   - For models already in valid_models, preserve existing short names
   - For new models, use the full model ID as the short name (temporary strategy)
   - Update valid_models dict in place

**Testing Requirements:**
- Create `tests/test_ProviderConfig.py` if it doesn't exist
- Test all helper methods with various inputs:
  - `get_valid_models()` with empty and populated dicts
  - `get_invalid_models()` with empty and populated lists
  - `find_model()` with exact matches, substring matches, and no matches
  - `merge_valid_models()` with new models, existing models, and mixed scenarios
- Test field initialization and defaults
- Test backward compatibility (loading config without invalid_models field)
- All tests must pass before proceeding to next step

### Step 2: Create ModelDiscoveryService.py Module

Create a new file at `modules/ModelDiscoveryService.py` to handle all API operations for model discovery.

**Requirements:**
- Import required dependencies: `requests`, `time`, `List`, `Any`, `Dict`, `Optional`
- Import `ProviderConfig` from the new module: `from modules.ProviderConfig import ProviderConfig`

**Class Structure:**
```python
class ModelDiscoveryService:
    def __init__(self):
        self.cache_duration = 300  # 5 minutes cache
```

**Methods to Implement:**

1. `discover_models(provider_config: ProviderConfig, force_refresh: bool = False) -> List[Dict[str, Any]]`

   **Purpose:** Query the provider's `/v1/models` endpoint for available models

   **Implementation Requirements:**
   - Check cache first unless force_refresh is True
   - Cache validation: check `provider_config._cached_models`, `provider_config._cache_timestamp`, and compare `time.time() - provider_config._cache_timestamp < provider_config.cache_duration`
   - If cache is valid, return `provider_config._cached_models`
   - Build API endpoint URL: `f"{provider_config.base_api_url}/models"`
   - Prepare headers with authentication:
     ```python
     headers = {
         "Authorization": f"Bearer {provider_config.api_key}",
         "Content-Type": "application/json"
     }
     ```
   - Make GET request with 10-second timeout
   - Parse response: `models_data.get("data", [])`
   - Update cache: set `provider_config._cached_models` and `provider_config._cache_timestamp`
   - Return models list

   **Error Handling (CRITICAL - PRESERVE EXACTLY):**
   - Wrap all API operations in try-except block
   - On any exception, fallback to `provider_config._cached_models` if available
   - Return empty list if no cached models available
   - This pattern must match the existing error handling in OpenAIChatCompletionApi:273-283

2. `validate_model(provider_config: ProviderConfig, model: str) -> bool`

   **Purpose:** Validate if a model supports chat completion via ping-pong test

   **Implementation Requirements:**
   - Build chat completions endpoint URL: `f"{provider_config.base_api_url}/chat/completions"`
   - Prepare headers (same as discover_models)
   - Prepare test payload:
     ```python
     data = {
         "model": model,
         "messages": [
             {"role": "system", "content": "If I say 'ping', you will respond with 'pong'."},
             {"role": "user", "content": "ping"}
         ],
         "max_tokens": 10,
         "temperature": 0.1
     }
     ```
   - Make POST request with 10-second timeout
   - Parse response and check if "pong" is in content (case-insensitive)
   - Return True if validation successful, False otherwise

   **Error Handling:**
   - Return False on any exception
   - Do not log or raise exceptions

3. `validate_api_key(provider_config: ProviderConfig) -> bool`

   **Purpose:** Validate if API key is configured

   **Implementation:** Return `bool(provider_config.api_key and provider_config.api_key.strip())`

**Testing Requirements:**
- Create `tests/test_ModelDiscoveryService.py`
- Use mocked HTTP responses for testing (do not make real API calls in tests)
- Test `discover_models()`:
  - Successful API response
  - Cache hit scenario
  - Force refresh behavior
  - Error with cached fallback
  - Error without cached fallback
- Test `validate_model()`:
  - Successful validation (response contains "pong")
  - Failed validation (response doesn't contain "pong")
  - API error handling
- Test `validate_api_key()`:
  - Valid key
  - Empty string
  - None value
  - Whitespace-only string
- All tests must pass before proceeding to next step

### Step 3: Update Types.py

Modify `modules/Types.py` to remove the ProviderConfig class and add necessary imports.

**Requirements:**
- Remove the entire `ProviderConfig` class definition
- Add import statement: `from modules.ProviderConfig import ProviderConfig`
- Keep all other content unchanged:
  - `PROVIDER_DATA` constant
  - `ConfigModel` class
  - All other type definitions and constants

**Testing Requirements:**
- Run the full test suite to ensure no regressions
- Verify that all imports still work correctly
- All existing tests must still pass

### Step 4: Update Example YAML Configuration

Update the example provider configuration file to include the new `invalid_models` field.

**File:** `data/openaicompat-providers.yaml`

**Requirements:**
- Add `invalid_models` field to each provider configuration
- Use empty list as default: `invalid_models: []`
- Add comment explaining the field's purpose
- Maintain all existing fields and formatting

**Example format:**
```yaml
providers:
  openai:
    api_key: your-api-key-here
    base_api_url: https://api.openai.com/v1
    name: OpenAI
    valid_models:
      gpt-4o-2024-08-06: 4o
      gpt-4o-mini-2024-07-18: 4o-mini
    invalid_models: []  # Models that don't support chat completion
```

**Note:** This is an example file update only. Real user YAML files do not need to be modified - backward compatibility ensures they will work unchanged.

## Post-Implementation Steps

### Step 1: Run Full Test Suite

Execute the complete test suite using `make test` or `pytest`.

**Success Criteria:**
- All existing tests must pass
- All new tests for Phase 1 must pass
- No test failures or errors

**On Failure:**
- Document which tests failed
- Update status document with details
- Notify user
- Do not proceed to status document creation

### Step 2: Create/Update Status Document

Create or update the file `admin/refactor-providers/status/phase_1_execution_status.md` with the current execution status.

**Status Document Format:**

```markdown
# Phase 1 Execution Status

## Last Updated
[Timestamp]

## Overall Status
[COMPLETED | IN PROGRESS | NOT STARTED | NEEDS CLARIFICATION]

## Test Suite Results
- Total Tests: [number]
- Passing: [number]
- Failing: [number]
- Details: [summary of any failures]

## Implementation Steps Status

### Pre-Implementation Steps
- [ ] Step 1: Read Master Plan - [STATUS]
- [ ] Step 2: Check Execution Status - [STATUS]
- [ ] Step 3: Run Test Suite - [STATUS]
- [ ] Step 4: Review Existing Codebase - [STATUS]

### Implementation Steps
- [ ] Step 1: Create ProviderConfig.py Module - [STATUS]
- [ ] Step 2: Create ModelDiscoveryService.py Module - [STATUS]
- [ ] Step 3: Update Types.py - [STATUS]
- [ ] Step 4: Update Example YAML Configuration - [STATUS]

### Post-Implementation Steps
- [ ] Step 1: Run Full Test Suite - [STATUS]
- [ ] Step 2: Create/Update Status Document - [STATUS]

## Detailed Notes
[Any issues encountered, decisions made, or clarifications needed]

## Next Step
[Single concrete next action to take, from the executor's perspective]
```

**Status Values:**
- `COMPLETED` - Step fully implemented and tested
- `IN PROGRESS` - Step started but not finished
- `NOT STARTED` - Step not yet begun
- `NEEDS CLARIFICATION` - Blocked waiting for user input

**Critical Requirements:**
- Status document must be concise
- Reference step numbers from this execution plan
- Do not repeat step instructions, only status
- End with exactly ONE next step
- Update timestamp each time document is modified

## Success Criteria

Phase 1 is considered complete when:

1. ✅ All pre-implementation steps completed successfully
2. ✅ `modules/ProviderConfig.py` created with all required fields and methods
3. ✅ `modules/ModelDiscoveryService.py` created with all required methods
4. ✅ `modules/Types.py` updated to import ProviderConfig
5. ✅ `data/openaicompat-providers.yaml` updated with invalid_models field
6. ✅ All new tests created and passing:
   - `tests/test_ProviderConfig.py`
   - `tests/test_ModelDiscoveryService.py`
7. ✅ All existing tests still passing
8. ✅ Status document created and up-to-date
9. ✅ No code breaks, no regressions, backward compatibility maintained

## Key Principles for Phase 1

1. **Preserve Existing Behavior**: When extracting code from OpenAIChatCompletionApi, copy it verbatim unless explicitly instructed otherwise

2. **Backward Compatibility**: Existing YAML files without `invalid_models` must continue to work

3. **Error Handling**: Maintain exact error handling patterns from existing code

4. **Testing**: Create comprehensive tests for all new functionality

5. **Incremental Progress**: Complete each step fully before moving to the next

6. **Status Tracking**: Update status document after completing each major step

7. **Stop on Failure**: If any step fails, stop immediately and notify user

## Related Master Plan Sections

- **Phase 1 Details**: Lines 205-353 in master_plan.md
- **ProviderConfig Structure**: Lines 84-93, 211-238
- **ModelDiscoveryService Structure**: Lines 95-108, 240-330
- **Backward Compatibility**: Lines 34-41, 233-238
- **Error Handling Preservation**: Lines 18-31, 330
- **Testing Strategy**: Lines 180-189, 349-353
