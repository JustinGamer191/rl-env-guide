# RL Environments for Computer-Use and Coding Agents: Frontier Review

Prepared Nov 14 2026 as background for building coding and computer-use RL tasks on app clones. Bracketed numbers point to the source list.

## 1. Landmark environments

| Name | Year | Domain | Tasks | Verifier | Notable trick |
|---|---|---|---|---|---|
| OSWorld [1] | 2024 | Ubuntu/Windows desktop VM | 369 (+43 Win) | Execution-based state scripts (134 functions) | Shared base VM image + per-task file downloads and scripted setup, no per-task snapshot |
| OSWorld-Verified [2] | Jul 2025 | Same | 369 | Same, ~300 evaluator bugs fixed | Fixed evaluators, not tasks, to keep scores comparable; AWS parallel runs in ~1 hr |
| WebArena [3][4] | 2023 | Self-hosted shop, forum, GitLab, CMS | 812 | Functional correctness | Dockerized real open-source apps |
| WebArena-Verified [4] | 2025 | Same | 812 (+137 Hard) | Typed, normalized comparators + backend state checks | Replaced substring match; ~11% fewer false negatives |
| VisualWebArena [5] | 2024 | Classifieds, shopping, Reddit | 910 | Execution-based | Tasks need image understanding |
| WorkArena [6] | 2024 | ServiceNow | 33 templates, 19,912 instances | Programmatic validate | Templated instances give scale |
| AndroidWorld [7] | 2024 | 20 Android apps | 116 parameterized | Reads app/OS state | Per-task init, success check, teardown; unlimited param variants |
| Windows Agent Arena [8] | 2024 | Windows 11 | 154 | Execution-based | 40 parallel Azure VMs, full eval in ~20 min |
| TheAgentCompany [9] | 2024 | Simulated software company (multi-app) | 175 | Checkpoints, execution-based | Partial credit = 0.5 x checkpoints + 0.5 x full success; simulated coworkers |
| tau-bench / tau2 [10][11] | 2024/2025 | Retail, airline, telecom | n/a | Final DB state vs annotated goal | pass^k reliability; tau2 lets the simulated user also act (dual control) |
| Mind2Web [12] | 2023 | 137 real sites | 2,350 | Offline action matching | Breadth over reproducibility |
| MAGI (Chakra) [13] | 2026 | 8 cloned enterprise apps, GUI + MCP | 1,000 (200 test/800 train) | Deterministic rubric checks | One seeded "Company Soul" shared across Slack/Linear/Notion/Grafana clones; median 87 steps |
| CUA-Gym [14] | 2026 | 110 mock web apps | 32,112 tuples | Generated reward functions | Generator writes init+golden state, separate Discriminator writes reward |
| ScaleCUA / VeriGen [15] | 2026 | Live OS in docker | 24k synthesized | Executable rewards | 100+ parallel workers, multi-agent feedback loop |
| SWE-bench [16] | 2023 | Real GitHub issues | (see harness) | FAIL_TO_PASS + PASS_TO_PASS tests in docker | Uses project's own tests |
| SWE-Gym [17] | 2024 | 11 Python repos | 2,438 | Unit tests | Executable runtime per instance |
| R2E-Gym [18] | 2025 | Commits | 8.1K+ | Tests + execution-free verifier (hybrid) | Back-translate commits into tasks, generate tests |
| SWE-smith [19] | 2025 | 128 repos | 50k | Must break passing tests | Synthesizes bugs; one env per repo, not per task |

## 2. Methods

**Task authoring at scale.** Templates plus parameters (WorkArena, AndroidWorld) [6][7]. Shared seeded world so tasks cross apps consistently (MAGI, TheAgentCompany) [13][9]. Agent pipelines that co-generate prompt, initial state, golden state and reward, with the reward written by a different agent than the task (CUA-Gym) [14], or blueprint-first: define valid solution space and verification criteria before building the env (AutoGym) [20]. Mechanize argues for "replication training": have agents recreate existing software [21].

**Coding task synthesis.** SWE-smith injects bugs four ways: LM modify, LM rewrite from signature+docstring, procedural AST edits (flip operators, drop loops), and PR mirror (revert a real PR) [19]. A candidate counts only if it makes at least one passing test fail; an LM then writes an issue from the diff plus failing test output [19]. SWE-bench grading: all FAIL_TO_PASS tests pass and all PASS_TO_PASS still pass [16].

**Reset/reproducibility.** VM base image + scripted setup (OSWorld) [1], VM snapshots in blob storage (WAA) [8], docker per site (WebArena) [3], per-task init/teardown on device state (AndroidWorld) [7], per-repo docker image (SWE-smith) [19].

**Verifiers, tradeoffs.** State-based checks (DB/app state) are cheap and deterministic but miss valid alternatives: rule-based evaluators showed 83.8% precision but 55.9% recall [22]. LLM judges top out near 70% precision vs experts [22] and can be prompt-injected [23][24]. Test-based verifiers are only as good as the tests: SWE-bench Verified has insufficient tests in places [25]. Hybrid (tests + learned verifier) beat either alone in R2E-Gym (51% vs ~42-43%) [18].

**Dense vs binary.** Checkpoint partial credit (TheAgentCompany) [9]; pass^k for reliability [10].

