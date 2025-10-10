# Phase 1 Execution Plan: Enhanced ProviderConfig and ModelDiscoveryService

## Introduction

This phase implements the foundational components for the provider refactoring: the enhanced ProviderConfig class and the new ModelDiscoveryService. These components establish the core data model and API operations layer that will be used throughout the refactored architecture.

**Critical Note**: If any step in this execution plan cannot be completed due to unexpected codebase structure, missing dependencies, or test failures, the execution should be aborted immediately. The status document should be updated to reflect the issue, and the user must be notified before proceeding.

## Phase Status Assessment

**Current Status**: No previous phase status documents found. This is the initial phase execution.

## Step 1: Read Master Plan

- Review the complete master plan at `admin/refactor-providers/master_plan.md`
- Focus on Phase 1 requirements (lines 205-354)
- Understand the Core Guiding Principles for preservation of existing behavior
- Note backward compatibility requirements

## Step 2: Verify Test Suite Baseline

- Run `make test` to ensure all 116 tests pass
- Confirm baseline functionality is working before starting refactoring
- If tests fail, stop execution and notify user

## Step 3: Codebase Analysis

Review the current codebase structure to understand:

- Current ProviderConfig class location in `modules/Types.py`
- Current OpenAIChatCompletionApi model discovery methods
- Existing imports and dependencies
- Current configuration loading patterns

## Step 4: Implementation Details

### 4.1 Create ProviderConfig.py

**File**: `modules/ProviderConfig.py`

**Imports**:
```python
from pydantic import BaseModel, Field, PrivateAttr
from typing import List, Any, Dict, Optional
```

**Enhanced ProviderConfig Class**:
```python
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

**Field Categorization**:
- **Persisted fields** (saved to YAML): `name`, `base_api_url`, `api_key`, `valid_models`, `invalid_models`
- **Runtime-only fields** (not saved to YAML): `_cached_models`, `_cache_timestamp`, `cache_duration`
- **Backward compatibility**: Existing YAML files without `invalid_models` will work unchanged - the field defaults to empty list

### 4.2 Create ModelDiscoveryService.py

**File**: `modules/ModelDiscoveryService.py`

**Imports**:
```python
import requests
import time
from typing import List, Any, Dict, Optional
from modules.ProviderConfig import ProviderConfig
```

**ModelDiscoveryService Class**:
```python
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
- Preserve exact error handling patterns from current OpenAIChatCompletionApi:273-283
- Include comprehensive error handling and fallback to cached models
- Maintain specific RequestException vs general Exception handling

### 4.3 Update ProviderConfig with Helper Methods

Add the following methods to ProviderConfig class:

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
    First search valid_models by exact match on long name or short name.
    If not found, search by substring match on long name or short name.
    Return the first match's long name, or None if none found.
    """
    # Exact match on long name
    if name in self.valid_models:
        return name

    # Exact match on short name
    for long_name, short_name in self.valid_models.items():
        if name == short_name:
            return long_name

    # Substring match on long name
    for long_name in self.valid_models.keys():
        if name in long_name:
            return long_name

    # Substring match on short name
    for long_name, short_name in self.valid_models.items():
        if name in short_name:
            return long_name

    return None

def merge_valid_models(self, models: List[str]) -> None:
    """
    Merge models with existing valid models.
    For new models without existing mappings, use full model ID as short name initially.
    """
    for model in models:
        if model not in self.valid_models:
            self.valid_models[model] = model  # Use full model ID as short name initially
```

### 4.4 Update Types.py

- Remove ProviderConfig class definition from `modules/Types.py`
- Keep PROVIDER_DATA constant for pre-populated model data
- Keep ConfigModel and other global types
- Update imports to reference new ProviderConfig module:
  ```python
  from modules.ProviderConfig import ProviderConfig
  ```

## Step 5: Testing Requirements

### Unit Tests for ProviderConfig

**File**: `tests/test_ProviderConfig.py`

Test methods:
- `test_get_valid_models()` - Verify returns correct list of valid models
- `test_get_invalid_models()` - Verify returns correct list of invalid models
- `test_find_model_exact_match()` - Test exact matching on long and short names
- `test_find_model_substring_match()` - Test substring matching
- `test_find_model_not_found()` - Test None return for non-existent models
- `test_merge_valid_models()` - Test merging new models with existing mappings
- `test_backward_compatibility()` - Test ProviderConfig works without invalid_models field

### Mock Tests for ModelDiscoveryService

**File**: `tests/test_ModelDiscoveryService.py`

Test methods:
- `test_discover_models_success()` - Test successful model discovery with mocked HTTP responses
- `test_discover_models_cache_hit()` - Test cache behavior when models are cached
- `test_discover_models_cache_miss()` - Test cache bypass with force_refresh
- `test_discover_models_error_fallback()` - Test error handling and fallback to cached models
- `test_validate_model_success()` - Test successful model validation with mocked responses
- `test_validate_model_failure()` - Test model validation failure
- `test_validate_api_key_valid()` - Test API key validation with valid key
- `test_validate_api_key_invalid()` - Test API key validation with invalid/empty key

### Partial Integration Tests

**File**: `tests/test_ProviderConfig_ModelDiscoveryService_integration.py`

Test methods:
- `test_provider_config_model_discovery_coordination()` - Test ProviderConfig ↔ ModelDiscoveryService interaction
- `test_caching_integration()` - Test caching behavior across both components
- `test_error_handling_integration()` - Test error handling coordination

### Regression Tests

- Run existing test suite to ensure no functionality regression
- Verify all 116 existing tests still pass
- Focus on tests in `test_Config.py`, `test_OpenAIChatCompletionApi.py`, and `test_dynamic_models.py`

## Step 6: Conclusion Steps

### 6.1 Run Full Test Suite

- Execute `make test` to verify all tests pass
- Address any test failures before proceeding
- Ensure no regression in existing functionality

### 6.2 Create Phase Status Document

**File**: `admin/refactor-providers/status/phase_1_execution_status.md`

Document the completion status of each step:
- Step 1: COMPLETED
- Step 2: COMPLETED
- Step 3: COMPLETED
- Step 4.1: COMPLETED/IN PROGRESS/NOT STARTED
- Step 4.2: COMPLETED/IN PROGRESS/NOT STARTED
- Step 4.3: COMPLETED/IN PROGRESS/NOT STARTED
- Step 4.4: COMPLETED/IN PROGRESS/NOT STARTED
- Step 5: COMPLETED/IN PROGRESS/NOT STARTED
- Test Suite Results: PASSED/FAILED

**Status Document Content**:
- Reference each step of this execution plan
- Capture current state of codebase with respect to phase execution
- Document test suite results
- Note any issues or clarifications needed

## Implementation Guidelines

### Preservation of Existing Behavior

- Move functionality verbatim when transferring between files/classes
- Maintain all current error handling patterns, logging, and fallback mechanisms
- Preserve API compatibility and method signatures
- Ensure existing tests continue to pass without modification

### Backward Compatibility

- Existing configuration files must work without changes
- YAML files without `invalid_models` field should continue working
- Field-level backward compatibility: `invalid_models` is optional with default empty list
- YAML loading logic should handle missing `invalid_models` field gracefully

### Code Style

- Follow existing code conventions and patterns
- Use descriptive variable names for readability
- Maintain existing import structure and organization
- Follow the modular architecture patterns

### Testing Strategy

- Write comprehensive unit tests for all new methods
- Use mocking for HTTP requests in ModelDiscoveryService tests
- Test edge cases and error conditions
- Ensure backward compatibility through regression testing