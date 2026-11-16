# Public task formats (map these onto your target format)

The target platform's own template wins when there is one. Use these to recognize what its fields mean and to fill gaps sensibly. Field names below are from public docs; verify against the linked source if one matters.

## SWE-bench instance (coding)
Source: https://www.swebench.com/SWE-bench/api/harness
Fields: `instance_id`, `repo`, `base_commit`, `problem_statement`, `patch` (gold fix, never shown to the agent), `test_patch` (tests added/changed, applied only at grading), `FAIL_TO_PASS` (test ids that must go fail to pass), `PASS_TO_PASS` (test ids that must stay passing), `environment_setup_commit`, `version`.
Grading: apply agent patch, apply test_patch, run tests in docker; resolved iff every F2P passes and every P2P passes.

## SWE-smith instance (synthetic bugs)
Source: https://arxiv.org/html/2504.21798 , https://github.com/SWE-bench/SWE-smith
Same core fields as SWE-bench plus `image_name` (one docker image per repo, not per task). Bug kept only if it breaks at least one previously passing test. Bug methods: LM modify, LM rewrite from signature+docstring, procedural AST edits, PR mirror (revert a real PR). Issue text generated from the diff plus failing-test output, then checked to not leak the fix.

## Harbor / Terminal-Bench 2 task (coding or terminal)
Source: https://docs.harborframework.com/tasks/overview
```
my-task/
  instruction.md     prompt shown to the agent
  task.toml          config (timeouts, resources, metadata)
  environment/       Dockerfile etc.
  solution/solve.sh  oracle
  tests/test.sh      verifier; writes /logs/verifier/reward.txt (or reward.json)
```
Tests are copied in only after the agent finishes, so the agent cannot read or edit them.

## HUD SDK template (computer use or coding)
Source: https://github.com/hud-evals/hud-python
```python
env = Environment(name="x")
@env.template()
async def task(param: str = "a"):
    answer = yield f"prompt using {param}"   # agent runs
    yield 1.0 if check_state(param) else 0.0  # reward
tasks = [task(param=p) for p in ("a", "b")]   # one template mints many tasks
```

## BrowserGym task (web computer use)
Source: https://github.com/ServiceNow/BrowserGym
Task class with `setup(page)` (returns goal + info, seeds state), `validate(page, chat_messages)` (returns reward, done, message, info), `cheat(page)` (scripted oracle solve), `teardown()`.

## OSWorld task JSON (desktop computer use)
Source: https://github.com/xlang-ai/OSWorld (evaluation_examples/)
Fields: `id`, `snapshot`, `instruction`, `source`, `config` (list of setup steps: download, launch, execute, open, sleep), `related_apps`, `evaluator` (`func`, `result` getter, `expected`, optional `postconfig`), `trajectory`.

## Common shape, whatever the wrapper
prompt | initial state + reset | oracle solution | verifier returning 0..1 | metadata (category, difficulty, apps involved). If the target template has a slot you cannot map to one of these, ask its owners.
