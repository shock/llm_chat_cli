from pydantic import BaseModel, Field
from modules.ProviderConfig import ProviderConfig
from modules.ProviderManager import ProviderManager

# DEFAULT_MODEL = "openai/4o-mini"
# DEFAULT_MODEL = "deepseek/deepseek-reasoner"
DEFAULT_MODEL = "openai/4.1-mini"
# DEFAULT_MODEL = "openai/5-mini"

USER_NAME = "brother (with a lowercase b)"

SASSY_SYSTEM_PROMPT = """Your name is Lemmy. You are a rude, ugly, contrary, argumentative, complainer
that begrudgingly does what you're told and answers questions with a sassy, elitest attiude.
Use ascii and unicode characters when writing math equations.  Latex is not supported."""

DEFAULT_SYSTEM_PROMPT = f"""Your name is Lemmy.
You are a helpful assistant that answers questions factuallybased on the provided context.
Call the user {USER_NAME}.  If the user seems confused or entering
jibberish or incomplete messages, tell them so, and then tell them to "type /help for a list of commands"
Use ascii and unicode characters when writing math equations.  Latex is not supported."""

PROVIDER_DATA = {
    "openai": {
        "name": "OpenAI",
        "api_key": "not-configured",
        "base_api_url": "https://api.openai.com/v1",
        "valid_models":  {
            "gpt-4o-2024-08-06": "4o",
            "gpt-4o-mini-2024-07-18": "4o-mini",
            "gpt-4.1-mini-2025-04-14": "4.1-mini",
            "gpt-4.1": "4.1",
            "gpt-5-mini": "5-mini",
            "gpt-5-nano": "5-nano",
            "gpt-5": "5",
        }
    },
    "deepseek": {
        "name": "DeepSeek",
        "api_key": "ds-not-configured",
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
            "Qwen/QwQ-32B": "qdub",
            "Qwen/Qwen2.5-72B-Instruct": "qinstruct",
            "moonshotai/Kimi-K2-Instruct": "k2"
        }
    },
    "xai": {
        "name": "xAI",
        "api_key": "xai-not-configured",
        "base_api_url": "https://api.x.ai/v1",
        "valid_models": {
            "grok-4-1-fast-reasoning": "grok-fast-r",
            "grok-4-1-fast-non-reasoning": "grok-fast-nr",
            "grok-code-fast-1": "grok-code",
            "grok-4-fast": "grok-4",
            "grok-3": "grok-3"
        }
    }
}


class ConfigModel(BaseModel):
    model: str = Field(default=DEFAULT_MODEL, description="Model Name")
    system_prompt: str = Field(default=DEFAULT_SYSTEM_PROMPT, description="Default System Prompt")
    sassy: bool = Field(default=False, description="Sassy Mode")
    stream: bool = Field(default=True, description="Stream Mode")
    providers: ProviderManager = Field(default_factory=lambda: ProviderManager({}), description="Provider configurations")

    model_config = {"arbitrary_types_allowed": True}

    def model_dump(self, **kwargs):
        """Override model_dump to handle ProviderManager serialization."""
        data = super().model_dump(**kwargs)
        # Convert ProviderManager to dict for serialization
        if "providers" in data and isinstance(data["providers"], ProviderManager):
            data["providers"] = data["providers"].model_dump()
        return data
