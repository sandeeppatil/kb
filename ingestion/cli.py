import argparse
from pathlib import Path

from .pipeline import run_ingestion


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run ingestion for a local RAG Space",
    )
    parser.add_argument("space_name", help="Name of the space to create or update")
    parser.add_argument("description", help="Short description of the space")
    parser.add_argument(
        "--kb-root",
        type=Path,
        default=None,
        help="Root folder for kb_root (defaults to $KB_KB_ROOT or ~/kb_root)",
    )
    parser.add_argument(
        "--pdf",
        type=Path,
        nargs="+",
        required=True,
        help="One or more PDF files to ingest",
    )

    args = parser.parse_args()
    meta = run_ingestion(
        space_name=args.space_name,
        description=args.description,
        pdf_paths=list(args.pdf),
        kb_root=args.kb_root,
    )

    print(f"Ingestion complete for space '{meta.space_name}' at {meta.last_updated_at.isoformat()}")


if __name__ == "__main__":  # pragma: no cover
    main()
