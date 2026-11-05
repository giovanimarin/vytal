# Phase 0 — Repository inventory (read-only analysis)

You are an auditing agent. Inspect the entire Vytal repository at the selected commit. Do not modify product code, dependencies, configuration, secrets, or deployments. Produce a documentation-only PR containing `docs/egm/00-inventory.md`.

## Scope
1. Identify actual entrypoints, official Android app `mobile/vytal-app/`, legacy candidates, web, backend, pipelines and deployment architecture.
2. Enumerate all API endpoints, methods, authentication/authorization checks, request/response models and mobile/web consumers. Flag routes accepting arbitrary user IDs.
3. Map persistent entities, schemas, migrations, local SQLite vs GCP BigQuery behavior, and data flows. Distinguish implemented code from documentation claims.
4. Inventory current screens, feature status (implemented/partial/unused/unknown), Google Fit integration, readiness calculation and dashboard.
5. Inspect test coverage and CI/CD triggers. Verify default branch `master` versus workflows targeting `main`/`staging`.
6. Identify security/privacy risks without disclosing secrets; pay special attention to development endpoints, CORS, OAuth tokens and personal health data.
7. Evaluate requirements and integration points for a proposed fasting timer, **without implementing it**: start/stop, persisted sessions, states, timezones, notification strategy, and evidence-aware educational explanations.
8. Record risks with severity, code references, uncertainty and a minimal validation plan.

## Required output
- Executive summary and factual evidence table with file paths.
- Architecture and data-flow description.
- Endpoint/consumer matrix.
- Feature inventory for official mobile app.
- Data model and persistence map.
- Security/privacy, CI/CD and test gaps.
- Questions that require owner decisions.
- Recommendations ordered by dependencies, not speculative effort estimates.

Never claim tests passed unless run. Do not implement fasting, alter `master`, merge PRs or deploy.
