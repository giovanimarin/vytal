# Phase 2 — Goldfish: independent adversarial review

You are a separate reviewer. Do not assume the Elephant spec is correct.

Read `docs/egm/00-inventory.md`, `docs/egm/01-master-spec.md` and source code. Produce `docs/egm/02-goldfish-review.md`.

Find contradictions, ambiguities, incomplete state machines, missing API and data constraints, security/privacy and health-claim issues, backward compatibility, offline edge cases, timezones, testability, rollout risks and unapproved assumptions. For each finding provide severity, requirement ID, evidence, impact and a concrete resolution or owner question.

Do not modify product code. The spec is not approved until blocking findings are resolved and the owner explicitly signs off.
