# Phase 1 Execution Plan: Enhanced ProviderConfig and ModelDiscoveryService

## Introduction

This phase establishes the foundational components for the provider configuration refactoring: creating the enhanced ProviderConfig class as a pure data model, and implementing the ModelDiscoveryService class to handle all API operations for model discovery and validation.

**CRITICAL**: If ANY step cannot be completed successfully, IMMEDIATELY:
1. Stop execution
2. Update the phase 1 status document with current state
3. Notify the user with details of the blocking issue

The goal is to create two independent, well-tested modules that will serve as building blocks for subsequent phases, while maintaining complete backward compatibility with existing configuration files.

---

## Pre-Implementation Steps

### Step 0.1: Read Master Plan

**Objective**: Understand the complete refactoring vision and architectural decisions.

**Actions**:
- Read `admin/refactor-providers/master_plan.md` in its entirety
- Pay special attention to:
  - Core Guiding Principles (lines 14-41)
  - Proposed Architecture (lines 66-178)
  - Phase 1 details (lines 205-353)
  - Critical Implementation Details (lines 719-900)

### Step 0.2: Review Current Status

**Objective**: Determine if Phase 1 has been started and what remains.

**Actions**:
- Check if `admin/refactor-providers/status/phase_1_execution_status.md` exists
- If it exists, read it and use its contents to determine where to resume execution
- If it doesn't exist, proceed from Step 0.3

### Step 0.3: Run Test Suite

**Objective**: Establish baseline - ensure all tests pass before making changes.

**Actions**:
- Run: `make test` or `pytest`
- Verify ALL tests pass
- **If tests fail**: Stop and notify user - do not proceed until baseline is clean

### Step 0.4: Review Current Codebase

**Objective**: Understand existing code structure before refactoring.

**Actions**:
- Read `modules/Types.py` to understand current ProviderConfig implementation
- Read `modules/OpenAIChatCompletionApi.py` focusing on:
  - Model discovery methods (lines ~273-283)
  - Caching logic
  - Error handling patterns
- Read `modules/Config.py` to understand configuration loading sequence (lines ~66-97)
- Identify all files that import or use ProviderConfig

---

## Implementation Steps

### Step 1.1: Create Enhanced ProviderConfig Module

**Objective**: Create standalone ProviderConfig class as pure data model with no API logic.

**Sub-Agent Delegation Opportunity**: ✅ **YES** - This is a well-defined module creation task

**Implementation Method**: Execute via sub-agent using Task tool:

