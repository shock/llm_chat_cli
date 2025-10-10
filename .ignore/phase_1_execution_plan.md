# Phase 1 Execution Plan: Enhanced ProviderConfig and ModelDiscoveryService

## Introduction

This execution plan details the implementation of Phase 1 of the provider configuration refactoring. The primary goal of this phase is to create the foundational components for the new architecture: an enhanced ProviderConfig class as a pure data model and a ModelDiscoveryService class to handle all API operations. This phase establishes the core separation of concerns between data storage and API operations.

**Critical Note**: If any step in this execution plan cannot be completed due to unexpected codebase complexities, implementation conflicts, or test failures that cannot be resolved, the execution should be aborted immediately. The status document should be updated to reflect the blockage, and the user must be notified before proceeding.

## Pre-Implementation Steps

### Step 1: Check Current Execution Status

Before beginning implementation, scan the `/admin/refactor-providers/status/` directory to determine if a status document for Phase 1 already exists. If `phase_1_execution_status.md` exists:
- Read the status document to understand the current state of phase execution
- Use the status information to determine which steps have been completed, are in progress, or need clarification
- Continue execution from the appropriate step based on the current status

If no status document exists, proceed with the full execution plan from the beginning.

### Step 2: Review Master Plan

Read the entire master plan document at `admin/refactor-providers/master_plan.md` to understand:
- The overall architecture vision and design principles
- Phase 1 specific requirements and implementation details
- Core guiding principles (especially preservation of existing behavior)
- Backward compatibility requirements
- Testing strategy and requirements

### Step 3: Run Full Test Suite

Execute the full test suite to establish a baseline:
```bash
make test
```

**Critical Requirement**: All tests must pass before proceeding. If any tests fail, stop execution immediately and notify the user. Do not continue with implementation until all tests pass.

### Step 4: Codebase Review

Review the current codebase to understand all relevant files and modules:
- `modules/Types.py` - Current ProviderConfig class location
- `modules/OpenAIChatCompletionApi.py` - Current model discovery and validation logic
- `tests/` directory - Existing test structure and patterns
- `modules/Config.py` - Configuration loading logic

## Phase 1 Implementation Steps

### Step 1: Create ProviderConfig.py

**File**: `modules/ProviderConfig.py`

**Implementation Requirements**:
- Create new file with appropriate imports
- Move ProviderConfig class from Types.py to new file
- Implement enhanced ProviderConfig as pure data model (no API logic)
- Add new `invalid_models` field as persisted field with default empty list
- Add runtime-only fields (`_cached_models`, `_cache_timestamp`, `cache_duration`) as PrivateAttr
- Implement `model_post_init` method to initialize runtime-only fields
- Maintain backward compatibility with existing configs

**Code Implementation**:
```python
from pydantic import BaseModel, Field, PrivateAttr
from typing import List, Any, Dict, Optional

class ProviderConfig(BaseModel):
    # Existing persisted fields
    name: str = Field(default="Test Provider", description="Provider Name")
    base_api_url: str = Field(default="https://test.openai.com/v1", description="Base API URL")
    api_key: str = Field(default="", description="API Key")
    valid_models: dict[str, str] = Field(default_factory=dict, description="Valid models")

    # New persisted field
    invalid_models: List[str] = Field(default_factory=list, description="Invalid models")

    # Runtime-only fields (excluded from serialization)
    _cached_models: List[Any] = PrivateAttr(default_factory=list)
    _cache_timestamp: float = PrivateAttr(default=0.0)
    cache_duration: int = PrivateAttr(default=300)

    def model_post_init(self, __context: Any) -> None:
        self._cached_models = []
        self._cache_timestamp = 0.0
        self.cache_duration = 300
```

**Backward Compatibility**:
- Existing YAML files without `invalid_models` must work unchanged
- The field defaults to empty list if not present in config
- All existing provider configurations remain valid

### Step 2: Create ModelDiscoveryService.py

**File**: `modules/ModelDiscoveryService.py`

**Implementation Requirements**:
- Create new file with appropriate imports
- Implement ModelDiscoveryService class to handle all API operations
- Preserve existing error handling patterns from OpenAIChatCompletionApi:273-283 verbatim
- Include comprehensive error handling and fallback to cached models
- Implement caching logic with 5-minute duration (same as current)

