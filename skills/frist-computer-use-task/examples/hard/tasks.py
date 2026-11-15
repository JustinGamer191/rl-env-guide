"""Four hard CU tasks on the Quillstack + Quillmail world.
Each task is a rule `plan(seed, **params)` that returns the intended change set. The verifier builds
expected = seed + plan(seed) and requires an empty full diff plus report_complete. Adversaries are the same rule run
with wrong parameters (wrong twin, wrong branch, wrong date cutoff, partial) and applied through the REST APIs, so
every trap the goal sets has a scripted agent that falls into it. Oracle and alt path run the correct plan in the UI."""
import copy, datetime, re
from world import GUEST, diff, norm_text, report, mail_call
import ui2

CLOSED = ("DONE", "CANCELED")
RANK = {"URGENT": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "NONE": 0}
TODAY = datetime.date(2026, 9, 15)
PRIYA, PRIYA_TWIN = "priya.shah@quillstack.dev", "priya.sharma@quillstack.dev"
MARCO = "marco.diaz@quillstack.dev"
LENA, LENA_TWIN = "lena.fischer@quillstack.dev", "lena.fisher@quillstack.dev"


def key(seed, n): return f"{seed['qs']['issues'][n]['project']}-{n}"


def plan_new():
    return {"issues": {}, "comments": {}, "creates": [], "mail": {}}
# issues:   {num: {field: value}}             fields: status, priority, assignee, labels_add
# comments: {num: (display_text, [accepted normalized forms])}   exactly one new comment by the user, required
# creates:  [spec]  spec: project,title_text,title_norm,status,priority,assignee,estimate,due,labels   exactly one, required
# mail:     {message_id: {"folder": "archive"}}


# ------------------------------------------------------------------ verifier (shared)
def new_comments(seed_i, final_i):
    left = list(final_i["comments"])
    for c in seed_i["comments"]:
        if c in left: left.remove(c)
        else: return None
    return left


def verify_plan(seed, final, rep, P):
    e = copy.deepcopy(seed); req = []
    EI, FI = e["qs"]["issues"], final["qs"]["issues"]
    for n, ch in P["issues"].items():
        i = EI[n]
        for f, v in ch.items():
            if f == "labels_add": i["labels"] = sorted(set(i["labels"]) | set(v))
            else: i[f] = v
    for n, (_, ok) in P["comments"].items():
        fi = FI.get(n); new = new_comments(seed["qs"]["issues"][n], fi) if fi else None
        if new is not None and len(new) == 1 and new[0]["author"] == GUEST and norm_text(new[0]["body"]) in ok:
            EI[n]["comments"] = fi["comments"]
        else: req.append(f"required comment on {n} missing or wrong: {new}")
    added = [n for n in FI if n not in seed["qs"]["issues"]]
    if P["creates"]:
        s = P["creates"][0]
        if len(added) == 1:
            f = FI[added[0]]
            want = dict(project=s["project"], status=s["status"], priority=s["priority"], assignee=s["assignee"], estimate=s["estimate"],
                        due=s["due"], labels=sorted(s["labels"]), parent=None, comments=[])
            bad = {k: (f[k], v) for k, v in want.items() if f[k] != v}
            if norm_text(f["title"]) != s["title_norm"]: bad["title"] = (f["title"], s["title_norm"])
            if bad: req.append(f"new issue {added[0]} wrong: {bad}")
            else: EI[added[0]] = f
        else: req.append(f"want exactly 1 new issue, got {added}")
    for mid, ch in P["mail"].items(): e["mail"][mid].update(ch)
    why = diff(e, final)
    if not rep or rep.get("status") != "complete": why.append(f"report={rep and rep.get('status')} want complete")
    return (0.0 if (req or why) else 1.0), req + why


# ------------------------------------------------------------------ executors
class API:
    def __init__(self, w):
        self.w = w; self.iss = {str(i["number"]): i for i in w.call("GET", "/api/issues")["issues"]}
        team = w.call("GET", "/api/teams/" + next(iter(self.iss.values()))["project"]["teamId"])
        self.uid = {m["user"]["email"]: m["userId"] for m in team["members"]}
        self.lid = {l["name"]: l["id"] for l in team["labels"]}; self.pid = {p["key"]: p["id"] for p in team["projects"]}

    def patch(self, n, ch):
        body = {}
        for f, v in ch.items():
            if f == "assignee": body["assigneeId"] = self.uid[v] if v else None
            elif f == "labels_add": body["labelIds"] = [l["labelId"] for l in self.iss[n]["labels"]] + [self.lid[x] for x in v]
            else: body[f] = v
        return self.w.call("PATCH", f"/api/issues/{self.iss[n]['id']}", body)

    def comment(self, n, text): return self.w.call("POST", f"/api/issues/{self.iss[n]['id']}/comments", {"body": text})

    def create(self, s):
        return self.w.call("POST", "/api/issues", {"projectId": self.pid[s["project"]], "title": s["title_text"], "status": s["status"],
                                                   "priority": s["priority"], "assigneeId": self.uid.get(s["assignee"]), "estimate": s["estimate"],
                                                   "dueDate": s["due"], "labelIds": [self.lid[l] for l in s["labels"]]})


def apply_api(w, P, done=True, comment_twice=False):
    a = API(w)
    for n, ch in P["issues"].items(): a.patch(n, ch)
    for n, (text, _) in P["comments"].items():
        a.comment(n, text)
        if comment_twice: a.comment(n, text)
    for s in P["creates"]: a.create(s)
    for mid, ch in P["mail"].items():
        if ch.get("folder") == "archive": mail_call(w, "POST", f"/api/messages/{mid}/archive")
    if done: report(w.run_dir, "complete", "done")


def apply_ui(w, P, route="A", text_variant=None):
    """route A: List filter + drawer, issue order as planned, comment then fields, mail one by one.
    route B: Cmd+K by key, reverse order, fields then comment (Cmd+Enter), bulk mail archive, compose via 'c'."""
    seed = w.seed; users = {u[0]: u[1] for u in seed["qs"]["users"]}
    nums = list(dict.fromkeys(list(P["issues"]) + list(P["comments"])))
    if route == "B": nums.reverse()
    with ui2.pages(w.url, w.mail_url if P["mail"] else None) as (page, mail):
        if P["mail"]:
            subj = {mid: seed["mail"][mid]["subject"] for mid in P["mail"]}
            if route == "A":
                for mid in P["mail"]: ui2.mail_find_and_open(mail, subj[mid]); ui2.mail_archive_open(mail)
            else: ui2.mail_bulk_archive(mail, list(subj.values()))
        for n in nums:
            k = key(seed, n)
            ui2.open_key_list(page, w.url, k) if route == "A" else ui2.open_key_search(page, k)
            ch = P["issues"].get(n, {}); c = P["comments"].get(n)
            text = (text_variant or {}).get(n, c[0]) if c else None
            if route == "A":
                if c: ui2.comment(page, text)
                ui2.set_fields(page, ch, users)
            else:
                ui2.set_fields(page, ch, users, order=("labels_add", "assignee", "priority", "status"))
                if c: ui2.comment(page, text, use_shortcut=True)
            ui2.close_drawer(page)
        for s in P["creates"]:
            spec = dict(s, title_text=(text_variant or {}).get("title", s["title_text"]))
            ui2.new_issue_modal(page, spec, users, via_shortcut=(route == "B"))
            created = max(int(x["number"]) for x in API(w).iss.values())
            k = f"{s['project']}-{created}"
            ui2.open_key_list(page, w.url, k) if route == "A" else ui2.open_key_search(page, k)
            ui2.set_fields(page, {"labels_add": s["labels"]}, users); ui2.close_drawer(page)
    report(w.run_dir, "complete", "Done.")


def plan_union(*Ps):
    out = plan_new()
    for P in Ps:
        for k in ("issues", "comments", "mail"): out[k].update(P[k])
        out["creates"] += P["creates"]
    return out