```python
Task(
    description="Create ProviderConfig module",
    subagent_type="general-purpose",
    prompt="""
Create the new file modules/ProviderConfig.py with enhanced ProviderConfig class.

REQUIREMENTS:

1. Create file: modules/ProviderConfig.py

2. Add required imports:
   - from pydantic import BaseModel, Field, PrivateAttr
   - from typing import List, Any, Dict, Optional

3. Implement ProviderConfig class EXACTLY as specified:

```python
class ProviderConfig(BaseModel):
    \"\"\"
    Provider configuration data model.

    Persisted fields (saved to YAML):
    - name, base_api_url, api_key, valid_models, invalid_models

    Runtime-only fields (not saved to YAML):
    - _cached_models, _cache_timestamp, cache_duration
    \"\"\"

    # Persisted fields
    name: str = Field(default="Test Provider", description="Provider Name")
    base_api_url: str = Field(default="https://test.openai.com/v1", description="Base API URL")
    api_key: str = Field(default="", description="API Key")
    valid_models: dict[str, str] = Field(default_factory=dict, description="Valid models (long_name: short_name)")
    invalid_models: List[str] = Field(default_factory=list, description="Invalid models")

    # Runtime-only fields (excluded from serialization)
    _cached_models: List[Any] = PrivateAttr(default_factory=list)
    _cache_timestamp: float = PrivateAttr(default=0.0)
    cache_duration: int = PrivateAttr(default=300)

    def model_post_init(self, __context: Any) -> None:
        \"\"\"Initialize runtime-only fields after model creation.\"\"\"
        self._cached_models = []
        self._cache_timestamp = 0.0
        self.cache_duration = 300

    def get_valid_models(self) -> List[str]:
        \"\"\"Return list of valid model long names.\"\"\"
        return list(self.valid_models.keys())

    def get_invalid_models(self) -> List[str]:
        \"\"\"Return list of invalid model names.\"\"\"
        return self.invalid_models.copy()

    def find_model(self, name: str) -> Optional[str]:
        \"\"\"
        Search for model by name across valid models.

        Search order:
        1. Exact match on long name
        2. Exact match on short name
        3. Substring match on long name (first match)
        4. Substring match on short name (first match)

        Args:
            name: Model name to search for

        Returns:
            Long model name if found, None otherwise
        \"\"\"
        name_lower = name.lower()

        # Exact match on long name
        for long_name in self.valid_models.keys():
            if long_name.lower() == name_lower:
                return long_name

        # Exact match on short name
        for long_name, short_name in self.valid_models.items():
            if short_name.lower() == name_lower:
                return long_name

        # Substring match on long name (first match)
        for long_name in self.valid_models.keys():
            if name_lower in long_name.lower():
                return long_name

        # Substring match on short name (first match)
        for long_name, short_name in self.valid_models.items():
            if name_lower in short_name.lower():
                return long_name

        return None

    def merge_valid_models(self, models: List[str]) -> None:
        \"\"\"
        Merge new models with existing valid_models.

        For new models without existing mappings, use full model ID as short name.
        Existing mappings are preserved.

        Args:
            models: List of model long names to merge
        \"\"\"
        for model_long_name in models:
            if model_long_name not in self.valid_models:
                # Use full model ID as short name initially
                self.valid_models[model_long_name] = model_long_name
```

4. CRITICAL BACKWARD COMPATIBILITY:
   - invalid_models field must have default_factory=list
   - Existing YAML files without invalid_models must work unchanged
   - All existing ProviderConfig fields must maintain exact same structure

5. OUTPUT REQUIREMENTS:
   - Report SUCCESS if file created with all methods implemented
   - Report FAILURE if any errors occur
   - Include file path and line count in success report
"""
)
```

**Expected Output**: Success report with confirmation that `modules/ProviderConfig.py` was created with all required methods.

---

### Step 1.2: Create ModelDiscoveryService Module

**Objective**: Create service class to handle all API operations for model discovery and validation.

**Sub-Agent Delegation Opportunity**: ✅ **YES** - This is a well-defined module creation task

**Implementation Method**: Execute via sub-agent using Task tool:

