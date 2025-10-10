"""
Provider configuration data model.

This module defines the ProviderConfig class for managing LLM provider configurations,
including API settings, model validation, and caching mechanisms.
"""

from pydantic import BaseModel, Field, PrivateAttr
from typing import List, Any, Dict, Optional


class ProviderConfig(BaseModel):
    """
    Provider configuration data model.

    Persisted fields (saved to YAML):
    - name, base_api_url, api_key, valid_models, invalid_models

    Runtime-only fields (not saved to YAML):
    - _cached_models, _cache_timestamp, cache_duration
    """

    # Persisted fields
    name: str = Field(default="Test Provider", description="Provider Name")
    base_api_url: str = Field(default="https://test.openai.com/v1", description="Base API URL")
    api_key: str = Field(default="", description="API Key")
    valid_models: dict[str, str] = Field(default_factory=dict, description="Valid models (long_name: short_name)")
    invalid_models: List[str] = Field(default_factory=list, description="Invalid models")

    # Runtime-only fields (excluded from serialization)
    _cached_models: List[Any] = PrivateAttr(default_factory=list)
    _cache_timestamp: float = PrivateAttr(default=0.0)
    _cache_duration: int = PrivateAttr(default=300)

    def model_post_init(self, __context: Any) -> None:
        """Initialize runtime-only fields after model creation."""
        self._cached_models = []
        self._cache_timestamp = 0.0
        self._cache_duration = 300

    def get_valid_models(self) -> List[str]:
        """Return list of valid model long names."""
        return list(self.valid_models.keys())

    def get_invalid_models(self) -> List[str]:
        """Return list of invalid model names."""
        return self.invalid_models.copy()

    def find_model(self, name: str) -> Optional[str]:
        """
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
        """
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
        """
        Merge new models with existing valid_models.

        For new models without existing mappings, use full model ID as short name.
        Existing mappings are preserved.

        Args:
            models: List of model long names to merge
        """
        for model_long_name in models:
            if model_long_name not in self.valid_models:
                # Use full model ID as short name initially
                self.valid_models[model_long_name] = model_long_name