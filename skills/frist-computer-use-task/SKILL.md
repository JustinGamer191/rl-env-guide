---
name: frist-computer-use-task
description: Create ACCEPTABLE cross-app computer-use tasks (100 pts each when accepted) in a Frist multi-app "world" built from finished clones, with a seeded reset, a state-based verifier, a scripted Playwright oracle, null and hack agents that score 0, and templates that mint variants fast. Use this whenever Justin says "computer use task", "CUA task", "world task", "multi-app task", "100 point task", mentions Frist's world or verifier format, or when coding-task authoring is blocked and there are parallel slots to fill. Rejected tasks score 0, so run the checklist every time.
---

# Frist computer-use task

A computer-use task: a shared world (several clone apps with seeded data), a natural-language goal, a reset that restores the seed, and a verifier that reads final state and returns a score. It is accepted only if the score is trustworthy. Published audits found 15% of computer-use FAIL verdicts were wrong (evaluator false negatives or broken tasks), and do-nothing or spam agents scored 38 to 40% on tau-bench, so the checklist below targets exactly those failures (`~/Documents/Hackathons/Frist/rl-env-research.md`).

**Frist's world, template and verifier API win.** Discover first: how the world is composed (which clones, ports, docker compose), the seed/fixture and reset mechanism, how a verifier reads state (DB query, internal API, provided helper), and an example task. Put it in DISCOVERY.md. Map our pieces onto their slots; `~/.claude/skills/frist-hackathon-playbook/references/task-formats.md` shows BrowserGym/OSWorld/HUD equivalents. Ask staff if the verifier interface is unclear.

## Known Frist world format (public, verify tomorrow)

From Frist's blog (FristWorld, Oct 17 2026: six cloned sites such as Air Canada, Nordstrom, Zappos, OpenTable with 31 cross-site tasks; MedPractice, Nov 6 2026: NetSuite, Bill.com, Gmail, Sheets clones), summarized in `~/Documents/Hackathons/Frist/frist-intel.md`:
- Each app runs its own backend; a **world ledger** across them tracks state and an event log, and grading deterministically checks final state (tables like `WorldState`, `WorldEvent`, `AuditLog` appeared in samples).
- The agent ends with `report_complete('...')` or `report_infeasible('...')`, so an infeasible task (correct answer: refuse) may be a valid kind; ask staff.
- Good tasks have exactly one correct answer, no hints, and a **trap**: a budget only one flight-and-fare combo fits, "lowest monthly payment, not lowest price", "stop before payment".
- Write checks as atomic sentences: "In Bill, invoice X has nothing scheduled and has a note; in NetSuite, Payment Hold is ticked." Each is one verifier assertion and a natural checkpoint.
- Frist mass-produces variants by changing dates, names and amounts, which fits the templatize step below.

## Point math

100 per accepted task versus 500 per coding task, so these are for idle parallel slots, for when coding tasks are blocked, or when a template makes them very cheap (one good template can mint several accepted variants if Frist accepts variants; ask).

## Designing a good task

- **Cross-app, read A then write B.** "Find the overdue invoice for Acme in the billing app and post its amount and due date in #finance in the chat app." Needing info from one app to act in another is what makes it a world task, not a single-app click.
- **Identify the target uniquely.** By a seeded name or ID, or by a property that matches exactly one record ("the unassigned open issue with the highest estimate"). Avoid "the latest", "recent", "a few"; ambiguity is the top cause of broken tasks.
- **Shapes that work** (all rehearsed): multi-step edit on an entity found by a property; near-twin trap (two urgent items, only the sooner-due one is right); read-then-act (read a total on one page, create a record carrying it); several records to one precise end state with a look-alike that must stay untouched; infeasible (the described entity does not exist, correct answer is `report_infeasible` with zero changes).
- **One correct end state, many paths.** The verifier checks the outcome, never the click path, the agent's final chat message, or UI text.
- **Enough checks to not be trivial.** Frist's MedPractice grades by atomic checks: 8 or fewer is easy, 9 to 19 medium, 20+ hard. Rehearsal tasks with 2 to 6 checks were solved 10/10 by Opus in about 2 to 4 minutes, so aim for medium: one rule applied over several records, a derived-metric trap, or the deciding fact hidden on a page the agent must open.
- **No wall clock, no randomness.** If dates matter, use seeded absolute dates in the goal ("due Nov 3"), not "today".

## Making it hard (rehearsal data, Nov 14)

