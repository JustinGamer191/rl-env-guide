"""World control for a two-app generated world (Quillstack tracker + Quillmail). Based on the tested single-app harness.
World control for a generated clone: reset (fresh boot), normalized state snapshot, report channel.
Verifier inputs come only from the backend SQLite DB and the run dir's report.json, never from the browser.
Layout: <ROOT>/app (the clone copy, override with CU_APP), <ROOT>/harness (these files), <ROOT>/runs (outputs).
To port to another clone: change the boot command/ports in World, the DB-path regex, and snapshot()'s table mapping."""
import datetime, json, os, re, shutil, signal, socket, sqlite3, subprocess, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.environ.get("CU_APP", os.path.join(ROOT, "app"))
MAIL = os.path.join(ROOT, "mail")
BUN = os.path.expanduser("~/.bun/bin/bun")
CHROME = os.path.expanduser("~/Library/Caches/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-mac-arm64/chrome-headless-shell")
GUEST = "guest@localhost"


def _sig_group(pgid, sig):
    """killpg, falling back to signaling each member (macOS killpg can return EPERM for bun/vite groups)."""
    try: os.killpg(pgid, sig); return
    except ProcessLookupError: return
    except PermissionError: pass
    out = subprocess.run(["ps", "-A", "-o", "pid=,pgid="], capture_output=True, text=True).stdout
    for line in out.splitlines():
        a = line.split()
        if len(a) == 2 and int(a[1]) == pgid:
            try: os.kill(int(a[0]), sig)
            except (ProcessLookupError, PermissionError): pass


class World:
    def __init__(self, slot, run_dir, seed="v2"):
        self.fport, self.bport, self.mport = 6100 + slot * 10, 6101 + slot * 10, 6102 + slot * 10
        self.url = f"http://127.0.0.1:{self.fport}"
        self.api = f"http://127.0.0.1:{self.bport}"
        self.mail_url = f"http://127.0.0.1:{self.mport}"
        self.run_dir = run_dir
        os.makedirs(run_dir, exist_ok=True)
        for f in ("report.json",):
            p = os.path.join(run_dir, f)
            if os.path.exists(p): os.remove(p)
        for port in (self.fport, self.bport, self.mport):  # a stale server on our port would hand the solver another run's state
            with socket.socket() as so:
                if so.connect_ex(("127.0.0.1", port)) == 0: raise RuntimeError(f"port {port} already in use; pick another slot")
        self.log = os.path.join(run_dir, "dev.log")
        sf = {"v1": ("seed-v1.json", "seed-v1.json"), "v2": ("seed-data.json", "seed.json"), "v3": ("seed-v3.json", "seed-v3.json")}[seed]
        env = {**os.environ, "PORT": str(self.fport), "BACKEND_PORT": str(self.bport), "SEED_FILE": sf[0]}
        self.proc = subprocess.Popen(["nice", "-n", "15", BUN, "dev.mjs"], cwd=APP, env=env, start_new_session=True,
                                     stdout=open(self.log, "w"), stderr=subprocess.STDOUT)
        self.mlog = os.path.join(run_dir, "mail.log")
        self.mproc = subprocess.Popen(["nice", "-n", "15", BUN, "server.mjs"], cwd=MAIL, env={**os.environ, "MAIL_PORT": str(self.mport), "MAIL_SEED": sf[1]},
                                      start_new_session=True, stdout=open(self.mlog, "w"), stderr=subprocess.STDOUT)
        self.db = self.mstate = None
        for _ in range(120):
            time.sleep(0.5)
            txt = open(self.log).read()
            m = re.search(r"database: file:(\S+)", txt)
            if m: self.db = m.group(1)
            m = re.search(r"\[mail\] state: (\S+)", open(self.mlog).read())
            if m: self.mstate = m.group(1)
            if self.db and self.mstate and self._ok(self.api + "/health") and self._ok(self.url + "/app") and self._ok(self.mail_url + "/health"): break
        else:
            self.stop(); raise RuntimeError("world did not boot: " + open(self.log).read()[-800:])
        time.sleep(0.5)
        self.seed = self.final()

    @staticmethod
    def _ok(u):
        try: return urllib.request.urlopen(u, timeout=2).status == 200
        except Exception: return False

    def stop(self):
        for pr in (self.proc, getattr(self, "mproc", None)):
            if pr is None: continue
            _sig_group(pr.pid, signal.SIGTERM)
            try: pr.wait(timeout=10)
            except Exception: _sig_group(pr.pid, signal.SIGKILL)
            time.sleep(1); _sig_group(pr.pid, signal.SIGKILL)  # stragglers (vite, esbuild) left in the group
        if self.db and "quillstack-clone-" in self.db: shutil.rmtree(os.path.dirname(self.db), ignore_errors=True)
        if self.mstate and "quillmail-" in self.mstate: shutil.rmtree(os.path.dirname(self.mstate), ignore_errors=True)

    def final(self): return {"qs": snapshot(self.db), "mail": mail_snapshot(self.mstate)}
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
    cycles = dict(q("select id,name from Cycle"))
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
        "cycles": sorted((name, n, _day(s), _day(e), projects[p]) for (n, name, s, e, p) in q("select number,name,startsAt,endsAt,projectId from Cycle")),
        "users": sorted(q("select email,name,avatarColor,title,bio,timezone from User")),
        "members": sorted((users[u], r) for (u, r) in q("select userId,role from Member")),
        "team": sorted(q("select name,slug,description,inviteCode from Team")),
    }
    c.close()
    return json.loads(json.dumps(out, default=list))  # tuples -> lists, so seed and final compare alike


def mail_snapshot(path):
    """Quillmail state keyed by message id. `read` is dropped: opening a message marks it read (a viewing side effect)."""
    st = json.load(open(path))
    return {m["id"]: {k: m.get(k) for k in ("folder", "starred", "from", "to", "subject", "body", "date", "inReplyTo")} for m in st["messages"]}


def mail_call(w, method, path, body=None):
    req = urllib.request.Request(w.mail_url + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"content-type": "application/json"})
    return json.load(urllib.request.urlopen(req))


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
