from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

import lancedb
import pyarrow as pa
from lancedb.pydantic import LanceModel, Vector

from .config import settings
from .models import ChunkRecord, EmbeddingModelInfo, SpaceMetadata


class ChunkRow(LanceModel):
    chunk_id: str
    document_path: str
    page_range: str
    section_path: str
    content_text: str
    content_structured: str | None
    content_type: str
    vector: Vector(384)  # aligned with all-MiniLM-L6-v2


class SpaceStore:
    def __init__(self, kb_root: Path | None = None) -> None:
        self.kb_root = kb_root or settings.kb_root
        self.db = lancedb.connect(str(self.kb_root / "spaces_db"))

    def _space_dir(self, space_name: str) -> Path:
        return self.kb_root / "spaces" / space_name

    def _metadata_path(self, space_name: str) -> Path:
        return self._space_dir(space_name) / "metadata.json"

    def load_or_create_metadata(
        self,
        space_name: str,
        description: str,
        embedding_info: EmbeddingModelInfo,
        chunking_strategy: str,
    ) -> SpaceMetadata:
        path = self._metadata_path(space_name)
        space_dir = path.parent
        space_dir.mkdir(parents=True, exist_ok=True)

        if path.exists():
            data = json.loads(path.read_text())
            return SpaceMetadata(**data)

        now = datetime.utcnow()
        meta = SpaceMetadata(
            space_name=space_name,
            description=description,
            embedding_model=embedding_info,
            chunking_strategy=chunking_strategy,
            created_at=now,
            last_updated_at=now,
        )
        path.write_text(meta.model_dump_json(indent=2, by_alias=True))
        return meta

    def save_metadata(self, meta: SpaceMetadata) -> None:
        path = self._metadata_path(meta.space_name)
        path.write_text(meta.model_dump_json(indent=2, by_alias=True))

    def upsert_chunks(self, space_name: str, chunks: Iterable[ChunkRow]) -> None:
        table_name = f"space_{space_name}"
        rows: List[ChunkRow] = list(chunks)
        if not rows:
            return

        if table_name in self.db.table_names():
            table = self.db.open_table(table_name)
            table.add([r.model_dump() for r in rows])
        else:
            self.db.create_table(table_name, [r.model_dump() for r in rows])
