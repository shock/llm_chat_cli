import requests
import time
from typing import List, Any, Dict, Optional
from modules.ProviderConfig import ProviderConfig


class ModelDiscoveryService:
    """
    Service for discovering and validating models via provider APIs.

    Handles:
    - Model discovery via /models endpoint
    - Model validation via ping tests
    - API key validation
    - Caching logic
    - Error handling and fallback mechanisms
    """

    def __init__(self):
        self.cache_duration = 300  # 5 minutes cache

    def parse_model_string(self, model_string: str) -> tuple[str, str]:
        """
        Parse a model string in format 'provider/model' or just model name.

        Args:
            model_string: Model string to parse

        Returns:
            tuple: (provider, model) where provider defaults to 'openai' if not specified
        """
        if '/' in model_string:
            provider, model = model_string.split('/', 1)
            return provider.lower(), model
        else:
            # Default to openai provider if no provider specified
            return 'openai', model_string

    def discover_models(self, provider_config: ProviderConfig, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
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
        """
        # Check cache first
        if (not force_refresh and
            provider_config._cached_models and
            provider_config._cache_timestamp and
            time.time() - provider_config._cache_timestamp < provider_config._cache_duration):
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

        Args:
            provider_config: Provider configuration with API credentials
            model: Model name to validate

        Returns:
            True if model is valid, False otherwise
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

        Args:
            provider_config: Provider configuration with API credentials

        Returns:
            False if API key is None or empty, True otherwise
        """
        return bool(provider_config.api_key and provider_config.api_key.strip())
