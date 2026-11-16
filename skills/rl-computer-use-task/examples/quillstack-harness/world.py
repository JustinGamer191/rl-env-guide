"""World control for a generated clone: reset (fresh boot), normalized state snapshot, report channel.
Verifier inputs come only from the backend SQLite DB and the run dir's report.json, never from the browser.
Layout: <ROOT>/app (the clone copy, override with CU_APP), <ROOT>/harness (these files), <ROOT>/runs (outputs).
To port to another clone: change the boot command/ports in World, the DB-path regex, and snapshot()'s table mapping."""
import datetime, json, os, re, shutil, signal, sqlite3, subprocess, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.environ.get("CU_APP", os.path.join(ROOT, "app"))
BUN = os.path.expanduser("~/.bun/bin/bun")
CHROME = os.path.expanduser("~/Library/Caches/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell")
GUEST = "guest@localhost"


class World:
    def __init__(self, slot, run_dir):
        self.fport, self.bport = 6010 + slot * 10, 6011 + slot * 10
        self.url = f"http://127.0.0.1:{self.fport}"
        self.api = f"http://127.0.0.1:{self.bport}"
        self.run_dir = run_dir
        os.makedirs(run_dir, exist_ok=True)
        for f in ("report.json",):
            p = os.path.join(run_dir, f)
            if os.path.exists(p): os.remove(p)
        self.log = os.path.join(run_dir, "dev.log")
        env = {**os.environ, "PORT": str(self.fport), "BACKEND_PORT": str(self.bport)}
        self.proc = subprocess.Popen(["nice", "-n", "15", BUN, "dev.mjs"], cwd=APP, env=env, start_new_session=True,
                                     stdout=open(self.log, "w"), stderr=subprocess.STDOUT)
        self.db = None
        for _ in range(120):
            time.sleep(0.5)
            txt = open(self.log).read()
            m = re.search(r"database: file:(\S+)", txt)
            if m: self.db = m.group(1)
            if self.db and self._ok(self.api + "/health") and self._ok(self.url + "/app"): break
        else:
            self.stop(); raise RuntimeError("world did not boot: " + open(self.log).read()[-800:])
        time.sleep(0.5)
        self.seed = snapshot(self.db)

    @staticmethod
    def _ok(u):
        try: return urllib.request.urlopen(u, timeout=2).status == 200
        except Exception: return False

    def stop(self):
        try: os.killpg(self.proc.pid, signal.SIGTERM)
        except ProcessLookupError: pass
        try: self.proc.wait(timeout=10)
        except Exception:
            try: os.killpg(self.proc.pid, signal.SIGKILL)
            except ProcessLookupError: pass
        if self.db and "quillstack-clone-" in self.db: shutil.rmtree(os.path.dirname(self.db), ignore_errors=True)

    def final(self): return snapshot(self.db)
    def report(self):
        p = os.path.join(self.run_dir, "report.json")
        return json.load(open(p)) if os.path.exists(p) else None

    # REST helper for adversarial agents (they test the verifier, not the UI)
    def call(self, method, path, body=None):
        if not hasattr(self, "_tok"):
            r = urllib.request.urlopen(urllib.request.Request(self.api + "/api/demo/session", method="POST", data=b"{}"))
            self._tok = json.load(r)["token"]
        req = urllib.request.Request(self.api + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                     headers={"Authorization": "Bearer " + self._tok, "content-type": "application/json"})
        return json.load(urllib.request.urlopen(req))


def report(run_dir, status, text):
    assert status in ("complete", "infeasible")
    json.dump({"status": status, "text": text}, open(os.path.join(run_dir, "report.json"), "w"))


def _day(ms): return None if ms is None else datetime.datetime.fromtimestamp(ms / 1000, datetime.timezone.utc).date().isoformat()


def snapshot(db):
    """Normalized, id-free view of the domain tables. Random cuids are mapped to stable keys
    (issue number, project key, label name, user email, cycle number); datetimes to UTC dates;
    updatedAt and the Activity/Notification logs are excluded (UI side effects, not outcomes)."""
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    q = lambda s: c.execute(s).fetchall()
    users = dict(q("select id,email from User"))
    labels = dict(q("select id,name from Label"))
    cycles = dict(q("select id,number from Cycle"))
    projects = dict(q("select id,key from Project"))
    issue_num = dict(q("select id,number from Issue"))
    issues = {}
    for (iid, pid, num, title, desc, status, prio, aid, cid, cyc, par, est, due, created) in q(
            "select id,projectId,number,title,description,status,priority,assigneeId,creatorId,cycleId,parentId,estimate,dueDate,createdAt from Issue"):
        issues[str(num)] = {"project": projects.get(pid), "title": title, "description": desc, "status": status, "priority": prio,
                            "assignee": users.get(aid), "creator": users.get(cid), "cycle": cycles.get(cyc), "parent": issue_num.get(par),
                            "estimate": est, "due": _day(due), "labels": [], "watchers": [], "comments": []}
    for iid, lid in q("select issueId,labelId from IssueLabel"): issues[str(issue_num[iid])]["labels"].append(labels[lid])
    for iid, uid in q("select issueId,userId from Watcher"): issues[str(issue_num[iid])]["watchers"].append(users[uid])
    for iid, aid, body in q("select issueId,authorId,body from Comment"): issues[str(issue_num[iid])]["comments"].append({"author": users[aid], "body": body})
    for i in issues.values():
        i["labels"].sort(); i["watchers"].sort(); i["comments"].sort(key=lambda x: (x["author"], x["body"]))
    out = {
        "issues": issues,
        "labels": sorted(q("select name,color from Label")),
        "projects": sorted(q("select key,name,description,color,icon,archived from Project")),
        "cycles": sorted((n, name, _day(s), _day(e), projects[p]) for (n, name, s, e, p) in q("select number,name,startsAt,endsAt,projectId from Cycle")),
        "users": sorted(q("select email,name,avatarColor,title,bio,timezone from User")),
        "members": sorted((users[u], r) for (u, r) in q("select userId,role from Member")),
        "team": sorted(q("select name,slug,description,inviteCode from Team")),
    }
    c.close()
    return json.loads(json.dumps(out, default=list))  # tuples -> lists, so seed and final compare alike


def diff(a, b, path=""):
    """Every place two normalized snapshots differ, as readable strings."""
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b), key=str):
            if k not in a: out.append(f"{path}/{k}: added")
            elif k not in b: out.append(f"{path}/{k}: removed")
            else: out += diff(a[k], b[k], f"{path}/{k}")
        return out
    return [] if a == b else [f"{path}: {json.dumps(a)[:120]} -> {json.dumps(b)[:120]}"]


def norm_text(s):
    """Case-fold, unify quotes/dashes, drop punctuation, collapse whitespace."""
    s = (s or "").casefold().replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()
