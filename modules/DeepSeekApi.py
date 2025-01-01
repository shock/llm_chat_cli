from .OpenAIChatCompletionApi import OpenAIChatCompletionApi

class DeepSeekApi(OpenAIChatCompletionApi):
    """Class to interact with the DeepSeek API."""

    def __init__(self, api_key: str, model: str = "deepseek-chat", 
                 base_api_url: str = "https://api.deepseek.com/v1"):
        """
        Initialize the DeepSeek API.
        
        Args:
            api_key: DeepSeek API key
            model: Model to use
            base_api_url: Base API URL
        """
        valid_models = {
            "deepseek-chat": "chat",
            "deepseek-coder": "coder"
        }
        super().__init__(api_key, model, base_api_url, valid_models)

    def validate_api_key(self) -> bool:
        """
        Validate the DeepSeek API key.
        
        Returns:
            bool: True if key is valid, False otherwise
        """
        # DeepSeek-specific API key validation logic
        return self.api_key.startswith("ds-") and len(self.api_key) == 51
