import os
from functools import lru_cache

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
#lhne t7ot les api keys 
class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    MODEL_PROVIDER: str = os.getenv("MODEL_PROVIDER", "anthropic")  
    MODEL_NAME: str = os.getenv("MODEL_NAME", "claude-sonnet-4-6")

    MAX_CONNECTIONS_PER_USER: int = 3
    AGENT_TIMEOUT_SECONDS: int = 120


@lru_cache
def get_settings() -> Settings:
    return Settings()
