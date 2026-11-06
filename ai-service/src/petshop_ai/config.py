# config.py — configuración tipada (equivale a IOptions<T> + appsettings en .NET)
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    proveedor_modelo: str = "ollama"  # ollama | openai_compatible | bedrock
    temperatura: float = 0.2
    max_tokens: int = 2048

    ollama_host: str = "http://localhost:11434"
    ollama_model_id: str = "gpt-oss:20b"

    openai_compat_api_key: str = ""
    openai_compat_base_url: str = ""
    openai_compat_model_id: str = ""

    bedrock_model_id: str = ""
    bedrock_region: str = "us-east-2"

    petshop_db: str = "petshop.db"
    internal_api_key: str = "dev-internal-key"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_model(settings: Settings | None = None):
    """Crea el modelo según PROVEEDOR_MODELO, sin que el resto del código sepa cuál es."""
    s = settings or get_settings()

    if s.proveedor_modelo == "ollama":
        from strands.models.ollama import OllamaModel

        return OllamaModel(
            host=s.ollama_host,
            model_id=s.ollama_model_id,
            temperature=s.temperatura,
            max_tokens=s.max_tokens,
        )

    if s.proveedor_modelo == "openai_compatible":
        # vLLM, Ollama (/v1), OpenAI, Groq, OpenRouter, Gemini (endpoint OpenAI), etc.
        from strands.models.openai import OpenAIModel

        return OpenAIModel(
            client_args={"api_key": s.openai_compat_api_key or "sin-key", "base_url": s.openai_compat_base_url},
            model_id=s.openai_compat_model_id,
            params={"temperature": s.temperatura, "max_tokens": s.max_tokens},
        )

    if s.proveedor_modelo == "bedrock":
        from strands.models import BedrockModel

        return BedrockModel(
            model_id=s.bedrock_model_id,
            region_name=s.bedrock_region,
            temperature=s.temperatura,
            max_tokens=s.max_tokens,
        )

    raise ValueError(
        f"PROVEEDOR_MODELO='{s.proveedor_modelo}' no soportado. Usa: ollama, openai_compatible o bedrock."
    )