def plan_minus(P, drop_issues=(), drop_comments=(), drop_mail=(), drop_create=False):
    Q = copy.deepcopy(P)
    for n in drop_issues: Q["issues"].pop(n, None)
    for n in drop_comments: Q["comments"].pop(n, None)
    for m in drop_mail: Q["mail"].pop(m, None)
    if drop_create: Q["creates"] = []
    return Q


def collateral(w, P):
    """Correct plan plus one unrelated change (priority on an issue the plan does not touch)."""
    apply_api(w, P)
    a = API(w); n = next(n for n, i in sorted(w.seed["qs"]["issues"].items(), key=lambda x: int(x[0]))
                         if n not in P["issues"] and n not in P["comments"] and i["priority"] != "LOW")
    a.patch(n, {"priority": "LOW"})


def change_everything(w, issue_filter, ch, text=None):
    a = API(w)
    for n, i in w.seed["qs"]["issues"].items():
        if issue_filter(i):
            a.patch(n, ch)
            if text: a.comment(n, text)
    report(w.run_dir, "complete", "done")


# ================================================================== H1  release freeze: date math + per-record conditional
H1_GOAL = ("Today is Tuesday, September 15, 2026. The Main project's release freeze starts at the end of Friday, September 18. "
           "Go through every open issue in the Main project (Backlog, Todo or In Progress) that is due on or before September 18, "
           "including any that are already overdue, and handle each one:\n"
           "- If its estimate is 5 points or more, it will not make the freeze: move it to Backlog (if it is not there already) "
           "and add the comment: Deferred past the Sep 18 freeze\n"
           "- Otherwise, set its priority to Urgent, and if it has no assignee, assign it to Priya Shah. Leave existing assignees as they are.\n"
           "Do not change any other issue.")
H1_TEXT = "Deferred past the Sep 18 freeze"
H1_OK = [norm_text(H1_TEXT), norm_text("Deferred past the September 18 freeze")]


def h1_plan(seed, cutoff="2026-09-18", big=5, priya=PRIYA, projects=("MAIN",), strict_big=False):
    P = plan_new()
    for n, i in seed["qs"]["issues"].items():
        if i["project"] in projects and i["status"] not in CLOSED and i["due"] and i["due"] <= cutoff:
            if (i["estimate"] > big) if strict_big else (i["estimate"] >= big):
                if i["status"] != "BACKLOG": P["issues"][n] = {"status": "BACKLOG"}
                P["comments"][n] = (H1_TEXT, H1_OK)
            else:
                ch = {}
                if i["priority"] != "URGENT": ch["priority"] = "URGENT"
                if i["assignee"] is None: ch["assignee"] = priya
                if ch: P["issues"][n] = ch
    return P


def h1_check_seed(seed):
    I = seed["qs"]["issues"]; P = h1_plan(seed)
    hits = [n for n, i in I.items() if i["project"] == "MAIN" and i["status"] not in CLOSED and i["due"] and i["due"] <= "2026-09-18"]
    assert len(hits) == 8 and len(P["comments"]) == 3, (hits, P)
    assert any(I[n]["status"] == "BACKLOG" for n in P["comments"]), "lost the already-in-Backlog defer case"
    assert any(I[n]["estimate"] == 5 for n in P["comments"]), "lost the boundary estimate"
    assert any(I[n]["priority"] == "URGENT" and n not in P["issues"] for n in hits), "lost the already-urgent keep case"
    assert any(i["project"] == "MAIN" and i["status"] not in CLOSED and i["due"] == "2026-09-19" for i in I.values()), "lost the Sep 19 twin"
    assert PRIYA_TWIN in [u[0] for u in seed["qs"]["users"]], "lost the Priya Sharma twin"


def h1_verify(seed, final, rep): h1_check_seed(seed); return verify_plan(seed, final, rep, h1_plan(seed))
def h1_oracle(w): apply_ui(w, h1_plan(w.seed), "A")
def h1_alt(w):
    P = h1_plan(w.seed); apply_ui(w, P, "B", text_variant={n: "deferred past the Sep 18 freeze." for n in P["comments"]})

H1_ADV = {
    "change_everything": lambda w: change_everything(w, lambda i: i["project"] == "MAIN" and i["status"] not in CLOSED,
                                                     {"priority": "URGENT"}, H1_TEXT),
    "wrong_twin_priya_sharma": lambda w: apply_api(w, h1_plan(w.seed, priya=PRIYA_TWIN)),
    "date_off_by_one_sep19": lambda w: apply_api(w, h1_plan(w.seed, cutoff="2026-09-19")),
    "date_excludes_overdue": lambda w: apply_api(w, {**h1_plan(w.seed), **{k: {n: v for n, v in h1_plan(w.seed)[k].items()
                                                  if w.seed["qs"]["issues"][n]["due"] >= "2026-09-15"} for k in ("issues", "comments")}}),
    "all_projects": lambda w: apply_api(w, h1_plan(w.seed, projects=("MAIN", "MOB", "WEB"))),
    "boundary_strict_gt5": lambda w: apply_api(w, h1_plan(w.seed, strict_big=True)),
    "partial_no_comments": lambda w: apply_api(w, plan_minus(h1_plan(w.seed), drop_comments=list(h1_plan(w.seed)["comments"]))),
    "comment_twice": lambda w: apply_api(w, h1_plan(w.seed), comment_twice=True),
    "oracle_plus_collateral": lambda w: collateral(w, h1_plan(w.seed)),
}


# ================================================================== H2  Marco's capacity: derived sum + conditional + greedy fill
H2_GOAL = ("Marco Diaz can carry at most 20 points in Cycle 2: Liftoff of the Main project. His load is the total estimate of his open "
           "issues (not Done or Canceled) in that cycle.\n"
           "- If his load is above 20, unassign his lowest-priority open Cycle 2 issue and change nothing else.\n"
           "- Otherwise, fill his spare capacity from the unassigned open issues in Cycle 2: go through them from highest to lowest "
           "priority (Urgent, High, Medium, Low, None; for equal priority, the larger estimate first). Assign an issue to Marco only if "
           "his load stays at or under 20 points; if it would go over, skip it and continue with the next one. For every issue you "
           "assign to him, set its status to Todo and add the comment: Added to Marco's Cycle 2 load")
H2_TEXT = "Added to Marco's Cycle 2 load"
H2_OK = [norm_text(H2_TEXT), norm_text("Added to Marcos Cycle 2 load")]


def h2_plan(seed, limit=20, count_closed=False, cycle="Cycle 2: Liftoff", order="priority", greedy_stop=False, who=MARCO):
    I = seed["qs"]["issues"]; P = plan_new()
    mine = [n for n, i in I.items() if i["assignee"] == who and i["cycle"] == cycle and (count_closed or i["status"] not in CLOSED)]
    load = sum(I[n]["estimate"] for n in mine)
    if load > limit:
        n = min((n for n in mine if I[n]["status"] not in CLOSED), key=lambda n: (RANK[I[n]["priority"]], -int(n)))
        P["issues"][n] = {"assignee": None}; return P
    cands = [n for n, i in I.items() if i["assignee"] is None and i["cycle"] == cycle and i["status"] not in CLOSED]
    if order == "priority": cands.sort(key=lambda n: (-RANK[I[n]["priority"]], -I[n]["estimate"]))
    else: cands.sort(key=lambda n: -I[n]["estimate"])
    for n in cands:
        if load + I[n]["estimate"] <= limit:
            load += I[n]["estimate"]; P["issues"][n] = {"assignee": who}
            if I[n]["status"] != "TODO": P["issues"][n]["status"] = "TODO"
            P["comments"][n] = (H2_TEXT, H2_OK)
        elif greedy_stop: break
    return P


def h2_check_seed(seed):
    I = seed["qs"]["issues"]
    cands = [(I[n]["priority"], I[n]["estimate"]) for n, i in I.items() if i["assignee"] is None and i["cycle"] == "Cycle 2: Liftoff" and i["status"] not in CLOSED]
    assert len(cands) == len(set(cands)), "H2 ordering has ties"
    P = h2_plan(seed); assert len(P["comments"]) == 3, P
    assert h2_plan(seed, count_closed=True)["issues"] != P["issues"], "counting closed issues no longer changes the branch"
    assert any(I[n]["status"] == "TODO" for n in P["comments"]), "lost the already-Todo case"


