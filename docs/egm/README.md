# EGM — Vytal specification workspace

Status: **bootstrap only**. No autonomous execution configured or verified.

## Deliverables
- `00-inventory.md`: evidence-backed as-is inventory and risk register.
- `01-master-spec.md`: Elephant master specification (after inventory).
- `02-goldfish-review.md`: independent critique and resolution log.
- `03-implementation-plan.md`: small tasks linked to approved requirements.

## Current gates
| Gate | Status | Required evidence |
|---|---|---|
| Repository access | Complete | GitHub read/write connection |
| Phase 0 inventory | In progress | Source-code evidence and gaps |
| Master specification | Not started | Product-owner review |
| Goldfish review | Not started | Independent findings and resolutions |
| Approval to implement | **Blocked** | Explicit owner approval |
| Production release | **Blocked** | Separate owner approval |

## Operating procedure
1. Run the inventory prompt from `prompts/00-inventory.md` in a cloud coding agent on `master`, producing documentation changes in its own branch/PR.
2. Review the inventory and resolve blocking questions.
3. Run Elephant, then a separate Goldfish review, iterating until review findings are resolved.
4. Ask the owner to approve the versioned specification.
5. Only then start coding tasks in independent PRs with CI checks.

The prompts are reusable instructions, **not** an installed scheduler, workflow or autonomous cloud worker. Do not claim unattended execution until Codex environment, trigger, permissions and CI are separately configured and tested.