```python
Task(
    description="Create ModelDiscoveryService module",
    subagent_type="general-purpose",
    prompt="""
Create the new file modules/ModelDiscoveryService.py with ModelDiscoveryService class.

REQUIREMENTS:

1. Create file: modules/ModelDiscoveryService.py

2. Add required imports:
   - import requests
   - import time
   - from typing import List, Any, Dict, Optional
   - from modules.ProviderConfig import ProviderConfig

3. Implement ModelDiscoveryService class with THREE methods:

```python
class ModelDiscoveryService:
    \"\"\"
    Service for discovering and validating models via provider APIs.

    Handles:
    - Model discovery via /models endpoint
    - Model validation via ping tests
    - API key validation
    - Caching logic
    - Error handling and fallback mechanisms
    \"\"\"

    def __init__(self):
        self.cache_duration = 300  # 5 minutes cache

    def discover_models(self, provider_config: ProviderConfig, force_refresh: bool = False) -> List[Dict[str, Any]]:
        \"\"\"
        Query the provider's /v1/models endpoint for available models.

        CRITICAL: Preserve EXACT error handling from OpenAIChatCompletionApi:273-283:
        - Try-except with fallback to cached models
        - Specific exception handling patterns
        - Same error recovery logic

        Args:
            provider_config: Provider configuration with API credentials
            force_refresh: Whether to bypass cache

        Returns:
            List of model dictionaries or empty list on error
        \"\"\"
        # Check cache first
        if (not force_refresh and
            provider_config._cached_models and
            provider_config._cache_timestamp and
            time.time() - provider_config._cache_timestamp < provider_config.cache_duration):
            return provider_config._cached_models

        try:
            # Build the API endpoint URL
            url = f"{provider_config.base_api_url}/models"

            # Prepare headers with authentication
            headers = {
                "Authorization": f"Bearer {provider_config.api_key}",
                "Content-Type": "application/json"
            }

            # Make the API request
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            # Parse and cache the response
            models_data = response.json()
            models_list = models_data.get("data", [])

            # Update cache
            provider_config._cached_models = models_list
            provider_config._cache_timestamp = time.time()

            return models_list

        except Exception as e:
            # Fallback to cached models if available
            if provider_config._cached_models:
                return provider_config._cached_models
            return []

    def validate_model(self, provider_config: ProviderConfig, model: str) -> bool:
        \"\"\"
        Validate if a model supports chat completion by performing a simple ping test.

        Args:
            provider_config: Provider configuration with API credentials
            model: Model name to validate

        Returns:
            True if model is valid, False otherwise
        \"\"\"
        try:
            # Simple ping test without creating OpenAIChatCompletionApi instance
            url = f"{provider_config.base_api_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {provider_config.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "If I say 'ping', you will respond with 'pong'."},
                    {"role": "user", "content": "ping"}
                ],
                "max_tokens": 10,
                "temperature": 0.1
            }

            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()

            # Check if response contains "pong"
            result = response.json()
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            return "pong" in content.lower()

        except Exception:
            return False

    def validate_api_key(self, provider_config: ProviderConfig) -> bool:
        \"\"\"
        Validate if API key is configured and potentially valid.

        Args:
            provider_config: Provider configuration with API credentials

        Returns:
            False if API key is None or empty, True otherwise
        \"\"\"
        return bool(provider_config.api_key and provider_config.api_key.strip())
```

4. CRITICAL ERROR HANDLING:
   - PRESERVE exact error handling patterns from OpenAIChatCompletionApi
   - Fallback to cached models on error
   - Use same exception handling approach

5. OUTPUT REQUIREMENTS:
   - Report SUCCESS if file created with all three methods implemented
   - Report FAILURE if any errors occur
   - Include file path and line count in success report
"""
)
```

**Expected Output**: Success report with confirmation that `modules/ModelDiscoveryService.py` was created with all three methods.

---

### Step 1.3: Update Types.py

**Objective**: Remove ProviderConfig class definition and update imports.

**Actions**:
1. Read `modules/Types.py` to understand current structure
2. Locate ProviderConfig class definition
3. Remove ProviderConfig class definition completely
4. Add import at top of file: `from modules.ProviderConfig import ProviderConfig`
5. Verify PROVIDER_DATA constant remains unchanged
6. Verify ConfigModel and other global types remain unchanged

**Critical Preservation**:
- Keep PROVIDER_DATA constant exactly as-is
- Keep ConfigModel class definition unchanged (for now)
- Keep all other type definitions unchanged

**Testing After This Step**:
- Run: `pytest tests/test_Types.py` (if it exists)
- Verify imports still work from other modules

---

### Step 1.4: Create Unit Tests for ProviderConfig

**Objective**: Comprehensive testing of ProviderConfig helper methods.

**Sub-Agent Delegation Opportunity**: ✅ **YES** - This is a discrete test creation task

**Implementation Method**: Execute via sub-agent using Task tool:

