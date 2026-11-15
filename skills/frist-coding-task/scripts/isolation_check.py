#!/usr/bin/env python3
"""Prove a role agent (solver, wrong-fix author, test author, reviewer) did not peek.

Instructions are not enforcement. This checks evidence after the agent finishes:
  1. Transcript: every tool call input (Read paths, Bash commands, Grep/Glob paths, URLs)
     is scanned. A path under a --forbid prefix is a VIOLATION. A path outside every
     --allow prefix is a WARNING (review it). History and upstream lookups
     (git log/show/reflog/blame/stash, gh repo clone, gh api repos, WebFetch/WebSearch
     when --no-network) are VIOLATIONS.
  2. Canaries in what the agent SAW: if any --canary token appears in a tool result,
     the agent read forbidden content, whatever path it used to get there.
  3. Canaries in what the agent WROTE: each --outputs path is grepped for every canary.

Plant canaries before dispatching roles: a unique token in the bug notes and in the
preamble of solution.patch (text before the first 'diff --git' is ignored by git apply),
a comment in every hidden test file and a field in golden files, and a non-functional
comment in the reference copy of each file the fix touches. Never put a canary in the
broken repo the solver gets.

Usage:
  python3 isolation_check.py --transcript ~/.claude/projects/<proj>/<session>/subagents/agent-<id>.jsonl \
      --allow /path/roles/b1/solver --allow ~/.claude/skills \
      --forbid /path/original --forbid /path/tasks --forbid /path/upstream \
      --canary CANARY-TEST-7f3a --canary CANARY-REF-91bc \
      --outputs /path/roles/b1/solver --no-network --upstream-hint toxic-jpg/BuddySplit
Exit 0 and "ISOLATION: CLEAN" only if there are no violations.
"""
import argparse
import json
import os
import re
import subprocess
import sys

PATH_RE = re.compile(r"(?:~|/)[\w.@+\-~]*(?:/[\w.@+\-*]*)*")
HISTORY_RE = re.compile(r"\bgit\b[^|;&\n]*\b(log|show|reflog|blame|stash|cat-file|rev-list|fsck|whatchanged)\b")
UPSTREAM_RE = re.compile(r"\bgh\s+(repo\s+clone|api\s+repos|search\s+code)|\bgit\s+clone\b|github\.com/|raw\.githubusercontent")


def norm(p):
    p = os.path.expanduser(p)
    return os.path.normpath(p) if p.startswith("/") else p


def expand_shell(cmd):
    """Expand VAR=/abs assignments ($VAR, ${VAR}) and resolve relative paths after `cd /abs`.
    Returns extra absolute paths the command touches."""
    vars_ = {}
    for m in re.finditer(r"\b([A-Za-z_]\w*)=([\"']?)([~/][^\s\"';|&)]*)\2", cmd):
        vars_[m.group(1)] = os.path.expanduser(m.group(3))
    for k in sorted(vars_, key=len, reverse=True):
        cmd = cmd.replace("${" + k + "}", vars_[k]).replace("$" + k, vars_[k])
    extra, cwd = [], None
    for seg in re.split(r"&&|\|\||;|\n|\|", cmd):
        toks = seg.strip().split()
        if len(toks) >= 2 and toks[0] in ("cd", "pushd") and toks[1].strip("'\"").startswith(("/", "~")):
            cwd = os.path.expanduser(toks[1].strip("'\""))
            continue
        if cwd:
            for t in toks:
                t = t.strip("'\"")
                if t and not t.startswith(("-", "/", "$", "~")) and re.match(r"^[\w.@+\-/*]+$", t):
                    cand = os.path.normpath(os.path.join(cwd, t.rstrip("*")))
                    if os.path.exists(cand):
                        extra.append(cand)
    return cmd, extra


