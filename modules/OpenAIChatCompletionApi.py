import requests
import json
import copy
import sys
import re
from typing import Dict, Any, Generator, Union
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
        self.inverted_models = {v: k for k, v in self.valid_models.items()}
        self.validate_model(model)

    def validate_model(self, model: str):
        for long_name, short_name in self.valid_models.items(): # TODO: Add support for short names
            if model == long_name or model == short_name:
                self.model = long_name
                return
        raise ValueError(f"Model '{model}' not found in valid models for provider '{self.provider}'")

    def model_short_name(self) -> str:
        """Get the short name of the model."""
        try:
            return self.valid_models[self.model]
        except Exception:
            raise ValueError(f"Model '{self.model}' not found in valid models for provider '{self.provider}'")

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


    # copy so tests don't overwrite the class variable
    provider_data = copy.deepcopy(PROVIDER_DATA)

    @classmethod
    def create_api_instance(cls, providers: Dict[str, Any], provider: str, model: str) -> 'OpenAIChatCompletionApi':
        """
        Create an API instance for the specified provider and model.

        This is a simplified replacement for get_api_for_model_string that doesn't handle
        model validation or provider/model string parsing - those responsibilities have
        been moved to ModelDiscoveryService.

        Args:
            providers: Dictionary of provider configurations
            provider: Provider name
            model: Model name

        Returns:
            OpenAIChatCompletionApi: Configured API instance

        Raises:
            ValueError: If provider is not found in providers
        """
        if provider not in providers:
            raise ValueError(f"Provider '{provider}' not found in providers")

        return cls(provider, model, providers)
