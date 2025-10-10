# Phase 1 Execution Plan: Enhanced ProviderConfig and ModelDiscoveryService

## Introduction

This execution plan details the implementation of Phase 1 of the provider refactoring project. Phase 1 focuses on creating the foundational classes (`ProviderConfig` and `ModelDiscoveryService`) that will form the basis for the new architecture.

**Sub-Agent Delegation Strategy:**
This plan leverages sub-agents for discrete, well-defined tasks that can be completed autonomously. The executor will use the Task tool to delegate:
- Module creation (ProviderConfig.py, ModelDiscoveryService.py)
- Test file creation (test_ProviderConfig.py, test_ModelDiscoveryService.py)
- Code extraction and migration tasks

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

**SUBPART A: Delegate to Sub-Agent**

Use the Task tool to create the ProviderConfig.py module with a general-purpose agent:

```python
Task(
    description="Create ProviderConfig module",
    prompt="""
Create a new file at modules/ProviderConfig.py with the enhanced ProviderConfig class.

REQUIREMENTS:
1. Import dependencies: from pydantic import BaseModel, Field, PrivateAttr, List, Any, Dict, Optional
2. Move ProviderConfig class from modules/Types.py to this new file
3. Implement the following field structure:

PERSISTED FIELDS (saved to YAML):
- name: str = Field(default="Test Provider", description="Provider Name")
- base_api_url: str = Field(default="https://test.openai.com/v1", description="Base API URL")
- api_key: str = Field(default="", description="API Key")
- valid_models: dict[str, str] = Field(default_factory=dict, description="Valid models")
- invalid_models: List[str] = Field(default_factory=list, description="Invalid models") [NEW FIELD]

RUNTIME-ONLY FIELDS (PrivateAttr, not saved to YAML):
- _cached_models: List[Any] = PrivateAttr(default_factory=list)
- _cache_timestamp: float = PrivateAttr(default=0.0)
- cache_duration: int = PrivateAttr(default=300)

4. Add model_post_init method:
   def model_post_init(self, __context: Any) -> None:
       self._cached_models = []
       self._cache_timestamp = 0.0
       self.cache_duration = 300

5. Implement helper methods:
   - get_valid_models() -> List[str]: Return list of valid model long names (keys from valid_models dict)
   - get_invalid_models() -> List[str]: Return copy of invalid_models list
   - find_model(name: str) -> Optional[str]: Search for model by name (exact match on long/short name, then substring match)
   - merge_valid_models(models: List[str]) -> None: Merge new models with existing mappings

6. Ensure backward compatibility: invalid_models defaults to empty list, existing YAML files without this field must work

OUTPUT REQUIREMENTS:
- Return the complete file content for modules/ProviderConfig.py
- Confirm all fields and methods are implemented correctly
- Verify backward compatibility is maintained
""",
    subagent_type="general-purpose"
)
```

**SUBPART B: Create Test File**

Use the Task tool to create comprehensive tests:

```python
Task(
    description="Create ProviderConfig tests",
    prompt="""
Create comprehensive unit tests for the ProviderConfig class in tests/test_ProviderConfig.py.

TEST REQUIREMENTS:
1. Test field initialization and defaults
2. Test get_valid_models() with empty and populated dicts
3. Test get_invalid_models() with empty and populated lists
4. Test find_model() with:
   - Exact matches on long names
   - Exact matches on short names
   - Substring matches on long names
   - Substring matches on short names
   - No matches
5. Test merge_valid_models() with:
   - New models (should use full model ID as short name)
   - Existing models (should preserve existing short names)
   - Mixed scenarios
6. Test backward compatibility (loading config without invalid_models field)
7. Use pytest fixtures and assertions
8. Ensure all tests pass

OUTPUT REQUIREMENTS:
- Return the complete file content for tests/test_ProviderConfig.py
- Confirm all test cases are implemented
- Verify tests use proper mocking and assertions
""",
    subagent_type="general-purpose"
)
```

**Executor Responsibilities:**
- Verify the sub-agent output matches requirements
- Save the generated files to the correct locations
- Run the tests to ensure they pass
- Update status document with results

