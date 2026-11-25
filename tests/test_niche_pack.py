"""The shipped niche pack must pass its own gates: no starter negative may block a seller search
on the allow-list, unless the list is a deliberate routing or out-of-area list."""
import re
from pathlib import Path

import pytest
import yaml

from gads import blocks, norm

NICHES = Path(__file__).resolve().parent.parent / "niches"


@pytest.mark.parametrize("niche", [p.name for p in NICHES.iterdir() if (p / "negatives.yaml").exists()])
def test_starter_negatives_never_block_allow_list(niche):
    d = NICHES / niche
    lists = yaml.safe_load((d / "negatives.yaml").read_text())["lists"]
    allow = [norm(l) for l in (d / "allow-list.txt").read_text().splitlines() if l.strip() and not l.startswith("#")]
    hits = []
    for l in lists:
        if l.get("exempt_from_intent_gate"):
            continue
        for grp, terms in l["groups"].items():
            for t in terms:
                for q in allow:
                    if blocks(t, l.get("match", "PHRASE"), q):
                        hits.append((l["name"], t, q))
    assert not hits, hits


@pytest.mark.parametrize("niche", [p.name for p in NICHES.iterdir() if (p / "intent.yaml").exists()])
def test_intent_pattern_recognises_allow_list(niche):
    d = NICHES / niche
    intent = yaml.safe_load((d / "intent.yaml").read_text())
    rx = re.compile(intent["customer_intent"])
    allow = [norm(l) for l in (d / "allow-list.txt").read_text().splitlines() if l.strip() and not l.startswith("#")]
    missed = [q for q in allow if not rx.search(q)]
    assert len(missed) <= len(allow) * 0.15, missed     # most seller searches must be recognised


def test_no_duplicate_terms_inside_a_list():
    for d in NICHES.iterdir():
        p = d / "negatives.yaml"
        if not p.exists():
            continue
        for l in yaml.safe_load(p.read_text())["lists"]:
            terms = [norm(t) for ts in l["groups"].values() for t in ts]
            dupes = {t for t in terms if terms.count(t) > 1}
            assert not dupes, (l["name"], dupes)
