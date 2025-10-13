"""
Provider management and cross-provider model resolution.

This module provides the ProviderManager class which serves as the primary interface
for all provider-related operations throughout the codebase, replacing direct
Dict[str, ProviderConfig] usage.
"""

import os
import yaml
from typing import List, Dict, Optional, Tuple, Any
from modules.ProviderConfig import ProviderConfig
from modules.ModelDiscoveryService import ModelDiscoveryService


class ProviderManager:
    """
    Unified provider management interface.

    Replaces Dict[str, ProviderConfig] globally throughout the codebase.
    Handles provider configuration, model discovery, cross-provider model resolution,
    and YAML persistence.
    """

    def __init__(self, providers: Dict[str, Any]):
        """
        Initialize ProviderManager with provider configurations.

        Args:
            providers: Dictionary of provider configurations (either ProviderConfig objects or dict data)
        """
        # Convert dict provider data to ProviderConfig objects if needed
        provider_configs = {}
        for provider_name, provider_data in providers.items():
            if isinstance(provider_data, ProviderConfig):
                provider_configs[provider_name] = provider_data
            else:
                # Convert dict to ProviderConfig
                provider_configs[provider_name] = ProviderConfig(**provider_data)

        self.providers = provider_configs
        self.discovery_service = ModelDiscoveryService()
        self.cached_valid_scoped_models = None

    # Dict-like Interface Methods

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

    def model_dump(self) -> Dict[str, Dict[str, Any]]:
        """Serialize ProviderManager to dictionary for Pydantic model_dump."""
        providers_data = {}
        for provider_name, provider_config in self.providers.items():
            providers_data[provider_name] = provider_config.model_dump()
        return providers_data

    # Provider Management Methods

    def get_provider_config(self, provider_name: str) -> ProviderConfig:
        """Get specific provider config by name."""
        if provider_name not in self.providers:
            raise KeyError(f"Provider '{provider_name}' not found.")
        return self.providers[provider_name]

    def get_all_provider_names(self) -> List[str]:
        """List all available provider names."""
        return list(self.providers.keys())

    # Cross-Provider Model Resolution Methods
    # (Moved from OpenAIChatCompletionApi with EXACT logic)

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
        if self.cached_valid_scoped_models is not None:
            return self.cached_valid_scoped_models

        model_list = [f"{provider}/{long_name} ({short_name})" for provider, (long_name, short_name) in self.merged_models()]
        self.cached_valid_scoped_models = model_list
        return model_list

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
        provider_prefix, model = self.split_first_slash(model_string)
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

    @staticmethod
    def split_first_slash(text: str) -> Tuple[str, str]:
        """
        Utility function for parsing provider/model strings.

        PRESERVE EXACT LOGIC from OpenAIChatCompletionApi.split_first_slash()
        """
        if '/' in text:
            parts = text.split('/', 1)
            return parts[0], parts[1]
        else:
            return '', text

    # Model Discovery and Validation Methods

    def discover_models(self, force_refresh: bool = False, persist_on_success: bool = True, provider: Optional[str] = None, data_directory: Optional[str] = None) -> bool:
        """
        Discover and validate models for providers.

        Args:
            force_refresh: Whether to bypass cache and force refresh
            persist_on_success: Whether to persist configs to YAML if successful
            provider: Optional provider name to limit discovery to specific provider

        Returns:
            True if successful for all targeted providers, False otherwise
        """
        # Invalidate cache at the start
        self.cached_valid_scoped_models = None

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
                print(f"Discovered {len(model_names)} models for {provider_name}")
                # Validate models
                valid_models = []
                invalid_models = []
                print(f"Validating models for {provider_name}")
                for model_name in model_names:
                    print(".", end="", flush=True)
                    if model_name in provider_config.valid_models:
                        valid_models.append(model_name)
                    elif model_name in provider_config.invalid_models:
                        invalid_models.append(model_name)
                    elif self.discovery_service.validate_model(provider_config, model_name):
                        valid_models.append(model_name)
                    else:
                        invalid_models.append(model_name)

                # Update provider config
                provider_config.invalid_models = invalid_models
                provider_config.merge_valid_models(valid_models)

                print(f"\nSuccessfully discovered {len(valid_models)} valid and {len(invalid_models)} invalid models for {provider_name}")

            except Exception as e:
                print(f"Error discovering models for {provider_name}: {e}")
                success = False

        # Persist only if completely successful and requested
        if success and persist_on_success:
            self.persist_provider_configs(data_directory)
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

    # Utility Methods

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

    # YAML Persistence Implementation

    def persist_provider_configs(self, data_directory: Optional[str] = None) -> None:
        """
        Persist provider configurations to YAML file in data directory.

        File location: data/openaicompat-providers.yaml

        Only persisted fields are saved:
        - name, base_api_url, api_key, valid_models, invalid_models

        Runtime-only fields are excluded:
        - _cached_models, _cache_timestamp, cache_duration
        """
        # Get data directory path from config
        data_directory = os.path.expanduser(data_directory or "~/.llm_chat_cli")
        yaml_file_path = os.path.join(data_directory, "openaicompat-providers.yaml")

        # Create data directory if it doesn't exist
        if not os.path.exists(data_directory):
            os.makedirs(data_directory)

        # Prepare data for serialization
        providers_data = {}
        for provider_name, provider_config in self.providers.items():
            # Only include persisted fields
            providers_data[provider_name] = {
                "name": provider_config.name,
                "base_api_url": provider_config.base_api_url,
                "api_key": provider_config.api_key,
                "valid_models": provider_config.valid_models,
                "invalid_models": provider_config.invalid_models
            }

        # Write to YAML file
        try:
            with open(yaml_file_path, 'w') as file:
                yaml_data = {"providers": providers_data}
                yaml.dump(yaml_data, file, default_flow_style=False, sort_keys=False)
        except Exception as e:
            print(f"Error persisting provider configurations to YAML: {e}")
            raise