Single levers did not lower the solve rate for Opus 5.5 or Fable 5.2: date math against the fixed clock, a derived sum or argmax, cross-app rules read from mail, a later correcting email, a look-alike sender, near-twin people and dates. Tasks with 12 to 20 checks across two apps still went 4/4 and 7/7 (3.6 to 8.5 min each); both models read every email, including corrections. What to try instead, stacked in one task:
- Layered amendments: rules spread across several messages, where a later one changes an earlier one and a second later one changes it again.
- Deciding facts that live only in per-item comments or history (who moved it to Done, a "merged to release" comment versus a "will merge" twin), not in list views.
- Branch flips: a late message that switches a record to the less obvious branch and makes the order of actions matter.
Before probing, assert offline that every trap still bites in the seed: run each "plausible mistake" against the expected state, and if it produces the same end state, it is not a trap; drop or redesign it. Then probe (playbook "Difficulty gate"); computer-use tasks are only 100 pts, so if two hardening rounds still give 4/4, ship the best one if Frist's reviewers accept it and move the time to coding tasks.

## Building one task (worker)

1. **Reset.** Confirm the world reset restores the seed exactly (reset, dump relevant tables/API state, reset again, dump, diff: identical). If the world has no reset, write one from fixtures and tell the orchestrator, since all tasks share it. A clone whose `dev.mjs` makes a fresh DB per boot resets by killing its process group and booting again; snapshot the seed from the DB after each boot, since ids and seed timestamps change per boot.
2. **Goal text.** Natural language a user would write, identifying each target uniquely (name, ID or a property only one record has). No hints about which buttons to press unless the task is about UI.
3. **Verifier** reading backend state (DB or API), returning a score in [0,1]. Default recipe (tested, `references/rehearsal-recipe.md` section 2, code in `examples/quillstack-harness/`): normalize the whole domain to stable keys, build `expected = seed + exactly the intended change`, score 1 only if `diff(expected, final)` is empty and the report status is right.
   - Locate the target by stable keys, not by "last row" (the agent may create drafts or extras). Map random ids to natural keys (issue number, email, label name), datetimes to dates, and drop `updatedAt` and activity or notification logs that merely viewing can touch.
   - **Fail closed.** Every intended change is a REQUIRED assertion. A new record or comment that is validated "if present" lets report-complete-and-do-nothing score 1; this happened on 2 of 5 rehearsal tasks and the null agent hid it, because null failed only on the missing report.
   - **Assert seed preconditions inside the verifier**: target unique, trap twin present, infeasible task still infeasible. A seed change then crashes the verifier loudly instead of silently changing the task.
   - Report status is required (`report_complete`, or `report_infeasible` for infeasible tasks); its text is never evidence.
   - Normalize before comparing: trim, case-fold, collapse whitespace, strip currency symbols and thousands separators, parse dates and numbers, compare sets for unordered lists. Accept equivalent valid forms ("$1,200.00", "1200").
   - **Collateral damage check:** snapshot the seed state of relevant tables; after the run, everything except the intended changes must be unchanged (no deleted records, no extra messages to other channels, no edited unrelated items). Any collateral change gives 0.
   - Optional checkpoints for partial credit (TheAgentCompany style: for example 0.5 x checkpoints passed + 0.5 x full success) only if Frist's format supports it.
   - No `eval` of agent-produced text; verifier code and expected values are not readable from inside the world (not served by any app, not in the browser-accessible filesystem, not in seed data). A Vite dev server serves its project root over `/@fs/`, so keep task files outside the app dir and confirm with curl that they return 403.