```python
Task(
    description="Create ProviderConfig unit tests",
    subagent_type="general-purpose",
    prompt="""
Create comprehensive unit tests for the new ProviderConfig class.

REQUIREMENTS:

1. Create or update file: tests/test_ProviderConfig.py

2. Import requirements:
   - import pytest
   - from modules.ProviderConfig import ProviderConfig

3. Implement test cases covering ALL methods:

TEST SUITE REQUIREMENTS:

a) test_provider_config_initialization()
   - Test default field values
   - Test custom field values
   - Test runtime field initialization via model_post_init

b) test_backward_compatibility()
   - Test ProviderConfig creation without invalid_models field
   - Verify invalid_models defaults to empty list
   - Test YAML-like dict input without invalid_models

c) test_get_valid_models()
   - Test with empty valid_models
   - Test with multiple valid_models
   - Verify returns list of long names only

d) test_get_invalid_models()
   - Test with empty invalid_models
   - Test with multiple invalid_models
   - Verify returns copy (not reference)

e) test_find_model_exact_match()
   - Test exact match on long name
   - Test exact match on short name
   - Test case-insensitive matching

f) test_find_model_substring_match()
   - Test substring match on long name
   - Test substring match on short name
   - Test priority order (long exact > short exact > long substring > short substring)

g) test_find_model_not_found()
   - Test with nonexistent model name
   - Verify returns None

h) test_merge_valid_models_new()
   - Test merging new models
   - Verify new models use full ID as short name

i) test_merge_valid_models_existing()
   - Test merging models that already exist
   - Verify existing mappings are preserved
   - Verify no duplicate entries created

j) test_merge_valid_models_mixed()
   - Test merging mix of new and existing models
   - Verify correct behavior for both

k) test_cache_fields()
   - Test _cached_models initialization
   - Test _cache_timestamp initialization
   - Test cache_duration initialization
   - Verify these are PrivateAttr (not serialized)

4. Use pytest best practices:
   - Use fixtures where appropriate
   - Clear test names
   - Comprehensive assertions
   - Edge case coverage

5. OUTPUT REQUIREMENTS:
   - Report number of test cases created
   - Report SUCCESS if all tests pass
   - Report FAILURE with details if any test fails
   - Include test file path in report
"""
)
```

**Expected Output**: Success report with test count and confirmation all tests pass.

---

### Step 1.5: Create Unit Tests for ModelDiscoveryService

**Objective**: Comprehensive testing with mocked HTTP responses.

**Sub-Agent Delegation Opportunity**: ✅ **YES** - This is a discrete test creation task

**Implementation Method**: Execute via sub-agent using Task tool:

```python
Task(
    description="Create ModelDiscoveryService unit tests",
    subagent_type="general-purpose",
    prompt="""
Create comprehensive unit tests for ModelDiscoveryService with mocked HTTP calls.

REQUIREMENTS:

1. Create file: tests/test_ModelDiscoveryService.py

2. Import requirements:
   - import pytest
   - import time
   - from unittest.mock import Mock, patch, MagicMock
   - from modules.ModelDiscoveryService import ModelDiscoveryService
   - from modules.ProviderConfig import ProviderConfig

3. Create fixtures:
   - mock_provider_config: ProviderConfig instance with test data
   - mock_discovery_service: ModelDiscoveryService instance

4. Implement test cases for ALL methods:

TEST SUITE REQUIREMENTS:

a) test_discover_models_success()
   - Mock requests.get to return valid model list
   - Verify models are cached
   - Verify cache timestamp is updated
   - Verify correct return value

b) test_discover_models_cache_hit()
   - Set up cached models with recent timestamp
   - Call discover_models without force_refresh
   - Verify no HTTP request made
   - Verify cached models returned

c) test_discover_models_cache_expired()
   - Set up cached models with old timestamp
   - Mock requests.get for new data
   - Verify HTTP request is made
   - Verify cache is updated

d) test_discover_models_force_refresh()
   - Set up cached models
   - Call discover_models with force_refresh=True
   - Verify HTTP request made despite cache
   - Verify cache is updated

e) test_discover_models_error_with_cache()
   - Set up cached models
   - Mock requests.get to raise exception
   - Verify fallback to cached models
   - Verify cached models returned

f) test_discover_models_error_without_cache()
   - No cached models
   - Mock requests.get to raise exception
   - Verify empty list returned
   - Verify no crash

g) test_validate_model_success()
   - Mock requests.post to return "pong" response
   - Verify returns True
   - Verify correct API endpoint called
   - Verify correct request payload

h) test_validate_model_failure()
   - Mock requests.post to raise exception
   - Verify returns False
   - Verify no crash

i) test_validate_model_wrong_response()
   - Mock requests.post to return response without "pong"
   - Verify returns False

j) test_validate_api_key_valid()
   - Test with valid API key
   - Verify returns True

k) test_validate_api_key_empty()
   - Test with empty string API key
   - Verify returns False

l) test_validate_api_key_none()
   - Test with None API key
   - Verify returns False

m) test_validate_api_key_whitespace()
   - Test with whitespace-only API key
   - Verify returns False

5. Use pytest and unittest.mock best practices:
   - Use @patch decorator for requests mocking
   - Clear assertions
   - Comprehensive edge case coverage

6. OUTPUT REQUIREMENTS:
   - Report number of test cases created
   - Report SUCCESS if all tests pass
   - Report FAILURE with details if any test fails
   - Include test file path in report
"""
)
```