def h2_verify(seed, final, rep): h2_check_seed(seed); return verify_plan(seed, final, rep, h2_plan(seed))
def h2_oracle(w): apply_ui(w, h2_plan(w.seed), "A")
def h2_alt(w):
    P = h2_plan(w.seed); apply_ui(w, P, "B", text_variant={n: "added to Marco's cycle 2 load." for n in P["comments"]})

H2_ADV = {
    "change_everything": lambda w: change_everything(w, lambda i: i["cycle"] == "Cycle 2: Liftoff" and i["assignee"] is None and i["status"] not in CLOSED,
                                                     {"assignee": MARCO, "status": "TODO"}, H2_TEXT),
    "wrong_branch_counts_done": lambda w: apply_api(w, h2_plan(w.seed, count_closed=True)),
    "wrong_order_estimate_only": lambda w: apply_api(w, h2_plan(w.seed, order="estimate")),
    "stops_at_first_misfit": lambda w: apply_api(w, h2_plan(w.seed, greedy_stop=True)),
    "wrong_cycle": lambda w: apply_api(w, h2_plan(w.seed, cycle="Cycle 1: Groundwork")),
    "partial_no_status": lambda w: apply_api(w, {**h2_plan(w.seed), "issues": {n: {"assignee": MARCO} for n in h2_plan(w.seed)["issues"]}}),
    "partial_two_of_three": lambda w: apply_api(w, plan_minus(h2_plan(w.seed), drop_issues=list(h2_plan(w.seed)["issues"])[-1:],
                                                              drop_comments=list(h2_plan(w.seed)["comments"])[-1:])),
    "oracle_plus_collateral": lambda w: collateral(w, h2_plan(w.seed)),
}


# ================================================================== H3  cross-app: Quillmail -> Quillstack, then archive
H3_GOAL = ("Northwind is a customer; their staff write from northwind.io addresses. Today is Tuesday, September 15, 2026. "
           "In Quillmail, handle every message in the Inbox from a northwind.io address that arrived on or after Monday, September 14. "
           "Each one names a Quillstack issue by its key. For each message:\n"
           "- If the named issue is open (Backlog, Todo or In Progress), comment on it: Northwind follow-up, and raise its priority "
           "to High unless it is already High or Urgent.\n"
           "- If the named issue is Done or Canceled, move it back to Todo and comment on it: Northwind reopened\n"
           "Then archive each handled message. Do not reply to anyone, and leave all other messages and issues as they are.")
KEY_RE = re.compile(r"\b(MAIN|MOB|WEB)-(\d+)\b")
H3_OPEN, H3_REOPEN = ("Northwind follow-up", [norm_text("Northwind follow-up"), "northwind followup"]), ("Northwind reopened", [norm_text("Northwind reopened")])


def h3_targets(seed, domain="@northwind.io", since="2026-09-14", folders=("inbox",)):
    return sorted(mid for mid, m in seed["mail"].items() if m["from"].endswith(domain) and m["folder"] in folders and m["date"][:10] >= since)


def h3_plan(seed, targets=None, swap_branches=False, raise_always=False):
    I = seed["qs"]["issues"]; P = plan_new()
    for mid in (h3_targets(seed) if targets is None else targets):
        keys = {f"{a}-{b}" for a, b in KEY_RE.findall(seed["mail"][mid]["body"])}; assert len(keys) == 1, (mid, keys)
        n = keys.pop().split("-")[1]
        closed = I[n]["status"] in CLOSED
        if closed != swap_branches:
            if I[n]["status"] != "TODO": P["issues"][n] = {"status": "TODO"}
            P["comments"][n] = H3_REOPEN
        else:
            if raise_always or RANK[I[n]["priority"]] < RANK["HIGH"]: P["issues"][n] = {"priority": "HIGH"}
            P["comments"][n] = H3_OPEN
        P["mail"][mid] = {"folder": "archive"}
    return P


def h3_check_seed(seed):
    I = seed["qs"]["issues"]; T = h3_targets(seed); assert len(T) == 6, T
    P = h3_plan(seed)
    assert sum(1 for n, c in P["comments"].items() if c is H3_REOPEN) == 2, "want 2 reopen cases"
    assert any(n not in P["issues"] for n in P["comments"]), "lost the already-High/Urgent case"
    assert h3_targets(seed, since="2026-09-13") != T and h3_targets(seed, domain="northwind.co") and h3_targets(seed, folders=("archive",)), "lost a mail twin"
    assert any("northwind" in m["body"].lower() and not m["from"].endswith("northwind.io") and m["folder"] == "inbox" for m in seed["mail"].values())


def h3_verify(seed, final, rep): h3_check_seed(seed); return verify_plan(seed, final, rep, h3_plan(seed))
def h3_oracle(w): apply_ui(w, h3_plan(w.seed), "A")
def h3_alt(w):
    P = h3_plan(w.seed)
    apply_ui(w, P, "B", text_variant={n: ("northwind follow up" if c is H3_OPEN else "Northwind reopened.") for n, c in P["comments"].items()})


def h3_reply_too(w):
    P = h3_plan(w.seed); apply_api(w, P)
    mail_call(w, "POST", f"/api/messages/{next(iter(P['mail']))}/reply", {"body": "Thanks, we are on it."})

H3_ADV = {
    "change_everything": lambda w: apply_api(w, h3_plan(w.seed, targets=sorted(mid for mid, m in w.seed["mail"].items() if KEY_RE.search(m["body"])))),
    "wrong_twin_northwind_co": lambda w: apply_api(w, plan_union(h3_plan(w.seed), h3_plan(w.seed, targets=h3_targets(w.seed, domain="@northwind.co")))),
    "date_includes_sunday": lambda w: apply_api(w, h3_plan(w.seed, targets=h3_targets(w.seed, since="2026-09-13"))),
    "includes_archived": lambda w: apply_api(w, h3_plan(w.seed, targets=h3_targets(w.seed, folders=("inbox", "archive")))),
    "comment_only_no_reopen": lambda w: apply_api(w, h3_plan(w.seed, swap_branches=True)),
    "raise_already_urgent": lambda w: apply_api(w, h3_plan(w.seed, raise_always=True)),
    "tracker_only_no_archive": lambda w: apply_api(w, {**h3_plan(w.seed), "mail": {}}),
    "mail_only_no_tracker": lambda w: apply_api(w, {**plan_new(), "mail": h3_plan(w.seed)["mail"]}),
    "replied_too": h3_reply_too,
    "oracle_plus_collateral": lambda w: collateral(w, h3_plan(w.seed)),
}


# ================================================================== H4  derived count + argmax + date math, create in another project
H4_GOAL = ("Create one issue in the Website project titled: Bug bash retro\n"
           "Give it status Todo, priority Medium and the Bug label. Its estimate must equal the number of issues, across all three "
           "projects, that are Done and have the Bug label (Canceled ones do not count). Assign it to the person who is the assignee "
           "on the most of those Done bugs, and set its due date to exactly 7 days after the latest due date among those Done bugs. "
           "Finally, comment on that latest-due Done bug: Included in the bug bash retro")
H4_TEXT = "Included in the bug bash retro"


def h4_plan(seed, statuses=("DONE",), label="Bug", projects=("MAIN", "MOB", "WEB"), days=7):
    I = seed["qs"]["issues"]
    bugs = [n for n, i in I.items() if i["status"] in statuses and label in i["labels"] and i["project"] in projects]
    cnt = {}
    for n in bugs: cnt[I[n]["assignee"]] = cnt.get(I[n]["assignee"], 0) + 1
    top = max(cnt.values()); who = [u for u, c in cnt.items() if c == top]
    dated = [n for n in bugs if I[n]["due"]]; last = max(I[n]["due"] for n in dated)
    latest = [n for n in dated if I[n]["due"] == last]
    due = (datetime.date.fromisoformat(last) + datetime.timedelta(days=days)).isoformat()
    P = plan_new()
    P["creates"].append(dict(project="WEB", title_text="Bug bash retro", title_norm="bug bash retro", status="TODO", priority="MEDIUM",
                             assignee=sorted(who)[0], estimate=len(bugs), due=due, labels=["Bug"]))
    P["comments"][latest[0]] = (H4_TEXT, [norm_text(H4_TEXT)])
    return P, dict(count=len(bugs), who=who, latest=latest, cnt=cnt)


