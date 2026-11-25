"""Shared helpers for every script in this repo.

- Loads Google Ads API credentials from a .env file (never from the repo).
- Loads a client config (clients/<name>.yaml) so no account ID or brand name
  is ever hard-coded in a script.
- Runs GAQL and stores raw pulls as JSON in work/<client>/data/.
- Holds the negative keyword matching rules and the write-safety guard.

Every script takes --client clients/<name>.yaml.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- config

def arg_parser(description: str) -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--client", required=True, help="Path to clients/<name>.yaml")
    return ap


def load_config(path: str | Path) -> dict:
    import yaml
    p = Path(path)
    if not p.exists():
        sys.exit(f"Client config not found: {p}. Copy clients/example.yaml and fill it in.")
    cfg = yaml.safe_load(p.read_text()) or {}
    for key in ("slug", "customer_id"):
        if not cfg.get(key):
            sys.exit(f"{p}: '{key}' is required.")
    cfg["customer_id"] = digits(cfg["customer_id"])
    cfg["login_customer_id"] = digits(cfg.get("login_customer_id") or cfg["customer_id"])
    cfg.setdefault("campaign_roles", {})
    cfg.setdefault("brand_terms", [])
    cfg.setdefault("competitors", [])
    cfg.setdefault("niche", None)
    safety = cfg.setdefault("safety", {})
    safety.setdefault("allowed_customer_ids", [cfg["customer_id"]])
    safety["allowed_customer_ids"] = [digits(x) for x in safety["allowed_customer_ids"]]
    safety.setdefault("max_ops_per_run", 500)
    cfg["_path"] = str(p)
    return cfg


def digits(x) -> str:
    return re.sub(r"\D", "", str(x))


def niche_dir(cfg: dict) -> Path | None:
    return (REPO / "niches" / cfg["niche"]) if cfg.get("niche") else None


def work_dir(cfg: dict, *parts: str) -> Path:
    d = REPO / "work" / cfg["slug"]
    for p in parts:
        d = d / p
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------- credentials

ENV_KEYS = ["GOOGLE_ADS_DEVELOPER_TOKEN", "GOOGLE_ADS_CLIENT_ID",
            "GOOGLE_ADS_CLIENT_SECRET", "GOOGLE_ADS_REFRESH_TOKEN"]


def env_path() -> Path:
    for cand in [os.environ.get("GOOGLE_ADS_ENV", ""), str(REPO / ".env"), "~/.google-ads.env"]:
        if cand and Path(cand).expanduser().exists():
            return Path(cand).expanduser()
    sys.exit("No credentials found. Create .env in the repo root (see .env.example and docs/setup.md) "
             "or set GOOGLE_ADS_ENV to the path of your .env file.")


def load_env() -> Path:
    from dotenv import load_dotenv
    p = env_path()
    load_dotenv(p, override=False)
    missing = [k for k in ENV_KEYS if not os.environ.get(k)]
    if missing:
        sys.exit(f"{p} is missing: {', '.join(missing)}. See docs/setup.md.")
    return p


def client(cfg: dict, login_customer_id: str | None = None):
    load_env()
    from google.ads.googleads.client import GoogleAdsClient
    return GoogleAdsClient.load_from_dict({
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_ADS_REFRESH_TOKEN"],
        # Some accounts only answer when login_customer_id is the account itself
        # (direct user access), others only through the manager (MCC). Set it in
        # the client yaml; docs/setup.md explains how to tell.
        "login_customer_id": login_customer_id or cfg["login_customer_id"],
        "use_proto_plus": True,
    })


# ---------------------------------------------------------------- GAQL

def run(ga, cid: str, query: str) -> list[dict]:
    from google.protobuf.json_format import MessageToDict
    rows = []
    for batch in ga.search_stream(customer_id=cid, query=query):
        for r in batch.results:
            rows.append(MessageToDict(r._pb, preserving_proto_field_name=True))
    return rows


def api_error(e: Exception) -> str:
    s = str(e)
    i = s.find("message:")
    return s[i:i + 300] if i >= 0 else s[:300]


def save(cfg: dict, name: str, rows) -> Path:
    p = work_dir(cfg, "data") / f"{name}.json"
    p.write_text(json.dumps(rows))
    return p


def load(cfg: dict, name: str, default=None):
    p = work_dir(cfg, "data") / f"{name}.json"
    if not p.exists():
        if default is not None:
            return default
        sys.exit(f"Missing {p}. Run: python scripts/pull.py --client {cfg['_path']}")
    return json.loads(p.read_text())


def date_range(days: int, end: dt.date | None = None) -> str:
    end = end or dt.date.today()
    return f"segments.date BETWEEN '{end - dt.timedelta(days=days)}' AND '{end}'"


def g(row: dict, *keys, default=None):
    """Safe nested get: g(r, 'campaign', 'name').
    Proto-plus renames fields that clash with Python names ('type' becomes 'type_'); both spellings work."""
    cur = row
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k, cur.get(k + "_"))
    return default if cur is None else cur


def money(micros) -> float:
    return int(micros or 0) / 1e6


# ---------------------------------------------------------------- campaign roles

def role_of(cfg: dict, campaign_name: str) -> str:
    """Map a campaign to a role (generic, competitors, brand, ...) by name prefix.
    Roles come from campaign_roles in the client yaml. Unmatched -> 'other'."""
    for role, prefixes in cfg.get("campaign_roles", {}).items():
        for p in prefixes or []:
            if campaign_name.lower().startswith(str(p).lower()):
                return role
    return "other"


# ---------------------------------------------------------------- negative matching

_ws = re.compile(r"\s+")
_strip = re.compile(r"[^a-z0-9'&.\s]")


def norm(t: str) -> str:
    t = (t or "").lower().replace("’", "'")
    t = _strip.sub(" ", t)
    return _ws.sub(" ", t).strip()


def blocks(neg_text: str, match: str, query: str) -> bool:
    """True if a NEGATIVE keyword blocks the query.

    Negatives never expand to close variants (plurals, misspellings, synonyms):
      EXACT  = the whole query equals the term
      PHRASE = the words appear together, in order
      BROAD  = all words appear, any order
    """
    n, q = norm(neg_text), norm(query)
    if not n:
        return False
    if match == "EXACT":
        return q == n
    if match == "PHRASE":
        return f" {n} " in f" {q} "
    qw = set(q.split())
    return all(w in qw for w in n.split())


# ---------------------------------------------------------------- write safety

class WriteBlocked(SystemExit):
    pass


def guard_write(cfg: dict, cid: str, op_count: int, executing: bool) -> None:
    """Single chokepoint every live write passes. Raises to abort.

    1. The customer ID must be on the client's allowlist.
    2. The op count must be under the per-run cap (loop / blast-radius guard).
    3. Executing requires the APPLY_ENABLED=1 kill switch in the environment,
       on top of the --execute flag. Dry runs never need it.
    """
    allowed = cfg["safety"]["allowed_customer_ids"]
    if digits(cid) not in allowed:
        raise WriteBlocked(f"Refusing to write to {cid}: not in safety.allowed_customer_ids {allowed}.")
    cap = int(cfg["safety"]["max_ops_per_run"])
    if op_count > cap:
        raise WriteBlocked(f"Refusing: {op_count} operations exceeds safety.max_ops_per_run ({cap}).")
    if executing and os.environ.get("APPLY_ENABLED", "").strip().lower() not in {"1", "true", "yes", "on"}:
        raise WriteBlocked("Refusing to execute: set APPLY_ENABLED=1 for this command after a human approved the dry run.")


def log_change(cfg: dict, action: str, detail: dict) -> None:
    p = work_dir(cfg) / "changes.log.jsonl"
    rec = {"at": dt.datetime.now().isoformat(timespec="seconds"), "action": action, **detail}
    with p.open("a") as f:
        f.write(json.dumps(rec) + "\n")


def latest_backup(cfg: dict, max_age_hours: float = 24) -> Path | None:
    d = work_dir(cfg, "backups")
    bs = sorted(d.glob("negatives-*"))
    if not bs:
        return None
    b = bs[-1]
    age = (dt.datetime.now() - dt.datetime.fromtimestamp(b.stat().st_mtime)).total_seconds() / 3600
    return b if age <= max_age_hours else None


# ---------------------------------------------------------------- output

def write_xlsx(path: Path, sheets: list[tuple[str, list[str], list[list]]]) -> Path:
    from openpyxl import Workbook
    from openpyxl.styles import Font
    wb = Workbook()
    wb.remove(wb.active)
    for name, head, rows in sheets:
        ws = wb.create_sheet(name[:31])
        ws.append(head)
        for c in ws[1]:
            c.font = Font(bold=True)
        for r in rows:
            ws.append(r)
        ws.freeze_panes = "A2"
    wb.save(path)
    return path