**Expected Output**: Success report with test count and confirmation all tests pass.

---

### Step 1.6: Integration Testing

**Objective**: Verify ProviderConfig and ModelDiscoveryService work together correctly.

**Actions**:
1. Create `tests/test_integration_phase1.py`
2. Implement integration tests:
   - Test ModelDiscoveryService modifying ProviderConfig cache fields
   - Test complete workflow: discover → validate → merge
   - Test error scenarios with fallback behavior
   - Test cache timing and expiration

**Test Requirements**:
```python
# Test: ModelDiscoveryService updates ProviderConfig cache correctly
# Test: Complete discovery workflow with mocked API
# Test: Error handling preserves ProviderConfig state
# Test: Cache expiration triggers re-discovery
```

**Expected Result**: All integration tests pass, demonstrating correct coordination.

---

### Step 1.7: Regression Testing

**Objective**: Ensure existing functionality remains unchanged.

**Actions**:
1. Run full test suite: `make test` or `pytest`
2. Verify ALL existing tests still pass
3. Pay special attention to:
   - Tests that import or use ProviderConfig
   - Tests that use Types.py
   - Configuration loading tests

**Expected Behavior**:
- Some tests may need import updates (from modules.ProviderConfig import ProviderConfig)
- No test logic should need changes
- All tests should pass

**If Tests Fail**:
- Investigate import issues first
- Check for missing backward compatibility
- Do not proceed until all tests pass

---

## Post-Implementation Steps

### Step 2.1: Run Full Test Suite

**Objective**: Final verification that all tests pass.

**Actions**:
1. Run: `make test` or `pytest -v`
2. Verify all tests pass (new and existing)
3. Note total test count and any warnings

**Expected Outcome**: 100% test pass rate with no critical warnings.

---

### Step 2.2: Create/Update Phase 1 Status Document

**Objective**: Document completion status and current state.

**Actions**:
1. Create `admin/refactor-providers/status/phase_1_execution_status.md`
2. Document status of each step using format below

**Status Document Format**:

```markdown
# Phase 1 Execution Status

**Last Updated**: [TIMESTAMP]

**Overall Status**: [COMPLETED | IN PROGRESS | BLOCKED]

---

## Pre-Implementation Steps

| Step | Status | Notes |
|------|--------|-------|
| 0.1: Read Master Plan | COMPLETED | - |
| 0.2: Review Current Status | COMPLETED | No prior status document existed |
| 0.3: Run Test Suite | COMPLETED | All [N] tests passed |
| 0.4: Review Current Codebase | COMPLETED | Reviewed Types.py, OpenAIChatCompletionApi.py, Config.py |

---

## Implementation Steps

| Step | Status | Notes |
|------|--------|-------|
| 1.1: Create ProviderConfig Module | [STATUS] | [NOTES] |
| 1.2: Create ModelDiscoveryService Module | [STATUS] | [NOTES] |
| 1.3: Update Types.py | [STATUS] | [NOTES] |
| 1.4: Create ProviderConfig Tests | [STATUS] | [N] test cases created |
| 1.5: Create ModelDiscoveryService Tests | [STATUS] | [N] test cases created |
| 1.6: Integration Testing | [STATUS] | [NOTES] |
| 1.7: Regression Testing | [STATUS] | All [N] tests passed |

---

## Post-Implementation Steps

| Step | Status | Notes |
|------|--------|-------|
| 2.1: Run Full Test Suite | [STATUS] | [N] total tests, [N] passed, [N] failed |
| 2.2: Create Status Document | COMPLETED | This document |

---

## Test Results Summary

**Total Tests**: [N]
**Passed**: [N]
**Failed**: [N]
**Warnings**: [N]

**New Tests Added**:
- test_ProviderConfig.py: [N] tests
- test_ModelDiscoveryService.py: [N] tests
- test_integration_phase1.py: [N] tests

---

## Files Created/Modified

**Created**:
- modules/ProviderConfig.py ([N] lines)
- modules/ModelDiscoveryService.py ([N] lines)
- tests/test_ProviderConfig.py ([N] lines)
- tests/test_ModelDiscoveryService.py ([N] lines)
- tests/test_integration_phase1.py ([N] lines)

**Modified**:
- modules/Types.py (removed ProviderConfig class, added import)

---

## Known Issues

[List any issues encountered, partial completions, or blockers]

---

## Next Step

**From Executor Perspective**: [Single most important next action - either "Phase 1 complete, ready for Phase 2" or "Address [specific issue]"]
```