**Code Implementation**:
```python
import requests
import time
from typing import List, Any, Dict, Optional
from modules.ProviderConfig import ProviderConfig

class ModelDiscoveryService:
    def __init__(self):
        self.cache_duration = 300  # 5 minutes cache

    def discover_models(self, provider_config: ProviderConfig, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Query the provider's /v1/models endpoint for available models.
        Returns a list of model dictionaries or empty list on error.
        """
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
        """
        Validate if a model supports chat completion by performing a simple ping test.
        Returns True if model is valid, False otherwise.
        """
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
        """
        Validate if API key is configured and potentially valid.
        Returns False if API key is None or empty.
        """
        return bool(provider_config.api_key and provider_config.api_key.strip())
```

**Error Handling Preservation**:
- Preserve exact error handling pattern from OpenAIChatCompletionApi:273-283
- Include specific RequestException handling vs general Exception
- Maintain fallback to cached models behavior
- Keep same error messages and logging patterns

### Step 3: Update ProviderConfig with Helper Methods

**File**: `modules/ProviderConfig.py`

**Implementation Requirements**:
- Add `get_valid_models()` method - returns list of valid models only
- Add `get_invalid_models()` method - returns list of invalid models only
- Add `find_model(name)` method - searches valid_models by exact match first, then substring match
- Add `merge_valid_models(models)` method - merges new models with existing mappings

**Code Implementation**:
```python
def get_valid_models(self) -> List[str]:
    """Return list of valid models only."""
    return list(self.valid_models.keys())

def get_invalid_models(self) -> List[str]:
    """Return list of invalid models only."""
    return self.invalid_models

def find_model(self, name: str) -> Optional[str]:
    """
    Search for model by name.
    First searches valid_models by exact match on long name or short name.
    If not found, searches by substring match on long name or short name.
    Returns the first match's long name, or None if none found.
    """
    # Exact match search
    if name in self.valid_models:
        return name
    if name in self.valid_models.values():
        # Find the long name for this short name
        for long_name, short_name in self.valid_models.items():
            if short_name == name:
                return long_name

    # Substring match search
    for long_name, short_name in self.valid_models.items():
        if name in long_name or name in short_name:
            return long_name

    return None

def merge_valid_models(self, models: List[str]) -> None:
    """
    Merge models with existing valid models.
    For new models without existing mappings, use full model ID as short name initially.
    """
    for model in models:
        if model not in self.valid_models:
            self.valid_models[model] = model  # Use full model ID as short name
```

**Short Name Strategy**:
- For new models without existing mappings, use full model ID as short name initially
- Future enhancement: Implement pattern-based short name generation strategy
- Preserve existing short names from PROVIDER_DATA static mappings

### Step 4: Update Types.py

**File**: `modules/Types.py`

**Implementation Requirements**:
- Remove ProviderConfig class definition
- Keep PROVIDER_DATA constant for pre-populated model data
- Keep ConfigModel and other global types
- Update imports to reference new ProviderConfig module

**Code Changes**:
- Remove ProviderConfig class definition
- Add import: `from modules.ProviderConfig import ProviderConfig`
- Ensure all other functionality remains unchanged

## Phase 1 Testing Requirements

### Unit Tests for ProviderConfig

**File**: `tests/test_ProviderConfig.py` (new file)

**Test Coverage**:
- Test ProviderConfig initialization with various field combinations
- Test `get_valid_models()` method returns correct list
- Test `get_invalid_models()` method returns correct list
- Test `find_model()` method with exact and substring matches
- Test `merge_valid_models()` method with new and existing models
- Test backward compatibility with missing `invalid_models` field
- Test runtime-only field initialization in `model_post_init`

**Example Test Cases**:
```python
def test_provider_config_initialization():
    config = ProviderConfig(
        name="Test Provider",
        base_api_url="https://api.test.com/v1",
        api_key="test-key",
        valid_models={"model1": "m1", "model2": "m2"},
        invalid_models=["bad-model"]
    )
    assert config.name == "Test Provider"
    assert config.get_valid_models() == ["model1", "model2"]
    assert config.get_invalid_models() == ["bad-model"]

def test_find_model_exact_match():
    config = ProviderConfig(valid_models={"gpt-4": "4", "gpt-3.5-turbo": "3.5"})
    assert config.find_model("gpt-4") == "gpt-4"
    assert config.find_model("4") == "gpt-4"

def test_merge_valid_models():
    config = ProviderConfig(valid_models={"existing": "ex"})
    config.merge_valid_models(["new-model"])
    assert "new-model" in config.valid_models
    assert config.valid_models["new-model"] == "new-model"
```

### Mock Tests for ModelDiscoveryService

**File**: `tests/test_ModelDiscoveryService.py` (new file)

**Test Coverage**:
- Test `discover_models()` with mocked successful API response
- Test `discover_models()` with mocked API error and fallback to cache
- Test `validate_model()` with mocked successful ping test
- Test `validate_model()` with mocked failed ping test
- Test `validate_api_key()` with various key formats
- Test caching behavior with force_refresh parameter
- Test error handling patterns match current OpenAIChatCompletionApi behavior

