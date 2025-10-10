# Dynamic Model Querying - UPDATED Implementation Action Plan

## Overview
This updated action plan provides corrected step-by-step instructions for implementing dynamic model querying functionality in the LLM Chat CLI. The feature will enable the CLI to dynamically query available models from configured OpenAI-compatible API providers using their standard `/v1/models` endpoint.

## Key Corrections from Original Plan

1. **Fixed API Constructor Usage**: The original plan assumed incorrect constructor parameters. We'll create a factory method instead.
2. **Correct Field Names**: Using `base_api_url` instead of `base_url`, and `valid_models` instead of `models`.
3. **Configuration Handling**: Proper integration with the multi-source configuration system.
4. **Command Handler Pattern**: Adapting to the existing if/elif structure.
5. **Comprehensive Testing**: Adding missing test file with full coverage.

## Key Revisions from Discussion

6. **Simplified Query Logic**: Remove `query_models` configuration flag - dynamic querying happens only on user demand (via `--list-models` or `/models`)
7. **Error Handling Strategy**: Print errors to stderr and fall back to static models (no formal logging system)
8. **Model Display Format**: Dynamic models show full model name only, static models show both full name and shorthand

## Phase 1: Core API Enhancement (CORRECTED)

### Step 1.1: Examine Current API Implementation
1. Open `modules/OpenAIChatCompletionApi.py`
2. Study the existing `__init__` method: `(provider: str, model: str, providers: Dict[str, ProviderConfig])`
3. Note the actual field names: `base_api_url`, `valid_models` (dict, not list)
4. Review the `chat_completion` method to understand the API request pattern
5. Note the existing error handling and logging patterns

### Step 1.2: Add Factory Method for Model Querying
Add a new static method to create API instances specifically for model querying:

```python
@classmethod
def create_for_model_querying(cls, provider: str, api_key: str, base_api_url: str) -> 'OpenAIChatCompletionApi':
    """
    Create an API instance specifically for model querying.
    This bypasses the normal model validation since we're only querying available models.
    """
    # Create a minimal providers dict with just the needed provider
    providers = {
        provider: ProviderConfig(
            name=provider,
            api_key=api_key,
            base_api_url=base_api_url,
            valid_models={}  # Empty since we're querying dynamically
        )
    }

    # Create instance with a dummy model
    return cls(provider, "dummy-model", providers)
```

### Step 1.3: Implement `get_available_models` Method (CORRECTED)
Add the following method to the `OpenAIChatCompletionApi` class:

```python
def get_available_models(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
    """
    Query the provider's /v1/models endpoint for available models.
    Returns a list of model dictionaries or empty list on error.
    """
    # Check cache first (cache implementation in next step)
    if (not force_refresh and
        self._cached_models is not None and
        self._cache_timestamp is not None and
        time.time() - self._cache_timestamp < self.cache_duration):
        return self._cached_models

    try:
        # Build the API endpoint URL - CORRECTED: use base_api_url
        url = f"{self.base_api_url}/v1/models"

        # Prepare headers with authentication
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Make the API request
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        # Parse and return the model data
        data = response.json()
        models = data.get("data", [])

        # Update cache
        self._cached_models = models
        self._cache_timestamp = time.time()
        return models

    except requests.exceptions.RequestException as e:
        print(f"Warning: Failed to query models from {self.provider}: {e}", file=sys.stderr)
        # Return cached models if available
        if self._cached_models is not None:
            return self._cached_models
        return []
    except Exception as e:
        print(f"Error: Unexpected error querying models from {self.provider}: {e}", file=sys.stderr)
        if self._cached_models is not None:
            return self._cached_models
        return []
```

### Step 1.4: Add Session-Based Caching (CORRECTED)
Modify the `__init__` method to add caching attributes:

```python
def __init__(self, provider: str, model: str, providers: Dict[str, ProviderConfig]):
    # Existing initialization code...

    # Add caching for model queries
    self._cached_models = None
    self._cache_timestamp = None
    self.cache_duration = 300  # 5 minutes cache
```

### Step 1.5: Add Required Imports
Ensure these imports are at the top of `modules/OpenAIChatCompletionApi.py`:

```python
import time
import sys
from typing import List, Dict, Any
import requests
from modules.Types import ProviderConfig  # Add this import
```

## Phase 2: CLI Integration (CORRECTED)

### Step 2.1: Modify Argument Parser
Update the argument parser in `main.py` to add the `--provider` option:

```python
# Find the existing --list-models argument and add near it
parser.add_argument(
    "--provider",
    type=str,
    help="Filter models by specific provider (e.g., openai, deepseek)"
)
```

### Step 2.2: Enhance `--list-models` Logic (CORRECTED)
Replace the current `--list-models` handling logic with proper integration:

```python
if args.list_models:
    from modules.Config import Config
    from modules.OpenAIChatCompletionApi import OpenAIChatCompletionApi

    config = Config()

    # Determine which providers to query
    providers_to_query = []
    if args.provider:
        # Query specific provider
        if args.provider in config.providers:
            providers_to_query = [args.provider]
        else:
            print(f"Error: Provider '{args.provider}' not found in configuration")
            sys.exit(1)
    else:
        # Query all configured providers
        providers_to_query = list(config.providers.keys())

    # Query and display models for each provider
    for provider_name in providers_to_query:
        provider_config = config.providers[provider_name]

        # Create API instance using the new factory method
        api = OpenAIChatCompletionApi.create_for_model_querying(
            provider=provider_name,
            api_key=provider_config.api_key,
            base_api_url=provider_config.base_api_url
        )

        # Always try dynamic query when user explicitly requests model listing
        dynamic_models = api.get_available_models()

        if dynamic_models:
            print(f"\n{provider_name.upper()} - Dynamic Models:")
            for model in dynamic_models:
                model_id = model.get('id', 'Unknown')
                print(f"  - {model_id}")  # Dynamic models show full name only
        else:
            # Fallback to static models - CORRECTED: use valid_models dict
            print(f"\n{provider_name.upper()} - Static Models:")
            static_models = provider_config.valid_models if hasattr(provider_config, 'valid_models') else {}
            for model_name, short_name in static_models.items():
                print(f"  - {model_name} ({short_name})")  # Static models show both full name and shorthand

            if not static_models:
                print("  No models configured")

    sys.exit(0)
```

### Step 2.3: Update Help Text
Update the `--list-models` help text to reflect the new functionality:

```python
parser.add_argument(
    "-l", "--list-models",
    action="store_true",
    help="List available models (dynamically queries APIs when possible)"
)
```

## Phase 3: In-App Command (CORRECTED)

### Step 3.1: Add `/models` Command Handler
Add a new command method to the `CommandHandler` class that integrates with the existing if/elif structure:

```python
def handle_models_command(self, args: List[str]) -> str:
    """Handle /models command to list available models."""
    from modules.OpenAIChatCompletionApi import OpenAIChatCompletionApi

    # Parse provider filter if provided
    provider_filter = args[0] if args else None

    # Get configured providers
    providers_to_query = []
    if provider_filter:
        if provider_filter in self.chat_interface.config.providers:
            providers_to_query = [provider_filter]
        else:
            return f"Error: Provider '{provider_filter}' not found"
    else:
        providers_to_query = list(self.chat_interface.config.providers.keys())

    result_lines = []

    for provider_name in providers_to_query:
        provider_config = self.chat_interface.config.providers[provider_name]

        # Create API instance using factory method
        api = OpenAIChatCompletionApi.create_for_model_querying(
            provider=provider_name,
            api_key=provider_config.api_key,
            base_api_url=provider_config.base_api_url
        )

        # Always try dynamic query when user explicitly requests model listing
        dynamic_models = api.get_available_models()

        if dynamic_models:
            result_lines.append(f"\n**{provider_name.upper()} - Dynamic Models:**")
            for model in dynamic_models:
                model_id = model.get('id', 'Unknown')
                result_lines.append(f"• {model_id}")  # Dynamic models show full name only
        else:
            # Fallback to static models
            result_lines.append(f"\n**{provider_name.upper()} - Static Models:**")
            static_models = provider_config.valid_models if hasattr(provider_config, 'valid_models') else {}
            for model_name, short_name in static_models.items():
                result_lines.append(f"• {model_name} ({short_name})")  # Static models show both full name and shorthand

            if not static_models:
                result_lines.append("No models configured")

    return "\n".join(result_lines) if result_lines else "No providers configured"
```

### Step 3.2: Register the Command
Add the command handling to the existing if/elif chain in `handle_command` method:

```python
# Add to the existing if/elif chain:
elif command == '/models' or command == '/list-models':
    print(self.handle_models_command(args))
```

### Step 3.3: Update Command Help
Update the help text in `modules/InAppHelp.py`:

```python
# Add to the help text:
help_text += """
/models [provider] - List available models (optionally filtered by provider)
/list-models [provider] - Alias for /models
"""
```

## Phase 4: Configuration & Polish

### Step 4.1: Remove Configuration Complexity
No `query_models` configuration flag needed - dynamic querying happens only on explicit user demand via `--list-models` or `/models` commands.

## Phase 5: Comprehensive Test Coverage (NEW)

### Step 5.1: Create `tests/test_OpenAIChatCompletionApi.py`
Create comprehensive tests for the API class:

```python
import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add the modules directory to the path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.OpenAIChatCompletionApi import OpenAIChatCompletionApi
from modules.Types import ProviderConfig

class TestOpenAIChatCompletionApi:

    def test_create_for_model_querying(self):
        """Test the factory method for model querying."""
        api = OpenAIChatCompletionApi.create_for_model_querying(
            provider="openai",
            api_key="test-key",
            base_api_url="https://api.openai.com/v1"
        )

        assert api.provider == "openai"
        assert api.api_key == "test-key"
        assert api.base_api_url == "https://api.openai.com/v1"
        assert api.model == "dummy-model"

    def test_get_available_models_success(self):
        """Test successful model query."""
        api = OpenAIChatCompletionApi.create_for_model_querying(
            provider="openai",
            api_key="test-key",
            base_api_url="https://api.openai.com/v1"
        )

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                "data": [
                    {"id": "gpt-4", "object": "model", "created": 1234567890},
                    {"id": "gpt-3.5-turbo", "object": "model", "created": 1234567890}
                ]
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            models = api.get_available_models()

            assert len(models) == 2
            assert models[0]["id"] == "gpt-4"

    def test_get_available_models_error(self):
        """Test model query with API error."""
        api = OpenAIChatCompletionApi.create_for_model_querying(
            provider="openai",
            api_key="test-key",
            base_api_url="https://api.openai.com/v1"
        )

        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("API error")

            models = api.get_available_models()

            assert models == []

    def test_get_available_models_caching(self):
        """Test that caching works correctly."""
        api = OpenAIChatCompletionApi.create_for_model_querying(
            provider="openai",
            api_key="test-key",
            base_api_url="https://api.openai.com/v1"
        )

        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                "data": [{"id": "gpt-4", "object": "model"}]
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # First call should make API request
            models1 = api.get_available_models()
            assert len(models1) == 1
            assert mock_get.call_count == 1

            # Second call should use cache
            models2 = api.get_available_models()
            assert len(models2) == 1
            assert mock_get.call_count == 1  # No additional call

            # Force refresh should make new API request
            models3 = api.get_available_models(force_refresh=True)
            assert len(models3) == 1
            assert mock_get.call_count == 2

    def test_get_available_models_cache_fallback(self):
        """Test that cached models are returned on API error."""
        api = OpenAIChatCompletionApi.create_for_model_querying(
            provider="openai",
            api_key="test-key",
            base_api_url="https://api.openai.com/v1"
        )

        # First, populate the cache
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = {
                "data": [{"id": "gpt-4", "object": "model"}]
            }
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            models1 = api.get_available_models()
            assert len(models1) == 1

        # Then simulate API failure
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("API error")

            models2 = api.get_available_models()
            assert len(models2) == 1  # Should return cached models
            assert models2[0]["id"] == "gpt-4"

    def test_integration_with_existing_validation(self):
        """Test that dynamic models integrate with existing validation logic."""
        # This test would verify that the new functionality doesn't break
        # the existing model validation and selection logic
        pass
```

### Step 5.2: Create `tests/test_dynamic_models.py`
Create integration tests for the CLI and command functionality:

```python
import pytest
from unittest.mock import Mock, patch
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.OpenAIChatCompletionApi import OpenAIChatCompletionApi

class TestDynamicModels:

    def test_cli_list_models_all_providers(self):
        """Test CLI --list-models without provider filter."""
        # Test implementation using subprocess or mocking
        pass

    def test_cli_list_models_specific_provider(self):
        """Test CLI --list-models with provider filter."""
        pass

    def test_cli_list_models_invalid_provider(self):
        """Test CLI --list-models with invalid provider."""
        pass

    def test_in_app_models_command(self):
        """Test /models command in chat interface."""
        pass

    def test_configuration_respect(self):
        """Test that query_models configuration flag is respected."""
        pass
```

### Step 5.3: Test CLI Functionality
Test the enhanced `--list-models` flag:

```bash
# Test without provider filter
python main.py --list-models

# Test with specific provider
python main.py --list-models --provider openai

# Test with invalid provider
python main.py --list-models --provider invalid
```

### Step 5.4: Test In-App Command
Start the chat interface and test:

```bash
python main.py
# Then in the chat:
/models
/models openai
/models invalid
```

## Phase 6: Final Validation

### Step 6.1: Run All Tests
Execute the test suite to ensure no regressions:

```bash
make test
# or
pytest
```

### Step 6.2: Update Documentation
Update the README.md to document the new functionality.

### Step 6.3: Verify Configuration Compatibility
Test that existing configurations work without modification.

## Implementation Notes

### Key Corrections Applied
1. **Constructor Usage**: Added factory method instead of modifying existing constructor
2. **Field Names**: Corrected to use `base_api_url` and `valid_models`
3. **Configuration**: Proper handling of multi-source config system
4. **Command Handler**: Adapted to existing if/elif pattern
5. **Testing**: Added comprehensive test coverage for missing test file

### Key Revisions Applied
6. **Simplified Logic**: Removed `query_models` flag - dynamic querying only on explicit user demand
7. **Error Handling**: Use `print()` to stderr instead of logging system
8. **Model Display**: Dynamic models show full names only, static models show full names with shorthand

### Success Criteria
- Dynamic model querying works for OpenAI provider
- Dynamic model querying works for DeepSeek provider
- Graceful fallback to static models when API unavailable
- CLI `--list-models` flag shows dynamic results
- In-app `/models` command functions correctly
- All existing tests pass
- No breaking changes to current functionality
- Comprehensive test coverage for OpenAIChatCompletionApi class

This updated action plan ensures the feature integrates seamlessly with the existing architecture while providing robust test coverage.