---

## Critical Requirements Verification

This execution plan explicitly addresses all items from the CRITICAL REQUIREMENTS CHECKLIST:

### ✅ SUB-AGENT DELEGATION
- **Step 1.1**: Sub-agent creates ProviderConfig.py with complete Task() syntax
- **Step 1.2**: Sub-agent creates ModelDiscoveryService.py with complete Task() syntax
- **Step 1.4**: Sub-agent creates ProviderConfig unit tests with complete Task() syntax
- **Step 1.5**: Sub-agent creates ModelDiscoveryService unit tests with complete Task() syntax
- All include clear description, detailed prompt with context, subagent_type, and expected output format

### ✅ TESTING REQUIREMENTS
- **Step 1.4**: Specific pytest requirements for ProviderConfig (11 test cases specified)
- **Step 1.5**: Specific pytest requirements for ModelDiscoveryService (13 test cases specified)
- **Step 1.6**: Integration testing requirements
- **Step 1.7**: Regression testing requirements
- **Step 2.1**: Final test suite verification

### ✅ BACKWARD COMPATIBILITY
- **Step 1.1**: Explicit requirement that invalid_models field defaults to empty list
- **Step 1.1**: Verification that existing YAML files without invalid_models work unchanged
- **Step 1.4**: Dedicated test case (test_backward_compatibility) to verify this
- **Step 1.7**: Regression testing to ensure existing tests pass

### ✅ ERROR HANDLING
- **Step 1.2**: Explicit instruction to preserve EXACT error handling from OpenAIChatCompletionApi:273-283
- **Step 1.2**: Requirement for fallback to cached models on error
- **Step 1.5**: Test cases for error scenarios (test_discover_models_error_with_cache, test_discover_models_error_without_cache)
- **Step 1.6**: Integration testing for error scenarios

### ✅ STATUS TRACKING
- **Step 2.2**: Complete instructions for creating/updating status document
- Detailed status document template with step-by-step tracking
- Format includes overall status, per-step status, test results, files created/modified, known issues, and next step

---

## Key Design Principles from Master Plan

This execution plan preserves the following critical principles:

1. **Preservation of Existing Behavior** (Master Plan lines 17-31):
   - Step 1.2 explicitly requires preserving error handling verbatim
   - Step 1.7 regression testing ensures no behavioral changes

2. **Backward Compatibility** (Master Plan lines 33-41):
   - Step 1.1 makes invalid_models optional with default empty list
   - Step 1.4 includes backward compatibility test case

3. **Clean Separation of Concerns** (Master Plan lines 76-93):
   - ProviderConfig is pure data model (Step 1.1)
   - ModelDiscoveryService handles all API operations (Step 1.2)
   - No circular dependencies

4. **Comprehensive Testing** (Master Plan lines 349-353):
   - Unit tests for each class
   - Mock tests for API operations
   - Partial integration tests
   - Regression validation

---

## Estimated Completion

**Time Estimate**: 2-4 hours for complete Phase 1 implementation

**Deliverables**:
- 2 new production modules (ProviderConfig.py, ModelDiscoveryService.py)
- 3 new test modules with 30+ test cases total
- 1 modified module (Types.py)
- 1 status document
- 100% test pass rate maintained
