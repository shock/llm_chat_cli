from .OpenAIChatCompletionApi import OpenAIChatCompletionApi

class OpenAIApi(OpenAIChatCompletionApi):
    """Class to interact with the OpenAI API."""
    
    DEFAULT_MODEL = "gpt-4o-mini-2024-07-18"

    def __init__(self, api_key: str, model: str = "gpt-4o-mini-2024-07-18", 
                 base_api_url: str = "https://api.openai.com/v1"):
        """
        Initialize the OpenAI API.
        
        Args:
            api_key: OpenAI API key
            model: Model to use
            base_api_url: Base API URL
        """
        valid_models = {
            "gpt-4o-2024-08-06": "4o",
            "gpt-4o-mini-2024-07-18": "4o-mini"
        }
        super().__init__(api_key, model, base_api_url, valid_models)
        self.inverted_models = {v: k for k, v in valid_models.items()}

    def brief_model(self) -> str:
        """Get a brief description of the model."""
        return self.inverted_models.get(self.model, self.model)

    def validate_api_key(self) -> bool:
        """
        Validate the OpenAI API key.
        
        Returns:
            bool: True if key is valid, False otherwise
        """
        # OpenAI-specific API key validation logic
        return self.api_key.startswith("sk-") and len(self.api_key) == 51

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
