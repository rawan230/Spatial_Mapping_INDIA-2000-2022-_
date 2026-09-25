"""Install the audit updates into each step repository (files only; git is run separately)."""
import glob
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(__file__))
from add_audit_banners import RULES  # noqa: E402  (same superseded-statement rules as the root docs)

ROOT = r"D:\FOREST FIRE MAPPING(INDIA)"
RES = os.path.join(ROOT, "results")
DOCS = os.path.join(RES, "repo_audit_docs")
MARK = "<!-- AUDIT-UPDATE-2026-09-25 -->"
man = json.load(open(os.path.join(DOCS, "manifest.json")))


def banner(text, name):
    if MARK in text:
        return None
    hits = [msg for pat, msg in RULES if re.search(pat, text, flags=re.I)]
    b = [MARK, "> ### Audit update (2026-09-25)",
         "> This repository's step was recalculated independently from the raw data in a full end-to-end audit.",
         "> **Corrected results, reproduction checks and audit code: [`AUDIT_2026-09-25.md`](AUDIT_2026-09-25.md)** and `audit_2026-09-25/`.",
         "> Earlier text below is kept for the record (it also remains in the git history). Statements superseded by the audit:", ">"]
    b += [f"> - {h}" for h in hits] or ["> - None of the specific numbers in this file were superseded; see `AUDIT_2026-09-25.md` for the audited results of this step."]
    b += [MARK, ""]
    lines = text.split("\n")
    ins = 1 if lines and lines[0].startswith("#") else 0
    return "\n".join(lines[:ins] + ([""] if ins else []) + b + lines[ins:])


report = {}
for repo, spec in man.items():
    rp = os.path.join(ROOT, repo)
    short = repo.split(" ")[0][:40]
    shutil.copy(os.path.join(DOCS, short, "AUDIT_2026-09-25.md"), os.path.join(rp, "AUDIT_2026-09-25.md"))
    ad = os.path.join(rp, "audit_2026-09-25")
    os.makedirs(ad, exist_ok=True)
    for s in spec["scripts"] + ["trend_stats.py"] * any(x.startswith(("recalc_02", "recalc_04", "recalc_05")) for x in spec["scripts"]):
        shutil.copy(os.path.join(RES, "code", s), ad)
    os.makedirs(os.path.join(ad, "results"), exist_ok=True)
    for r in spec["results"]:
        shutil.copy(os.path.join(RES, r), os.path.join(ad, "results", os.path.basename(r)))
    open(os.path.join(ad, "README.md"), "w", encoding="utf-8").write(
        "# Audit code and results (2026-09-24/25)\n\nScripts copied from the project-level audit (`results/code/` in the project root). "
        "Paths inside them refer to the author's project folder (`D:\\FOREST FIRE MAPPING(INDIA)`); adjust `audit_common.py` to re-run. "
        "`results/` holds the small report and metric files that the numbers in `../AUDIT_2026-09-25.md` are read from.\n")
    changed = []
    if repo == "Physics_Informed_FireRisk_Model":   # Design_and_Paper = copies of the (already updated) root docs
        for p in glob.glob(os.path.join(rp, "Design_and_Paper", "*.md")):
            src = os.path.join(ROOT, os.path.basename(p))
            if os.path.exists(src):
                shutil.copy(src, p); changed.append("Design_and_Paper/" + os.path.basename(p))
    for p in glob.glob(os.path.join(rp, "**", "*.md"), recursive=True):
        rel = os.path.relpath(p, rp).replace("\\", "/")
        if rel.startswith(("old_versions/", "audit_2026-09-25/", "Design_and_Paper/")) or rel == "AUDIT_2026-09-25.md":
            continue
        t = open(p, encoding="utf-8").read()
        new = banner(t, rel)
        if new:
            open(p, "w", encoding="utf-8").write(new); changed.append(rel)
    report[repo] = changed
    print(f"{repo[:45]:47s} updated: {changed}")
