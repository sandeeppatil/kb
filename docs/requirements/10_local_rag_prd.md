# Product Requirements Document: Local RAG Developer Tool

## 1. Executive Summary
This document specifies the requirements for a local, privacy-first Retrieval-Augmented Generation (RAG) system tailored for technical research and code generation. The system leverages Docling for layout-aware document ingestion and the Model Context Protocol (MCP) to serve intelligent context directly into IDEs like VS Code (via Copilot) and Claude. The architecture emphasizes high retriever speed, multi-modal structure preservation, and seamless sharing of isolated knowledge bases ("spaces") across development teams.

**Example Scenario:** A developer querying "What are the safety requirements in ISO 26262 Part 6?" gets an instant, context-aware answer injected directly into their VS Code Copilot Chat, sourced from a pre-processed, team-shared "Automotive Standards Space" without any documents ever leaving the developer's laptop.

## 2. Terminology & Core Concepts
- **Space:** An isolated, domain-specific knowledge base consisting of a file-based vector database (e.g., LanceDB or Chroma) and a metadata manifest.
- **MCP Server:** A local service implementing the Model Context Protocol that acts as the bridge between IDE clients and the Vector Spaces.
- **Docling:** An IBM-developed document processing tool used to parse complex layouts (nested tables, images, paragraphs) into structured chunks.
- **Local Embedder:** A locally hosted embedding engine (e.g., using Ollama or HuggingFace local pipelines) ensuring zero data egress.

## 3. System Architecture
The system consists of two primary interfaces designed to run locally, ensuring data privacy and low latency.

