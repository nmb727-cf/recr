# ICC AI Interview Refactor 01

## Scope
- Module: `ICC-AI-INTERVIEW-ENGINE-01`
- Placement: `Interview Command Center -> Interview Types -> AI Interviews`
- Route preserved: `/interviews/types/ai-interviews`

## Refactor Checks
- `Types`, `Templates`, `Prompt Sets`, `Evaluation`, and `Usage` are split into separate sub-navigation areas.
- `Templates` hold runtime configuration only.
- `Prompt Sets` hold opening prompt, AI instruction shell, ordered questions, follow-up shell, expected answer guidance, evaluation dimensions, and skill tags.
- `Evaluation` holds AI/manual assessment settings.
- `Usage` holds flow and decision-rule placement.
- Candidate preview shows question sequence and response mode, not only decorative summary data.

## Validation
- Verified no route break for `/interviews/types/ai-interviews`.
- Verified template list and AI type list still load from existing APIs.
- Verified save path remains on template API and preserves compatibility metadata shell.
- Verified `npm run build` passes.

## Risks / Notes
- Prompt Set persistence is separated in UX and metadata structure, but still stored inside the template record because there is no dedicated backend prompt-set entity yet.
- Usage page shows detected flow usage by AI interview type and supports linked flow/stage/decision configuration in metadata.
