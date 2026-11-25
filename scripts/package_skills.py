"""Zip each skills/<name>/ folder into dist/<name>.skill for upload to Claude (Cowork / claude.ai).

  python scripts/package_skills.py
"""
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
dist = REPO / "dist"
dist.mkdir(exist_ok=True)
for sk in sorted((REPO / "skills").iterdir()):
    if not (sk / "SKILL.md").exists():
        continue
    out = dist / f"{sk.name}.skill"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in sorted(sk.rglob("*")):
            if f.is_file() and "__pycache__" not in f.parts:
                z.write(f, f"{sk.name}/{f.relative_to(sk)}")
    print(f"{out.relative_to(REPO)}")
