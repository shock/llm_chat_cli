# Phase 3 Execution Plan: ProviderManager Implementation

## Introduction

This phase introduces the **ProviderManager** class, which serves as the primary interface for all provider-related operations throughout the codebase. This is a critical architectural change that replaces `Dict[str, ProviderConfig]` globally, including in ConfigModel.

**CRITICAL**: If any step cannot be completed successfully, **ABORT EXECUTION IMMEDIATELY**, update the status document, and notify the user. Do not proceed with partial implementation.

---

## Pre-Implementation Steps

### Step 1: Read Master Plan
Read the complete master plan document at `admin/refactor-providers/master_plan.md` to understand the full context and architectural vision.

### Step 2: Check Phase Status
Scan the `/admin/refactor-providers/status` directory to determine the current status of plan execution:
- If a status document for Phase 3 already exists, read it carefully
- Use the status document to determine the current state and how to proceed with remaining steps
- Identify which steps are completed, in progress, or not started

### Step 3: Run Full Test Suite
Run the full test suite using `make test` or `pytest`:
- **ALL tests must pass** before proceeding
- If any tests fail, **STOP** and notify the user
- Do not proceed until the test suite is clean

### Step 4: Review Current Codebase
Review and understand all relevant code files and modules as they currently exist:
- `modules/ProviderConfig.py` - Enhanced ProviderConfig class (from Phase 1)
- `modules/ModelDiscoveryService.py` - Model discovery service (from Phase 1)
- `modules/OpenAIChatCompletionApi.py` - Cleaned chat API (from Phase 2)
- `modules/Types.py` - Global types and ConfigModel
- `modules/Config.py` - Configuration loading logic
- `main.py` - Entry point and CLI
- `modules/CommandHandler.py` - Command processing

---

## Implementation Steps

### Overview
Phase 3 creates the ProviderManager class and integrates it into ConfigModel, replacing all `Dict[str, ProviderConfig]` usage throughout the codebase.

### Step 5: Create ProviderManager.py

**File**: `modules/ProviderManager.py`

**Required Imports**:
```python
from modules.ProviderConfig import ProviderConfig
from modules.ModelDiscoveryService import ModelDiscoveryService
from typing import List, Dict, Optional, Tuple
```

**Implementation Requirements**:

#### 5.1 Class Structure
```python
class ProviderManager:
    def __init__(self, providers: Dict[str, ProviderConfig]):
        self.providers = providers
        self.discovery_service = ModelDiscoveryService()
```

**Key Architectural Points**:
- ProviderManager will replace `Dict[str, ProviderConfig]` throughout the codebase
- Configuration loading flow: Config.py loads data → creates ProviderManager → passes to ConfigModel
- **NO circular dependency**: ProviderManager is instantiated BEFORE ConfigModel using raw provider dict data
- ProviderManager instances will be initialized with fully-merged configuration data from Config.py

#### 5.2 Dict-like Interface Methods
Implement dict-like access methods for backward compatibility:

```python
def get(self, provider_name: str) -> Optional[ProviderConfig]:
    """Get provider config by name, returns None if not found."""
    return self.providers.get(provider_name)

def __getitem__(self, provider_name: str) -> ProviderConfig:
    """Dict-style access to provider configs."""
    return self.providers[provider_name]

def __contains__(self, provider_name: str) -> bool:
    """Check if provider exists."""
    return provider_name in self.providers

def keys(self) -> List[str]:
    """Get all provider names."""
    return list(self.providers.keys())

def values(self) -> List[ProviderConfig]:
    """Get all provider configs."""
    return list(self.providers.values())

def items(self) -> List[Tuple[str, ProviderConfig]]:
    """Get all (name, config) pairs."""
    return list(self.providers.items())
```

#### 5.3 Provider Management Methods

```python
def get_provider_config(self, provider_name: str) -> Optional[ProviderConfig]:
    """Get specific provider config by name."""
    return self.providers.get(provider_name)

def get_all_provider_names(self) -> List[str]:
    """List all available provider names."""
    return list(self.providers.keys())
```

#### 5.4 Cross-Provider Model Resolution Methods

**CRITICAL**: These methods must be moved from `OpenAIChatCompletionApi` with EXACTLY the same logic and behavior. Preserve all current validation patterns, error messages, and edge case handling.

**From OpenAIChatCompletionApi - Move these methods with preserved logic**:

```python
def merged_models(self) -> List[Tuple[str, Tuple[str, str]]]:
    """
    Combine models from all providers.
    Returns: List of (provider_name, (long_model_name, short_model_name))

    PRESERVE EXACT LOGIC from OpenAIChatCompletionApi.merged_models()
    """
    merged_models = []
    for provider_name, provider_config in self.providers.items():
        if provider_config.valid_models is None or not isinstance(provider_config.valid_models, dict):
            continue
        for long_name, short_name in provider_config.valid_models.items():
            merged_models.append((provider_name, (long_name, short_name)))
    return merged_models

def valid_scoped_models(self) -> List[str]:
    """
    Generate formatted model strings for display.
    Returns: List of formatted strings like "provider/long_name (short_name)"

    PRESERVE EXACT LOGIC from OpenAIChatCompletionApi.valid_scoped_models()
    """
    return [f"{provider}/{long_name} ({short_name})" for provider, (long_name, short_name) in self.merged_models()]

def get_api_for_model_string(self, model_string: str) -> Tuple[ProviderConfig, str]:
    """
    Resolve model string to provider and model.
    Returns: (ProviderConfig, model_name)

    PRESERVE EXACT LOGIC from OpenAIChatCompletionApi.get_api_for_model_string()
    Including:
    - Provider-prefixed model strings ("openai/gpt-4o")
    - Unprefixed model strings that search across all providers
    - Both long and short model name matching
    - Same error messages and validation patterns
    """
    provider_prefix, model = split_first_slash(model_string)
    provider_prefix = provider_prefix.lower()

    # Handle provider-prefixed model strings
    if provider_prefix and provider_prefix in self.providers:
        provider_config = self.providers[provider_prefix]
        # Validate the model exists in this provider
        if model in provider_config.valid_models or model in provider_config.valid_models.values():
            return provider_config, model
        raise ValueError(f"Invalid model for provider {provider_prefix}: {model}")

    # Handle unprefixed model strings - search across all providers
    for provider_name, (long_name, short_name) in self.merged_models():
        if model == long_name or model == short_name:
            return self.providers[provider_name], long_name

    raise ValueError(f"Invalid model: {model}")

def validate_model(self, model_string: str) -> str:
    """
    Validate model string and return resolved model name.
    Returns: Validated long model name

    PRESERVE EXACT LOGIC from OpenAIChatCompletionApi.validate_model()
    """
    provider_config, model = self.get_api_for_model_string(model_string)
    return model
```

**Utility Function** (move from OpenAIChatCompletionApi):
```python
def split_first_slash(text: str) -> Tuple[str, str]:
    """
    Utility function for parsing provider/model strings.

    PRESERVE EXACT LOGIC from OpenAIChatCompletionApi.split_first_slash()
    """
    # Move implementation verbatim from OpenAIChatCompletionApi
```

#### 5.5 Model Discovery and Validation Methods

```python
def discover_models(self, force_refresh: bool = False, persist_on_success: bool = True, provider: Optional[str] = None) -> bool:
    """
    Discover and validate models for providers.

    Args:
        force_refresh: Whether to bypass cache and force refresh
        persist_on_success: Whether to persist configs to YAML if successful
        provider: Optional provider name to limit discovery to specific provider

    Returns:
        True if successful for all targeted providers, False otherwise
    """
    success = True
    targeted_providers = {}

    # Filter providers if specified
    if provider:
        if provider in self.providers:
            targeted_providers[provider] = self.providers[provider]
        else:
            print(f"Provider '{provider}' not found")
            return False
    else:
        targeted_providers = self.providers

    for provider_name, provider_config in targeted_providers.items():
        if not self.discovery_service.validate_api_key(provider_config):
            print(f"Skipping {provider_name}: No valid API key configured")
            continue

        try:
            # Discover models
            models = self.discovery_service.discover_models(provider_config, force_refresh)
            model_names = [model["id"] for model in models]

            # Validate models
            valid_models = []
            invalid_models = []

            for model_name in model_names:
                if model_name in provider_config.invalid_models:
                    invalid_models.append(model_name)
                elif self.discovery_service.validate_model(provider_config, model_name):
                    valid_models.append(model_name)
                else:
                    invalid_models.append(model_name)

            # Update provider config
            provider_config.invalid_models = invalid_models
            provider_config.merge_valid_models(valid_models)

            print(f"Successfully discovered {len(valid_models)} valid and {len(invalid_models)} invalid models for {provider_name}")

        except Exception as e:
            print(f"Error discovering models for {provider_name}: {e}")
            success = False

    # Persist only if completely successful and requested
    if success and persist_on_success:
        self.persist_provider_configs()
        print("Provider configurations persisted to YAML")

    return success

def get_available_models(self, filter_by_provider: Optional[str] = None) -> List[str]:
    """
    Get available models from all providers or a specific provider.
    """
    models = []
    for provider_name, provider_config in self.providers.items():
        if filter_by_provider and provider_name != filter_by_provider:
            continue
        models.extend(provider_config.get_valid_models())
    return models
```