**Example Test Cases**:
```python
import pytest
from unittest.mock import Mock, patch

def test_discover_models_success(mocker):
    service = ModelDiscoveryService()
    config = ProviderConfig(base_api_url="https://api.test.com/v1", api_key="test-key")

    mock_response = Mock()
    mock_response.json.return_value = {"data": [{"id": "model1"}, {"id": "model2"}]}
    mock_response.raise_for_status.return_value = None

    with patch('requests.get', return_value=mock_response):
        models = service.discover_models(config)
        assert len(models) == 2
        assert config._cached_models == models

def test_discover_models_fallback_to_cache(mocker):
    service = ModelDiscoveryService()
    config = ProviderConfig(base_api_url="https://api.test.com/v1", api_key="test-key")
    config._cached_models = [{"id": "cached-model"}]
    config._cache_timestamp = time.time()

    with patch('requests.get', side_effect=Exception("API error")):
        models = service.discover_models(config)
        assert models == [{"id": "cached-model"}]
```

### Partial Integration Tests

**File**: `tests/test_phase1_integration.py` (new file)

**Test Coverage**:
- Test ProviderConfig ↔ ModelDiscoveryService coordination
- Test model discovery updates ProviderConfig cache correctly
- Test model validation updates ProviderConfig state correctly
- Test backward compatibility with existing configuration patterns

### Regression Tests

**Existing Test Files**:
- Ensure all existing tests in `tests/test_Config.py` still pass
- Ensure all existing tests in `tests/test_OpenAIChatCompletionApi.py` still pass
- Ensure all existing tests in `tests/test_dynamic_models.py` still pass
- Run full test suite to verify no regression

## Conclusion Steps

### Step 1: Run Full Test Suite

After completing all Phase 1 implementation steps, execute the full test suite:
```bash
make test
```

**Success Criteria**: All tests must pass, including:
- All existing 116 tests (no regression)
- New ProviderConfig unit tests
- New ModelDiscoveryService mock tests
- New integration tests

If any tests fail, address the failures before proceeding to status documentation.

### Step 2: Create/Update Status Document

Create or update the status document at `admin/refactor-providers/status/phase_1_execution_status.md` with the following format:

```markdown
# Phase 1 Execution Status

## Overall Status
COMPLETED | IN PROGRESS | NOT STARTED | NEEDS CLARIFICATION

## Step Status

### Pre-Implementation Steps
- [ ] Step 1: Check Current Execution Status - COMPLETED
- [ ] Step 2: Review Master Plan - COMPLETED
- [ ] Step 3: Run Full Test Suite - COMPLETED
- [ ] Step 4: Codebase Review - COMPLETED

### Phase 1 Implementation Steps
- [ ] Step 1: Create ProviderConfig.py - COMPLETED
- [ ] Step 2: Create ModelDiscoveryService.py - COMPLETED
- [ ] Step 3: Update ProviderConfig with Helper Methods - COMPLETED
- [ ] Step 4: Update Types.py - COMPLETED

### Testing Requirements
- [ ] Unit Tests for ProviderConfig - COMPLETED
- [ ] Mock Tests for ModelDiscoveryService - COMPLETED
- [ ] Partial Integration Tests - COMPLETED
- [ ] Regression Tests - COMPLETED

### Conclusion Steps
- [ ] Step 1: Run Full Test Suite - COMPLETED
- [ ] Step 2: Create/Update Status Document - COMPLETED

## Test Results
- Total Tests: 116 + [new test count]
- Passing: [number]
- Failing: [number]
- Test Coverage: [percentage]

## Issues Encountered
- [List any implementation issues or blockers]

## Next Steps
Proceed to Phase 2 implementation
```

**Status Document Requirements**:
- Be extremely concise - do not repeat information from the execution plan
- Reference each step of the phase execution plan and its status
- Use status values: "COMPLETED", "IN PROGRESS", "NOT STARTED", or "NEEDS CLARIFICATION"
- Include test results summary
- Document any issues encountered
- Provide clear next steps

## Critical Success Factors

1. **Backward Compatibility**: Existing YAML configurations must work without changes
2. **Behavior Preservation**: All existing functionality must remain unchanged
3. **Test Coverage**: All new code must have comprehensive test coverage
4. **No Regression**: All existing tests must continue to pass
5. **Error Handling**: Preserve exact error handling patterns from current implementation

If any of these success factors cannot be met, execution must be aborted and the user notified immediately.