def h4_check_seed(seed):
    P, m = h4_plan(seed)
    assert m["count"] == 9 and m["who"] == [LENA] and len(m["latest"]) == 1, m
    assert m["cnt"].get(LENA_TWIN, 0) == m["cnt"][LENA] - 1, "lost the Lena Fisher runner-up twin"
    P2, m2 = h4_plan(seed, statuses=("DONE", "CANCELED"))
    assert m2["latest"] != m["latest"] and m2["count"] != m["count"], "lost the Canceled-bug twin"
    P3, m3 = h4_plan(seed, label="Regression"); assert m3["count"] >= 1


def h4_verify(seed, final, rep): h4_check_seed(seed); return verify_plan(seed, final, rep, h4_plan(seed)[0])
def h4_oracle(w): apply_ui(w, h4_plan(w.seed)[0], "A")
def h4_alt(w):
    P = h4_plan(w.seed)[0]; apply_ui(w, P, "B", text_variant={"title": "Bug Bash Retro ", **{n: "included in the bug-bash retro" for n in P["comments"]}})


def h4_variant(w, f=None, **kw):
    P = h4_plan(w.seed, **kw)[0]
    if f: f(P)
    apply_api(w, P)

H4_ADV = {
    "change_everything": lambda w: (h4_variant(w), change_everything(w, lambda i: "Bug" in i["labels"] and i["status"] in CLOSED, {}, H4_TEXT)),
    "counts_canceled": lambda w: h4_variant(w, statuses=("DONE", "CANCELED")),
    "counts_regressions_too": lambda w: h4_variant(w, f=lambda P: P["creates"][0].update(estimate=P["creates"][0]["estimate"] + 2)),
    "wrong_twin_lena_fisher": lambda w: h4_variant(w, f=lambda P: P["creates"][0].update(assignee=LENA_TWIN)),
    "due_off_by_one": lambda w: h4_variant(w, days=6),
    "wrong_project_main": lambda w: h4_variant(w, f=lambda P: P["creates"][0].update(project="MAIN")),
    "missing_label": lambda w: h4_variant(w, f=lambda P: P["creates"][0].update(labels=[])),
    "partial_no_comment": lambda w: h4_variant(w, f=lambda P: P["comments"].clear()),
    "created_twice": lambda w: h4_variant(w, f=lambda P: P["creates"].append(dict(P["creates"][0]))),
    "oracle_plus_collateral": lambda w: collateral(w, h4_plan(w.seed)[0]),
}



# ################################################################## seed v2: X1-X4, the hardened set
# Levers on top of H1-H4: the rules live in another app (and are amended by a later email, with a look-alike sender
# proposing different rules), derived capacity from date math across two views, key corrections and duplicate
# redirects, and a filter that only the per-issue history view can answer.
OMAR = "omar.haddad@quillstack.dev"
C2N = "Cycle 2: Liftoff"


def by_title(seed, title):
    hits = [n for n, i in seed["qs"]["issues"].items() if i["title"] == title]
    assert len(hits) == 1, (title, hits); return hits[0]


def mail_by_subject(seed, subject):
    hits = [m for m, v in seed["mail"].items() if v["subject"] == subject]
    assert len(hits) == 1, (subject, hits); return hits[0]


def weekdays(a, b):
    """Weekdays in [a, b) as ISO strings."""
    d, out = datetime.date.fromisoformat(a), []
    while d < datetime.date.fromisoformat(b):
        if d.weekday() < 5: out.append(d.isoformat())
        d += datetime.timedelta(days=1)
    return out


# ================================================================== X1  freeze plan read from email, amended by a correction
X1_GOAL = ("Priya Shah emailed you a release freeze plan for the Main project. Carry out her plan in Quillstack today, "
           "Tuesday, September 15, 2026, including any corrections she has sent since. Do not reply to any email.")
X1_TEXT = "Deferred past the Sep 18 freeze"


def x1_plan(seed, big=8, cutoff="2026-09-18", owner=PRIYA, customer_rule=True, projects=("MAIN",), overdue=True):
    P = plan_new()
    for n, i in seed["qs"]["issues"].items():
        if i["project"] in projects and i["status"] not in CLOSED and i["due"] and i["due"] <= cutoff and (overdue or i["due"] >= "2026-09-15"):
            if i["estimate"] >= big and not (customer_rule and "Customer" in i["labels"]):
                if i["status"] != "BACKLOG": P["issues"][n] = {"status": "BACKLOG"}
                P["comments"][n] = (X1_TEXT, H1_OK)
            else:
                ch = {}
                if i["priority"] != "URGENT": ch["priority"] = "URGENT"
                if i["assignee"] is None: ch["assignee"] = owner
                if ch: P["issues"][n] = ch
    return P


def x1_check_seed(seed):
    M = seed["mail"]; I = seed["qs"]["issues"]
    p1 = M[mail_by_subject(seed, "Release freeze plan for Main")]; p3 = M[mail_by_subject(seed, "Correction: release freeze plan")]
    assert p1["from"] == PRIYA and "5 points or more" in p1["body"] and "Customer-labeled" in p1["body"], "plan email changed"
    assert p3["from"] == PRIYA and "8 points, not 5" in p3["body"], "correction email changed"
    assert M[mail_by_subject(seed, "Re: Release freeze plan for Main")]["from"] == PRIYA_TWIN, "lost the Priya Sharma reply twin"
    P = x1_plan(seed)
    assert len(P["comments"]) == 3, P["comments"]
    assert x1_plan(seed, big=5)["comments"] != P["comments"], "the correction no longer matters"
    assert x1_plan(seed, customer_rule=False)["comments"] != P["comments"], "the Customer exception no longer matters"
    assert any(I[n]["status"] == "BACKLOG" for n in P["comments"]) and any(I[n]["priority"] == "URGENT" and n not in P["issues"] and n not in P["comments"]
               for n, i in I.items() if i["project"] == "MAIN" and i["status"] not in CLOSED and i["due"] and i["due"] <= "2026-09-18")


def x1_verify(seed, final, rep): x1_check_seed(seed); return verify_plan(seed, final, rep, x1_plan(seed))
def x1_oracle(w): apply_ui(w, x1_plan(w.seed), "A")
def x1_alt(w):
    P = x1_plan(w.seed); apply_ui(w, P, "B", text_variant={n: "Deferred past the September 18 freeze." for n in P["comments"]})


def x1_reply(w):
    apply_api(w, x1_plan(w.seed))
    mail_call(w, "POST", f"/api/messages/{mail_by_subject(w.seed, 'Correction: release freeze plan')}/reply", {"body": "Done, thanks."})

X1_ADV = {
    "change_everything": lambda w: change_everything(w, lambda i: i["project"] == "MAIN" and i["status"] not in CLOSED and i["due"] and i["due"] <= "2026-09-18",
                                                     {"priority": "URGENT", "assignee": PRIYA}, X1_TEXT),
    "ignores_correction_cutoff5": lambda w: apply_api(w, x1_plan(w.seed, big=5)),
    "follows_priya_sharma_reply": lambda w: apply_api(w, x1_plan(w.seed, big=3, owner=PRIYA_TWIN)),
    "wrong_twin_owner": lambda w: apply_api(w, x1_plan(w.seed, owner=PRIYA_TWIN)),
    "misses_customer_exception": lambda w: apply_api(w, x1_plan(w.seed, customer_rule=False)),
    "date_off_by_one_sep19": lambda w: apply_api(w, x1_plan(w.seed, cutoff="2026-09-19")),
    "excludes_overdue": lambda w: apply_api(w, x1_plan(w.seed, overdue=False)),
    "all_projects": lambda w: apply_api(w, x1_plan(w.seed, projects=("MAIN", "MOB", "WEB"))),
    "partial_no_comments": lambda w: apply_api(w, plan_minus(x1_plan(w.seed), drop_comments=list(x1_plan(w.seed)["comments"]))),
    "replied_to_priya": x1_reply,
    "oracle_plus_collateral": lambda w: collateral(w, x1_plan(w.seed)),
}