def walk_strings(x):
    if isinstance(x, str):
        yield x
    elif isinstance(x, dict):
        for v in x.values():
            yield from walk_strings(v)
    elif isinstance(x, list):
        for v in x:
            yield from walk_strings(v)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--allow", action="append", default=[])
    ap.add_argument("--forbid", action="append", default=[])
    ap.add_argument("--canary", action="append", default=[])
    ap.add_argument("--outputs", action="append", default=[])
    ap.add_argument("--no-network", action="store_true", help="any WebFetch/WebSearch/curl to the internet is a violation")
    ap.add_argument("--allow-history", action="store_true", help="role may use git history in its own sandbox (bug author)")
    ap.add_argument("--upstream-hint", default="", help="e.g. owner/repo of the app; any mention in a call is a violation")
    ap.add_argument("--ignore-path", action="append", default=["/dev/null", "/tmp", "/usr", "/bin", "/opt", "/private/var", "/var", "/etc", "/Library/Developer"],
                    help="prefixes never reported as outside-sandbox warnings")
    a = ap.parse_args()

    allow = [norm(p) for p in a.allow]
    forbid = [norm(p) for p in a.forbid]
    ignore = [norm(p) for p in a.ignore_path]
    viol, warn, calls = [], [], 0

    def under(p, prefixes):
        return any(p == q or p.startswith(q.rstrip("/") + "/") for q in prefixes)

    for n, line in enumerate(open(os.path.expanduser(a.transcript), encoding="utf-8", errors="replace")):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        msg = d.get("message") or {}
        content = msg.get("content") if isinstance(msg, dict) else None
        if not isinstance(content, list):
            continue
        for it in content:
            if not isinstance(it, dict):
                continue
            if it.get("type") == "tool_use":
                calls += 1
                name, inp = it.get("name", "?"), it.get("input", {})
                if name in ("SubagentHandback", "SendMessage", "TodoWrite"):
                    continue  # the agent's own report text, not an action
                text = "\n".join(walk_strings(inp))
                short = text.replace("\n", " ")[:160]
                text, extra = expand_shell(text)
                text += "\n" + "\n".join(extra)
                if a.no_network and name in ("WebFetch", "WebSearch"):
                    viol.append(f"call {calls} {name}: network tool used: {short}")
                if HISTORY_RE.search(text) and not a.allow_history:
                    viol.append(f"call {calls} {name}: git history command: {short}")
                if UPSTREAM_RE.search(text) or (a.upstream_hint and a.upstream_hint.lower() in text.lower()):
                    viol.append(f"call {calls} {name}: upstream/source lookup: {short}")
                if a.no_network and re.search(r"\b(curl|wget)\b[^\n]*https?://(?!(localhost|127\.0\.0\.1))", text):
                    viol.append(f"call {calls} {name}: internet fetch: {short}")
                for m in PATH_RE.findall(text):
                    p = norm(m)
                    if len(p) < 3 or not p.startswith("/"):
                        continue
                    if under(p, forbid):
                        viol.append(f"call {calls} {name}: forbidden path {p}: {short}")
                    elif allow and not under(p, allow) and not under(p, ignore):
                        warn.append(f"call {calls} {name}: outside sandbox {p}")
                if re.search(r"(^|[\s'\"=])\.\./", text):
                    warn.append(f"call {calls} {name}: relative parent path: {short}")
            elif it.get("type") == "tool_result":
                seen = "\n".join(walk_strings(it.get("content", "")))
                for c in a.canary:
                    if c in seen:
                        viol.append(f"line {n}: canary {c} appeared in a tool result (agent saw forbidden content)")

    for out in a.outputs:
        for c in a.canary:
            r = subprocess.run(["grep", "-rIl", "--exclude-dir=node_modules", "--exclude-dir=node_modules.nosync", c, out],
                               stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            for f in r.stdout.split():
                viol.append(f"output {f} contains canary {c}")

    print(f"transcript: {a.transcript}\ntool calls scanned: {calls}")
    for w in dict.fromkeys(warn):
        print(f"WARN: {w}")
    for v in dict.fromkeys(viol):
        print(f"VIOLATION: {v}")
    if viol:
        print(f"ISOLATION: VIOLATED ({len(set(viol))}) -> discard this role's output and rerun it")
        sys.exit(1)
    print(f"ISOLATION: CLEAN ({len(set(warn))} warnings to eyeball)")


if __name__ == "__main__":
    main()
