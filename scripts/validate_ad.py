"""Validate a draft RSA + assets against Google Ads editorial rules.

Deterministic checks from docs/playbook/ads-rsa-spec.md §5/§6/§8 and ads-assets-spec.md §5.
Judgment checks (angle coverage, LP match, distinctness of meaning) stay
with the human/agent.

Input JSON format:
{
  "headlines": [{"text": "...", "pin": 1}, {"text": "..."}, ...],
  "descriptions": ["...", "..."],
  "path1": "...", "path2": "...",
  "sitelinks": [{"title": "...", "description_1": "...", "description_2": "..."}],
  "callouts": ["..."],
  "structured_snippets": [{"header": "Services", "values": ["...", ...]}]
}
All keys optional except headlines/descriptions.

Usage:  validate_ad.py draft.json
Exit 0 = no errors (warnings allowed), 1 = errors found.
"""

import json
import re
import sys

issues = []


def err(msg):
    issues.append(("ERROR", msg))


def warn(msg):
    issues.append(("WARNING", msg))


SUPERLATIVES = re.compile(
    r"(?<![\w★.])(#1|best|cheapest|top rated|number one|guaranteed cheapest)(?![\w])",
    re.IGNORECASE,
)
PHONE = re.compile(r"\d{3}[-.\s]\d{3}[-.\s]\d{4}|\(\d{3}\)\s?\d{3}")
BANNED_SYMBOLS = re.compile(r"[→>]{2,}|[!?.]{2,}|\*|★{2,}|[\U0001F300-\U0001FAFF]")
GIMMICK_SPACING = re.compile(r"\b(?:[A-Za-z][\s.\-*]){2,}[A-Za-z]\b")


def all_caps_words(text):
    return [w for w in re.findall(r"[A-Z]{2,}", text)
            if w not in {"AI", "SEO", "GTA", "USA", "FAQ", "CRM", "PPC", "RSA"}]


def check_text(label, text, max_len, allow_exclaim):
    if len(text) > max_len:
        err(f"{label}: {len(text)} chars (max {max_len}): {text!r}")
    if not allow_exclaim and "!" in text:
        err(f"{label}: exclamation mark not allowed here: {text!r}")
    caps = all_caps_words(text)
    if caps:
        err(f"{label}: ALL-CAPS word(s) {caps}: {text!r}")
    if BANNED_SYMBOLS.search(text):
        err(f"{label}: banned symbol/repeated punctuation: {text!r}")
    if GIMMICK_SPACING.search(text):
        warn(f"{label}: possible gimmicky spacing: {text!r}")
    if PHONE.search(text):
        err(f"{label}: phone number in copy (use call assets): {text!r}")
    if SUPERLATIVES.search(text):
        err(f"{label}: unsubstantiated superlative: {text!r}")
    if re.search(r"\b(we|our|us)\b", text, re.IGNORECASE):
        warn(f"{label}: talks about 'we/our/us' instead of the customer: {text!r}")
    if re.search(r"\bclick here\b", text, re.IGNORECASE):
        warn(f"{label}: 'click here' scores poorly: {text!r}")


def main(path):
    with open(path) as f:
        ad = json.load(f)

    headlines = ad.get("headlines", [])
    descriptions = ad.get("descriptions", [])

    # Headlines
    if len(headlines) < 3:
        err(f"only {len(headlines)} headlines (min 3)")
    if len(headlines) != 15:
        warn(f"{len(headlines)} headlines, fill all 15 for +6% CTR")
    pinned1 = [h for h in headlines if h.get("pin") == 1]
    other_pins = [h for h in headlines if h.get("pin") not in (None, 1)]
    if len(pinned1) != 3:
        warn(f"{len(pinned1)} headlines pinned to slot 1 (spec: 3 keyword variants)")
    if other_pins:
        err(f"{len(other_pins)} headline(s) pinned beyond slot 1, single-pin only "
            f"(costs 10-15% performance): {[h['text'] for h in other_pins]}")
    seen = set()
    for i, h in enumerate(headlines, 1):
        text = h["text"]
        check_text(f"headline {i}", text, 30, allow_exclaim=False)
        key = re.sub(r"\W+", "", text.lower())
        if key in seen:
            err(f"headline {i}: duplicate of another headline: {text!r}")
        seen.add(key)

    # Descriptions
    if len(descriptions) < 2:
        err(f"only {len(descriptions)} descriptions (min 2)")
    if len(descriptions) != 4:
        warn(f"{len(descriptions)} descriptions, fill all 4")
    total_exclaims = 0
    seen = set()
    for i, d in enumerate(descriptions, 1):
        check_text(f"description {i}", d, 90, allow_exclaim=True)
        if d.count("!") > 1:
            err(f"description {i}: more than one exclamation mark")
        total_exclaims += d.count("!")
        if not 61 <= len(d) <= 70:
            warn(f"description {i}: {len(d)} chars (sweet spot 61-70)")
        key = re.sub(r"\W+", "", d.lower())
        if key in seen:
            err(f"description {i}: duplicate description")
        seen.add(key)
    if total_exclaims > 1:
        err(f"{total_exclaims} exclamation marks across descriptions (max 1 per ad)")

    # Paths
    for k in ("path1", "path2"):
        if ad.get(k) and len(ad[k]) > 15:
            err(f"{k}: {len(ad[k])} chars (max 15): {ad[k]!r}")

    # Sitelinks
    sitelinks = ad.get("sitelinks", [])
    if sitelinks and len(sitelinks) < 2:
        warn("fewer than 2 sitelinks, none will show")
    urls = set()
    for i, s in enumerate(sitelinks, 1):
        t = s.get("title", "")
        if len(t) > 25:
            err(f"sitelink {i} title: {len(t)} chars (max 25): {t!r}")
        elif len(t) > 15:
            warn(f"sitelink {i} title: {len(t)} chars (aim 12-15 for mobile): {t!r}")
        if t.lower() in {"learn more", "about us", "contact", "about"}:
            warn(f"sitelink {i}: generic title kills CTR: {t!r}")
        for dk in ("description_1", "description_2"):
            if s.get(dk) and len(s[dk]) > 35:
                err(f"sitelink {i} {dk}: {len(s[dk])} chars (max 35)")
        u = s.get("final_url")
        if u:
            if u in urls:
                err(f"sitelink {i}: duplicate URL {u}")
            urls.add(u)

    # Callouts
    callouts = ad.get("callouts", [])
    if callouts and len(callouts) < 2:
        warn("fewer than 2 callouts, none will show")
    if callouts and len(callouts) < 8:
        warn(f"{len(callouts)} callouts (spec: 8-12)")
    for i, c in enumerate(callouts, 1):
        if len(c) > 25:
            err(f"callout {i}: {len(c)} chars (max 25): {c!r}")

    # Structured snippets
    for s in ad.get("structured_snippets", []):
        vals = s.get("values", [])
        if len(vals) < 3:
            err(f"snippet '{s.get('header')}': {len(vals)} values (min 3)")
        for v in vals:
            if len(v) > 25:
                err(f"snippet '{s.get('header')}' value: {len(v)} chars (max 25): {v!r}")

    errors = [m for lvl, m in issues if lvl == "ERROR"]
    for lvl, msg in issues:
        print(f"{lvl}: {msg}")
    print(f"\n{len(errors)} error(s), {len(issues) - len(errors)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