# ================================================================== X2  capacity derived from cycle dates + time-off emails
X2_GOAL = ("Plan Cycle 2: Liftoff of the Main project for Marco Diaz and Omar Haddad.\n"
           "- A person's capacity is 2 points for each working day of the cycle on which they are not out. The cycle's working days are "
           "the weekdays from its start date up to, but not including, its end date. Their time off is in the emails they sent you in Quillmail.\n"
           "- A person's load is the total estimate of their open (not Done or Canceled) Main issues in Cycle 2.\n"
           "Do Marco first, then Omar. If the person's load is over capacity, unassign their open Cycle 2 issues one at a time, lowest "
           "priority first, until it is not, and comment on each one you unassign: Unassigned, over capacity. Otherwise, fill their spare "
           "capacity from the unassigned open Cycle 2 issues, going from highest to lowest priority (Urgent, High, Medium, Low, None; for equal "
           "priority, the larger estimate first): give an issue to the person only if their load stays at or under capacity, otherwise skip it "
           "and try the next one. For each issue you give someone, set its status to Todo and comment: Planned for Cycle 2\n"
           "Issues you unassign stay unassigned. Do not change anything else.")
X2_FILL, X2_OVER = ("Planned for Cycle 2", [norm_text("Planned for Cycle 2")]), ("Unassigned, over capacity", [norm_text("Unassigned, over capacity"), norm_text("Unassigned over capacity")])
X2_OUT = {MARCO: ["2026-09-24", "2026-09-25", "2026-09-28", "2026-09-29"], OMAR: ["2026-10-02", "2026-10-05"]}


def x2_caps(seed, include_end=False, ignore_mail=False):
    cyc = next(c for c in seed["qs"]["cycles"] if c[0] == C2N)
    end = (datetime.date.fromisoformat(cyc[3]) + datetime.timedelta(days=1)).isoformat() if include_end else cyc[3]
    days = weekdays(cyc[2], end)
    return {who: 2 * len([d for d in days if ignore_mail or d not in out]) for who, out in X2_OUT.items()}


def x2_plan(seed, caps=None, order=(MARCO, OMAR), count_closed=False, freed_reusable=False, sort="priority"):
    I = seed["qs"]["issues"]; P = plan_new(); caps = caps or x2_caps(seed); taken = set(); freed = set()
    for who in order:
        mine = [n for n, i in I.items() if i["assignee"] == who and i["cycle"] == C2N and (count_closed or i["status"] not in CLOSED)]
        load = sum(I[n]["estimate"] for n in mine)
        if load > caps[who]:
            for n in sorted((n for n in mine if I[n]["status"] not in CLOSED), key=lambda n: (RANK[I[n]["priority"]], I[n]["estimate"])):
                if load <= caps[who]: break
                P["issues"][n] = {"assignee": None}; P["comments"][n] = X2_OVER; load -= I[n]["estimate"]; freed.add(n)
            continue
        cands = [n for n, i in I.items() if (i["assignee"] is None or (freed_reusable and n in freed)) and i["cycle"] == C2N
                 and i["status"] not in CLOSED and n not in taken and i["project"] == "MAIN"]
        cands.sort(key=(lambda n: (-RANK[I[n]["priority"]], -I[n]["estimate"])) if sort == "priority" else (lambda n: -I[n]["estimate"]))
        for n in cands:
            if load + I[n]["estimate"] <= caps[who]:
                load += I[n]["estimate"]; taken.add(n); P["issues"][n] = {"assignee": who}
                if I[n]["status"] != "TODO": P["issues"][n]["status"] = "TODO"
                P["comments"][n] = X2_FILL
    return P


def x2_check_seed(seed):
    M = seed["mail"]
    o1, o2 = M[mail_by_subject(seed, "Time off")], M[mail_by_subject(seed, "PTO")]
    assert o1["from"] == MARCO and "September 24 through Tuesday, September 29" in o1["body"]
    assert o2["from"] == OMAR and "October 2 and Monday, October 5" in o2["body"]
    assert M[mail_by_subject(seed, "Out Tuesday and Wednesday")]["folder"] == "archive", "lost the old Marco time-off twin"
    caps = x2_caps(seed); assert caps == {MARCO: 12, OMAR: 18}, caps
    P = x2_plan(seed); I = seed["qs"]["issues"]
    over = [n for n, c in P["comments"].items() if c is X2_OVER]; fill = [n for n, c in P["comments"].items() if c is X2_FILL]
    assert len(over) == 1 and len(fill) == 3, P
    assert all(I[n]["cycle"] == C2N for n in P["issues"])
    cands = [(i["priority"], i["estimate"]) for i in I.values() if i["assignee"] is None and i["cycle"] == C2N and i["status"] not in CLOSED]
    assert len(cands) == len(set(cands)), "priority ties"
    for bad in (x2_caps(seed, include_end=True), x2_caps(seed, ignore_mail=True)):
        assert x2_plan(seed, caps=bad) != P, "a cap trap no longer matters"


def x2_verify(seed, final, rep): x2_check_seed(seed); return verify_plan(seed, final, rep, x2_plan(seed))
def x2_oracle(w): apply_ui(w, x2_plan(w.seed), "A")
def x2_alt(w):
    P = x2_plan(w.seed)
    apply_ui(w, P, "B", text_variant={n: ("planned for cycle 2." if c is X2_FILL else "Unassigned (over capacity)") for n, c in P["comments"].items()})

X2_ADV = {   # Omar-first, freed-issue-reuse and estimate-only order give the same end state in this seed (scored 1), so they are not traps here
    "change_everything": lambda w: change_everything(w, lambda i: i["cycle"] == C2N and i["assignee"] is None and i["status"] not in CLOSED,
                                                     {"assignee": OMAR, "status": "TODO"}, X2_FILL[0]),
    "ignores_time_off": lambda w: apply_api(w, x2_plan(w.seed, caps=x2_caps(w.seed, ignore_mail=True))),
    "includes_end_date": lambda w: apply_api(w, x2_plan(w.seed, caps=x2_caps(w.seed, include_end=True))),
    "counts_done": lambda w: apply_api(w, x2_plan(w.seed, count_closed=True)),
    "partial_marco_only": lambda w: apply_api(w, x2_plan(w.seed, order=(MARCO,))),
    "partial_no_status": lambda w: apply_api(w, {**x2_plan(w.seed), "issues": {n: {k: v for k, v in ch.items() if k != "status"} for n, ch in x2_plan(w.seed)["issues"].items()}}),
    "oracle_plus_collateral": lambda w: collateral(w, x2_plan(w.seed)),
}


# ================================================================== X3  Northwind triage with key corrections, duplicates, repeats
X3_GOAL = ("Northwind is a customer; their staff write from northwind.io addresses. Today is Tuesday, September 15, 2026. In Quillmail, "
           "handle every Inbox message from a northwind.io address that arrived on or after Monday, September 14. Each message is about one "
           "Quillstack issue, named by its key. If a sender corrects a key in a later message, the corrected issue is the one that counts. "
           "If the named issue was closed as a duplicate of another issue, the issue it duplicates is the one that counts. Handle each issue "
           "once, even if several messages are about it:\n"
           "- Open (Backlog, Todo or In Progress): comment Northwind follow-up, and raise its priority to High unless it is already High or Urgent.\n"
           "- Done: move it back to Todo and comment: Northwind reopened\n"
           "- Canceled: leave its status as it is and comment: Not planned, Northwind asked again\n"
           "Then archive every message you handled, including corrections. Do not reply to anyone, and leave all other messages and issues as they are.")
