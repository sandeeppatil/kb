# Product Requirements Document: Local RAG Developer Tool

## 1. Executive Summary
This document specifies the requirements for a local, privacy-first Retrieval-Augmented Generation (RAG) system tailored for technical research and code generation. The system leverages Docling for layout-aware document ingestion and the Model Context Protocol (MCP) to serve intelligent context directly into IDEs like VS Code (via Copilot) and Claude. The architecture emphasizes high retriever speed, multi-modal structure preservation, and seamless sharing of isolated knowledge bases ("spaces") across development teams.

## 2. Terminology & Core Concepts
- **Space:** An isolated knowledge base consisting of a file-based vector database (e.g., LanceDB or Chroma) and a metadata manifest.
- **MCP Server:** A local service implementing the Model Context Protocol that acts as the bridge between IDE clients and the Vector Spaces.
- **Docling:** An IBM-developed document processing tool used to parse complex layouts (nested tables, images, paragraphs) into structured chunks.

## 3. System Architecture
The system consists of two primary interfaces running locally via Docker.

### 3.1. Interface 1: Document Ingestion Pipeline
**Purpose:** Transform complex raw PDFs (e.g., technical ISOs, research papers) into structured, queryable vectors.
- **Containerization:** Runs as a dedicated Docker container to manage system dependencies and ensure environment consistency.
- **Parsing Engine:** Uses `Docling` to extract structured components rather than plain text.
- **Chunking Strategy:** Implements logical, hierarchy-aware chunking (e.g., via LangChain's `DoclingLoader` and `HybridChunker`). 
  - **Tables:** Preserves nested tables as structured hierarchical units rather than flattening them.
  - **Multi-modal:** Extracts and maintains references to images and figures.
- **Storage:** Writes outputs directly to a local, file-based vector database (e.g., LanceDB or ChromaDB) designated as a specific "Space".

### 3.2. Interface 2: Retrieval & MCP Server
**Purpose:** Expose "Spaces" to AI coding clients and dynamically route queries.
- **Protocol:** Fully implements the Model Context Protocol (MCP).
- **Client Integration:** Connects seamlessly with GitHub Copilot Chat (VS Code), Claude Desktop, and Open Code.
- **Routing Engine:** Reads space metadata to expose descriptions to the client LLM, enabling the LLM to choose the correct space for a user's query.
- **Dynamic Retrieval Pipeline:** Dynamically instantiates the correct embedding model on the fly based on the chosen Space's metadata to ensure compatibility.
- **Performance:** Optimized for low-latency vector similarity search and accurate multi-modal retrieval.

## 4. Functional Requirements

### 4.1. Space Management & Sharing
- **F-1.1:** The system MUST allow the creation of multiple isolated Spaces for different sets of input data.
- **F-1.2:** Each Space MUST be stored as portable file(s) (e.g., LanceDB or Chroma files + `metadata.json`).
- **F-1.3:** Spaces MUST be shareable across teams (e.g., via Git LFS, shared drives, or S3).
- **F-1.4:** Space metadata MUST include:
  - Short description of contents.
  - Embedding model used.
  - Version information.

### 4.2. Ingestion & Chunking
- **F-2.1:** The ingestion pipeline MUST process PDFs using Docling.
- **F-2.2:** Chunking MUST be logical (paragraph/section boundaries) rather than fixed-size character splitting.
- **F-2.3:** Nested and simple tables MUST be extracted while retaining their row/column structure.

### 4.3. Retrieval & Routing
- **F-3.1:** The MCP server MUST read all available Space metadata and expose descriptions to the client.
- **F-3.2:** The retriever MUST detect the embedding model from the Space metadata and use it to embed the user's query.
- **F-3.3:** The retriever MUST prioritize both execution speed and semantic accuracy.

## 5. Non-Functional Requirements
- **Privacy:** 100% local execution. No document data should leave the local Docker environment.
- **Portability:** Database files must be lightweight enough to sync without complex database migrations.
- **Compatibility:** Built with Python, leveraging LangChain/LangGraph paradigms compatible with existing n8n workflows.

## 6. Known Challenges & Mitigation Strategies
1. **Docker Networking (MCP to n8n):** When triggering workflows or connecting via n8n, use `host.docker.internal` or Docker Compose networks to prevent `localhost` resolution errors.
2. **Table Embedding Quality:** Instead of embedding raw tabular text, embed summaries of tables while storing the raw structure in metadata for faithful reconstruction upon retrieval.
3. **Corpus Scale:** For hundreds of technical PDFs, semantic search may degrade. Consider implementing Hybrid Vector RAG (combining BM25 exact-match search with vector embeddings) within the MCP retriever to handle exact clause references (e.g., "ISO 26262-6").
