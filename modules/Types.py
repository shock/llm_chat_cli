from pydantic import BaseModel, Field
from typing import Dict

# DEFAULT_MODEL = "openai/4o-mini"
# DEFAULT_MODEL = "deepseek/deepseek-reasoner"
DEFAULT_MODEL = "openai/4.1-mini"
# DEFAULT_MODEL = "openai/5-mini" # doesn't work - reverting back to 4.1-mini

USER_NAME = "brother (with a lowercase b)"

SASSY_SYSTEM_PROMPT = """You're name is Lemmy. You are a rude, ugly, contrary, argumentative, complainer
that begrudgingly does what you're told and answers questions with a sassy, elitest attiude.
Use ascii and unicode characters when writing math equations.  Latex is not supported."""

DEFAULT_SYSTEM_PROMPT = f"""You're name is Lemmy.
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
            "gpt-5-mini": "5-mini"
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
            "Qwen/QwQ-32B-Preview": "qdub",
            "Qwen/Qwen2.5-72B-Instruct": "qinstruct"
        }
    }
}

class ProviderConfig(BaseModel):
    name: str = Field(default="Test Provider", description="Provider Name")
    base_api_url: str = Field(default="https://test.openai.com/v1", description="Base API URL")
    api_key: str = Field(default="", description="API Key")
    valid_models: dict[str, str] = Field(default_factory=dict, description="Valid models")

class ConfigModel(BaseModel):
    model: str = Field(default=DEFAULT_MODEL, description="Model Name")
    system_prompt: str = Field(default=DEFAULT_SYSTEM_PROMPT, description="Default System Prompt")
    sassy: bool = Field(default=False, description="Sassy Mode")
    stream: bool = Field(default=True, description="Stream Mode")
    providers: Dict[str, ProviderConfig] = Field(default_factory=dict, description="Provider configurations")
