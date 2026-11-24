#!/usr/bin/env python3
"""Checks: slug format, i18n/aliases keys exist, every image file maps to a record.
Missing images are warnings (known gaps); everything else is an error. Exit 1 on errors."""
import json, os, sys, glob
sys.path.insert(0, os.path.dirname(__file__))
from lib.slug import SLUG_RE
from lib.paths import ROOT

E_ = lambda n: json.load(open(f"{ROOT}/data/entities/{n}.json", encoding="utf-8"))
ent = {n: E_(n) for n in ("killers", "survivors", "perks-killer", "perks-survivor", "addons-power", "addons-item",
                          "items", "offerings", "maps", "realms", "chapters")}
errors, warns = [], []

# slug format + parent references
for n, d in ent.items():
    for k in d:
        if not SLUG_RE.match(k): errors.append(f"{n}: bad slug {k!r}")
for k, v in ent["addons-power"].items():
    if k.split("/")[0] != v["killer"] or v["killer"] not in ent["killers"]: errors.append(f"addons-power: bad parent {k}")
for k, v in ent["addons-item"].items():
    if k.split("/")[0] != v["item"] or v["item"] not in ent["items"]: errors.append(f"addons-item: bad parent {k}")

# i18n / aliases keys
valid = dict(ent); valid["item-variants"] = {f"{t}/{v}": 1 for t, i in ent["items"].items() for v in i["variants"]}
for f in glob.glob(f"{ROOT}/data/i18n/*/*.json"):
    n = os.path.basename(f)[:-5]
    for k in json.load(open(f, encoding="utf-8")):
        if n not in valid or k not in valid[n]: errors.append(f"{os.path.relpath(f, ROOT)}: unknown key {k}")
for f in glob.glob(f"{ROOT}/data/aliases/*.json"):
    n = os.path.basename(f)[:-5]
    for k in json.load(open(f, encoding="utf-8")):
        if k not in ent[n]: errors.append(f"{os.path.relpath(f, ROOT)}: unknown key {k}")

# images <-> records
expected = {}
def exp(path, label): expected[path] = label
for k in ent["perks-killer"]: exp(f"perks/killer/{k}.webp", k)
for k in ent["perks-survivor"]: exp(f"perks/survivor/{k}.webp", k)
for k in ent["offerings"]: exp(f"offerings/{k}.webp", k)
for k in ent["survivors"]: exp(f"survivors/portrait/{k}.webp", k)
for k in ent["killers"]:
    for kind in ("portrait", "lore"): exp(f"killers/{kind}/{k}.webp", k)
    exp(f"powers/{k}/icon.webp", k)
for k in ent["addons-power"]: p, l = k.split("/"); exp(f"powers/{p}/addons/{l}.webp", k)
for t, v in ent["items"].items():
    exp(f"items/{t}/icon.webp", t)
    for vs in v["variants"]: exp(f"items/{t}/variants/{vs}.webp", f"{t}/{vs}")
for k in ent["addons-item"]: p, l = k.split("/"); exp(f"items/{p}/addons/{l}.webp", k)
have = {os.path.relpath(p, f"{ROOT}/images") for p in glob.glob(f"{ROOT}/images/**/*", recursive=True) if os.path.isfile(p)}
for p in sorted(have - set(expected)): errors.append(f"images/{p}: no data record")
# a variant sharing its item's name uses icon.webp (e.g. flashlight); not a gap
for p in sorted(set(expected) - have):
    if "/variants/" in p and f"items/{p.split('/')[1]}/icon.webp" in have and p.split("/")[1] == os.path.basename(p)[:-5]: continue
    warns.append(f"missing image: {p}")

print(f"{len(errors)} errors, {len(warns)} warnings")
for e in errors: print("ERROR", e)
for w in warns: print("warn ", w)
sys.exit(1 if errors else 0)
