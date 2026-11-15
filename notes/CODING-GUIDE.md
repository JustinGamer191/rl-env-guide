# Frist coding guide (condensed from portal, 10:05 Nov 15)
- Unlock: 1 finished clone OR 10 tickets. Limits: 4 active claims, 4 checks running, 4 awaiting review (separate).
- Claim = one cell (clone x shape). Reclaimed if no task scaffolded within 1h, or 3h no commits/review.
- Your line on a clone is serial: next task starts from previous merged task.
- Package (scaffold): bun tools/new-task.ts --clone <clone> --id T1-<name> --repo <clone path> --base origin/main
  1 ticket: plain title; Context (2-3 sentences); Acceptance criteria AC1..ACn (>=3, user-visible behaviour, ONLY place behaviour is stated); Pins (every name tests assert that the task introduces: visible text, test ids, routes, response fields, error strings). Never mention tests/grading; never pin file paths.
  2 hidden tests from outside (bun test unit lane; browser lane = pinned headless Chromium, run twice, flaky = rejected; wait for state, never fixed time)
  3 reference solution passes all
  4 one mutation per AC: bun tools/new-mutation.ts <clone>/<id> AC1 [--save]; tests must catch every one
- Local check in /workspace/gym: bun tools/sync-cases.ts <clone>/<id> (in sync) and bun checks/gate.ts <clone>/<id> -> GREEN. Commit, one task per submission, Submit task on Task tab.
- TaskCheck (1-3 h): static checks; controls (empty=0, reference=1); mutations; tests match ticket; DIFFICULTY = 5 frontier models x 3 attempts, too easy if top two mostly solve; attempt inspection for unfair failures; shortcut attempt (model tries to pass tests without building feature); case review.
- 3 reds in a row -> human reviewer. Accepted = 500.
- Shapes on board: Resilience, Concurrency, AuthZ/tenant, Schema migrations/contract/FFI, Long-horizon (may not merge), Visual & interaction bugs (browser lane), Full-stack bugs, Performance regressions, Propose other (approval ~45 min, 1 pending at a time).
- Base changes (Go service, Redis, queue, GraphQL, more tenants, counters) submitted separately first, no points, engineer approves, then task on top via --after.
- Clones: one request at a time per API process; races only between their two API copies; few roles; no down migrations; no render/memory counters (base change to add).
- Models strong at CRUD, single-file features, boilerplate, textbook algos, cosmetic UI: never make those the hard part.
- Hard: state across many files + 2 services; concurrency/ordering/retries/time zones; system invariants; root cause far from symptom; O(n^2) at scale.
- Rules: work only in your own workspace; tasks must be your own work.
