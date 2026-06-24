# Local RAG Developer Tool – Ingestion Pipeline (Skeleton)

This is the initial implementation of the **ingestion/Space creation pipeline** as described in the technical architecture. It is intentionally scoped to ingestion only – no MCP server, retrieval, or UI wiring is included yet.

## Features

- Scans a configured `kb_root/spaces/<space_name>/` folder layout (creates it if missing).
- Uses Docling to parse PDFs into structured documents.
- Applies a simple, section-aware chunking strategy.
- Stores chunks and embeddings into a LanceDB-backed Space store.
- Writes/updates `metadata.json` with basic Space information and source manifest.

## Layout

```text
kb/
└── ingestion/
    ├── __init__.py
    ├── config.py
    ├── models.py
    ├── pipeline.py
    ├── space_store.py
    └── cli.py
```

- `config.py` – environment/config handling (kb_root, default models, etc.).
- `models.py` – pydantic data models for metadata and chunk records.
- `space_store.py` – LanceDB-backed persistence for chunks and metadata.
- `pipeline.py` – orchestration: parse → chunk → embed → write.
- `cli.py` – thin CLI to run ingestion against a Space.

This skeleton is ready to be wired into the future admin console and MCP server.
