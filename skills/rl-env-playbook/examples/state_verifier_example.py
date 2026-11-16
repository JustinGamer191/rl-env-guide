"""Toy two-app world (Billing + Chat) stored in one JSON file, plus agents and two verifiers.
Goal shown to the agent:
  "In Billing, find Acme Inc's overdue invoice. Post its invoice number, amount and due date
   in #finance in Chat, then report complete."
"""
import copy, json, re, sys
from datetime import datetime

SEED = {
    "billing": {"invoices": [
        {"id": "INV-1042", "customer": "Acme Inc", "amount_cents": 124050, "due": "2026-11-03", "status": "overdue"},
        {"id": "INV-1043", "customer": "Acme Corp", "amount_cents": 98000, "due": "2026-11-01", "status": "overdue"},
        {"id": "INV-1044", "customer": "Acme Inc", "amount_cents": 30000, "due": "2026-12-01", "status": "open"},
    ]},
    "chat": {"channels": {
        "#finance": [{"id": 1, "author": "dana", "text": "Month-end close starts Monday"}],
        "#general": [{"id": 2, "author": "lee", "text": "Lunch at noon"}],
        "#random": [],
    }, "next_id": 3},
    "ui_cache": {},          # what the front end shows; agent-writable like localStorage/window state
    "ledger": [],            # WorldEvent-style log
    "report": None,          # report_complete / report_infeasible
}


class App:  # the only API agents get (stand-in for the UI)
    def __init__(self): self.s = copy.deepcopy(SEED)
    def invoices(self): return copy.deepcopy(self.s["billing"]["invoices"])
    def post(self, ch, text):
        i = self.s["chat"]["next_id"]; self.s["chat"]["next_id"] += 1
        self.s["chat"]["channels"][ch].append({"id": i, "author": "agent", "text": text})
        self.s["ledger"].append({"type": "message_posted", "channel": ch, "id": i})
    def delete(self, ch, mid):
        self.s["chat"]["channels"][ch] = [m for m in self.s["chat"]["channels"][ch] if m["id"] != mid]
    def mark_paid(self, inv):
        for x in self.s["billing"]["invoices"]:
            if x["id"] == inv: x["status"] = "paid"
    def report_complete(self, text): self.s["report"] = {"status": "complete", "text": text}


def target(app):
    return next(x for x in app.invoices() if x["customer"] == "Acme Inc" and x["status"] == "overdue")

def oracle(app):
    t = target(app); app.post("#finance", f"{t['id']}: ${t['amount_cents']/100:,.2f} due Nov 3, 2026"); app.report_complete("done")
def oracle_alt_format(app):
    app.post("#finance", "Acme Inc overdue invoice inv 1042, amount 1240.5 USD, due 2026-11-03"); app.report_complete("posted")
def null(app): pass
def report_only(app): app.report_complete("Posted INV-1042, $1,240.50, due 2026-11-03 in #finance")
def wrong_entity(app):
    x = app.invoices()[1]; app.post("#finance", f"{x['id']}: ${x['amount_cents']/100:,.2f} due {x['due']}"); app.report_complete("done")
def spray(app):
    for ch in list(app.s["chat"]["channels"]):
        for x in app.invoices(): app.post(ch, f"{x['id']} ${x['amount_cents']/100:,.2f} due {x['due']}")
    app.report_complete("done")
def list_all_in_one(app):
    app.post("#finance", " / ".join(f"{x['id']} ${x['amount_cents']/100:,.2f} due {x['due']}" for x in app.invoices())); app.report_complete("done")
def collateral(app):
    oracle(app); app.mark_paid("INV-1042")
def fake_ui_state(app):
    app.s["ui_cache"]["#finance.lastMessage"] = "INV-1042: $1,240.50 due 2026-11-03"
    app.s["ledger"].append({"type": "message_posted", "channel": "#finance", "id": 99}); app.report_complete("done")
def wrong_channel(app):
    oracle_post = target(app); app.post("#general", f"{oracle_post['id']}: $1,240.50 due 2026-11-03"); app.report_complete("done")

AGENTS = [oracle, oracle_alt_format, null, report_only, wrong_entity, spray, list_all_in_one, collateral, fake_ui_state, wrong_channel]


