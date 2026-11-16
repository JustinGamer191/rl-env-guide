#!/usr/bin/env bash
# Stack-agnostic acceptance check for a SWE-style coding task.
# Every attempt is graded the way a real grader would: start from a fresh copy
# of the broken repo, apply the attempt, then overlay the HIDDEN tests fresh
# (so an attempt that edits or deletes tests gains nothing), then run commands.
#
# Usage:
#   TASK_DIR=path/to/task \
#   F2P_CMD='npx vitest run tests/hidden/pagination.test.ts' \
#   P2P_CMD='npx vitest run --exclude tests/hidden/**' \
#   SETUP_CMD='npm ci --prefer-offline' \
#   RUNS=3 bash verify_task.sh
#
# TASK_DIR layout (adapt names to the target template, then point vars here):
#   repo/            the broken repo exactly as the agent will see it (no hidden tests)
#   solution.patch   oracle fix (git diff relative to repo/)
#   hidden_tests/    files overlaid onto repo/ at grading time, same relative paths
#   hacks/*.patch    cheating attempts (from the hack author, role-prompts.md 3b); each must FAIL
#
# Optional hardening knobs (defaults keep the original behavior plus extra checks):
#   F2P_PASS_REGEX   a passing F2P run must ALSO print this (ERE), e.g. '([3-9]|[1-9][0-9]+) passed'.
#                    Without it, exit code 0 alone counts as a pass, which os._exit(0) can fake.
#   PROTECTED        space-separated globs the ORACLE must not touch (tests, runner config,
#                    import hooks). Hidden test paths are always protected. Hacks touching them
#                    are listed. Set PROTECTED=' ' to disable the default list.
#   AUTO_HACKS=1     also run built-in generic cheats (runner-binary stub, pytest conftest
#                    report rewrite, conftest os._exit(0)). Set 0 to skip.
#   MIN_HACKS=4      warn if fewer hand-written hacks exist.
#
# Exit 0 only if: no leaks, null attempt fails F2P and passes P2P, oracle passes both on
# every run and stays in scope, every hack (hand-written and auto) fails, and no attempt
# rewrites the hidden tests at runtime.
set -u
: "${TASK_DIR:?set TASK_DIR}" "${F2P_CMD:?set F2P_CMD}" "${P2P_CMD:?set P2P_CMD}"
TASK_DIR="$(cd "$TASK_DIR" && pwd)" || { echo "TASK_DIR not found"; exit 2; }  # absolute: patches are applied from inside copies
SETUP_CMD="${SETUP_CMD:-true}"
RUNS="${RUNS:-3}"
F2P_PASS_REGEX="${F2P_PASS_REGEX:-}"
AUTO_HACKS="${AUTO_HACKS:-1}"
MIN_HACKS="${MIN_HACKS:-4}"
DEFAULT_PROTECTED='conftest.py */conftest.py pytest.ini */pytest.ini tox.ini setup.cfg sitecustomize.py */sitecustomize.py usercustomize.py *.pth tests/* test/* */tests/* */test/* __tests__/* */__tests__/* *.test.* *.spec.* test_*.py */test_*.py *_test.py *_test.go jest.config.* jest.setup.* vitest.config.* vitest.setup.* playwright.config.* bunfig.toml .github/*'
PROTECTED="${PROTECTED:-$DEFAULT_PROTECTED}"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/verify_task.XXXXXX")"
FAILS=0
ORACLE_SECS=""
say() { printf '%s\n' "$*"; }
bad() { say "FAIL: $*"; FAILS=$((FAILS+1)); }
now() { perl -MTime::HiRes=time -e 'printf "%.2f\n", time' 2>/dev/null || date +%s; }

