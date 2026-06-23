# Work Breakdown Structure: Local RAG Developer Tool

## 1. Purpose
This WBS decomposes the PRD into delivery phases, work packages, and role-aligned assignments for implementing the Local RAG Developer Tool.

## 2. Delivery Assumptions
- The project is delivered as a local-first Python-based system.
- Scope includes ingestion, portable Spaces, MCP retrieval, and an operational admin UI.
- The WBS assumes a small cross-functional team with shared ownership of documentation and testing.

## 3. Roles
| Role | Responsibility |
| --- | --- |
| Product Owner | Prioritization, requirement decisions, acceptance |
| Tech Lead | System design, interface definitions, technical risk management |
| Backend Engineer | Space management, ingestion orchestration, storage integration |
| ML or Search Engineer | Embeddings, chunking, hybrid retrieval tuning |
| Dev Tools Engineer | MCP server, IDE integration, packaging |
| Frontend Engineer | Admin console UX and state management |
| QA Engineer | Verification planning, test execution, release readiness |

## 4. Phase Summary
| WBS ID | Phase | Outcome |
| --- | --- | --- |
| 1.0 | Project foundation | Approved scope, architecture, and schemas |
| 2.0 | Space management | Portable Space lifecycle implemented |
| 3.0 | Ingestion pipeline | PDF-to-vector workflow operational |
| 4.0 | Retrieval and MCP | Search and IDE integration operational |
| 5.0 | Admin UI | Usable control plane for local operations |
| 6.0 | Validation and hardening | Performance, offline, and portability verified |
| 7.0 | Release readiness | Packaged, documented, and ready for team use |

## 5. Detailed WBS

### 1.0 Project Foundation
| WBS ID | Task | Owner | Dependencies | Deliverable |
| --- | --- | --- | --- | --- |
| 1.1 | Review PRD and confirm MVP scope | Product Owner, Tech Lead | None | Scope baseline |
| 1.2 | Define architecture and component boundaries | Tech Lead | 1.1 | Architecture spec |
| 1.3 | Define `metadata.json` schema | Tech Lead, Backend Engineer | 1.2 | JSON schema draft |
| 1.4 | Select core libraries and packaging approach | Tech Lead, Dev Tools Engineer | 1.2 | Technology decision record |
| 1.5 | Define verification strategy and acceptance matrix | QA Engineer | 1.1 | Test plan |
| 1.6 | Define logging, health checks, and observability standards | Tech Lead, QA Engineer | 1.2 | Observability spec |

### 2.0 Space Management
| WBS ID | Task | Owner | Dependencies | Deliverable |
| --- | --- | --- | --- | --- |
| 2.1 | Implement Space root configuration | Backend Engineer | 1.3 | Config module |
| 2.2 | Implement `space create` workflow | Backend Engineer | 2.1 | Space initialization command |
| 2.3 | Write and validate `metadata.json` against schema | Backend Engineer | 2.2 | Metadata validation logic |
| 2.4 | Implement Space listing and health inspection | Backend Engineer | 2.2 | Space registry service |
| 2.5 | Add portability checks for copied Spaces | Backend Engineer, QA Engineer | 2.3 | Portability validation test |
| 2.6 | Implement source manifest, last-updated tracking, and incremental update support for each Space | Backend Engineer | 2.3 | Space manifest service |