4. **Oracle.** Scripted solve with Playwright through the UI (preferred, proves the UI path works) or via API if Frist allows. Must score 1. Also script an **alt path** that differs in entry point (list vs board vs search vs keyboard shortcut), order of edits and text format; it must score 1 too. For an infeasible task the alt path opens every candidate, then refuses (viewing must not count as a change).
5. **Adversarial agents**, each must score 0, and each for a STATE reason, not only a missing report (read the verifier's reasons). Drive them through the backend API: they test the verifier, take a second each, and can do what the UI cannot:
   - **Null:** reset, do nothing, verify.
   - **Change everything:** edit or post to every candidate entity (all invoices, all channels) so a lax verifier would find the right value somewhere.
   - **Wrong entity:** do the right action on a near-miss entity (Acme Corp vs Acme Inc, the other overdue invoice).
   - **Answer-only:** `report_complete` with the right answer in its text, state unchanged.
   - **Partial:** one of N records, or one of N fields (priority set, comment missing).
   - **Overwrite and duplicate:** replace a list instead of adding to it (labels), post the required comment twice, edit an existing record instead of creating one.
   - **Collateral:** oracle plus one unrelated change.
   - **Infeasible tasks:** act on the near miss and report complete; make it feasible (add the missing label) and act; act partly, then report infeasible.
6. **Determinism.** Reset, oracle, verify, 3 times: always 1. Reset, null, verify: always 0.
7. **Real-solver probe (orchestrator, after READY).** Two fresh subagents get only the goal, the URL, how to launch Playwright and a report command, each on its own world and port pair, with UI-only rules. Audit each transcript for `evaluate(`, `__app`, `/api/`, curl or sqlite and paths outside its work dir, then verify. A failure from the trap is the intended difficulty; a misread goal means rewrite it. Prompt and runner: `references/rehearsal-recipe.md` section 4.
8. **Templatize.** Turn the task into a function of parameters (entity, target app, value) with goal, verifier expectations and oracle all derived from the same seeded parameters. Mint variants only from parameter combos that are unambiguous in the seed, and run steps 5 and 6 on every variant (cheap, it is scripted).
9. **Package** in Frist's exact template with metadata (apps involved, difficulty).

## Pre-submit checklist (reviewer runs every item, with evidence)

1. Matches Frist's template and verifier interface exactly; their validator passes if one exists.
2. Goal is unambiguous: every named or property-described target matches exactly one record in the seed (asserted in the verifier); a stranger would do the same thing; the real-solver probe shows no misreading.
3. Spans at least two apps of the world (or whatever Frist requires) and needs info from one to act in another.
4. Reset restores state exactly (dump diff is empty).
5. Oracle scores 1 on 3 consecutive reset-run-verify cycles.
6. Null agent scores 0.
7. Change-everything, wrong-entity, answer-only, partial and collateral agents score 0, each for a state reason; the verifier fails closed when the required change is absent.
8. Verifier checks backend state, normalizes values, and accepts alternative valid paths and formats (reviewer tries one alternative path, such as a different UI route or the API, and confirms 1).
9. Collateral damage check present and working (reviewer makes one unrelated extra change after the oracle and confirms the score drops to 0).
10. No leaks: expected values and verifier code unreachable from the agent's browser or filesystem (curl `/@fs/<task path>` on a Vite app returns 403); goal text does not contain the answer.
11. No time or randomness dependence; seeded absolute values only.
12. Different from our other submitted tasks (or, for variants, Frist confirmed variants are accepted).

## Worker prompt template (paste and fill)

```
You are a worker authoring ONE computer-use task (or one template with N variants) for the Frist hackathon. Read <workspace>/DISCOVERY.md first (world composition, ports, seed and reset, verifier API, Frist's task template).
Then read ~/.claude/skills/frist-computer-use-task/SKILL.md and follow "Building one task" exactly.
World: <how to start it, URLs>. Your dir: <workspace>/cu-tasks/<task-id>/ (do not edit the clones or the shared seed; if the world needs a reset script or seed change, stop and report NEEDS-WORLD).
Apps to span: <app A> -> <app B>. Idea: <one line>. Variants wanted: <N or 0>.
Other workers own: <their ideas>; do not overlap. If you run the world yourself, use ports <ports> so you do not collide.

Deliverables, mapped onto Frist's template: goal text, verifier, oracle and alt-path (Playwright scripts), adversarial agents (null, answer-only, change-everything, wrong-entity, partial, collateral, plus the infeasible set if relevant) as scripts, metadata, and a run_checks script that does reset -> agent -> verify for each and prints score plus reasons. Start from ~/.claude/skills/frist-computer-use-task/examples/quillstack-harness/.

Before reporting, run run_checks: oracle = 1 on 3 runs, alt path = 1, every adversarial agent = 0 for a state reason, reset dump diff empty. Iterate until true. Then self-check checklist items 1 to 12.

Report exactly:
STATUS: READY | BLOCKED | NEEDS-WORLD
TASK DIR: <path>
GOAL TEXT: <full text>
SCORES: oracle x3, alt, null, answer-only, change-everything, wrong-entity, partial, collateral (with reasons)
CHECKLIST: <1-12 each ok/not ok with one line of evidence>
NOTES: <risks, anything ambiguous in Frist's format>
```

After READY, the orchestrator runs the real-solver probe (step 7) and launches a fresh reviewer (prompt in frist-hackathon-playbook, "Reviewer subagent prompt") pointed at this skill's checklist. Only PASS gets submitted.

## Shared-world caution

All tasks share the seed. Changing seed data can silently break earlier tasks' verifiers and goals. Seed changes go through one integrator worker; after any seed change, rerun every existing task's run_checks before submitting more.

Each worker boots its own world on its own port pair (one dev server and one headless browser per worker, `nice -n 15`); Chromium refuses port 6000, so avoid it. Kill your world's process group when done.
