import requests
import json
from typing import Dict, Any, Generator

PROVIDER_DATA = {
    "openai": {
        "name": "OpenAI",
        "api_key": "",
        "base_api_url": "https://api.openai.com/v1",
        "valid_models":  {
            "gpt-4o-2024-08-06": "4o",
            "gpt-4o-mini-2024-07-18": "4o-mini",
            "gpt-4.1-mini-2025-04-14": "4.1-mini",
            "gpt-5-mini": "5-mini"
        }
    },
    "deepseek": {
        "name": "DeepSeek",
        "api_key": "",
        "base_api_url": "https://api.deepseek.com/v1",
        "valid_models": {
            "deepseek-chat": "dschat",
            "deepseek-reasoner": "r1"
        }
    },
    "hyperbolic": {
        "name": "Hyperbolic",
        "api_key": "",
        "base_api_url": "https://api.hyperbolic.xyz/v1",
        "valid_models": {
            "Qwen/QwQ-32B-Preview": "qdub",
            "Qwen/Qwen2.5-72B-Instruct": "qinstruct"
        }
    }
}

# DEFAULT_MODEL = "openai/4o-mini"
# DEFAULT_MODEL = "deepseek/deepseek-reasoner"
DEFAULT_MODEL = "openai/4.1-mini"
# DEFAULT_MODEL = "openai/5-mini" # doesn't work - reverting back to 4.1-mini

def merged_models():
    """Aggregate models from all supported providers into a unified list.

    Iterates through predefined providers and combines their model configurations,
    returning a list of tuples containing provider name and model tuples.

    Returns:
        list[tuple]: Each entry contains (provider_name, (long_model_name, short_model_name))
        Example: [('openai', ('gpt-4o-2024-08-06', '4o')), ...]
    """
    merged_models = []
    for provider in PROVIDER_DATA.keys():
        models = [ [x,y] for x,y in PROVIDER_DATA[provider]["valid_models"].items() ]
        for long, short in models:
            merged_models.append((provider, (long, short)))
    return merged_models

def valid_scoped_models():
    return [ f"{x}/{y[0]} ({y[1]})" for x,y in merged_models() ]

class OpenAIChatCompletionApi:
    """Base class for OpenAI-compatible chat completion APIs."""

    def __init__(self, api_key: str, model: str, base_api_url: str, valid_models: Dict[str, str], provider: str):
        """
        Initialize the API with provider-specific configuration.

        Args:
            api_key: Provider API key
            model: Model to use
            base_api_url: Base API URL for the provider
            valid_models: Dictionary of valid models for this provider
            provider: Provider name
        """
        self.provider = provider
        self.api_key = api_key
        self.base_api_url = base_api_url
        self.valid_models = valid_models.copy()
        self.inverted_models = {v: k for k, v in valid_models.items()}
        self.model = self.validate_model(model)

    def set_model(self, model_string: str):
        """
        Set the model to use.

        Args:
            model: model_string name to use

        Raises:
            ValueError: If model is not supported
        """
        provider, model = self.get_provider_and_model_for_model_string(model_string)
        new_api = OpenAIChatCompletionApi.get_api_for_model_string(model_string)
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

        for provider, models in merged_models():
            if self.provider == provider:
                if model_string == models[0]:
                    return models[0]
                elif model_string == models[1]:
                    return models[0]
        raise ValueError(
            f"Invalid model: {model_string}. Valid models: {', '.join(valid_scoped_models())}"
        )

    def brief_model(self) -> str:
        """Get a brief description of the model."""
        return self.valid_models.get(self.model, self.model)

    def get_chat_completion(self, messages: list, stream: bool = False) -> Dict[str, Any]:
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

    def validate_api_key(self) -> bool:
        """
        Validate the DeepSeek API key.

        Returns:
            bool: True if key is valid, False otherwise
        """
        # DeepSeek-specific API key validation logic
        return self.api_key.startswith("sk-") and len(self.api_key) >= 36

    provider_data = PROVIDER_DATA

    @classmethod
    def get_api_for_model_string(cls, model_string: str = "4o-mini") -> 'OpenAIChatCompletionApi':
        """Get an API instance for the specified model string.

        Args:
            model_string: Model identifier in format 'provider/model' or just model name

        Returns:
            OpenAIChatCompletionApi: Configured API instance

        Raises:
            ValueError: If provider or model is invalid
        """
        provider, model = split_first_slash(model_string)
        provider = provider.lower()

        # Handle provider-prefixed model strings
        if provider:
            if provider not in cls.provider_data:
                raise ValueError(f"Invalid provider prefix: {provider}")

            provider_data = cls.provider_data[provider]
            try:
                return OpenAIChatCompletionApi(
                    provider_data['api_key'],
                    model,
                    provider_data['base_api_url'],
                    provider_data['valid_models'],
                    provider
                )
            except ValueError as e:
                raise ValueError(f"Invalid model for provider {provider}: {model}") from e

        # Handle unprefixed model strings
        for provider_name, models in merged_models():
            if model in models:
                provider_data = cls.provider_data[provider_name]
                return OpenAIChatCompletionApi(
                    provider_data['api_key'],
                    model,
                    provider_data['base_api_url'],
                    provider_data['valid_models'],
                    provider_name
                )

        raise ValueError(f"Invalid model: {model}. Valid models: {', '.join(valid_scoped_models())}")

    @classmethod
    def get_provider_and_model_for_model_string( cls, model_string: str = "4o-mini") -> tuple[str, str]:
        # match the provider prefix (contiguous characters leading up to a '/')
        provider, model = split_first_slash(model_string)
        print(provider, model)
        provider = provider.lower()
        if provider == "":
            provider = "openai"
        try:
            provider_data = cls.provider_data[provider]
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