### Step 2: Create ModelDiscoveryService.py Module

**SUBPART A: Delegate to Sub-Agent**

Use the Task tool to create the ModelDiscoveryService.py module:

```python
Task(
    description="Create ModelDiscoveryService module",
    prompt="""
Create a new file at modules/ModelDiscoveryService.py with the ModelDiscoveryService class.

REQUIREMENTS:
1. Import dependencies: requests, time, List, Any, Dict, Optional
2. Import ProviderConfig: from modules.ProviderConfig import ProviderConfig
3. Class structure:
   class ModelDiscoveryService:
       def __init__(self):
           self.cache_duration = 300  # 5 minutes cache

4. Implement discover_models() method:
   def discover_models(provider_config: ProviderConfig, force_refresh: bool = False) -> List[Dict[str, Any]]:
   - Check cache first unless force_refresh is True
   - Cache validation: check provider_config._cached_models, provider_config._cache_timestamp, and time.time() - provider_config._cache_timestamp < provider_config.cache_duration
   - If cache valid, return provider_config._cached_models
   - Build API URL: f"{provider_config.base_api_url}/models"
   - Prepare headers: {"Authorization": f"Bearer {provider_config.api_key}", "Content-Type": "application/json"}
   - Make GET request with 10-second timeout
   - Parse response: models_data.get("data", [])
   - Update cache: provider_config._cached_models = models_list, provider_config._cache_timestamp = time.time()
   - Return models list

   CRITICAL ERROR HANDLING (preserve exactly from OpenAIChatCompletionApi:273-283):
   - Wrap all API operations in try-except
   - On any exception, fallback to provider_config._cached_models if available
   - Return empty list if no cached models available

5. Implement validate_model() method:
   def validate_model(provider_config: ProviderConfig, model: str) -> bool:
   - Build URL: f"{provider_config.base_api_url}/chat/completions"
   - Prepare headers (same as discover_models)
   - Test payload: {"model": model, "messages": [{"role": "system", "content": "If I say 'ping', you will respond with 'pong'."}, {"role": "user", "content": "ping"}], "max_tokens": 10, "temperature": 0.1}
   - Make POST request with 10-second timeout
   - Parse response and check if "pong" in content.lower()
   - Return True if successful, False on any exception

6. Implement validate_api_key() method:
   def validate_api_key(provider_config: ProviderConfig) -> bool:
   - Return bool(provider_config.api_key and provider_config.api_key.strip())

OUTPUT REQUIREMENTS:
- Return the complete file content for modules/ModelDiscoveryService.py
- Confirm all methods are implemented with proper error handling
- Verify the exact error handling pattern is preserved
""",
    subagent_type="general-purpose"
)
```

**SUBPART B: Create Test File**

Use the Task tool to create comprehensive tests:

```python
Task(
    description="Create ModelDiscoveryService tests",
    prompt="""
Create comprehensive unit tests for the ModelDiscoveryService class in tests/test_ModelDiscoveryService.py.

TEST REQUIREMENTS:
1. Use mocked HTTP responses (do not make real API calls)
2. Test discover_models() with:
   - Successful API response
   - Cache hit scenario (return cached models)
   - Force refresh behavior (bypass cache)
   - Error with cached fallback (return cached models on error)
   - Error without cached fallback (return empty list)
3. Test validate_model() with:
   - Successful validation (response contains "pong")
   - Failed validation (response doesn't contain "pong")
   - API error handling (return False on exception)
4. Test validate_api_key() with:
   - Valid API key (return True)
   - Empty string (return False)
   - None value (return False)
   - Whitespace-only string (return False)
5. Use pytest fixtures and proper mocking (unittest.mock)
6. Ensure all tests pass

OUTPUT REQUIREMENTS:
- Return the complete file content for tests/test_ModelDiscoveryService.py
- Confirm all test cases are implemented with proper mocking
- Verify tests cover all error scenarios
""",
    subagent_type="general-purpose"
)
```

**Executor Responsibilities:**
- Verify the sub-agent output matches requirements
- Save the generated files to the correct locations
- Run the tests to ensure they pass
- Update status document with results

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
