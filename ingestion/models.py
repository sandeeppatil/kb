from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field


class EmbeddingModelInfo(BaseModel):
    name: str
    provider: str = "sentence-transformers"
    dimension: int


class IngestionRun(BaseModel):
    run_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    added_documents: List[str] = Field(default_factory=list)
    skipped_documents: List[str] = Field(default_factory=list)


class SpaceMetadata(BaseModel):
    space_name: str
    description: str
    embedding_model: EmbeddingModelInfo
    chunking_strategy: str
    created_at: datetime
    last_updated_at: datetime
    source_manifest: List[str] = Field(default_factory=list)
    ingestion_runs: List[IngestionRun] = Field(default_factory=list)

    @classmethod
    def path_for(cls, kb_root: Path, space_name: str) -> Path:
        return kb_root / "spaces" / space_name / "metadata.json"


class ChunkRecord(BaseModel):
    chunk_id: str
    document_path: str
    page_range: str
    section_path: str
    content_text: str
    content_structured: Optional[str] = None
    content_type: str = "paragraph"
