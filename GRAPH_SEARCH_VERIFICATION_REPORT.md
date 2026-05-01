# GRAPH_SEARCH_VERIFICATION_REPORT.md

This report provides a comprehensive verification of the **Graph Search / Similar Candidate Engine** implementation against Phase 2 requirements.

## 1. Implemented
- **None**: No component of the graph-based candidate similarity engine is currently implemented in the codebase.

## 2. Partial
- **Candidate Metadata**: The `Candidate` and `CandidateProfile` models capture sufficient structured data (Skills, Experience, Education, Work History) to support a future similarity engine.
- **Deduplication Infrastructure**: The `global_hash` system in `Candidate` model successfully identifies the same person across multiple tenants, providing a foundation for cross-tenant graph relationships.

## 3. Missing
- **Find Similar Candidates**: No API or service exists to find candidates similar to a given candidate ID or profile.
- **Relationship-aware Search**:
    - **Same Companies**: No logic to find candidates who shared employers.
    - **Same Agencies**: No logic to find candidates placed by the same agencies.
    - **Career Trajectory**: No trajectory-based matching (e.g., matching a "Junior dev to Senior" progression).
- **Similarity Engine**:
    - **Vector Foundation**: `pgvector` fields and embedding generation services are entirely missing.
    - **Relationship Enrichment**: No graph database or relationship JOIN logic for "People who worked at X also worked at Y" analysis.
- **Similarity Explanations**: No engine to generate reasons for similarity (e.g., "shared skill cluster", "similar title progression").
- **UI Discoverability**:
    - No "Find Similar" button on candidate profiles.
    - No "Relationship" tab in the sourcing flow for similar candidates.
    - The `CandidateRelations.tsx` UI exists but is focused on CRM lead management, not candidate-to-candidate similarity search.

## 4. Logic Issues
- **Documentation Overpromise**: Architecture docs (`architecture.md`, `module_map.md`) claim `pgvector` similarity search is "Already running" and handles "all graph queries," but no such code exists in the repository.

## 5. Architecture Issues
- **Relational vs. Graph**: The system is currently purely relational (PostgreSQL). To support "Trajectory" and "Placement Pattern" search at scale, a dedicated graph extension (like FalkorDB as mentioned in docs) or complex recursive CTEs are needed, neither of which are present.

## 6. UI / Discoverability Issues
- **Hidden Intelligence**: While the `Intelligence Hub` UI is architecturally ready to show "AI Actions," the `similarity_search` action is not seeded or wired to any frontend component.

## 7. Phase 2 Blockers
1.  **Vector/Embedding Layer**: Implementation of `pgvector` and an embedding service (e.g., Ollama or OpenAI) is a prerequisite for semantic similarity.
2.  **Graph Relationship Logic**: Build the service layer to perform "Shared Employer" and "Shared Agency" lookups across the global candidate pool.
3.  **UI Integration**: Add a "Similar Candidates" panel to the `CandidateWorkbench.tsx` and Job Sourcing views.