fresh() { # $1 = name; copies repo, runs setup
  local d="$WORK/$1"; rm -rf "$d"; { cp -cR "$TASK_DIR/repo" "$d" 2>/dev/null || { rm -rf "$d"; cp -R "$TASK_DIR/repo" "$d"; }; }
  (cd "$d" && eval "$SETUP_CMD") >"$WORK/$1.setup.log" 2>&1 || say "warn: setup failed for $1 (see $WORK/$1.setup.log)"
  printf '%s' "$d"
}
overlay() { [ -d "$TASK_DIR/hidden_tests" ] && cp -R "$TASK_DIR/hidden_tests/." "$1/"; return 0; }
run() { # $1 dir, $2 cmd, $3 log ; returns cmd exit code
  (cd "$1" && eval "$2") >"$3" 2>&1
}
hidden_files() { [ -d "$TASK_DIR/hidden_tests" ] && (cd "$TASK_DIR/hidden_tests" && find . -type f | sed 's#^\./##'); return 0; }
hidden_sum() { # checksum of the overlaid hidden tests inside dir $1
  hidden_files | while read -r f; do [ -e "$1/$f" ] && cksum <"$1/$f" || echo "missing $f"; done
}
# F2P with tamper and evidence checks. Sets F2P_SECS. Returns 0 only on a real pass.
f2p() { # $1 dir, $2 log
  local before after t0 t1 rc
  before=$(hidden_sum "$1"); t0=$(now)
  run "$1" "$F2P_CMD" "$2"; rc=$?
  t1=$(now); F2P_SECS=$(awk -v a="$t0" -v b="$t1" 'BEGIN{printf "%.2f", b-a}')
  after=$(hidden_sum "$1")
  if [ "$before" != "$after" ]; then echo "TAMPER: hidden tests changed during the run" >>"$2"; return 4; fi
  if [ "$rc" -eq 0 ] && [ -n "$F2P_PASS_REGEX" ] && ! grep -Eq "$F2P_PASS_REGEX" "$2"; then
    echo "NO-EVIDENCE: exit 0 but output lacks F2P_PASS_REGEX" >>"$2"; return 3
  fi
  return "$rc"
}
patch_files() { # files a unified diff touches (headers only)
  awk '/^--- /{p=$2; next} /^\+\+\+ /{for(i=0;i<2;i++){f=(i?$2:p); sub(/^[ab]\//,"",f); if(f!="/dev/null"&&f!="") print f}}' "$1" | sort -u
}
is_protected() { # $1 path
  local pat f
  for pat in $PROTECTED; do case "$1" in $pat) return 0;; esac; done
  for f in $(hidden_files); do [ "$1" = "$f" ] && return 0; done
  return 1
}
protected_hits() { patch_files "$1" | while read -r f; do is_protected "$f" && printf '%s ' "$f"; done; return 0; }
apply_patch() { # $1 dir, $2 patch
  (cd "$1" && { git apply --whitespace=nowarn "$2" 2>/dev/null || patch -p1 <"$2"; }) >/dev/null 2>&1
}

# 0. Leak checks: hidden tests, git history, backup files, oracle lines already present
if [ -d "$TASK_DIR/hidden_tests" ]; then
  hidden_files | while read -r f; do
    [ -e "$TASK_DIR/repo/$f" ] && say "FAIL: hidden test $f is visible in repo/"
  done | tee "$WORK/leak.txt"
  [ -s "$WORK/leak.txt" ] && FAILS=$((FAILS+1))
fi
if [ -d "$TASK_DIR/repo/.git" ]; then
  n=$(git -C "$TASK_DIR/repo" rev-list --all --count 2>/dev/null || echo 0)
  [ "${n:-0}" -gt 1 ] && bad "repo/.git has $n commits; agents mine git log --all for the fix (squash to one commit or delete .git)"
  r=$(git -C "$TASK_DIR/repo" for-each-ref 2>/dev/null | wc -l | tr -d ' ')
  [ "${r:-0}" -gt 1 ] && say "warn: repo/.git has $r refs; remove extra branches, tags, remotes, stash and reflog"
fi
bk=$(find "$TASK_DIR/repo" \( -name node_modules -o -name .git \) -prune -o -type f \( -name '*.orig' -o -name '*.rej' -o -name '*.bak' -o -name '*~' -o -name '*.swp' -o -name '*.patch' -o -name '*.diff' \) -print 2>/dev/null | head -5)
[ -n "$bk" ] && bad "backup/patch files in repo/ may leak the fix: $bk"
if [ -f "$TASK_DIR/solution.patch" ]; then
  grep -E '^\+[^+]' "$TASK_DIR/solution.patch" | sed 's/^+[[:space:]]*//' | awk 'length($0)>=30' | sort -u | while IFS= read -r l; do
    grep -rqF --exclude-dir=node_modules --exclude-dir=.git -- "$l" "$TASK_DIR/repo" 2>/dev/null && say "warn: oracle line already present in repo/ (leak or legit reuse?): $l"
  done
fi
[ -z "$F2P_PASS_REGEX" ] && say "warn: F2P counts exit code 0 as a pass. Set F2P_PASS_REGEX (a test-count line) or grade inside a harness that checks a report file, so early exit cannot pass."

# 1. Null attempt (agent does nothing)
d=$(fresh null); overlay "$d"
if f2p "$d" "$WORK/null.f2p.log"; then
  bad "null attempt PASSES F2P (task is trivial or tests do not exercise the bug)"
else
  say "ok: null fails F2P. Confirm it fails on an ASSERTION, not an import/collection/setup error:"
  tail -n 4 "$WORK/null.f2p.log" | sed 's/^/    | /'
  grep -qiE 'ModuleNotFound|ImportError|Cannot find module|command not found|No module named|SyntaxError' "$WORK/null.f2p.log" \
    && bad "null F2P failure looks like an environment/import error, not the bug"
fi
run "$d" "$P2P_CMD" "$WORK/null.p2p.log" || bad "P2P fails on the untouched repo (P2P must be green before the fix; see $WORK/null.p2p.log)"