X3_OK = {"open": ("Northwind follow-up", [norm_text("Northwind follow-up"), "northwind followup"]),
         "done": ("Northwind reopened", [norm_text("Northwind reopened")]),
         "canceled": ("Not planned, Northwind asked again", [norm_text("Not planned, Northwind asked again"), norm_text("Not planned. Northwind asked again")])}
DUP_RE = re.compile(r"Duplicate of ((?:MAIN|MOB|WEB)-\d+)")


def x3_targets(seed, domain="@northwind.io", since="2026-09-14", folders=("inbox",)):
    return sorted(mid for mid, m in seed["mail"].items() if m["from"].endswith(domain) and m["folder"] in folders and m["date"][:10] >= since)


def x3_resolve(seed, mids, corrections=True, dups=True):
    """message id -> issue number, applying sender corrections and duplicate redirects."""
    M, I = seed["mail"], seed["qs"]["issues"]; out = {}
    for mid in mids:
        b = M[mid]["body"]; keys = [f"{a}-{n}" for a, n in KEY_RE.findall(b)]
        m = re.search(r"The crash is ((?:MAIN|MOB|WEB)-\d+), not", b)
        k = m.group(1) if m else keys[0]
        if not m: assert len(set(keys)) == 1, (mid, keys)
        out[mid] = k.split("-")[1]
    if corrections:   # a correction replaces what the sender's earlier message named
        for mid in mids:
            m = re.search(r"The crash is ((?:MAIN|MOB|WEB)-\d+), not ((?:MAIN|MOB|WEB)-\d+)", M[mid]["body"])
            if m:
                for o in mids:
                    if out[o] == m.group(2).split("-")[1]: out[o] = m.group(1).split("-")[1]
    else:
        for mid in mids:
            if re.search(r"The crash is", M[mid]["body"]): out[mid] = re.search(r"not ((?:MAIN|MOB|WEB)-\d+)", M[mid]["body"]).group(1).split("-")[1]
    if dups:
        for mid, n in list(out.items()):
            for c in I[n]["comments"]:
                d = DUP_RE.search(c["body"])
                if d and I[n]["status"] in CLOSED: out[mid] = d.group(1).split("-")[1]
    return out


def x3_plan(seed, mids=None, corrections=True, dups=True, reopen_canceled=False, raise_always=False):
    I = seed["qs"]["issues"]; P = plan_new(); mids = x3_targets(seed) if mids is None else mids
    for mid, n in x3_resolve(seed, mids, corrections, dups).items():
        st = I[n]["status"]
        if st == "DONE" or (st == "CANCELED" and reopen_canceled):
            P["issues"][n] = {"status": "TODO"}; P["comments"][n] = X3_OK["done"]
        elif st == "CANCELED": P["comments"][n] = X3_OK["canceled"]
        else:
            if raise_always or RANK[I[n]["priority"]] < RANK["HIGH"]: P["issues"][n] = {"priority": "HIGH"}
            P["comments"][n] = X3_OK["open"]
        P["mail"][mid] = {"folder": "archive"}
    return P


def x3_check_seed(seed):
    T = x3_targets(seed); assert len(T) == 8, T
    P = x3_plan(seed); kinds = sorted(c[0] for c in P["comments"].values())
    assert len(P["comments"]) == 6 and kinds.count(X3_OK["canceled"][0]) == 1 and kinds.count(X3_OK["done"][0]) == 1, P["comments"]
    assert x3_plan(seed, corrections=False)["comments"] != P["comments"], "the correction no longer matters"
    assert x3_plan(seed, dups=False)["comments"] != P["comments"], "the duplicate no longer matters"
    assert len(set(x3_resolve(seed, T).values())) < len(T) - 1, "lost the repeat messages"
    assert x3_targets(seed, since="2026-09-13") != T and x3_targets(seed, domain="@northwind.co") and x3_targets(seed, folders=("archive",))


def x3_verify(seed, final, rep): x3_check_seed(seed); return verify_plan(seed, final, rep, x3_plan(seed))
def x3_oracle(w): apply_ui(w, x3_plan(w.seed), "A")
def x3_alt(w):
    P = x3_plan(w.seed); alt = {"Northwind follow-up": "northwind follow up", "Northwind reopened": "Northwind reopened.",
                                "Not planned, Northwind asked again": "Not planned. Northwind asked again."}
    apply_ui(w, P, "B", text_variant={n: alt[c[0]] for n, c in P["comments"].items()})


def x3_reply_too(w):
    P = x3_plan(w.seed); apply_api(w, P)
    mail_call(w, "POST", f"/api/messages/{next(iter(P['mail']))}/reply", {"body": "Thanks, we are on it."})


def x3_comment_per_message(w):
    """Comments once per message instead of once per issue (repeats get two comments)."""
    P = x3_plan(w.seed); apply_api(w, P); a = API(w)
    res = x3_resolve(w.seed, x3_targets(w.seed)); seen = set()
    for mid, n in res.items():
        if n in seen: a.comment(n, P["comments"][n][0])
        seen.add(n)

X3_ADV = {
    "change_everything": lambda w: apply_api(w, x3_plan(w.seed, mids=sorted(m for m, v in w.seed["mail"].items() if KEY_RE.search(v["body"]) and v["folder"] == "inbox"), dups=False)),
    "ignores_correction": lambda w: apply_api(w, x3_plan(w.seed, corrections=False)),
    "ignores_duplicate": lambda w: apply_api(w, x3_plan(w.seed, dups=False)),
    "reopens_canceled": lambda w: apply_api(w, x3_plan(w.seed, reopen_canceled=True)),
    "raise_already_urgent": lambda w: apply_api(w, x3_plan(w.seed, raise_always=True)),
    "wrong_twin_northwind_co": lambda w: apply_api(w, plan_union(x3_plan(w.seed), x3_plan(w.seed, mids=x3_targets(w.seed, domain="@northwind.co")))),
    "date_includes_sunday": lambda w: apply_api(w, x3_plan(w.seed, mids=x3_targets(w.seed, since="2026-09-13"))),
    "comment_per_message": x3_comment_per_message,
    "skips_correction_mail_archive": lambda w: apply_api(w, plan_minus(x3_plan(w.seed), drop_mail=[mail_by_subject(w.seed, "Re: Shared board links crash the iOS app")])),
    "tracker_only_no_archive": lambda w: apply_api(w, {**x3_plan(w.seed), "mail": {}}),
    "replied_too": x3_reply_too,
    "oracle_plus_collateral": lambda w: collateral(w, x3_plan(w.seed)),
}


# ================================================================== X4  filter only the history view answers, then count/argmax/date math
X4_GOAL = ("Prepare the Cycle 1 bug bash retro. A bug counts if it has the Bug label (in any project), its status is Done, and it was moved "
           "to Done on or after the day Cycle 1: Groundwork started; each issue's history shows when and by whom it was moved.\n"
           "Create one issue in the Website project titled: Bug bash retro\n"
           "Give it status Todo, priority Medium and the Bug label. Its estimate must equal the number of bugs that count. Assign it to the "
           "person who moved the most of those bugs to Done, and set its due date to exactly 7 days after the latest due date among them. "
           "Then comment on every bug that counts: Counted in the bug bash retro")
X4_TEXT = "Counted in the bug bash retro"
# who moved each Done bug to Done and how many days before the clock (mirrors seedgen2 closed=(who, days); the history view shows it)
X4_CLOSED = {"Login form ignores the Enter key": (LENA, 6), "Board drag drops card in wrong column": (PRIYA, 4),
             "Comment count stale after delete": (OMAR, 1), "Keyboard covers the reply box": (PRIYA, 3),
             "Avatar cache never expires": ("lena.fisher@quillstack.dev", 12), "Badge count wrong after logout": ("dana.kim@quillstack.dev", 2),
             "Footer links 404 on the blog": (LENA, 20), "Signup button misaligned on Safari": (PRIYA, 5),
             "Rotate API keys without downtime": (GUEST, 7), "Mention emails sent twice": (LENA, 2),
             "Docs sidebar collapses on scroll": ("lena.fisher@quillstack.dev", 10), "Search results flicker on refresh": ("lena.fisher@quillstack.dev", 3),
             "Hero video stutters on Firefox": ("lena.fisher@quillstack.dev", 2), "Login screen freezes on iPad": ("lena.fisher@quillstack.dev", 3)}