#### 5.6 Utility Methods

```python
@staticmethod
def get_short_name(long_name: str) -> str:
    """
    Generate short name for model.
    For now, just returns the long name.
    Future enhancement: Implement pattern-based short-name generation strategy.
    """
    return long_name

def find_model(self, name: str) -> List[Tuple[ProviderConfig, str]]:
    """
    Find model by name across all configured providers.

    Returns: List of (provider_config, model_name) tuples
    """
    results = []
    for provider_name, provider_config in self.providers.items():
        model_name = provider_config.find_model(name)
        if model_name:
            results.append((provider_config, model_name))
    return results
```

#### 5.7 YAML Persistence Implementation

**CRITICAL BACKWARD COMPATIBILITY REQUIREMENTS**:
- Existing YAML files without `invalid_models` will continue working unchanged
- The `invalid_models` field is optional with default empty list
- Only persisted fields are saved to YAML: `name`, `base_api_url`, `api_key`, `valid_models`, `invalid_models`
- Runtime-only fields are excluded: `_cached_models`, `_cache_timestamp`, `cache_duration`

**YAML Format Specification**:
```yaml
providers:
  openai:
    api_key: sk-...
    base_api_url: https://api.openai.com/v1
    name: OpenAI
    valid_models:
      gpt-4o-2024-08-06: 4o
      gpt-4o-mini-2024-07-18: 4o-mini
    invalid_models:
      - gpt-3.5-turbo-instruct
      - text-davinci-003
```

**Implementation**:
```python
def persist_provider_configs(self) -> None:
    """
    Persist provider configurations to YAML file in data directory.

    File location: data/openaicompat-providers.yaml

    Only persisted fields are saved:
    - name, base_api_url, api_key, valid_models, invalid_models

    Runtime-only fields are excluded:
    - _cached_models, _cache_timestamp, cache_duration
    """
    # Implementation must:
    # 1. Get data directory path from config
    # 2. Construct YAML file path: data/openaicompat-providers.yaml
    # 3. Serialize providers dict to YAML with only persisted fields
    # 4. Write to file with proper error handling
    # 5. Preserve backward compatibility (invalid_models is optional)
```

### Step 6: Update Types.py

**File**: `modules/Types.py`

**Changes Required**:
1. Add import: `from modules.ProviderManager import ProviderManager`
2. Update ConfigModel field:
   - **OLD**: `providers: Dict[str, ProviderConfig]`
   - **NEW**: `providers: ProviderManager`

**CRITICAL**: This is a global change that affects all code accessing `config.config.providers`. All such code must now use ProviderManager methods instead of direct dict access.

### Step 7: Update Config.py to Support ProviderManager

**File**: `modules/Config.py`

**Changes Required in `load_config()` method**:

After all configuration merging is complete (after line 97), convert the providers dict to ProviderManager BEFORE creating ConfigModel:

```python
# After all merging is complete (after line 97), convert providers dict to ProviderManager
if 'providers' in config_data:
    provider_manager = ProviderManager(config_data['providers'])
    config_data['providers'] = provider_manager

return ConfigModel(**config_data)
```

**Key Points**:
- ProviderManager is instantiated BEFORE ConfigModel
- No circular dependency: uses raw provider dict data
- Preserves existing configuration loading sequence
- All configuration merging logic remains unchanged

### Step 8: Global Codebase Updates

**CRITICAL**: Update ALL code that accesses `config.config.providers` to use ProviderManager methods instead of direct dict access.

**Files to Review and Update**:
- `main.py` - Update provider access patterns
- `modules/CommandHandler.py` - Update provider access patterns
- `modules/ChatInterface.py` - Update provider access patterns if needed
- Any other files that access `config.config.providers`

**Migration Pattern**:
```python
# OLD: Direct dict access
provider_config = config.config.providers[provider_name]
for provider_name in config.config.providers:
    # ...

# NEW: ProviderManager methods
provider_config = config.config.providers.get_provider_config(provider_name)
for provider_name in config.config.providers.keys():
    # ...
```

**Alternative Pattern** (if backward compatibility is needed):
ProviderManager implements dict-like interface, so some existing code may continue working:
```python
# This still works due to __getitem__
provider_config = config.config.providers[provider_name]

# This still works due to __contains__
if provider_name in config.config.providers:
    # ...
```

