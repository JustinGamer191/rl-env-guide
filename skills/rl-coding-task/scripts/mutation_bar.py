#!/usr/bin/env python3
"""Mutation bar for a SWE-style coding task: are the hidden tests strong enough?

A task's hidden tests are only worth something if they reject wrong fixes. This
script grades candidate repos the way the real grader would (fresh copy, apply
the candidate, overlay hidden tests fresh, run the grading commands) and checks:

  1. null      broken repo as shipped                      -> must FAIL (and P2P alone must PASS on it)
  2. reference broken + solution.patch                      -> must PASS
  3. wrong     broken + each wrong_fixes/*.patch            -> each must FAIL (100% required)
  4. alt       broken + each alt_fixes/*.patch (valid fixes)-> each must PASS (tests not over-fit)
  5. auto      reference with one operator mutated in the files the fix touches
               (or --mutate-files)                          -> kill rate >= --min-auto-score

Auto mutants are limited to --mutate-context lines around the fix hunks (default 25).
Runs whose command exits with an --infra-exit-codes code (default 3: harness could not
start, port busy) are UNGRADED and fail the bar; they are never counted as kills.
Concurrent runs need disjoint --slot-base ranges (and their own MB_PORT_BASE if the
harness supports it). Prefix with `nice -n 15` on a laptop; --jobs 1 or 2.

Survivors of step 5 are printed with their diff. Either they are equivalent
(list their ids in --equivalent FILE) or the tests are missing a check.

Stdlib only. Works for any stack: you supply the commands.

Example (toy node task):
  python3 mutation_bar.py --task-dir task \
      --test-cmd 'node --test "tests/hidden/*.test.mjs"' \
      --p2p-cmd 'node --test "tests/*.test.mjs"' \
      --syntax-cmd 'node --check {file}'

Example (generated app clone, Playwright journeys; {slot} lets parallel jobs pick ports):
  python3 mutation_bar.py --task-dir tasks/ct-3 --jobs 3 \
      --setup-cmd 'bun install --frozen-lockfile' \
      --test-cmd 'PORT_BASE=$((5200+{slot}*10)) bun run hidden/journeys.mjs --feature' \
      --p2p-cmd  'PORT_BASE=$((5200+{slot}*10)) bun run hidden/journeys.mjs --regression' \
      --syntax-cmd 'bunx tsc --noEmit -p . >/dev/null' --max-auto 25

Exit 0 and "MUTATION BAR: PASS" only when every check holds.
"""
import argparse
import concurrent.futures as cf
import json
import os
import random
import re
import queue
import shutil
import signal
import subprocess
import sys
import tempfile

# ---------- operator mutations (one occurrence per mutant) ----------
OPS = [
    ("eq-strict", r"===", "!=="), ("neq-strict", r"!==", "==="),
    ("eq", r"(?<![=!<>])==(?!=)", "!="), ("neq", r"!=(?!=)", "=="),
    ("le-lt", r"<=", "<"), ("ge-gt", r">=", ">"),
    ("lt-le", r"(?<![<=])<(?![<=])", "<="), ("gt-ge", r"(?<![=>-])>(?![>=])", ">="),
    ("and-or", r"&&", "||"), ("or-and", r"\|\|", "&&"), ("nullish-or", r"\?\?", "||"),
    ("py-and-or", r"\band\b", "or"), ("py-or-and", r"\bor\b", "and"),
    ("plus-minus", r"(?<=\s)\+(?=\s)", "-"), ("minus-plus", r"(?<=\s)-(?=\s)", "+"),
    ("mul-div", r"(?<=\s)\*(?=\s)", "/"),
    ("true-false", r"\btrue\b", "false"), ("false-true", r"\bfalse\b", "true"),
    ("True-False", r"\bTrue\b", "False"), ("False-True", r"\bFalse\b", "True"),
    ("drop-not", r"!(?=[A-Za-z_(])", ""), ("py-drop-not", r"\bnot\s+", ""),
    ("int+1", r"(?<![\w.$])(\d+)(?![\w.])", None),  # handled specially
]
SKIP_LINE = re.compile(r"^\s*(//|#|\*|/\*|import\b|from\s+\S+\s+import\b|export\s+\*|$)")


def line_mutants(line):
    """Yield (op_name, occurrence_index, new_line) for one source line."""
    code = line
    for name, pat, rep in OPS:
        for k, m in enumerate(re.finditer(pat, code)):
            if name == "int+1":
                new = code[: m.start()] + str(int(m.group(1)) + 1) + code[m.end():]
            else:
                new = code[: m.start()] + rep + code[m.end():]
            if new != code:
                yield name, k, new
    s = line.strip()
    if s.endswith(";") and not re.match(r"(return|const|let|var|import|export|throw)\b", s):
        indent = line[: len(line) - len(line.lstrip())]
        yield "drop-stmt", 0, indent + "/* mutant: statement removed */\n"


