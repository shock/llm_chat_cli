import requests
import json
import copy
import sys
import time
from typing import Dict, Any, Generator, Union, List
from modules.Types import ProviderConfig, PROVIDER_DATA

class OpenAIChatCompletionApi:
    """Base class for OpenAI-compatible chat completion APIs."""

    def __init__(self, provider: str, model: str, providers: Dict[str, ProviderConfig]):
        """
        Initialize the API with provider-specific configuration.

        Args:
            provider: Provider name
            model: Model name
            providers: Dictionary of provider configurations
        """
        provider_data = providers.get(provider)
        if provider_data is None:
            raise ValueError(f"No configuration found for provider: {provider}")
        self.providers = providers
        self.provider = provider
        self.api_key = provider_data.api_key
        self.base_api_url = provider_data.base_api_url
        self.valid_models = provider_data.valid_models
        # self.valid_models = valid_models.copy()
        self.inverted_models = {v: k for k, v in self.valid_models.items()}
        self.model = self.validate_model(model)

        # Add caching for model queries
        self._cached_models = None
        self._cache_timestamp = None
        self.cache_duration = 300  # 5 minutes cache

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
                valid_models={"dummy-model": "dummy"}  # Add dummy model to avoid validation errors
            )
        }

        # Create instance with a dummy model
        return cls(provider, "dummy-model", providers)

    @classmethod
    def merged_models(cls, providers: Dict[str, Any]) -> list[tuple[str, tuple[str, str]]]:
        """Aggregate models from all supported providers into a unified list.

        Iterates through predefined providers and combines their model configurations,
        returning a list of tuples containing provider name and model tuples.

        Returns:
            list[tuple]: Each entry contains (provider_name, (long_model_name, short_model_name))
            Example: [('openai', ('gpt-4o-2024-08-06', '4o')), ...]
        """
        merged_models = []
        for provider in providers.keys():
            if providers[provider].valid_models is None or not isinstance(providers[provider].valid_models, dict):
                continue
            models = [ [x,y] for x,y in providers[provider].valid_models.items() ]
            for long, short in models:
                merged_models.append((provider, (long, short)))
        return merged_models


    @classmethod
    def valid_scoped_models(cls, providers: Dict[str, Any]) -> list[str]:
        return [ f"{x}/{y[0]} ({y[1]})" for x,y in cls.merged_models(providers) ]

    def set_model(self, model_string: str):
        """
        Set the model to use.

        Args:
            model: model_string name to use

        Raises:
            ValueError: If model is not supported
        """
        provider, model = self.get_provider_and_model_for_model_string(model_string)
        new_api = OpenAIChatCompletionApi.get_api_for_model_string(self.providers, model_string)
        new_api.provider = provider
        new_api.model = new_api.validate_model(model)
        return new_api

    def validate_model(self, model_string: str) -> str:
        """
        Validate the model against the provider's supported models.

        Args:
            model: Model name to validate

        Returns:
            Validated model name

        Raises:
            ValueError: If model is not supported
        """

        for provider, models in self.merged_models(self.providers):
            if self.provider == provider:
                if model_string == models[0]:
                    return models[0]
                elif model_string == models[1]:
                    return models[0]
        raise ValueError(
            f"Invalid model: {model_string}. Valid models: {', '.join(self.valid_scoped_models(self.providers))}"
        )

    def brief_model(self) -> str:
        """Get a brief description of the model."""
        return self.valid_models.get(self.model, self.model)

    def _extract_gpt_version(self) -> int | None:
        """
        Extract the GPT version number from the model string.

        Returns:
            int: The GPT version number if found, otherwise None.
        """
        if not self.provider == "openai" or not self.model.startswith("gpt-"):
            return None
        try:
            # Extract the part after 'gpt-'
            short_model = self.model.split("-")[1]
            # Extract leading digits from short_model
            match = re.match(r"(\d+)", short_model)
            if match:
                return int(match.group(1))
        except (IndexError, ValueError):
            pass
        return None

    def get_chat_completion(self, messages: list, stream: bool = False) -> Union[Generator[Any, Any, Any], Dict[str, Any]]:
        """
        Get a chat completion from the API.

        Args:
            messages: List of messages in the conversation
            stream: Whether to stream the response

        Returns:
            Dictionary containing the API response
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.0,
            "stream": stream
        }
        gpt_version = self._extract_gpt_version()
        if gpt_version is not None and gpt_version > 4:
            # print("Using required temperature 1 for GPT-5 or higher", file=sys.stderr)
            data["temperature"] = 1
        response = requests.post(
            f"{self.base_api_url}/chat/completions",
            headers=headers,
            json=data,
            stream=stream
        )

        if stream:
            return self._stream_response(response)
        return response.json()

    def stream_chat_completion(self, messages: list) -> str:
        """
        Stream a chat completion and print as it's received.

        Args:
            messages: List of messages in the conversation

        Returns:
            Complete response as a string
        """
        response = ""
        for chunk in self.get_chat_completion(messages, stream=True):
            print(chunk, end='', flush=True)
            response += chunk
        print()  # Print a newline at the end
        return response

    def _stream_response(self, response) -> Generator[Any, Any, Any]:
        """
        Stream the response and yield chunks as they arrive.

        Args:
            response: Streaming response object

        Yields:
            Chunks of the response as they arrive
        """
        reasoning = False
        if response.status_code == 401:
            raise Exception(f"API request failed with status code {response.status_code}.  Is your API key valid?")
        elif response.status_code != 200:
            payload = response.json()
            print(payload, file=sys.stderr)
            raise Exception(f"API request failed with status code {response.status_code}.")
        for chunk in response.iter_lines():
            if chunk:
                chunk = chunk.decode('utf-8')
                if chunk.startswith(': keep-alive'): # deepseek reasoner sends this
                    continue
                if chunk.startswith('data: '):
                    chunk = chunk[6:]  # Remove the 'data: ' prefix
                if chunk != '[DONE]':
                    chunk_data = json.loads(chunk)
                    content = chunk_data['choices'][0]['delta'].get('content', '')
                    if content:
                        if reasoning:
                            yield "\n\nANSWER:\n\n"
                            reasoning = False
                        yield content
                    reasoning_content = chunk_data['choices'][0]['delta'].get('reasoning_content', '')
                    if reasoning_content:
                        if not reasoning:
                            yield "REASONING:\n\n"
                        yield reasoning_content
                        reasoning = True

    def get_available_models(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Query the provider's /v1/models endpoint for available models.
        Returns a list of model dictionaries or empty list on error.
        """
        # Check cache first
        if (not force_refresh and
            self._cached_models is not None and
            self._cache_timestamp is not None and
            time.time() - self._cache_timestamp < self.cache_duration):
            return self._cached_models

        try:
            # Build the API endpoint URL
            url = f"{self.base_api_url}/models"

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

    # copy so tests don't overwrite the class variable
    provider_data = copy.deepcopy(PROVIDER_DATA)

    @classmethod
    def get_api_for_model_string(cls, providers: Dict[str, Any], model_string: str = "4o-mini") -> 'OpenAIChatCompletionApi':
        """Get an API instance for the specified model string.

        Args:
            providers: Dictionary of provider configurations
            model_string: Model identifier in format 'provider/model' or just model name

        Returns:
            OpenAIChatCompletionApi: Configured API instance

        Raises:
            ValueError: If provider or model is invalid
        """
        provider, model = split_first_slash(model_string)
        provider = provider.lower()

        # convert providers values to ProviderConfig if they are dicts
        providers = copy.deepcopy(providers)
        for p in providers.keys():
            if isinstance(providers[p], dict):
                providers[p] = ProviderConfig(**providers[p])

        # Handle provider-prefixed model strings
        if provider:
            if provider not in providers:
                raise ValueError(f"Invalid provider prefix: {provider}")

            try:
                return OpenAIChatCompletionApi(
                    provider,
                    model,
                    providers
                )
            except ValueError as e:
                raise ValueError(f"Invalid model for provider {provider}: {model}") from e

        # Handle unprefixed model strings
        for provider_name, models in cls.merged_models(providers):
            if model in models:
                    return OpenAIChatCompletionApi(
                    provider_name,
                    model,
                    providers,
                )

        raise ValueError(f"Invalid model: {model}. Valid models: {', '.join(cls.valid_scoped_models(providers))}")

    @classmethod
    def get_provider_and_model_for_model_string( cls, model_string: str = "4o-mini") -> tuple[str, str]:
        # match the provider prefix (contiguous characters leading up to a '/')
        provider, model = split_first_slash(model_string)
        print(provider, model)
        provider = provider.lower()
        if provider == "":
            provider = "openai"
        try:
            if provider in cls.provider_data.keys():
                return provider, model
        except KeyError:
            raise ValueError(f"Invalid provider prefix: {provider}")
        raise ValueError(f"Invalid provider prefix: {provider}")

import re
def split_first_slash(text):
    # Use regex to split at the first slash
    match = re.match(r'([^/]*)/?(.*)', text)
    if match:
        if match.groups()[1] == '':
            return ('', match.groups()[0])
        return match.groups()
    return ('', text)