def x4_plan(seed, since_days=8, statuses=("DONE",), labels=("Bug",), by="closer", days=7, scope="counted"):
    I = seed["qs"]["issues"]
    bugs = [n for n, i in I.items() if i["status"] in statuses and any(l in i["labels"] for l in labels)
            and X4_CLOSED.get(i["title"], (None, 40))[1] < since_days]   # unlisted closed issues were closed at seed time, 40 days back
    cnt = {}
    for n in bugs:
        who = X4_CLOSED.get(I[n]["title"], (I[n]["assignee"] or I[n]["creator"],))[0] if by == "closer" else I[n]["assignee"]
        cnt[who] = cnt.get(who, 0) + 1
    top = max(cnt.values()); who = sorted(u for u, c in cnt.items() if c == top)
    last = max(I[n]["due"] for n in bugs if I[n]["due"])
    P = plan_new()
    P["creates"].append(dict(project="WEB", title_text="Bug bash retro", title_norm="bug bash retro", status="TODO", priority="MEDIUM",
                             assignee=who[0], estimate=len(bugs), due=(datetime.date.fromisoformat(last) + datetime.timedelta(days=days)).isoformat(), labels=["Bug"]))
    for n in bugs: P["comments"][n] = (X4_TEXT, [norm_text(X4_TEXT)])
    return P, dict(count=len(bugs), who=who, cnt=cnt, last=last)


def x4_check_seed(seed):
    I = seed["qs"]["issues"]
    assert {i["title"] for i in I.values() if "Bug" in i["labels"] and i["status"] in CLOSED or "Regression" in i["labels"]} >= set(X4_CLOSED)
    assert all(i["title"] in X4_CLOSED for i in I.values() if i["status"] == "DONE" and ("Bug" in i["labels"] or "Regression" in i["labels"])), "a Done bug lacks history data"
    assert next(c for c in seed["qs"]["cycles"] if c[0] == "Cycle 1: Groundwork")[2] == "2026-09-07"
    import json, os   # the history table is not in the snapshot; check our copy against the seed file the app loaded
    pd = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app/backend/prisma")
    hist = [{i["title"]: (i["closedBy"], i["closedDaysAgo"]) for i in json.load(open(os.path.join(pd, f)))["issues"] if i.get("closedBy")}
            for f in ("seed-data.json", "seed-v3.json") if os.path.exists(os.path.join(pd, f))]
    assert X4_CLOSED in hist, "history seed changed"
    P, m = x4_plan(seed); assert m["count"] == 8 and m["who"] == [PRIYA] and m["last"] == "2026-09-16", m
    for kw in (dict(since_days=99), dict(statuses=("DONE", "CANCELED")), dict(by="assignee"), dict(labels=("Bug", "Regression"))):
        assert x4_plan(seed, **kw)[0] != P, kw


def x4_verify(seed, final, rep): x4_check_seed(seed); return verify_plan(seed, final, rep, x4_plan(seed)[0])
def x4_oracle(w): apply_ui(w, x4_plan(w.seed)[0], "A")
def x4_alt(w):
    P = x4_plan(w.seed)[0]; apply_ui(w, P, "B", text_variant={"title": "Bug Bash Retro ", **{n: "counted in the bug-bash retro." for n in P["comments"]}})


def x4_variant(w, f=None, **kw):
    P = x4_plan(w.seed, **kw)[0]
    if f: f(P)
    apply_api(w, P)

X4_ADV = {
    "change_everything": lambda w: x4_variant(w, since_days=99, statuses=("DONE", "CANCELED"), labels=("Bug", "Regression")),
    "ignores_history_all_done_bugs": lambda w: x4_variant(w, since_days=99),
    "counts_canceled": lambda w: x4_variant(w, statuses=("DONE", "CANCELED")),
    "counts_regressions": lambda w: x4_variant(w, labels=("Bug", "Regression")),
    "assignee_not_closer": lambda w: x4_variant(w, by="assignee"),
    "wrong_twin_priya_sharma": lambda w: x4_variant(w, f=lambda P: P["creates"][0].update(assignee=PRIYA_TWIN)),
    "due_off_by_one": lambda w: x4_variant(w, days=6),
    "wrong_project_main": lambda w: x4_variant(w, f=lambda P: P["creates"][0].update(project="MAIN")),
    "partial_no_comments": lambda w: x4_variant(w, f=lambda P: P["comments"].clear()),
    "partial_comment_half": lambda w: x4_variant(w, f=lambda P: [P["comments"].pop(k) for k in list(P["comments"])[:4]]),
    "created_twice": lambda w: x4_variant(w, f=lambda P: P["creates"].append(dict(P["creates"][0]))),
    "oracle_plus_collateral": lambda w: collateral(w, x4_plan(w.seed)[0]),
}


# ================================================================== X1b (seed v3)  X1 plus a comment-only exception and a second amendment
X1B_TEXT = "Deferred past the release freeze"
X1B_OK = [norm_text(X1B_TEXT), norm_text("Deferred past the release freeze.")]
MERGED_RE = re.compile(r"^merged to the release branch", re.I)


def x1b_plan(seed, big=8, cutoff="2026-09-17", owner=PRIYA, merged_rule=True, merged_loose=False, text=(X1B_TEXT, X1B_OK), **kw):
    I = seed["qs"]["issues"]
    def merged(i): return any((("release branch" in c["body"].lower()) if merged_loose else MERGED_RE.search(c["body"])) for c in i["comments"])
    skip = {n for n, i in I.items() if merged_rule and merged(i)}
    view = {**seed, "qs": {**seed["qs"], "issues": {n: i for n, i in I.items() if n not in skip}}}
    P = x1_plan(view, big=big, cutoff=cutoff, owner=owner, **kw)
    for n in P["comments"]: P["comments"][n] = text
    return P


def x1b_check_seed(seed):
    M = seed["mail"]; I = seed["qs"]["issues"]
    assert "release branch" in M[mail_by_subject(seed, "Correction: release freeze plan")]["body"]
    p4 = M[mail_by_subject(seed, "Re: Correction: release freeze plan")]
    assert p4["from"] == PRIYA and "Thursday, September 17" in p4["body"] and X1B_TEXT in p4["body"]
    P = x1b_plan(seed); assert len(P["comments"]) == 2 and count_checks_plan(P) == 17, (P, count_checks_plan(P))
    for kw in (dict(cutoff="2026-09-18"), dict(merged_rule=False), dict(merged_loose=True), dict(big=5)):
        assert x1b_plan(seed, **kw) != P, kw
    x1_check_seed_v3(seed)


def x1_check_seed_v3(seed):
    M = seed["mail"]
    assert M[mail_by_subject(seed, "Release freeze plan for Main")]["from"] == PRIYA
    assert M[mail_by_subject(seed, "Re: Release freeze plan for Main")]["from"] == PRIYA_TWIN


def count_checks_plan(P):
    return sum(len(ch) for ch in P["issues"].values()) + len(P["comments"]) + len(P["mail"]) + 9 * len(P["creates"]) + 2


def x1b_verify(seed, final, rep): x1b_check_seed(seed); return verify_plan(seed, final, rep, x1b_plan(seed))
def x1b_oracle(w): apply_ui(w, x1b_plan(w.seed), "A")
def x1b_alt(w):
    P = x1b_plan(w.seed); apply_ui(w, P, "B", text_variant={n: "deferred past the release freeze." for n in P["comments"]})

