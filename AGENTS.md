# Vytal — Engineering agent instructions

## Mission
Implement approved GitHub issues as small, secure, reviewable changes. Product owner decides product behavior, architecture tradeoffs, cost, privacy policy, release and deployment. Do not ask for approval for ordinary engineering hygiene.

## Source of truth and queue
- GitHub issues are the execution backlog. Pick only issues explicitly marked ready by the owner or coordinator; never treat every open issue as authorized work.
- Read the issue, relevant code and tests before changes. Respect dependencies and avoid overlapping branches.
- Use one issue -> one branch -> one PR targeting master. Link issue in PR. No merge or deploy without explicit owner approval.
- Never invent CI results. Verify GitHub Actions for the exact head SHA and inspect failed job logs.
- When an issue is blocked by an architectural/product decision, document alternatives, recommendation, impact and request a decision. Do not silently change product behavior.

## Mandatory engineering baseline
- AuthN/AuthZ and account isolation on every account-scoped API and data access.
- Input validation, secure defaults, secret handling, no token/PII logging, least privilege.
- Data integrity, migrations, transaction safety, idempotency where applicable, concurrent-request handling.
- Stable contracts and error semantics across backend, Android and web; no mock identities in production.
- Unit, integration and negative-path tests; regression tests for every fixed bug; deterministic CI.
- Small, testable, decoupled modules and business rules isolated from transport/storage.
- Check lint, typecheck, relevant builds, lockfile consistency, tests and CI. Do not bypass failures by disabling checks.
- Do not claim APK/device validation unless performed. No production changes without explicit approval.

## Autonomous execution loop
1. Select an explicitly ready issue with satisfied dependencies.
2. Review implementation and tests; write a concise technical plan in issue or PR if useful.
3. Implement, add regression tests, run checks locally.
4. Commit and push a dedicated branch; create a draft PR via GitHub REST if GraphQL fails.
5. Inspect PR CI; fix failures in scope and rerun until green or genuinely blocked.
6. Report user-visible behavior, risks, test evidence, PR and exact SHA.
7. Stop at PR review; never merge/deploy automatically.
8. Escalate only: product/architecture choice, secret/credential access, permissions requiring human action, external service/cost, destructive changes, or repeated non-recoverable failure.

## GitHub auth troubleshooting
- Never print or commit tokens. Use GitHub App installation token or fine-grained PAT with repository Contents and Pull requests read/write, Issues read/write if needed, Actions read for verification; workflow changes may require additional permission.
- Check authentication identity and repository access; distinguish HTTP 401, 403, 404 and rate limiting.
- For GraphQL Forbidden, attempt supported GitHub REST pull-request endpoint with existing credentials; do not circumvent organization policy.
- If permissions remain insufficient, report the precise operation, status and permission needed.

## Cloud execution requirement
This file contains instructions only. It does not start a persistent Codex worker. A separately authorized Codex Cloud environment or agent runner must be connected to the repository and explicitly configured to dispatch ready issues. Do not claim unattended execution is enabled until a real end-to-end issue -> agent -> PR test succeeds.