### 3.1. Interface 1: Document Ingestion Pipeline
**Purpose:** Transform complex raw PDFs (e.g., technical ISOs, research papers) into structured, queryable vectors.
- **Environment:** Runs as a dedicated CLI tool or Docker container to manage system dependencies (e.g., OCR libraries) and ensure environment consistency.
- **Parsing Engine:** Uses `Docling` to extract structured components (headers, lists, tables) rather than flattening into plain text.
- **Chunking Strategy:** Implements logical, hierarchy-aware chunking (e.g., via LangChain's `DoclingLoader` and `HybridChunker`). 
  - **Tables:** Preserves nested tables as structured hierarchical units.
  - **Multi-modal:** Extracts and maintains local references to images and figures.
- **Storage:** Writes outputs directly to a local, file-based vector database (LanceDB is preferred for handling multi-modal data efficiently) designated as a specific "Space", and supports repeated ingestion runs that append more PDFs into an existing Space.

### 3.2. Interface 2: Retrieval & MCP Server
**Purpose:** Expose "Spaces" to AI coding clients and dynamically route queries.
- **Protocol:** Fully implements the Model Context Protocol (MCP) with tools for searching specific spaces.
- **Client Integration:** Connects seamlessly with GitHub Copilot Chat (VS Code), Claude Desktop, and Open Code.
- **Routing Engine:** Reads space metadata to expose descriptions to the client LLM, enabling the LLM to choose the correct space for a user's query dynamically.
- **Dynamic Retrieval Pipeline:** Instantiates the correct local embedding model on the fly based on the chosen Space's metadata to ensure compatibility.

## 4. Functional Requirements & Verification Criteria

### 4.1. Space Management & Sharing
- **F-1.1:** The system MUST allow the creation of multiple isolated Spaces for different sets of input data.
- **F-1.2:** Each Space MUST be stored as portable file(s) (e.g., a LanceDB folder + `metadata.json`).
- **F-1.3:** Spaces MUST be shareable across teams (e.g., via Git LFS, shared drives, or S3) without requiring re-computation.
- **F-1.4:** Space metadata MUST include: short description, embedding model name/version, chunking strategy used, and creation timestamp.
- **F-1.5:** The system MUST allow an existing Space to be updated by ingesting additional PDFs into that Space without recreating it from scratch.
- **F-1.6:** When a Space is updated, the system MUST preserve existing indexed content, refresh affected vector and keyword indices, and record the update in Space metadata or ingestion history.

**Example:** A team creates an "HR Policies" space and an "API Docs" space. They commit the isolated space directories to Git LFS. New developers clone the repo and can immediately query API documentation locally without running the ingestion pipeline. Later, the API team adds a new PDF release note to the existing `API Docs` space. The ingestion pipeline appends the new content, refreshes the indices, and makes the new material searchable without rebuilding the entire Space.

Here is an example structure of a root knowledge base folder containing these two spaces:

```text
kb_root/
└── spaces/
    ├── hr_policies_space/
    │   ├── metadata.json                 # Space details: model, version, description
    │   └── lancedb_store/                # LanceDB vector and full-text data
    │       ├── data/                     # Subdirectory for raw vector payload
    │       │   └── _1.lance              # Parquet files containing the embedded chunks and text
    │       └── indices/                  # Index files for fast vector and full-text (BM25) search
    │           └── ivf_pq/               # Specific vector indices for fast nearest-neighbor
    └── api_docs_space/
        ├── metadata.json
        └── lancedb_store/
            ├── data/
            │   └── _1.lance
            └── indices/
```

**Verification Criteria:**
- **VC-1.1:** User can initialize two distinct spaces and query them independently without data crossover.
- **VC-1.2:** A space directory copied from Machine A to Machine B is successfully read by Machine B's MCP server without any re-ingestion steps.
- **VC-1.3:** `metadata.json` exists in the space root and validates against a predefined JSON schema.
- **VC-1.4:** User can select an existing Space, add one or more new PDFs, and retrieve newly added content without recreating the Space.
- **VC-1.5:** Existing documents remain queryable after the update, and the Space's metadata or ingestion history reflects the incremental ingestion run.

### 4.2. Ingestion & Chunking
- **F-2.1:** The ingestion pipeline MUST process PDFs using Docling, supporting text, tables, and images.
- **F-2.2:** Chunking MUST be logical (by paragraph, section, or structural element) rather than fixed-size character splitting.
- **F-2.3:** Nested and simple tables MUST be extracted while retaining their row/column semantic structure (e.g., formatted as Markdown or HTML within the chunk).
- **F-2.4:** The ingestion pipeline MUST support append-mode ingestion for an existing Space, including duplicate-file detection or warning before new chunks are written.

**Example:** When ingesting a 100-page hardware manual, a pinout configuration table spanning two pages is ingested as a complete, logically linked entity rather than being split arbitrarily at the 1,000-character mark. If the team later adds an appendix PDF to the same manual Space, the system appends only the new document content and updates the existing indices.

**Verification Criteria:**
- **VC-2.1:** System successfully ingests a standard, layout-heavy test PDF (e.g., an IEEE paper) and populates the vector store without crashing.
- **VC-2.2:** Inspecting the generated chunks reveals that text boundaries align with structural elements (headers, paragraphs) consistently.
- **VC-2.3:** A complex table embedded in the output retains identifiable structure enabling an LLM to accurately answer granular tabular questions (e.g., "What is the voltage for Pin 4?").
- **VC-2.4:** Running ingestion a second time against the same Space with one new PDF and one already ingested PDF results in newly indexed content plus a duplicate warning or skip for the repeated file.

### 4.3. Retrieval & Routing
- **F-3.1:** The MCP server MUST read all available Space metadata on startup and expose them as descriptive Tools or Resources to the client.
- **F-3.2:** The retriever MUST detect the embedding model from the Space metadata and verify it is loaded before attempting similarity search.
- **F-3.3:** The retriever MUST support hybrid search (Vector + BM25 keyword matching) to improve accuracy on exact technical terms.

**Example:** If a user asks Claude Desktop "How do I authenticate with the billing API?", the MCP Server provides tools representing available spaces. The client LLM reads the tool descriptions and autonomously selects the `search_api_docs_space` tool over the `search_hr_policies_space` tool.

**Verification Criteria:**
- **VC-3.1:** The MCP server correctly responds to `tools/list` with dynamically generated tools for each local space based on `metadata.json`.
- **VC-3.2:** Search executes without errors matching the embedding dimension of the user query with the stored vector dimensions.
- **VC-3.3:** An exact-match query for a rare ID (e.g., "ERR_CODE_9019") successfully retrieves the correct chunk despite low semantic similarity, demonstrating active Hybrid Search.

## 5. Non-Functional Requirements
- **Privacy:** 100% local execution. No document data or user queries should leave the local machine.
  - *VC-NFR-1:* Running the entire pipeline (ingestion and retrieval) with the machine disconnected from the internet results in no degradation of capability.
- **Performance:** Optimized for low-latency vector similarity search to minimize chat lag.
  - *VC-NFR-2:* Time-to-retrieval for a semantic query against a local space containing 10,000 chunks is under 300ms.
- **Compatibility:** Built with Python, leveraging standard open-source libraries (e.g., LangChain, LanceDB).

## 6. Known Challenges & Mitigation Strategies
1. **Container Networking (if Docker is used):** When triggering workflows or connecting via tools like n8n, use `host.docker.internal` to prevent `localhost` resolution errors.
2. **Table Embedding Quality:** Instead of exclusively embedding raw tabular text, embed AI-generated summaries of tables while storing the raw Markdown table structure in the metadata payload for faithful reconstruction upon retrieval.
3. **Corpus Scale & Keyword Importance:** For technical PDFs, dense semantic search often fails on arbitrary part numbers. **Strategy:** Enforce Hybrid Vector RAG (Vector + BM25) within the space retriever, heavily weighting BM25 for queries containing numbers, hyphens, or uppercase IDs.
4. **Embedding Model Drift:** If a locally shared space expects an embedding model that the user hasn't downloaded (e.g., `nomic-embed-text`), retrieval will fail. **Strategy:** The MCP server should auto-detect missing local models and either prompt the user or automatically pull them via Ollama.