X1B_ADV = {
    "change_everything": lambda w: change_everything(w, lambda i: i["project"] == "MAIN" and i["status"] not in CLOSED and i["due"] and i["due"] <= "2026-09-18",
                                                     {"priority": "URGENT", "assignee": PRIYA}, X1B_TEXT),
    "misses_second_amendment": lambda w: apply_api(w, x1b_plan(w.seed, cutoff="2026-09-18")),
    "misses_second_amendment_text": lambda w: apply_api(w, x1b_plan(w.seed, text=(X1_TEXT, H1_OK))),
    "ignores_merged_exception": lambda w: apply_api(w, x1b_plan(w.seed, merged_rule=False)),
    "treats_will_merge_as_merged": lambda w: apply_api(w, x1b_plan(w.seed, merged_loose=True)),
    "ignores_first_correction": lambda w: apply_api(w, x1b_plan(w.seed, big=5)),
    "wrong_twin_owner": lambda w: apply_api(w, x1b_plan(w.seed, owner=PRIYA_TWIN)),
    "misses_customer_exception": lambda w: apply_api(w, x1b_plan(w.seed, customer_rule=False)),
    "excludes_overdue": lambda w: apply_api(w, x1b_plan(w.seed, overdue=False)),
    "partial_no_comments": lambda w: apply_api(w, plan_minus(x1b_plan(w.seed), drop_comments=list(x1b_plan(w.seed)["comments"]))),
    "replied_to_priya": lambda w: (apply_api(w, x1b_plan(w.seed)), mail_call(w, "POST", f"/api/messages/{mail_by_subject(w.seed, 'Correction: release freeze plan')}/reply", {"body": "Done."})),
    "oracle_plus_collateral": lambda w: collateral(w, x1b_plan(w.seed)),
}


# ================================================================== X2b (seed v3)  X2 plus a time-off correction that flips Marco's branch
X2B_OUT = {MARCO: ["2026-09-24", "2026-09-25"], OMAR: ["2026-10-02", "2026-10-05"]}


def x2b_caps(seed, out=None, include_end=False):
    cyc = next(c for c in seed["qs"]["cycles"] if c[0] == C2N)
    end = (datetime.date.fromisoformat(cyc[3]) + datetime.timedelta(days=1)).isoformat() if include_end else cyc[3]
    days = weekdays(cyc[2], end)
    return {who: 2 * len([d for d in days if d not in o]) for who, o in (out or X2B_OUT).items()}


def x2b_check_seed(seed):
    M = seed["mail"]
    assert M[mail_by_subject(seed, "PTO")]["folder"] == "archive" and M[mail_by_subject(seed, "PTO")]["from"] == OMAR
    o5 = M[mail_by_subject(seed, "Re: Time off")]; assert o5["from"] == MARCO and "only out Thursday the 24th and Friday the 25th" in o5["body"]
    caps = x2b_caps(seed); assert caps == {MARCO: 16, OMAR: 18}, caps
    P = x2b_plan(seed); I = seed["qs"]["issues"]
    assert len(P["comments"]) == 4 and all(c is X2_FILL for c in P["comments"].values()), P
    for bad in (dict(caps=x2_caps(seed)), dict(caps=x2b_caps(seed, include_end=True)), dict(caps=x2_caps(seed, ignore_mail=True)),
                dict(caps=x2b_caps(seed), order=(OMAR, MARCO)), dict(caps=x2b_caps(seed, out={MARCO: X2B_OUT[MARCO], OMAR: []})),
                dict(caps=x2b_caps(seed), count_closed=True)):
        assert x2_plan(seed, **bad) != P, bad  # every trap must change the end state, judged with the X2b caps


def x2b_plan(seed, **kw): return x2_plan(seed, **{"caps": x2b_caps(seed), **kw})
def x2b_verify(seed, final, rep): x2b_check_seed(seed); return verify_plan(seed, final, rep, x2b_plan(seed))
def x2b_oracle(w): apply_ui(w, x2b_plan(w.seed), "A")
def x2b_alt(w): apply_ui(w, x2b_plan(w.seed), "B", text_variant={n: "planned for cycle 2." for n in x2b_plan(w.seed)["comments"]})

X2B_ADV = {
    "change_everything": X2_ADV["change_everything"],
    "uses_first_marco_email": lambda w: apply_api(w, x2_plan(w.seed, caps=x2_caps(w.seed))),
    "misses_archived_omar_pto": lambda w: apply_api(w, x2_plan(w.seed, caps=x2b_caps(w.seed, out={MARCO: X2B_OUT[MARCO], OMAR: []}))),
    "ignores_time_off": lambda w: apply_api(w, x2_plan(w.seed, caps=x2_caps(w.seed, ignore_mail=True))),
    "includes_end_date": lambda w: apply_api(w, x2_plan(w.seed, caps=x2b_caps(w.seed, include_end=True))),
    "omar_first": lambda w: apply_api(w, x2b_plan(w.seed, order=(OMAR, MARCO))),
    "counts_done": lambda w: apply_api(w, x2b_plan(w.seed, count_closed=True)),
    "partial_marco_only": lambda w: apply_api(w, x2b_plan(w.seed, order=(MARCO,))),
    "partial_no_status": lambda w: apply_api(w, {**x2b_plan(w.seed), "issues": {n: {k: v for k, v in ch.items() if k != "status"} for n, ch in x2b_plan(w.seed)["issues"].items()}}),
    "oracle_plus_collateral": lambda w: collateral(w, x2b_plan(w.seed)),
}

COMMON_ADV = {
    "null": lambda w: None,
    "report_only": lambda w: report(w.run_dir, "complete", "Done: all requested changes are made."),
}

TASKS = {
    "H1": dict(goal=H1_GOAL, verify=h1_verify, oracle=h1_oracle, alt=h1_alt, adv=H1_ADV, seed="v1", apps=["quillstack"]),
    "H2": dict(goal=H2_GOAL, verify=h2_verify, oracle=h2_oracle, alt=h2_alt, adv=H2_ADV, seed="v1", apps=["quillstack"]),
    "H3": dict(goal=H3_GOAL, verify=h3_verify, oracle=h3_oracle, alt=h3_alt, adv=H3_ADV, seed="v1", apps=["quillmail", "quillstack"]),
    "H4": dict(goal=H4_GOAL, verify=h4_verify, oracle=h4_oracle, alt=h4_alt, adv=H4_ADV, seed="v1", apps=["quillstack"]),
    "X1": dict(goal=X1_GOAL, verify=x1_verify, oracle=x1_oracle, alt=x1_alt, adv=X1_ADV, seed="v2", apps=["quillmail", "quillstack"]),
    "X1b": dict(goal=X1_GOAL, verify=x1b_verify, oracle=x1b_oracle, alt=x1b_alt, adv=X1B_ADV, seed="v3", apps=["quillmail", "quillstack"]),
    "X2b": dict(goal=X2_GOAL, verify=x2b_verify, oracle=x2b_oracle, alt=x2b_alt, adv=X2B_ADV, seed="v3", apps=["quillmail", "quillstack"]),
    "X2": dict(goal=X2_GOAL, verify=x2_verify, oracle=x2_oracle, alt=x2_alt, adv=X2_ADV, seed="v2", apps=["quillmail", "quillstack"]),
    "X3": dict(goal=X3_GOAL, verify=x3_verify, oracle=x3_oracle, alt=x3_alt, adv=X3_ADV, seed="v2", apps=["quillmail", "quillstack"]),
    "X4": dict(goal=X4_GOAL, verify=x4_verify, oracle=x4_oracle, alt=x4_alt, adv=X4_ADV, seed="v2", apps=["quillstack"]),
}


def count_checks(seed, tid):
    """Atomic checks, MedPractice style: one per required field change, comment, created-issue field, archived message,
    one per twin that must stay untouched (named in the seed assertions), plus report status and the no-collateral check."""
    P = {"H1": h1_plan, "H2": h2_plan, "H3": h3_plan, "H4": lambda s: h4_plan(s)[0], "X1": x1_plan, "X2": x2_plan, "X3": x3_plan,
         "X4": lambda s: x4_plan(s)[0]}[tid](seed)
    n = sum(len(ch) for ch in P["issues"].values()) + len(P["comments"]) + len(P["mail"]) + sum(9 for _ in P["creates"])
    return n + 2
