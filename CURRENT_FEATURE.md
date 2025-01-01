# Support non-OpenAI providers as long as they support the OpenAI chat completion api.

We'll change the class name to OpenAIChatCompletionApi and add a new class called OpenAIApi that inherits from it and implements the chat completion api.  Additionally, we'll add a new class called DeepSeekApi that implements the chat completion api for the DeepSeek provider.  Note that the vast bulk of the logic should remain in the OpenAIChatCompletionApi class.  Only logic that is specific to the DeepSeek or OpenAI providers should be added to the DeepSeekApi or OpenAIApi classes respectively.

The provider data will be stored in a config file and the config file will be loaded when the app starts.  By default, the open ai provider will be configured with the same information currently being used and info for a new provider "DeepSeek" will be added.  Use placeholders where values are not known.  Each provider should have a list of valid models that can be used.  For now, we'll just support two provider: "deepseek" and "openai".  The provider name will be used to select the appropriate provider specific info from the config data.

API keys can be stored against a provider in the config file.  They can also be overerriden the way they are now using environment variables.  The appropriate API key will still be passed to the OpenAIChatCompletionApi sub-class as a constructor argument.  The OpenAIApi class will validate the API key and throw an exception if it is invalid.  The model passed to the OpenAIChatCompletionApi sub-class will be validated against the list of valid models for the provider.  A prefix may be added to chooise the provider.  The prefix can be any character sequence not containing a space or a forward slash.  This string converted to lowercase will be used as the provivder name, by which the provider specific info such as API endpoint URL will be selected from the config data.

Write an example config file with placeholders for the API keys and model names for each provider.  The model/provider config file should be stored in the data directory specified in the config file.  The config file should be named "openaicompat-providers.json" and should be in YAML format.

Don't write any code.  Just write the config file.

>>>>  DeepSeek

Here's a step-by-step plan to implement support for multiple OpenAI-compatible providers:

 1 File Structure Changes
    • Create new file: modules/OpenAIChatCompletionApi.py (base class)
    • Rename existing: modules/OpenAIApi.py → modules/OpenAIApi.py (OpenAI-specific)
    • Create new file: modules/DeepSeekApi.py (DeepSeek-specific)
    • Create new config file: data/openaicompat-providers.yaml
 2 Configuration Changes
    • Add new YAML config file with provider-specific details:

       providers:
         openai:
           base_api_url: "https://api.openai.com/v1"
           api_key: "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
           valid_models:
             - "gpt-4o-2024-08-06"
             - "gpt-4o-mini-2024-07-18"
         deepseek:
           base_api_url: "https://api.deepseek.com/v1"
           api_key: "ds-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
           valid_models:
             - "deepseek-chat"
             - "deepseek-coder"

 3 Class Hierarchy
    • OpenAIChatCompletionApi (Base class):
       • Contains core chat completion logic
       • Handles model validation
       • Manages API requests
    • OpenAIApi (Inherits from OpenAIChatCompletionApi):
       • OpenAI-specific validation
       • OpenAI-specific error handling
    • DeepSeekApi (Inherits from OpenAIChatCompletionApi):
       • DeepSeek-specific validation
       • DeepSeek-specific error handling
 4 Provider Selection
    • Add provider prefix support to model selection:
       • openai:gpt-4o → Uses OpenAI provider
       • deepseek:deepseek-chat → Uses DeepSeek provider
       • gpt-4o → Defaults to OpenAI provider (backward compatible)
 5 Configuration Loading
    • Modify Config class to load provider config from openaicompat-providers.yaml
    • Add method to get provider-specific configuration
    • Maintain backward compatibility for existing OpenAI configuration
 6 API Key Handling
    • Keep existing environment variable override mechanism
    • Add provider-specific environment variables:
       • OPENAI_API_KEY (existing)
       • DEEPSEEK_API_KEY (new)
 7 Error Handling
    • Add provider-specific error handling
    • Maintain consistent error messages across providers
    • Add provider-specific validation for API keys and models
 8 Testing
    • Add tests for new provider selection logic
    • Add tests for provider-specific validation
    • Update existing tests to handle multiple providers