def sh(cmd, cwd, timeout, slot, log):
    """Run in its own process group; on timeout kill the whole group so dev servers die too."""
    cmd = cmd.replace("{slot}", str(slot))
    env = dict(os.environ, MB_SLOT=str(slot), TZ=os.environ.get("TZ", "UTC"))
    p = subprocess.Popen(cmd, shell=True, cwd=cwd, env=env, start_new_session=True,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        out, _ = p.communicate(timeout=timeout)
        code = p.returncode
    except subprocess.TimeoutExpired:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        out, _ = p.communicate()
        out, code = (out or "") + "\n[mutation_bar] TIMEOUT (process group killed)", 124
    with open(log, "a") as f:
        f.write(f"$ {cmd}\n{out}\n[exit {code}]\n")
    return code


def cow_copy(src, dst):
    """Copy a tree, using APFS clonefile (cp -c) when available so node_modules is cheap."""
    for flags in (["-cR"], ["-R"]):
        r = subprocess.run(["cp", *flags, src, dst], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode == 0:
            return
        shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(src, dst, symlinks=True)


def apply_patch(patch, cwd):
    for cmd in (["git", "apply", "--whitespace=nowarn", patch], ["patch", "-p1", "-s", "-i", patch]):
        if subprocess.run(cmd, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
            return True
    return False


def patch_files(patch):
    files = []
    for line in open(patch, encoding="utf-8", errors="replace"):
        m = re.match(r"^\+\+\+ (?:[ab]/)?(\S+)", line)
        if m and m.group(1) != "/dev/null":
            files.append(m.group(1))
    return files


def hunk_ranges(patch):
    """{file: [(start, end)]} of new-side line ranges per hunk."""
    out, cur = {}, None
    for line in open(patch, encoding="utf-8", errors="replace"):
        m = re.match(r"^\+\+\+ (?:[ab]/)?(\S+)", line)
        if m:
            cur = m.group(1); out.setdefault(cur, []); continue
        m = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", line)
        if m and cur:
            st = int(m.group(1)); out[cur].append((st, st + int(m.group(2) or 1) - 1))
    return out


try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--task-dir", required=True)
    ap.add_argument("--test-cmd", required=True, help="F2P grading command, run from the repo root")
    ap.add_argument("--p2p-cmd", default="", help="regression command; a candidate passes only if both pass")
    ap.add_argument("--setup-cmd", default="", help="run once on the base copy (e.g. bun install)")
    ap.add_argument("--tests-dir", default="hidden_tests", help="overlay dir inside task dir")
    ap.add_argument("--wrong-dir", default="wrong_fixes")
    ap.add_argument("--alt-dir", default="alt_fixes")
    ap.add_argument("--mutate-files", default="", help="comma list; default = files solution.patch touches")
    ap.add_argument("--mutate-context", type=int, default=25, help="only mutate lines within N lines of a solution.patch hunk (0 = whole file); whole-file mode mostly measures unrelated endpoints")
    ap.add_argument("--syntax-cmd", default="", help="'{file}' placeholder; non-compiling mutants are discarded")
    ap.add_argument("--equivalent", default="", help="file of auto-mutant ids judged equivalent (ignored)")
    ap.add_argument("--max-auto", type=int, default=40, help="sample at most this many auto mutants (seeded)")
    ap.add_argument("--min-auto-score", type=float, default=0.8)
    ap.add_argument("--no-auto", action="store_true")
    ap.add_argument("--jobs", type=int, default=1, help="parallel candidates; use {slot} in commands for ports")
    ap.add_argument("--slot-base", type=int, default=0, help="first slot number; give concurrent mutation_bar runs disjoint ranges")
    ap.add_argument("--infra-exit-codes", default="3", help="exit codes meaning the harness itself failed (port busy, server did not boot); such runs are reported as UNGRADED, never as a kill")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--json-out", default="")
    a = ap.parse_args()

    T = os.path.abspath(a.task_dir)
    repo, sol, tests = f"{T}/repo", f"{T}/solution.patch", f"{T}/{a.tests_dir}"
    for p in (repo, sol, tests):
        if not os.path.exists(p):
            sys.exit(f"missing {p}")
    work = tempfile.mkdtemp(prefix="mutation_bar.", dir=os.environ.get("TMPDIR"))
    print(f"work dir: {work}")

    base = f"{work}/base"
    cow_copy(repo, base)
    if a.setup_cmd and sh(a.setup_cmd, base, a.timeout, 0, f"{work}/setup.log") != 0:
        print(f"warn: setup failed, see {work}/setup.log")
    ref_tree = f"{work}/reference-tree"
    cow_copy(base, ref_tree)
    if not apply_patch(sol, ref_tree):
        sys.exit("solution.patch does not apply to repo/")

    def grade(name, patches=(), from_ref=False, mutate=None, slot=0, p2p_only=False):
        """Fresh copy -> apply -> (mutate) -> overlay hidden tests -> run. Returns (passed, note)."""
        d = f"{work}/c-{re.sub(r'[^A-Za-z0-9_.-]', '_', name)}"
        cow_copy(ref_tree if from_ref else base, d)
        log = f"{d}.log"
        try:
            for p in patches:
                if not apply_patch(p, d):
                    return None, "patch did not apply"
            if mutate:
                rel, idx, new_line = mutate
                path = f"{d}/{rel}"
                lines = open(path, encoding="utf-8").read().splitlines(keepends=True)
                lines[idx] = new_line if new_line.endswith("\n") else new_line + "\n"
                open(path, "w", encoding="utf-8").writelines(lines)
                if a.syntax_cmd and sh(a.syntax_cmd.replace("{file}", path), d, a.timeout, slot, log) != 0:
                    return None, "unviable (does not compile)"
            subprocess.run(["cp", "-R", f"{tests}/.", f"{d}/"], check=True)
            infra = {int(x) for x in a.infra_exit_codes.split(",") if x.strip()}
            if p2p_only:
                rc = sh(a.p2p_cmd, d, a.timeout, slot, log)
                return (None, f"UNGRADED: harness error exit {rc} (see {log})") if rc in infra else (rc == 0, log)
            rc = sh(a.test_cmd, d, a.timeout, slot, log)
            if rc in infra:
                return None, f"UNGRADED: harness error exit {rc} (see {log})"
            ok = rc == 0
            if ok and a.p2p_cmd:
                rc = sh(a.p2p_cmd, d, a.timeout, slot, log)
                if rc in infra:
                    return None, f"UNGRADED: harness error exit {rc} (see {log})"
                ok = rc == 0
            return ok, log
        finally:
            shutil.rmtree(d, ignore_errors=True)

    free_slots = queue.Queue()
    for k in range(max(1, a.jobs)):
        free_slots.put(a.slot_base + k)

    def with_slot(label, kw):
        slot = free_slots.get()  # a slot is held only while its job runs, so ports never collide
        try:
            return grade(label, slot=slot, **kw)
        finally:
            free_slots.put(slot)

    def run_many(jobs):
        """jobs: list of (label, kwargs). Returns {label: (passed, note)}."""
        res = {}
        with cf.ThreadPoolExecutor(max_workers=max(1, a.jobs)) as ex:
            futs = {ex.submit(with_slot, label, kw): label for label, kw in jobs}
            for f in cf.as_completed(futs):
                res[futs[f]] = f.result()
        return res

    report = {"problems": []}
    bad = report["problems"].append

    # 1-2. null and reference
    first = [("null", {}), ("reference", {"from_ref": True})]
    if a.p2p_cmd:
        first.append(("null-p2p", {"p2p_only": True}))
    r = run_many(first)
    if a.p2p_cmd:
        if r["null-p2p"][0] is None:
            bad(f"P2P on the untouched broken repo could not be graded: {r['null-p2p'][1]}")
        elif not r["null-p2p"][0]:
            bad(f"P2P fails on the untouched broken repo (regression tests touch the bug's path, or flake; log {r['null-p2p'][1]})")
        print(f"P2P on broken repo: {'UNGRADED' if r['null-p2p'][0] is None else 'passes' if r['null-p2p'][0] else 'FAILS'}")
    for k in ("null", "reference"):
        if r[k][0] is None:
            bad(f"{k} could not be graded: {r[k][1]}")
    print(f"null (broken repo): {'UNGRADED' if r['null'][0] is None else 'PASSES' if r['null'][0] else 'fails'}")
    print(f"reference (original code): {'UNGRADED' if r['reference'][0] is None else 'passes' if r['reference'][0] else 'FAILS'}")
    if r["null"][0]:
        bad("null attempt passes: tests do not detect the bug")
    if r["reference"][0] is False:
        bad(f"reference fails the hidden tests (log: {r['reference'][1]})")

    # 3-4. hand-written wrong fixes and alternative valid fixes
    def listdir(sub):
        d = f"{T}/{sub}"
        return sorted(f"{d}/{x}" for x in os.listdir(d) if x.endswith(".patch")) if os.path.isdir(d) else []
    wrong, alt = listdir(a.wrong_dir), listdir(a.alt_dir)
    r = run_many([(f"wrong:{os.path.basename(p)}", {"patches": [p]}) for p in wrong] +
                 [(f"alt:{os.path.basename(p)}", {"patches": [p]}) for p in alt])
    killed = 0
    print(f"\nwrong fixes ({len(wrong)}), each must be KILLED:")
    for p in wrong:
        ok, note = r[f"wrong:{os.path.basename(p)}"]
        if ok is None:
            print(f"  ?? {os.path.basename(p)}: {note}"); bad(f"{os.path.basename(p)}: {note}")
        elif ok:
            print(f"  SURVIVED {os.path.basename(p)}"); bad(f"wrong fix survives: {os.path.basename(p)}")
        else:
            killed += 1; print(f"  killed   {os.path.basename(p)}")
    report["wrong_killed"], report["wrong_total"] = killed, len(wrong)
    if wrong:
        print(f"  wrong-fix kill rate: {killed}/{len(wrong)} = {100*killed/len(wrong):.0f}%")
    if alt:
        print(f"\nalternative valid fixes ({len(alt)}), each must PASS:")
    for p in alt:
        ok, note = r[f"alt:{os.path.basename(p)}"]
        print(f"  {'UNGRADED' if ok is None else 'passes' if ok else 'REJECTED'} {os.path.basename(p)}")
        if ok is None:
            bad(f"{os.path.basename(p)}: {note}")
        elif not ok:
            bad(f"valid alternative fix rejected (tests over-fit to one implementation): {os.path.basename(p)}")

    # 5. auto operator mutants of the reference
    if not a.no_auto:
        files = [f.strip() for f in a.mutate_files.split(",") if f.strip()] or patch_files(sol)
        equiv = set()
        if a.equivalent and os.path.exists(a.equivalent):
            equiv = {l.split("#", 1)[0].strip() for l in open(a.equivalent) if l.split("#", 1)[0].strip()}
        cands, ranges = [], hunk_ranges(sol)
        for rel in files:
            path = f"{ref_tree}/{rel}"
            if not os.path.isfile(path):
                continue
            for i, line in enumerate(open(path, encoding="utf-8").read().splitlines(keepends=True)):
                if SKIP_LINE.match(line):
                    continue
                if a.mutate_context and rel in ranges and not any(st - a.mutate_context <= i + 1 <= en + a.mutate_context for st, en in ranges[rel]):
                    continue
                for op, k, new in line_mutants(line):
                    mid = f"{rel}:{i+1}:{op}:{k}"
                    if mid not in equiv:
                        cands.append((mid, rel, i, line, new))
        random.Random(1115).shuffle(cands)
        cands = cands[: a.max_auto]
        r = run_many([(c[0], {"from_ref": True, "mutate": (c[1], c[2], c[4])}) for c in cands])
        ungraded = [c for c in cands if r[c[0]][1] and str(r[c[0]][1]).startswith("UNGRADED")]
        if ungraded:
            bad(f"{len(ungraded)} auto mutants UNGRADED (harness errors); rerun")
        viable = [c for c in cands if r[c[0]][0] is not None]
        surv = [c for c in viable if r[c[0]][0]]
        score = 1 - len(surv) / len(viable) if viable else 1.0
        report.update(auto_viable=len(viable), auto_killed=len(viable) - len(surv), auto_score=round(score, 3),
                      auto_unviable=len(cands) - len(viable), survivors=[c[0] for c in surv])
        print(f"\nauto mutants of the reference in {', '.join(files)}: "
              f"{len(viable)-len(surv)}/{len(viable)} killed = {100*score:.0f}% "
              f"({len(cands)-len(viable)} unviable discarded; bar {100*a.min_auto_score:.0f}%)")
        for c in surv:
            print(f"  SURVIVED {c[0]}\n    - {c[3].strip()}\n    + {c[4].strip()}")
        if surv:
            print("  -> add a check that kills each survivor, or list its id in --equivalent if it cannot change behavior")
        if score < a.min_auto_score:
            bad(f"auto mutation score {100*score:.0f}% below bar {100*a.min_auto_score:.0f}%")

    if a.json_out:
        json.dump(report, open(a.json_out, "w"), indent=1)
    print()
    for p in report["problems"]:
        print(f"FAIL: {p}")
    if report["problems"]:
        print(f"MUTATION BAR: FAIL ({len(report['problems'])} problems)")
        sys.exit(1)
    print("MUTATION BAR: PASS")


if __name__ == "__main__":
    main()