### 3.0 Ingestion Pipeline
| WBS ID | Task | Owner | Dependencies | Deliverable |
| --- | --- | --- | --- | --- |
| 3.1 | Integrate Docling parser | Backend Engineer | 1.4 | Parsing adapter |
| 3.2 | Implement file intake and job orchestration | Backend Engineer | 3.1 | Ingestion service |
| 3.3 | Implement hierarchy-aware chunking | ML or Search Engineer | 3.1 | Chunking module |
| 3.4 | Implement table preservation and image reference handling | ML or Search Engineer | 3.3 | Structured chunk payloads |
| 3.5 | Integrate local embedding runtime | ML or Search Engineer | 1.4 | Embedding adapter |
| 3.6 | Write vectors and payloads to LanceDB | Backend Engineer | 3.3, 3.5 | Storage writer |
| 3.7 | Build lexical index for hybrid search | ML or Search Engineer | 3.6 | BM25 or equivalent index |
| 3.8 | Persist ingestion run logs and summaries | Backend Engineer | 3.2 | Run history module |
| 3.9 | Add containerized ingestion option | Dev Tools Engineer | 3.2 | Docker packaging |
| 3.10 | Implement append-mode ingestion into an existing Space | Backend Engineer | 2.6, 3.6, 3.8 | Incremental ingestion workflow |
| 3.11 | Detect duplicate or previously ingested PDFs before write | Backend Engineer | 2.6, 3.10 | Deduplication guardrail |
| 3.12 | Refresh affected indices and corpus totals after incremental updates | Backend Engineer, ML or Search Engineer | 3.7, 3.10 | Incremental reindex logic |
| 3.13 | Implement health checks for ingestion services | Backend Engineer | 3.2, 1.6 | Ingestion health endpoint or CLI |

### 4.0 Retrieval and MCP
| WBS ID | Task | Owner | Dependencies | Deliverable |
| --- | --- | --- | --- | --- |
| 4.1 | Implement Space discovery on server startup | Dev Tools Engineer | 2.4 | Discovery service |
| 4.2 | Generate MCP tools from Space metadata | Dev Tools Engineer | 4.1 | MCP tool registry |
| 4.3 | Implement query embedding with model compatibility checks | ML or Search Engineer | 3.5, 4.1 | Query embedder service |
| 4.4 | Implement hybrid retrieval pipeline | ML or Search Engineer | 3.6, 3.7, 4.3 | Retriever service |
| 4.5 | Return citations and structured payloads | Dev Tools Engineer | 4.4 | MCP response formatter |
| 4.6 | Implement exact-term weighting heuristics | ML or Search Engineer | 4.4 | Query scoring logic |
| 4.7 | Add missing-model detection and local remediation flow | Dev Tools Engineer | 4.3 | Model guardrail workflow |
| 4.8 | Implement MCP server health checks and basic metrics | Dev Tools Engineer | 4.2, 1.6 | MCP health endpoint or CLI |

### 5.0 Admin UI
| WBS ID | Task | Owner | Dependencies | Deliverable |
| --- | --- | --- | --- | --- |
| 5.1 | Define information architecture and wireframes | Frontend Engineer, Product Owner | 1.2 | UI design spec |
| 5.2 | Implement dashboard and Space list | Frontend Engineer | 2.4 | Dashboard screen |
| 5.3 | Implement Create Space flow | Frontend Engineer | 2.2 | Create Space UI |
| 5.4 | Implement ingestion wizard (including append-mode UI, duplicate detection, and incremental summary) | Frontend Engineer | 3.2, 3.8, 3.10 | Ingestion UI |
| 5.5 | Implement Space Detail and Search Console | Frontend Engineer | 4.4, 4.5 | Validation UI |
| 5.6 | Implement MCP status and configuration screen | Frontend Engineer | 4.2 | MCP operations UI |
| 5.7 | Implement settings and model management screen | Frontend Engineer | 4.7 | Settings UI |
| 5.8 | Integrate UI-level health and status indicators (ingestion, MCP, model availability) | Frontend Engineer | 3.13, 4.8 | Status and alerts UI |

