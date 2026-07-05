"""Central application configuration loaded from environment variables."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Security
    secret_key: str = "dev-insecure-secret-change-me"
    access_token_expire_minutes: int = 10080
    algorithm: str = "HS256"

    # Database
    database_url: str = "sqlite:///./agritech.db"

    # Groq LLM
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    # Current Groq multimodal model. The old llama-3.2 vision *preview* IDs were
    # decommissioned; scout is the supported vision model (qwen/qwen3.6-27b is an
    # alternative). Override via GROQ_VISION_MODEL if Groq rotates it again.
    groq_vision_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"

    # Open-source local CV disease classifiers (Hugging Face image-classification)
    cv_local_enabled: bool = True
    cv_use_gpu: bool = False
    plant_disease_model: str = "linkanjarad/mobilenet_v2_1.0_224-plant-disease-identification"
    animal_disease_model: str = "SrimathiE21ALR044/Cattle_Skin_Disease"

    # Gemini embeddings
    gemini_api_key: str = ""
    gemini_embedding_model: str = "models/text-embedding-004"

    # News
    news_api_key: str = ""
    news_cache_ttl_seconds: int = 1800

    # CORS
    frontend_origin: str = "http://localhost:5173"

    @property
    def groq_enabled(self) -> bool:
        return bool(self.groq_api_key)

    @property
    def gemini_enabled(self) -> bool:
        return bool(self.gemini_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