**Recommendation**: Prefer explicit ProviderManager methods for clarity, but dict-like interface provides backward compatibility during transition.

---

## Post-Implementation Steps

### Step 9: Run Full Test Suite

Run the complete test suite using `make test` or `pytest`:
- ALL tests must pass
- If any tests fail, investigate and fix before proceeding
- Document any test failures in status document

### Step 10: Create/Update Status Document

Create or update `admin/refactor-providers/status/phase_3_execution_status.md` with the current phase execution status.

**Status Document Format**:

```markdown
# Phase 3 Execution Status

## Overall Status
[COMPLETED | IN PROGRESS | NOT STARTED | NEEDS CLARIFICATION]

## Test Suite Results
- Total tests: [number]
- Passed: [number]
- Failed: [number]
- Status: [PASS | FAIL]

## Step-by-Step Status

### Pre-Implementation Steps
- **Step 1**: Read Master Plan - [COMPLETED | IN PROGRESS | NOT STARTED]
- **Step 2**: Check Phase Status - [COMPLETED | IN PROGRESS | NOT STARTED]
- **Step 3**: Run Full Test Suite - [COMPLETED | IN PROGRESS | NOT STARTED]
- **Step 4**: Review Current Codebase - [COMPLETED | IN PROGRESS | NOT STARTED]

### Implementation Steps
- **Step 5**: Create ProviderManager.py - [COMPLETED | IN PROGRESS | NOT STARTED]
  - Substep 5.1: Class Structure - [status]
  - Substep 5.2: Dict-like Interface - [status]
  - Substep 5.3: Provider Management - [status]
  - Substep 5.4: Cross-Provider Resolution - [status]
  - Substep 5.5: Model Discovery - [status]
  - Substep 5.6: Utility Methods - [status]
  - Substep 5.7: YAML Persistence - [status]
- **Step 6**: Update Types.py - [COMPLETED | IN PROGRESS | NOT STARTED]
- **Step 7**: Update Config.py - [COMPLETED | IN PROGRESS | NOT STARTED]
- **Step 8**: Global Codebase Updates - [COMPLETED | IN PROGRESS | NOT STARTED]

### Post-Implementation Steps
- **Step 9**: Run Full Test Suite - [COMPLETED | IN PROGRESS | NOT STARTED]
- **Step 10**: Create/Update Status Document - [COMPLETED | IN PROGRESS | NOT STARTED]

## Current State of Codebase

### Files Modified
- `modules/ProviderManager.py` - [CREATED | NOT CREATED]
- `modules/Types.py` - [MODIFIED | NOT MODIFIED]
- `modules/Config.py` - [MODIFIED | NOT MODIFIED]
- `main.py` - [MODIFIED | NOT MODIFIED]
- `modules/CommandHandler.py` - [MODIFIED | NOT MODIFIED]
- [Other modified files]

### Outstanding Issues
[List any issues, blockers, or concerns]

### Notes
[Any additional notes or observations]

## Next Step
[Single overarching next step from executor's perspective]
```

---

## Testing Requirements

### Unit Tests for ProviderManager

**File**: `tests/test_ProviderManager.py`

**Required Test Cases**:

1. **Dict-like Interface Tests**
   - Test `get()` with valid and invalid provider names
   - Test `__getitem__()` access
   - Test `__contains__()` membership testing
   - Test `keys()`, `values()`, `items()` iteration

2. **Provider Management Tests**
   - Test `get_provider_config()` with valid and invalid names
   - Test `get_all_provider_names()`

3. **Cross-Provider Resolution Tests**
   - Test `merged_models()` aggregation across providers
   - Test `valid_scoped_models()` formatting
   - Test `get_api_for_model_string()` with:
     - Provider-prefixed model strings ("openai/gpt-4o")
     - Unprefixed model strings
     - Both long and short model names
     - Invalid model strings (expect ValueError)
   - Test `validate_model()` validation logic

4. **Model Discovery Tests** (with mocked ModelDiscoveryService)
   - Test `discover_models()` with all providers
   - Test `discover_models()` with specific provider filter
   - Test `discover_models()` with force_refresh
   - Test `discover_models()` error handling
   - Test `get_available_models()` with and without provider filter

5. **Utility Method Tests**
   - Test `get_short_name()` static method
   - Test `find_model()` across providers

6. **YAML Persistence Tests**
   - Test `persist_provider_configs()` creates valid YAML
   - Test backward compatibility (YAML without invalid_models)
   - Test runtime-only fields are excluded from YAML
   - Test YAML file path construction

