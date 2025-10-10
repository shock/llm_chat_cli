# Dynamic Model Querying - Implementation Action Plan

## Overview
This action plan provides step-by-step instructions for implementing dynamic model querying functionality in the LLM Chat CLI. The feature will enable the CLI to dynamically query available models from configured OpenAI-compatible API providers using their standard `/v1/models` endpoint.

## Phase 1: Core API Enhancement

### Step 1.1: Examine Current API Implementation
1. Open `modules/OpenAIChatCompletionApi.py`
2. Study the existing `__init__` method and understand how providers are configured
3. Review the `chat_completion` method to understand the API request pattern
4. Note the existing error handling and logging patterns

### Step 1.2: Implement `get_available_models` Method
Add the following method to the `OpenAIChatCompletionApi` class in `modules/OpenAIChatCompletionApi.py`:

```python
def get_available_models(self) -> List[Dict[str, Any]]:
    """
    Query the provider's /v1/models endpoint for available models.
    Returns a list of model dictionaries or empty list on error.
    """
    try:
        # Build the API endpoint URL
        url = f"{self.base_url}/v1/models"

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
        return data.get("data", [])

    except requests.exceptions.RequestException as e:
        logger.warning(f"Failed to query models from {self.provider}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error querying models from {self.provider}: {e}")
        return []
```

### Step 1.3: Add Session-Based Caching
Modify the `__init__` method to add caching:

```python
def __init__(self, provider: str, api_key: str, base_url: str, **kwargs):
    # Existing initialization code...

    # Add caching for model queries
    self._cached_models = None
    self._cache_timestamp = None
    self.cache_duration = 300  # 5 minutes cache
```

Update the `get_available_models` method to use caching:

```python
def get_available_models(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
    """Query models with caching support."""
    # Check cache first
    if (not force_refresh and
        self._cached_models is not None and
        self._cache_timestamp is not None and
        time.time() - self._cache_timestamp < self.cache_duration):
        return self._cached_models

    try:
        # Existing API call code...
        models = # ... API call logic

        # Update cache
        self._cached_models = models
        self._cache_timestamp = time.time()
        return models

    except Exception as e:
        # Return cached models if available, otherwise empty list
        if self._cached_models is not None:
            logger.warning(f"Using cached models due to error: {e}")
            return self._cached_models
        return []
```

### Step 1.4: Add Required Imports
Ensure these imports are at the top of `modules/OpenAIChatCompletionApi.py`:

```python
import time
from typing import List, Dict, Any
import requests
```

## Phase 2: CLI Integration

### Step 2.1: Examine Current CLI Implementation
1. Open `main.py`
2. Find the `--list-models` flag handling in the argument parser
3. Study how the current static model listing works
4. Understand the provider configuration system

### Step 2.2: Modify Argument Parser
Update the argument parser in `main.py` to add the `--provider` option:

```python
# Find the existing --list-models argument and add near it
parser.add_argument(
    "--provider",
    type=str,
    help="Filter models by specific provider (e.g., openai, deepseek)"
)
```

### Step 2.3: Enhance `--list-models` Logic
Replace the current `--list-models` handling logic:

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

        # Create API instance
        api = OpenAIChatCompletionApi(
            provider=provider_name,
            api_key=provider_config.api_key,
            base_url=provider_config.base_url
        )

        # Try dynamic query first
        dynamic_models = api.get_available_models()

        if dynamic_models:
            print(f"\n{provider_name.upper()} - Dynamic Models:")
            for model in dynamic_models:
                model_id = model.get('id', 'Unknown')
                print(f"  - {model_id}")
        else:
            # Fallback to static models
            print(f"\n{provider_name.upper()} - Static Models:")
            static_models = provider_config.models if hasattr(provider_config, 'models') else []
            for model in static_models:
                print(f"  - {model}")

            if not static_models:
                print("  No models configured")

    sys.exit(0)
```

### Step 2.4: Update Help Text
Update the `--list-models` help text to reflect the new functionality:

```python
parser.add_argument(
    "--list-models",
    action="store_true",
    help="List available models (dynamically queries APIs when possible)"
)
```

## Phase 3: In-App Command

### Step 3.1: Examine Command Handler
1. Open `modules/CommandHandler.py`
2. Study how existing commands like `/help`, `/clear`, and `/model` are implemented
3. Understand the command registration pattern

### Step 3.2: Add `/models` Command Handler
Add a new command method to the `CommandHandler` class:

```python
def handle_models_command(self, args: List[str]) -> str:
    """Handle /models command to list available models."""
    from modules.OpenAIChatCompletionApi import OpenAIChatCompletionApi

    # Parse provider filter if provided
    provider_filter = args[0] if args else None

    # Get configured providers
    providers_to_query = []
    if provider_filter:
        if provider_filter in self.config.providers:
            providers_to_query = [provider_filter]
        else:
            return f"Error: Provider '{provider_filter}' not found"
    else:
        providers_to_query = list(self.config.providers.keys())

    result_lines = []

    for provider_name in providers_to_query:
        provider_config = self.config.providers[provider_name]

        # Create API instance
        api = OpenAIChatCompletionApi(
            provider=provider_name,
            api_key=provider_config.api_key,
            base_url=provider_config.base_url
        )

        # Try dynamic query
        dynamic_models = api.get_available_models()

        if dynamic_models:
            result_lines.append(f"\n**{provider_name.upper()} - Dynamic Models:**")
            for model in dynamic_models:
                model_id = model.get('id', 'Unknown')
                result_lines.append(f"• {model_id}")
        else:
            # Fallback to static models
            result_lines.append(f"\n**{provider_name.upper()} - Static Models:**")
            static_models = provider_config.models if hasattr(provider_config, 'models') else []
            for model in static_models:
                result_lines.append(f"• {model}")

            if not static_models:
                result_lines.append("No models configured")

    return "\n".join(result_lines) if result_lines else "No providers configured"
