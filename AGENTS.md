# Vytal — Agent Operating Contract

This repository uses a specification-first workflow. All agents must follow the gates below.

## Repository facts
- Default branch: `master` (do not assume `main`).
- Official Android app: `mobile/vytal-app/` (Expo/React Native).
- `mobile/` is a candidate legacy app; do not delete it without evidence and approval.
- Backend: `backend/` (FastAPI). Web: `web/` (Next.js). Pipelines: `pipelines/`.
- Existing product features must be preserved. A fasting controller is proposed, **not yet specified or authorized for implementation**.

## Phases and approval gates
0. INVENTORY: inspect repository read-only. Record architecture, routes, contracts, persistence, tests, security, CI/CD, feature status and uncertainties. Do not change product code.
1. ELEPHANT: create a coherent master product specification, with functional and nonfunctional requirements, acceptance criteria, API/data contracts and migration strategy.
2. GOLDFISH: independently challenge each specification for ambiguity, contradictions, missing cases, security/privacy, testability and implementation risk. Record findings and resolutions.
3. APPROVAL: wait for explicit owner approval of the versioned master specification. No product-code implementation before this gate.
4. IMPLEMENT: break approved specs into small traceable tasks, code in separate branches, add tests, open pull requests. Do not self-merge.
5. RELEASE: production deployment requires separate explicit owner approval.

## Guardrails
- Never push directly to `master`, auto-merge, or deploy to production.
- Never commit secrets, tokens, personal health data or credentials.
- Treat health/fasting phase descriptions as educational estimates, not personalized physiological claims. Include safety, contraindication and uncertainty review in the specification.
- Check user-level authorization on all APIs accepting user IDs.
- Validate tests and lint where available; report what was actually run.
- Do not claim an automated agent or workflow is running unless it is configured and verified.
- Track decisions and unresolved questions in `docs/egm/`.