### 6.0 Validation and Hardening
| WBS ID | Task | Owner | Dependencies | Deliverable |
| --- | --- | --- | --- | --- |
| 6.1 | Create layout-heavy PDF test corpus | QA Engineer | 1.5 | Test dataset |
| 6.2 | Verify structural chunk quality | QA Engineer, ML or Search Engineer | 3.3, 3.4 | Chunk inspection report |
| 6.3 | Verify complex table retrieval accuracy | QA Engineer | 4.4 | Table retrieval test results |
| 6.4 | Verify Space portability across machines | QA Engineer | 2.5, 4.2 | Portability test report |
| 6.5 | Verify offline execution end to end | QA Engineer | 3.9, 4.7 | Offline readiness report |
| 6.6 | Benchmark retrieval latency against 10,000 chunks | ML or Search Engineer | 4.4 | Performance report |
| 6.7 | Perform failure-mode testing for missing models and invalid metadata | QA Engineer | 4.7 | Negative test report |
| 6.8 | Verify updating an existing Space with additional PDFs preserves prior data and exposes new content in retrieval | QA Engineer | 3.10, 3.11, 3.12, 4.4 | Incremental update test report |
| 6.9 | Validate observability: ingestion and MCP logs, health checks, and basic metrics behave as specified | QA Engineer | 3.13, 4.8, 1.6 | Observability validation report |

### 7.0 Release Readiness
| WBS ID | Task | Owner | Dependencies | Deliverable |
| --- | --- | --- | --- | --- |
| 7.1 | Write operator documentation | Product Owner, Tech Lead | 5.7, 6.5 | User guide |
| 7.2 | Write developer setup and contribution docs | Tech Lead | 3.9, 4.2 | Developer guide |
| 7.3 | Package local distribution artifacts (CLI via Python package and Docker image for ingestion pipeline) | Dev Tools Engineer | 6.5 | Release bundle |
| 7.4 | Conduct UAT with representative technical corpora | Product Owner, QA Engineer | 7.1 | UAT sign-off |
| 7.5 | Approve v1 release | Product Owner, Tech Lead | 7.4 | Release approval |

## 6. Milestones
| Milestone | Exit Criteria |
| --- | --- |
| M1: Foundation complete | Architecture, schema, test plan, and observability spec approved |
| M2: Space lifecycle complete | Spaces can be created, updated, validated, and copied across machines |
| M3: Ingestion MVP complete | PDFs can be parsed, chunked, embedded, indexed, and appended into existing Spaces |
| M4: Retrieval MVP complete | MCP server exposes Space tools and returns hybrid search results |
| M5: UI MVP complete | Users can manage Spaces, inspect health, and validate retrieval through the admin console |
| M6: Hardening complete | Offline, portability, performance, and observability criteria verified |
| M7: Release ready | Docs, packaging, and UAT sign-off completed |

## 7. Suggested Delivery Sequence
1. Complete foundation work before coding retrieval or UI.
2. Deliver Space management before large-scale ingestion work.
3. Build ingestion and storage before MCP integration.
4. Add the admin UI once backend contracts are stable enough to avoid churn.
5. Reserve explicit time for hybrid search tuning, observability, and portability verification.

## 8. Acceptance Mapping to PRD Verification Criteria
| PRD Area | WBS Coverage |
| --- | --- |
| Space isolation and portability | 2.0, 6.4 |
| Incremental Space updates (F-1.5, F-1.6, F-2.4, VC-1.4, VC-1.5, VC-2.4) | 2.6, 3.10–3.12, 5.4, 6.8 |
| Layout-aware ingestion | 3.1 through 3.4, 6.2 |
| Table preservation | 3.4, 6.3 |
| MCP tool exposure | 4.1, 4.2 |
| Embedding compatibility | 3.5, 4.3, 4.7 |
| Hybrid search | 3.7, 4.4, 4.6 |
| Offline and performance non-functional goals | 6.5, 6.6 |
| Environment and telemetry guarantees | 1.6, 3.13, 4.8, 6.9 |

## 9. Recommended Team Checkpoints
- Weekly architecture and dependency review led by the Tech Lead.
- Twice-weekly ingestion and retrieval quality review for the ML or Search Engineer and QA.
- End-of-milestone demo using a real technical PDF corpus and one copied Space from another machine.