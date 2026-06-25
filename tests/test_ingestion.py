"""Unit tests for the ingestion pipeline.

All heavy I/O (Docling PDF parsing, SentenceTransformer model loading,
LanceDB writes) is mocked so these tests run fast in CI without
downloading models or requiring real PDF files.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ingestion.models import (
    ChunkRecord,
    EmbeddingModelInfo,
    IngestionRun,
    SpaceMetadata,
)
from ingestion.config import IngestionSettings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_metadata(space_name: str = "test_space") -> SpaceMetadata:
    now = datetime.utcnow()
    return SpaceMetadata(
        space_name=space_name,
        description="A test space",
        embedding_model=EmbeddingModelInfo(
            name="sentence-transformers/all-MiniLM-L6-v2",
            provider="sentence-transformers",
            dimension=384,
        ),
        chunking_strategy="simple_page_blocks",
        created_at=now,
        last_updated_at=now,
    )


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class TestEmbeddingModelInfo:
    def test_defaults(self):
        m = EmbeddingModelInfo(name="test-model", dimension=384)
        assert m.provider == "sentence-transformers"

    def test_custom_provider(self):
        m = EmbeddingModelInfo(name="ollama/nomic", provider="ollama", dimension=768)
        assert m.dimension == 768


class TestSpaceMetadata:
    def test_round_trip_json(self, tmp_path: Path):
        meta = _make_metadata()
        path = tmp_path / "metadata.json"
        path.write_text(meta.model_dump_json(indent=2))
        loaded = SpaceMetadata(**json.loads(path.read_text()))
        assert loaded.space_name == meta.space_name
        assert loaded.description == meta.description

    def test_path_for(self, tmp_path: Path):
        path = SpaceMetadata.path_for(tmp_path, "my_space")
        assert path == tmp_path / "spaces" / "my_space" / "metadata.json"

    def test_source_manifest_appends(self):
        meta = _make_metadata()
        meta.source_manifest.append("/docs/file.pdf")
        assert len(meta.source_manifest) == 1

    def test_ingestion_run_records(self):
        meta = _make_metadata()
        run = IngestionRun(
            run_id=str(uuid.uuid4()),
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
            added_documents=["/docs/a.pdf"],
            skipped_documents=[],
        )
        meta.ingestion_runs.append(run)
        assert len(meta.ingestion_runs) == 1
        assert meta.ingestion_runs[0].added_documents == ["/docs/a.pdf"]


class TestChunkRecord:
    def test_defaults(self):
        chunk = ChunkRecord(
            chunk_id=str(uuid.uuid4()),
            document_path="/docs/test.pdf",
            page_range="1",
            section_path="/Introduction",
            content_text="Hello world",
        )
        assert chunk.content_type == "paragraph"
        assert chunk.content_structured is None


# ---------------------------------------------------------------------------
# Config tests
# ---------------------------------------------------------------------------

class TestIngestionSettings:
    def test_default_kb_root(self):
        s = IngestionSettings()
        assert s.kb_root.name == "kb_root"

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("KB_DEFAULT_EMBEDDING_MODEL", "nomic-embed-text")
        s = IngestionSettings()
        assert s.default_embedding_model == "nomic-embed-text"


# ---------------------------------------------------------------------------
# SpaceStore tests (LanceDB mocked)
# ---------------------------------------------------------------------------

class TestSpaceStore:
    def test_create_metadata_on_new_space(self, tmp_path: Path):
        with patch("ingestion.space_store.lancedb.connect") as mock_connect:
            mock_connect.return_value = MagicMock()
            from ingestion.space_store import SpaceStore
            store = SpaceStore(kb_root=tmp_path)
            meta = store.load_or_create_metadata(
                space_name="demo",
                description="Demo space",
                embedding_info=EmbeddingModelInfo(
                    name="all-MiniLM-L6-v2", dimension=384
                ),
                chunking_strategy="simple_page_blocks",
            )
        assert meta.space_name == "demo"
        metadata_file = tmp_path / "spaces" / "demo" / "metadata.json"
        assert metadata_file.exists()

    def test_load_existing_metadata(self, tmp_path: Path):
        meta = _make_metadata("existing")
        space_dir = tmp_path / "spaces" / "existing"
        space_dir.mkdir(parents=True)
        (space_dir / "metadata.json").write_text(meta.model_dump_json())

        with patch("ingestion.space_store.lancedb.connect") as mock_connect:
            mock_connect.return_value = MagicMock()
            from ingestion.space_store import SpaceStore
            store = SpaceStore(kb_root=tmp_path)
            loaded = store.load_or_create_metadata(
                space_name="existing",
                description="Will be ignored",
                embedding_info=EmbeddingModelInfo(
                    name="all-MiniLM-L6-v2", dimension=384
                ),
                chunking_strategy="simple_page_blocks",
            )
        assert loaded.description == "A test space"  # original description preserved

    def test_upsert_chunks_creates_new_table(self, tmp_path: Path):
        mock_db = MagicMock()
        mock_db.table_names.return_value = []

        with patch("ingestion.space_store.lancedb.connect", return_value=mock_db):
            from ingestion.space_store import SpaceStore, ChunkRow
            store = SpaceStore(kb_root=tmp_path)
            rows = [
                ChunkRow(
                    chunk_id=str(uuid.uuid4()),
                    document_path="/doc.pdf",
                    page_range="1",
                    section_path="/",
                    content_text="Sample text",
                    content_structured=None,
                    content_type="paragraph",
                    vector=[0.0] * 384,
                )
            ]
            store.upsert_chunks("new_space", rows)
        mock_db.create_table.assert_called_once()

    def test_upsert_chunks_appends_to_existing_table(self, tmp_path: Path):
        mock_table = MagicMock()
        mock_db = MagicMock()
        mock_db.table_names.return_value = ["space_existing"]
        mock_db.open_table.return_value = mock_table

        with patch("ingestion.space_store.lancedb.connect", return_value=mock_db):
            from ingestion.space_store import SpaceStore, ChunkRow
            store = SpaceStore(kb_root=tmp_path)
            rows = [
                ChunkRow(
                    chunk_id=str(uuid.uuid4()),
                    document_path="/doc.pdf",
                    page_range="2",
                    section_path="/",
                    content_text="More text",
                    content_structured=None,
                    content_type="paragraph",
                    vector=[0.1] * 384,
                )
            ]
            store.upsert_chunks("existing", rows)
        mock_table.add.assert_called_once()


# ---------------------------------------------------------------------------
# Pipeline tests (Docling + SentenceTransformer mocked)
# ---------------------------------------------------------------------------

class TestPipeline:
    def _make_mock_docling_result(self):
        """Build a minimal Docling result mock with two text blocks on page 1."""
        block1 = MagicMock()
        block1.to_text.return_value = "Introduction text."
        block2 = MagicMock()
        block2.to_text.return_value = "  "  # should be skipped (blank)
        block3 = MagicMock()
        block3.to_text.return_value = "Section body."

        page = MagicMock()
        page.page_number = 1
        page.text_blocks = [block1, block2, block3]

        doc = MagicMock()
        doc.pages = [page]

        result = MagicMock()
        result.document = doc
        return result

    def test_parse_pdf_to_chunks_skips_blank_blocks(self, tmp_path: Path):
        dummy_pdf = tmp_path / "test.pdf"
        dummy_pdf.write_bytes(b"%PDF-1.4 fake")

        mock_result = self._make_mock_docling_result()

        with patch("ingestion.pipeline.DocumentConverter") as MockConverter:
            MockConverter.return_value.convert.return_value = mock_result
            from ingestion.pipeline import parse_pdf_to_chunks
            chunks = parse_pdf_to_chunks(dummy_pdf)

        # Only 2 non-blank blocks should produce chunks
        assert len(chunks) == 2
        assert all(c.content_type == "paragraph" for c in chunks)
        assert all(c.page_range == "1" for c in chunks)

    def test_embed_chunks_produces_chunk_rows(self):
        chunks = [
            ChunkRecord(
                chunk_id=str(uuid.uuid4()),
                document_path="/doc.pdf",
                page_range="1",
                section_path="/",
                content_text="Hello world",
            )
        ]
        mock_model = MagicMock()
        mock_model.encode.return_value = [[0.1] * 384]

        from ingestion.pipeline import embed_chunks
        rows = embed_chunks(chunks, mock_model)

        assert len(rows) == 1
        assert rows[0].content_text == "Hello world"
        assert len(rows[0].vector) == 384

    def test_run_ingestion_full_flow(self, tmp_path: Path):
        dummy_pdf = tmp_path / "doc.pdf"
        dummy_pdf.write_bytes(b"%PDF-1.4 fake")

        mock_result = self._make_mock_docling_result()
        mock_db = MagicMock()
        mock_db.table_names.return_value = []

        mock_st_model = MagicMock()
        mock_st_model.encode.return_value = [[0.0] * 384, [0.0] * 384]
        mock_st_model.get_sentence_embedding_dimension.return_value = 384

        with (
            patch("ingestion.pipeline.DocumentConverter") as MockConverter,
            patch("ingestion.pipeline.SentenceTransformer", return_value=mock_st_model),
            patch("ingestion.space_store.lancedb.connect", return_value=mock_db),
        ):
            MockConverter.return_value.convert.return_value = mock_result
            from ingestion.pipeline import run_ingestion
            meta = run_ingestion(
                space_name="ci_space",
                description="CI test space",
                pdf_paths=[dummy_pdf],
                kb_root=tmp_path,
            )

        assert meta.space_name == "ci_space"
        assert str(dummy_pdf) in meta.source_manifest
        assert len(meta.ingestion_runs) == 1
        assert meta.ingestion_runs[0].completed_at is not None
        mock_db.create_table.assert_called_once()
