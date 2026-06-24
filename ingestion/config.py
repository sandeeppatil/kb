from pathlib import Path
from pydantic import BaseSettings


class IngestionSettings(BaseSettings):
    """Configuration for the ingestion pipeline.

    This is intentionally minimal for v1 and can later be extended
    or replaced by a richer config system or UI-driven settings.
    """

    kb_root: Path = Path.home() / "kb_root"
    default_embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    class Config:
        env_prefix = "KB_"
        env_file = ".env"


settings = IngestionSettings()