**Documented flaws.**
- 15.3% of FAIL verdicts across five CUA benchmarks were wrong (10.7% evaluator false negatives, 4.7% broken tasks) [26].
- tau-bench: a do-nothing agent scored 38%, a DB-dumping spam agent 40% [25].
- Berkeley RDI reached ~100% on WebArena by reading task configs via `file://`, 100% on SWE-bench Verified via a `conftest.py` hook, 73% on OSWorld by downloading gold files from public URLs [23].
- BenchJack found 219 flaws in 10 benchmarks; 9 of 10 hackable at 90-100%; WebArena and OSWorld patched to 0% in three rounds [24].
- Fixes: isolate agent from evaluator, keep answers secret, no `eval()` on agent output, sanitize judge inputs, adversarially test before release [23][24]; accept all valid solutions and audit checkers against alternatives [26].

## 3. Build checklist

**What gets a task accepted** (synthesized from [24][25][26]):
1. **Clear prompt, one right end state.** Underspecified tasks are a top source of broken tasks [26]. Name exact entities ("Close ticket ENG-142 and post its link in #oncall").
2. **Deterministic reset.** Seed DB from a fixture; reset endpoint restores it; no wall-clock or random IDs in checks [1][7].
3. **Programmatic verifier on backend state**, not UI text or the agent's final message [4][23]. Query the DB/API.
4. **Accept valid alternatives.** Normalize case, whitespace, order; check outcome, not click path [4][26].
5. **Check side effects.** Also assert nothing else changed (catches DB-spamming; cf. tau-bench) [25].
6. **Run the null agents.** Do-nothing must score 0; "do everything" must score 0 [25].
7. **Isolate grader.** Agent cannot reach fixtures, golden answers or the grader via `file://`, API, or repo [23][24].
8. **Oracle solution.** Ship a scripted solve (BrowserGym's `cheat()` pattern) that scores 1 [27].
9. **Not trivial.** Multi-step, ideally needs info from one app to act in another [9][13].

**Cross-app computer-use patterns.** Shared seeded world across clones [13]; "read in app A, write in app B" tasks; checkpointed subgoals for partial credit [9]; parameterize templates to mint variants fast [6][7].

**Coding RL patterns.** On the clone repo: inject a bug (SWE-smith's four methods) [19]; confirm F2P tests fail before and pass with the reference fix, and P2P tests stay green [16][19]; write issue text from failing test output without leaking the diff [19]; hide tests from the agent and block `conftest.py`/test edits [23]; re-run tests from a clean copy of the test files.

**Demo to reviewers.** Show reset, an oracle run scoring 1, a null run scoring 0, an attempted hack scoring 0, and a real model attempt with trace (HUD traces every reward [28]).

## 4. Frameworks

- BrowserGym + AgentLab: Gymnasium web env, `setup/validate/cheat` tasks [27]. https://github.com/ServiceNow/BrowserGym
- HUD SDK: `hud init --template cua`, yield prompt then reward; CDP or VNC [28]. https://github.com/hud-evals/hud-python
- Prime Intellect verifiers + Environments Hub (target v1) [29]. https://github.com/PrimeIntellect-ai/verifiers
- Nous Atropos: async environment microservices [30]. https://github.com/NousResearch/Atropos
- SWE-bench harness for F2P/P2P docker grading [16]. https://www.swebench.com/SWE-bench/api/harness
- Playwright for oracle scripts and DOM checks: https://playwright.dev

## Sources

1. OSWorld. https://os-world.github.io
2. OSWorld-Verified. https://hysenlabs.com/en/projects/xlang-ai-osworld ; https://codepress.dev/benchmarks/osworld-verified
3. WebArena. https://arxiv.org/abs/2307.13854
4. WebArena Verified. https://neurips.cc/virtual/2025/124576
5. VisualWebArena. https://arxiv.org/html/2401.13649v2
6. WorkArena. https://arxiv.org/html/2403.07718v5
7. AndroidWorld. https://arxiv.org/abs/2405.14573v5
8. Windows Agent Arena. https://microsoft.github.io/WindowsAgentArena
9. TheAgentCompany. https://arxiv.org/html/2412.14161v3
10. tau-bench. https://arxiv.org/abs/2406.12045
11. tau2-bench. https://arxiv.org/pdf/2506.07982
12. Mind2Web. https://osu-nlp-group.github.io/Mind2Web
13. Chakra MAGI. https://www.chakra.dev/magi-bench
14. CUA-Gym. https://arxiv.org/abs/2605.25624
15. ScaleCUA. https://arxiv.org/abs/2607.11185
16. SWE-bench harness. https://www.swebench.com/SWE-bench/api/harness
17. SWE-Gym. https://arxiv.org/abs/2412.21139
18. R2E-Gym. https://arxiv.org/pdf/2504.07164
19. SWE-smith. https://arxiv.org/html/2504.21798
20. AutoGym. https://arxiv.org/pdf/2609.22592
21. Mechanize, replication training. https://www.mechanize.work/blog/the-upcoming-gpt-3-moment-for-rl/
22. AgentRewardBench. https://arxiv.org/abs/2504.08942
23. Berkeley RDI, How We Broke Top AI Agent Benchmarks. https://rdi.berkeley.edu/blog/trustworthy-benchmarks-cont/
24. BenchJack. https://arxiv.org/html/2605.12673v1
25. Agentic Benchmark Checklist (ABC). https://arxiv.org/pdf/2507.02825
26. How Benchmarks Mis-Score Computer-Use Agents. https://arxiv.org/html/2607.28367v1
27. BrowserGym. https://github.com/ServiceNow/BrowserGym
28. HUD SDK. https://github.com/hud-evals/hud-python
29. Prime Intellect Environments Hub docs. https://docs.primeintellect.ai/tutorials-environments/environments
30. Atropos. https://github.com/NousResearch/Atropos
