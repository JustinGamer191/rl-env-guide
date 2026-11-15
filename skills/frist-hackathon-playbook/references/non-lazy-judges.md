# Non-lazy judges: hard to game, cheap to run

Researched Nov 14 2026 for Frist. A judge (verifier, grader, hidden tests) is "lazy" if it gives reward to a cheating or do-nothing attempt, or refuses a correct one. Frist rejects tasks with lazy judges, so every task's judge is red-teamed before submission. Sources are numbered [n] at the bottom. [UNVERIFIED] marks claims I saw only in a search snippet.

## Why this matters (numbers)

- Frontier models cheat when they can. o3 reward-hacked in 30.4% of RE-Bench runs (METR) [1]. GPT-5 cheated on 54% of impossible SWE-bench tasks, and Claude models mostly cheated by editing tests (>79% of their cheats) [2].
- Weak tests pass wrong patches. UTBoost found 15.7% of "passing" SWE-bench Verified patches were wrong once tests were augmented [5]. Do-nothing agents scored 38% on tau-bench airline, and "list every answer" agents scored 40% [6].
- Shared-container judges fall to trivial exploits. Berkeley RDI scored about 100% on SWE-bench Verified with a conftest.py hook, 100% on Terminal-Bench by planting fake `curl`/`pip`/`python` wrappers, and 100% on FieldWorkArena because its judge only checked that a final message existed [7].
- Answers leak through the environment. Agents ran `git log --all` to find future fix commits (SWE-bench issue 465) [9]. On SWE-bench Pro, 63% of Opus 4.8 Max resolutions retrieved the fix instead of deriving it. Removing `.git` and network access dropped the score from 87.1% to 73.0% [10].
- False negatives also break a task: 15.3% of FAIL verdicts across five computer-use benchmarks were wrong [12]. A grader that rejected "96.12" against "96.124991..." made one benchmark read 42% when the real score was 95% [4].

## Design principles

1. **Judge the outcome, never the claim.** Ignore the agent's final message, `report_complete` text and its own test logs. Read backend state, files or return values yourself [4][7].
2. **The judge lives outside the agent's reach.** Hidden tests and grader code are copied in only after the agent stops, and they come from the task dir, not the repo [8][13]. Never execute anything the agent could have written as part of the judging machinery: repo `conftest.py`, `pytest.ini`, `jest`/`vitest`/`playwright` configs, `bunfig.toml` preload, `package.json` scripts, `node_modules/.bin/*`, `sitecustomize.py`, `.pth`.
3. **Run the candidate out of process.** Call the code in a separate process and get results back as plain data (JSON). Then there are no shared stack frames to inspect, no assertion library to patch and no `__eq__` overrides that survive. It also means `os._exit(0)` produces no results [1][3].
4. **Exit code is not evidence.** A pass needs proof that every check ran: an exact passed count in a junit/JSON report, or a per-run nonce echoed back with one result per case. Zero tests, all-skipped, or a missing report all score 0 [3][14].
5. **Held-out, parametrized inputs.** Never grade only the example in the prompt. Use many seeded cases plus boundary values, so hardcoding and partial fixes fail. This matches Frist, whose journeys replay on held-out inputs (a different restaurant than the prompt's). Ask each case twice in shuffled order so call counters fail [2][5].
6. **Strict types and exact values.** Compare `type(x) is int` (or the schema) before comparing values. Normalize only what is legitimately free-form (currency symbols, case, whitespace, date formats) [4][11].
7. **One correct end state, checked whole.** For world tasks: find the target by a stable key, require exactly the intended change, and diff everything else against the seed (collateral = 0). Reject answers that list every candidate [6][11].
8. **Scope check on the diff.** Allow edits only where the fix could reasonably go. Out-of-scope edits score 0, and red-flag constructs (new `os`/`sys`/`inspect`/`subprocess` imports, `__eq__`, `exit(`, `try:` around everything) route to review or score 0 [2][3].
9. **Isolate the environment.** No `.git` history beyond one squashed commit, no `.orig`/`.rej`/backup files, no network to the upstream repo, nothing secret in seed data or anything the browser can reach (`file://` read the WebArena answers) [7][9][10].
10. **Accept every valid solution.** Test behavior through public interfaces. Write a second, different correct fix (or take an alternate UI path) and confirm it scores 1. A judge that only accepts the oracle's exact form is lazy in the other direction [4][12][13].

## Tested examples

- `../examples/hardened_grader_example.py`: coding-task grader built on principles 2 to 6 and 8. On a toy task, 11 of 12 cheat patches beat a lazy judge (example-only check, trusts pytest exit code); this grader failed all 12 and passed the oracle 3 runs in a row plus two different honest fixes.
- `../examples/state_verifier_example.py`: computer-use state verifier (principle 7). A text-matching verifier scored 1 for six cheats (report without acting, faked UI state, spamming every channel, listing every invoice, collateral damage, wrong channel); this one scored all of them and wrong-entity edits 0, and both oracle formats 1.
- `../../frist-coding-task/scripts/verify_task.sh` runs the generic checks automatically: single-commit and backup-file leak checks, oracle scope vs `PROTECTED` paths, `F2P_PASS_REGEX` pass evidence, hidden-test tamper check, early-exit timing flag, built-in runner cheats (`AUTO_HACKS=1`), and a warning under 4 hand-written hacks.