# 2. Oracle, repeated for determinism; must stay out of tests and grader config
hits=$(protected_hits "$TASK_DIR/solution.patch")
[ -n "$hits" ] && bad "oracle touches protected paths ($hits). The fix must not need test or runner edits; move them to hidden_tests or adjust PROTECTED"
for i in $(seq 1 "$RUNS"); do
  d=$(fresh "oracle$i")
  apply_patch "$d" "$TASK_DIR/solution.patch" || { bad "oracle patch does not apply"; break; }
  overlay "$d"
  f2p "$d" "$WORK/oracle$i.f2p.log" || bad "oracle run $i fails F2P ($WORK/oracle$i.f2p.log)"
  [ -z "$ORACLE_SECS" ] && ORACLE_SECS="$F2P_SECS"
  run "$d" "$P2P_CMD" "$WORK/oracle$i.p2p.log" || bad "oracle run $i fails P2P ($WORK/oracle$i.p2p.log)"
done

# 3. Hacks: each prepared attempt must score 0
judge_attempt() { # $1 name, $2 dir (attempt already applied, overlay not yet)
  local n="$1" d="$2" rc l
  l=$(printf '%s' "$n" | tr -c 'A-Za-z0-9._-' '_')
  overlay "$d"
  f2p "$d" "$WORK/$l.f2p.log"; rc=$?
  if [ "$rc" -eq 4 ]; then bad "$n rewrote hidden tests at runtime and the grader did not notice on its own"; return; fi
  if [ "$rc" -eq 0 ] && run "$d" "$P2P_CMD" "$WORK/$l.p2p.log"; then
    local hint=""
    [ -n "$ORACLE_SECS" ] && awk -v h="$F2P_SECS" -v o="$ORACLE_SECS" 'BEGIN{exit !(o>0.4 && h*4<o)}' && hint=" (F2P took ${F2P_SECS}s vs oracle ${ORACLE_SECS}s: early exit suspected)"
    bad "$n PASSES (verifier is gameable)$hint; see $WORK/$l.f2p.log"
  else
    [ "$rc" -eq 3 ] && say "ok: $n fails (exit 0 without pass evidence)" || say "ok: $n fails"
  fi
}
nh=0
if [ -d "$TASK_DIR/hacks" ]; then
  for h in "$TASK_DIR"/hacks/*.patch; do
    [ -e "$h" ] || continue; n=$(basename "$h" .patch); nh=$((nh+1))
    d=$(fresh "hack-$n")
    apply_patch "$d" "$h" || { say "warn: hack $n did not apply"; continue; }
    hits=$(protected_hits "$h"); [ -n "$hits" ] && say "info: hack $n touches protected paths: $hits"
    judge_attempt "hack $n" "$d"
  done
fi
[ "$nh" -lt "$MIN_HACKS" ] && say "warn: only $nh hand-written hacks (want >= $MIN_HACKS). Run the hack author (rl-coding-task references/role-prompts.md, 3b)."

if [ "$AUTO_HACKS" = "1" ]; then
  # 3a. Runner stub: grading command resolves an executable the agent could overwrite.
  d=$(fresh auto-runner-stub); stubbed=""
  hf=" $(hidden_files | tr '\n' ' ') "
  for w in $F2P_CMD; do
    w=${w#\'}; w=${w%\'}; w=${w#\"}; w=${w%\"}
    for c in "$w" "node_modules/.bin/$w" ".venv/bin/$w" "venv/bin/$w" "bin/$w"; do
      case "$c" in /*|*..*|-*|"") continue;; esac
      case "$hf" in *" $c "*) continue;; esac
      if [ -f "$d/$c" ] && [ -x "$d/$c" ]; then
        printf '#!/bin/sh\necho "Tests: 999 passed, 0 failed"\necho "999 passed"\nexit 0\n' >"$d/$c"; stubbed="$stubbed $c"
      fi
    done
  done
  if [ -n "$stubbed" ]; then judge_attempt "auto-runner-stub ($stubbed )" "$d"
  else say "skip: auto-runner-stub (F2P_CMD runs no executable from inside the repo)"; fi
  # 3b/3c. pytest hooks an agent can drop in the repo root.
  case "$F2P_CMD $P2P_CMD" in *pytest*)
    d=$(fresh auto-conftest-pass)
    printf '\nimport pytest\n@pytest.hookimpl(hookwrapper=True)\ndef pytest_runtest_makereport(item, call):\n    outcome = yield\n    rep = outcome.get_result()\n    rep.outcome = "passed"\n    rep.longrepr = None\n' >>"$d/conftest.py"
    judge_attempt "auto-conftest-pass" "$d"
    d=$(fresh auto-conftest-exit0)
    printf '\nimport os\nos._exit(0)\n' >>"$d/conftest.py"
    judge_attempt "auto-conftest-exit0" "$d"
  ;; esac
fi

say "logs: $WORK"
[ "$FAILS" -eq 0 ] && { say "VERIFY: PASS"; exit 0; } || { say "VERIFY: FAIL ($FAILS problems)"; exit 1; }