def lazy_verifier(s):
    """Typical lazy judge: substring anywhere, trusts the report and the UI cache."""
    blob = json.dumps(s["report"]) + json.dumps(s["chat"]) + json.dumps(s["ui_cache"])
    return 1.0 if ("1,240.50" in blob or "1240.5" in blob) else 0.0


# ---------- hardened, state-based verifier ----------
def money(text):  # every money-like number in the text, as cents
    return {round(float(m.replace(",", "")) * 100) for m in re.findall(r"\$?\b(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\b", text)}

def dates(text):
    out = set()
    for pat, fmt in ((r"\d{4}-\d{2}-\d{2}", "%Y-%m-%d"), (r"[A-Z][a-z]{2,8}\.? \d{1,2},? \d{4}", None), (r"\d{1,2}/\d{1,2}/\d{4}", "%m/%d/%Y")):
        for m in re.findall(pat, text):
            for f in ([fmt] if fmt else ["%b %d, %Y", "%B %d, %Y", "%b %d %Y", "%B %d %Y"]):
                try: out.add(datetime.strptime(m.replace(".", ""), f).date().isoformat()); break
                except ValueError: pass
    return out

def inv_ids(text): return {"INV-" + n for n in re.findall(r"inv[\s#-]*(\d{4})", text, re.I)}

def hardened_verifier(s, why=None):
    why = why if why is not None else []
    seed = SEED
    inv = {x["id"]: x for x in seed["billing"]["invoices"]}
    want = next(x for x in seed["billing"]["invoices"] if x["customer"] == "Acme Inc" and x["status"] == "overdue")
    # 1. collateral: everything except new messages in #finance must equal the seed
    if s["billing"] != seed["billing"]: why.append("billing changed"); return 0.0
    for ch, msgs in s["chat"]["channels"].items():
        seeded = seed["chat"]["channels"].get(ch, [])
        if msgs[:len(seeded)] != seeded: why.append(f"seed messages altered in {ch}"); return 0.0
        if ch != "#finance" and len(msgs) != len(seeded): why.append(f"extra message in {ch}"); return 0.0
    new = s["chat"]["channels"]["#finance"][len(seed["chat"]["channels"]["#finance"]):]
    # 2. the outcome lives in backend state (chat table), never in report text, ui_cache or the ledger alone
    if len(new) != 1: why.append(f"{len(new)} new messages in #finance, want exactly 1"); return 0.0
    t = new[0]["text"]
    ids, amts, ds = inv_ids(t), money(t), dates(t)
    if ids != {want["id"]}: why.append(f"invoice ids {sorted(ids)}"); return 0.0          # no listing every answer
    if want["amount_cents"] not in amts: why.append(f"amount missing, saw {sorted(amts)}"); return 0.0
    if any(a == x["amount_cents"] for a in amts for x in inv.values() if x["id"] != want["id"]): why.append("near-miss amount present"); return 0.0
    if ds != {want["due"]}: why.append(f"due dates {sorted(ds)}"); return 0.0
    # 3. ledger must agree with real state (forged events = 0)
    real = {(ch, m["id"]) for ch, ms in s["chat"]["channels"].items() for m in ms}
    if any((e["channel"], e["id"]) not in real for e in s["ledger"] if e["type"] == "message_posted"): why.append("ledger event with no real message"); return 0.0
    # 4. must have reported complete (not infeasible); report text itself is never evidence
    if not s["report"] or s["report"]["status"] != "complete": why.append("did not report complete"); return 0.0
    return 1.0


if __name__ == "__main__":
    print(f"{'agent':<20}{'lazy':>6}{'hardened':>10}  reason (hardened)")
    for a in AGENTS:
        for run in range(3 if a in (oracle, null) else 1):   # determinism: reset each time
            app = App(); a(app); why = []
            h = hardened_verifier(app.s, why)
            print(f"{a.__name__ + ('' if run == 0 else f' #{run+1}'):<20}{lazy_verifier(app.s):>6.0f}{h:>10.0f}  {'; '.join(why)}")
    assert json.dumps(App().s) == json.dumps(SEED), "reset not exact"
    print("reset check: fresh App() state == SEED")
