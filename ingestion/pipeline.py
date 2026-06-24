from __future__ import annotations

import uuid
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from docling.document_converter import DocumentConverter
from docling.pipeline_options import PipelineOptions
from sentence_transformers import SentenceTransformer

from .config import settings
from .models import ChunkRecord, EmbeddingModelInfo, IngestionRun, SpaceMetadata
from .space_store import ChunkRow, SpaceStore


def parse_pdf_to_chunks(pdf_path: Path) -> List[ChunkRecord]:
    """Very small, section-aware chunking over a single PDF.

    This is intentionally minimal and can later be replaced by a richer
    HybridChunker-style implementation.
    """

    converter = DocumentConverter(
        pipeline_options=PipelineOptions(do_ocr=True, do_table_structure=True)
    )
    result = converter.convert(str(pdf_path))
    doc = result.document

    chunks: List[ChunkRecord] = []
    for page in doc.pages:
        for block in page.text_blocks:
            text = block.to_text()
            if not text.strip():
                continue
            chunk = ChunkRecord(
                chunk_id=str(uuid.uuid4()),
                document_path=str(pdf_path),
                page_range=str(page.page_number),
                section_path="/",  # placeholder for richer hierarchy
                content_text=text,
                content_structured=None,
                content_type="paragraph",
            )
            chunks.append(chunk)

    return chunks


def embed_chunks(
    chunks: Iterable[ChunkRecord], model: SentenceTransformer
) -> List[ChunkRow]:
    texts = [c.content_text for c in chunks]
    vectors = model.encode(texts, show_progress_bar=False)

    rows: List[ChunkRow] = []
    for chunk, vec in zip(chunks, vectors):
        rows.append(
            ChunkRow(
                chunk_id=chunk.chunk_id,
                document_path=chunk.document_path,
                page_range=chunk.page_range,
                section_path=chunk.section_path,
                content_text=chunk.content_text,
                content_structured=chunk.content_structured,
                content_type=chunk.content_type,
                vector=vec.tolist(),
            )
        )
    return rows


def run_ingestion(
    space_name: str,
    description: str,
    pdf_paths: list[Path],
    kb_root: Path | None = None,
) -> SpaceMetadata:
    store = SpaceStore(kb_root=kb_root)
    model = SentenceTransformer(settings.default_embedding_model)

    embedding_info = EmbeddingModelInfo(
        name=settings.default_embedding_model,
        provider="sentence-transformers",
        dimension=model.get_sentence_embedding_dimension(),
    )

    meta = store.load_or_create_metadata(
        space_name=space_name,
        description=description,
        embedding_info=embedding_info,
        chunking_strategy="simple_page_blocks",
    )

    run_id = str(uuid.uuid4())
    run = IngestionRun(
        run_id=run_id,
        started_at=datetime.utcnow(),
        added_documents=[],
        skipped_documents=[],
    )

    all_chunks: List[ChunkRecord] = []
    for pdf in pdf_paths:
        chunks = parse_pdf_to_chunks(pdf)
        if not chunks:
            run.skipped_documents.append(str(pdf))
            continue
        all_chunks.extend(chunks)
        run.added_documents.append(str(pdf))
        meta.source_manifest.append(str(pdf))

    embedded_rows = embed_chunks(all_chunks, model)
    store.upsert_chunks(space_name, embedded_rows)

    run.completed_at = datetime.utcnow()
    meta.last_updated_at = run.completed_at
    meta.ingestion_runs.append(run)
    store.save_metadata(meta)

    return meta
