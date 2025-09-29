import os
import sys
import toml
import yaml
import copy
from pydantic import ValidationError
from modules.OpenAIChatCompletionApi import OpenAIChatCompletionApi
from modules.Types import ConfigModel, ProviderConfig, SASSY_SYSTEM_PROMPT

class Config:
    """Class to handle configuration load and storage."""

    def __init__(self, data_directory=None, config_file=None, overrides={}, create_config=False):
        self.data_directory = os.path.expanduser(data_directory or "~/.llm_chat_cli")
        config_file = config_file or os.path.join(self.data_directory, "config.toml")
        self.config_file = os.path.join(self.data_directory, "config.toml")
        self.overrides = overrides
        self.config = self.load_config(config_file, create_config)
        self.echo_mode = False

        if not os.path.exists(self.data_directory):
            if create_config:
                os.makedirs(self.data_directory)
            else:
                raise FileNotFoundError(f"Data directory {self.data_directory} does not exist.")

        if not os.path.exists(os.path.join(self.data_directory, "config.toml")):
            if create_config:
                self.save()
                print(f"Created default configuration file in {self.data_directory}")


    def load_config(self, config_file, create_config=False):
        """Load configuration from the specified file."""
        config_data = {}
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as file:
                    config_data = toml.load(file)
            except Exception as e:
                if not create_config:
                    print(f"Error loading config file: {e}")
                    raise e
                config_data = {}
        else:
            if not create_config:
                print(f"WARNING: no config file found at {config_file}.", file=sys.stderr)

        if config_data.get("sassy", False):
            config_data["system_prompt"] = SASSY_SYSTEM_PROMPT

        # Merges dicts recursively, with d2 values taking precedence over d1
        # returns a new dict, does not modify d1 or d2
        def merge_dicts(d1, d2):
            d1 = copy.deepcopy(d1)
            for key, value in d2.items():
                if value is None:
                    continue
                if key in d1 and isinstance(d1[key], dict) and isinstance(value, dict):
                    d1[key] = merge_dicts(d1[key], value)
                else:
                    d1[key] = value
            return d1

        # Save provider overrides from config file, if any
        providers_overrides = config_data.get("providers", {})

        # Start with built-in provider data
        config_data["providers"] = copy.deepcopy(OpenAIChatCompletionApi.provider_data)

        # Load provider YAML configurations, if present.  Merge with existing provider data, giving precedence to YAML file.
        provider_config_path = os.path.join(self.data_directory, "openaicompat-providers.yaml")
        if os.path.exists(provider_config_path):
            try:
                with open(provider_config_path, 'r') as file:
                    provider_data = yaml.safe_load(file)
                    if provider_data and 'providers' in provider_data:
                        config_data['providers'] = merge_dicts(config_data['providers'], provider_data['providers'])
            except Exception as e:
                print(f"Error loading provider config: {e}")

        # do final overrides with provider data from config file, if any
        config_data["providers"] = merge_dicts(config_data["providers"], providers_overrides)

        # Check environment variables for API keys that are not set or are set to "not-configured"
        providers = config_data.get("providers", {})
        for provider in providers.keys():
            api_key = os.getenv(f"{provider.upper()}_API_KEY")
            if api_key:
                providers[provider] = {} if not providers.get(provider) else providers[provider]
                # override the current API key with the environment variable if it's not already set or ends with "not-configured"
                if not providers[provider].get("api_key") or providers[provider]["api_key"].endswith("not-configured"):
                    print(f"Using API key from environment variable {provider.upper()}_API_KEY for provider {provider}", file=sys.stderr)
                    providers[provider]["api_key"] = api_key

        # override config values with command line flags or environment variables
        config_data = merge_dicts(config_data, self.overrides)

        try:
            return ConfigModel(**config_data)
        except ValidationError as e:
            raise e


    def save(self):
        """Save the configuration to the config file."""
        config_file = os.path.join(self.data_directory, "config.toml")
        with open(config_file, 'w') as f:
            f.write("# LLM API Chat Configuration File\n\n")
            for key, value in self.config.model_dump().items():
                f.write(f"# {ConfigModel.model_fields[key].description}\n")  # Use .description directly
                f.write(f"{toml.dumps({key: value})}\n\n")
        self.new_config = False

    def get(self, key):
        """Get a configuration value by key."""
        return self.data_directory if key == 'data_directory' else getattr(self.config, key)

    def is_sassy(self):
        """Check if sassy mode is enabled."""
        return self.config.sassy

    def get_provider_config(self, provider: str) -> ProviderConfig:
        """Get configuration for a specific provider."""
        provider = provider.lower()
        if provider in self.config.providers:
            return self.config.providers[provider]
        raise ValueError(f"Provider '{provider}' not found in configuration")

    def get_provider_api_key(self, provider: str) -> str:
        """Get API key for a specific provider."""
        provider = provider.lower()
        if provider in self.config.providers:
            return self.config.providers[provider].api_key
        raise ValueError(f"Provider '{provider}' not found in configuration")

    def get_provider_base_url(self, provider: str) -> str:
        """Get base API URL for a specific provider."""
        provider = provider.lower()
        if provider in self.config.providers:
            return self.config.providers[provider].base_api_url
        raise ValueError(f"Provider '{provider}' not found in configuration")

    def get_provider_valid_models(self, provider: str) -> dict[str, str]:
        """Get valid models for a specific provider."""
        provider = provider.lower()
        if provider in self.config.providers:
            return self.config.providers[provider].valid_models
        raise ValueError(f"Provider '{provider}' not found in configuration")