### Integration Tests

**File**: `tests/test_integration_phase3.py`

**Required Test Cases**:

1. **ProviderManager ↔ ProviderConfig ↔ ModelDiscoveryService Integration**
   - Test full model discovery workflow
   - Test cross-provider model resolution
   - Test YAML persistence after discovery

2. **ConfigModel Integration**
   - Test Config.py creates ProviderManager correctly
   - Test ConfigModel accepts ProviderManager
   - Test configuration loading sequence preservation

3. **Global Access Pattern Tests**
   - Test `config.config.providers` is ProviderManager instance
   - Test dict-like access works throughout codebase
   - Test ProviderManager methods work as expected

### Regression Tests

**Ensure ALL existing tests still pass**:
- Run full test suite with `make test` or `pytest`
- No existing functionality should be broken
- All previous phases' tests must continue passing

---

## Error Handling Requirements

**PRESERVE ALL EXISTING ERROR HANDLING PATTERNS**:
- Specific exception types from OpenAIChatCompletionApi methods
- Error messages must remain identical
- Fallback mechanisms must be preserved
- Logging patterns must be maintained

**New Error Handling**:
- Provider not found errors in `discover_models()`
- API key validation failures
- YAML persistence errors
- Invalid model string errors (preserve existing ValueError patterns)

---

## Backward Compatibility Guarantees

1. **Configuration Files**: Existing YAML files without `invalid_models` will continue working unchanged
2. **Field Compatibility**: The `invalid_models` field is optional with default empty list
3. **YAML Loading**: Current YAML loading logic handles missing `invalid_models` field gracefully
4. **Serialization**: Only persisted fields are saved to YAML, maintaining existing format
5. **API Usage**: Dict-like interface provides backward compatibility for existing code patterns
6. **Model Resolution**: Validation and resolution behavior stays consistent
7. **No Breaking Changes**: All current interfaces remain functional

---

## Critical Implementation Guidelines

### Preservation of Existing Behavior

**When moving functionality from OpenAIChatCompletionApi to ProviderManager**:
- Implementation should be preserved **verbatim**
- All error handling patterns must be maintained
- Logging statements and output formatting unchanged
- Caching behavior and timing preserved
- Validation logic and edge case handling identical
- API response parsing and error recovery unchanged

### Cross-Provider Method Migration

**Methods to move from OpenAIChatCompletionApi**:
- `merged_models()` - Aggregate models from all providers
- `valid_scoped_models()` - Generate formatted model strings
- `get_api_for_model_string()` - Resolve model strings to provider/model pairs
- `validate_model()` - Cross-provider model validation
- `split_first_slash()` - Utility function for parsing provider/model strings

**CRITICAL**: Move these methods with EXACTLY the same logic, signatures, and behaviors.

### Configuration Loading Sequence

**MUST PRESERVE**: The existing configuration loading sequence in Config.py:
1. config.toml providers - loaded first and saved as providers_overrides
2. PROVIDER_DATA constant - provides baseline provider configuration
3. YAML provider configuration - always loaded and merged with existing providers
4. providers_overrides - final merge, taking precedence
5. Environment variable API keys - final API key overrides

**ProviderManager initialization** occurs AFTER all merging is complete, before ConfigModel creation.

---

## Key Architectural Points

1. **Primary Interface**: ProviderManager is now the primary interface for all provider-related operations
2. **Global Replacement**: Replaces `Dict[str, ProviderConfig]` throughout codebase, including ConfigModel
3. **No Circular Dependency**: ProviderManager is instantiated BEFORE ConfigModel using raw provider dict
4. **Configuration Flow**: Config.py → ProviderManager → ConfigModel
5. **Dict-like Interface**: Backward compatibility through dict-like access methods
6. **Cross-Provider Logic**: All cross-provider methods moved from OpenAIChatCompletionApi
7. **Model Discovery Orchestration**: ProviderManager coordinates all model discovery operations
8. **YAML Persistence**: ProviderManager handles persisting configurations to YAML

---

## Summary

Phase 3 is a critical architectural phase that:
- Creates the ProviderManager class as the unified provider management interface
- Replaces `Dict[str, ProviderConfig]` globally throughout the codebase
- Integrates ProviderManager into ConfigModel and Config.py
- Migrates all cross-provider logic from OpenAIChatCompletionApi
- Implements YAML persistence for provider configurations
- Maintains full backward compatibility with existing configurations
- Preserves all existing behavior and error handling patterns

Upon completion, ProviderManager will be the single point of access for all provider-related operations, providing a clean, testable, and extensible interface for provider management.