```

### Step 3.3: Register the Command
Add the command registration in the `__init__` method of `CommandHandler`:

```python
# Find the command registration section and add:
self.commands["models"] = self.handle_models_command
self.commands["list-models"] = self.handle_models_command  # alias
```

### Step 3.4: Update Command Help
Update the help text in `handle_help_command` method:

```python
# Add to the help text:
help_text += """
/models [provider] - List available models (optionally filtered by provider)
/list-models [provider] - Alias for /models
"""
```

## Phase 4: Configuration & Polish

### Step 4.1: Add Configuration Option
In `modules/Types.py`, modify the `ProviderConfig` class to add a `query_models` flag:

```python
class ProviderConfig(BaseModel):
    api_key: str
    base_url: str
    models: List[str] = []
    query_models: bool = True  # New field: enable dynamic model querying
```

### Step 4.2: Update Model Querying Logic
Modify the model querying logic in both `main.py` and `CommandHandler.py` to respect the configuration:

```python
# In both files, before calling get_available_models():
if getattr(provider_config, 'query_models', True):
    # Try dynamic query
    dynamic_models = api.get_available_models()
else:
    dynamic_models = []
```

### Step 4.3: Add Error Handling for Configuration
Update the configuration loading to handle the new field gracefully:

```python
# In modules/Config.py, ensure the field is handled during config loading
# The Pydantic model should handle this automatically
```

## Testing Requirements

### Step 5.1: Create Unit Tests
Create `tests/test_dynamic_models.py` with the following tests:

```python
import pytest
from unittest.mock import Mock, patch
from modules.OpenAIChatCompletionApi import OpenAIChatCompletionApi

def test_get_available_models_success():
    """Test successful model query."""
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

        api = OpenAIChatCompletionApi("openai", "test-key", "https://api.openai.com")
        models = api.get_available_models()

        assert len(models) == 2
        assert models[0]["id"] == "gpt-4"

def test_get_available_models_error():
    """Test model query with API error."""
    with patch('requests.get') as mock_get:
        mock_get.side_effect = Exception("API error")

        api = OpenAIChatCompletionApi("openai", "test-key", "https://api.openai.com")
        models = api.get_available_models()

        assert models == []

def test_get_available_models_caching():
    """Test that caching works correctly."""
    # Test implementation...
```

### Step 5.2: Test CLI Functionality
Test the enhanced `--list-models` flag:

```bash
# Test without provider filter
python main.py --list-models

# Test with specific provider
python main.py --list-models --provider openai

# Test with invalid provider
python main.py --list-models --provider invalid
```

### Step 5.3: Test In-App Command
Start the chat interface and test:

```bash
python main.py
# Then in the chat:
/models
/models openai
/models invalid
```

## Final Steps

### Step 6.1: Run All Tests
Execute the test suite to ensure no regressions:

```bash
make test
# or
pytest
```

### Step 6.2: Update Documentation
Update the README.md to document the new functionality:

```markdown
## Dynamic Model Querying

The CLI now supports dynamic model querying from configured providers:

### CLI Usage
```bash
# List all models from all providers
python main.py --list-models

# List models from specific provider
python main.py --list-models --provider openai
```

### In-App Commands
- `/models` - List available models from all providers
- `/models <provider>` - List models from specific provider
- `/list-models` - Alias for `/models`
```

### Step 6.3: Verify Configuration Compatibility
Test that existing configurations work without modification:

```bash
# Ensure your existing config.toml still works
python main.py --list-models
```

## Implementation Notes

### Key Considerations
1. **Error Handling**: Always provide graceful fallback to static models
2. **Caching**: Use session-based caching to avoid excessive API calls
3. **Backward Compatibility**: Ensure existing functionality remains unchanged
4. **Performance**: Dynamic queries should not significantly impact CLI startup time

### Common Pitfalls to Avoid
1. Don't forget to import required modules in each file
2. Ensure proper error handling for network timeouts
3. Test with providers that may not support the `/v1/models` endpoint
4. Verify that the caching mechanism works correctly

### Success Criteria
- Dynamic model querying works for OpenAI provider
- Dynamic model querying works for DeepSeek provider
- Graceful fallback to static models when API unavailable
- CLI `--list-models` flag shows dynamic results
- In-app `/models` command functions correctly
- All existing tests pass
- No breaking changes to current functionality

This action plan provides complete implementation instructions. Follow each step in order, testing as you go to ensure each phase works correctly before proceeding to the next.