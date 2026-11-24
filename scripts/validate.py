#!/usr/bin/env python3
"""Checks: slug format, i18n/aliases keys exist, every image file maps to a record.
Missing images are warnings (known gaps); everything else is an error. Exit 1 on errors."""
import json, os, re, sys, glob
from PIL import Image
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

# perk aliases/abbreviations: non-empty strings; no alias may equal (normalized) another perk's name, renamed_from.name or alias on the same side
norm = lambda s: re.sub(r"[\s\-_'.&\"]+", "", s.lower())
for side in ("killer", "survivor"):
    f, recs = f"{ROOT}/data/aliases/perks-{side}.json", ent[f"perks-{side}"]
    if not os.path.exists(f): continue
    rel, owner = os.path.relpath(f, ROOT), {}
    for k, v in recs.items():
        for nm in (v["name"], (v.get("renamed_from") or {}).get("name")):
            if nm: owner.setdefault(norm(nm), set()).add(k)
    for k, d in json.load(open(f, encoding="utf-8")).items():
        for field, vals in d.items():
            if field not in ("aliases", "abbreviations") or not isinstance(vals, list):
                errors.append(f"{rel}: {k}: expected only list fields 'aliases'/'abbreviations', got {field!r}"); continue
            for a in vals:
                if not isinstance(a, str) or not a.strip(): errors.append(f"{rel}: {k}: empty/non-string {field} entry {a!r}"); continue
                owner.setdefault(norm(a), set()).add(k)
    # collisions: any normalized string claimed by more than one perk (own name/renamed_from/alias of a different slug)
    for n, ks in sorted(owner.items()):
        if len(ks) > 1: errors.append(f"{rel}: '{n}' is claimed by multiple perks: {sorted(ks)}")

# images <-> records
expected = {}
def exp(path, label): expected[path] = label
# A renamed perk keeps its old file: "renamed_from": {"slug": <old slug>, "name": <old name>} -> image stored under the old slug.
for side in ("killer", "survivor"):
    recs = ent[f"perks-{side}"]
    for k, v in recs.items():
        r = v.get("renamed_from")
        if r is None: exp(f"perks/{side}/{k}.webp", k); continue
        old = r.get("slug", "") if isinstance(r, dict) else ""
        if not SLUG_RE.match(old) or not r.get("name"): errors.append(f"perks-{side}: {k}: renamed_from needs valid 'slug' and 'name'"); continue
        if old in recs: errors.append(f"perks-{side}: {k}: renamed_from slug '{old}' is also a live record")
        path = f"perks/{side}/{old}.webp"
        if path in expected: errors.append(f"perks-{side}: {k}: image {path} is already claimed by '{expected[path]}'")
        exp(path, f"{k} (renamed from {old})")
for k in ent["offerings"]: exp(f"offerings/{k}.webp", k)
for k in ent["survivors"]: exp(f"survivors/portrait/{k}.webp", k)
for k in ent["killers"]:
    exp(f"killers/portrait/{k}.webp", k)
    exp(f"powers/{k}/icon.webp", k)
for k in ent["addons-power"]: p, l = k.split("/"); exp(f"powers/{p}/addons/{l}.webp", k)
for t, v in ent["items"].items():
    # An item has no representative icon of its own. Only the variant sharing the item's slug (flashlight, toolbox,
    # firecracker) is stored as icon.webp; every other variant (incl. the uncommon one, e.g. artisan-s-fog-vial,
    # dull-key, scribbled-map, first-aid-kit) lives in variants/.
    for vs in v["variants"]:
        if vs == t: exp(f"items/{t}/icon.webp", f"{t}/{vs}")
        else: exp(f"items/{t}/variants/{vs}.webp", f"{t}/{vs}")
for k in ent["addons-item"]: p, l = k.split("/"); exp(f"items/{p}/addons/{l}.webp", k)
have = {os.path.relpath(p, f"{ROOT}/images") for p in glob.glob(f"{ROOT}/images/**/*", recursive=True) if os.path.isfile(p)}
# Generic UI art (not records): fixed allow-list, must exist, nothing else allowed under ui/.
UI_IMAGES = {f"ui/empty-slot/{s}.webp" for s in ("perk", "item", "addon", "offering")}
for p in sorted(UI_IMAGES - have): errors.append(f"images/{p}: expected UI image is missing")
for p in sorted(have - set(expected)):
    if p in UI_IMAGES: continue
    errors.append(f"images/{p}: " + ("unexpected file under images/ui/ (allow-list in scripts/validate.py)" if p.startswith("ui/") else "no data record"))
# Categories where record <-> image must match both ways: perks, power add-ons, items (+variants), item add-ons, offerings.
STRICT = ("perks/", "offerings/", "items/")
is_strict = lambda p: p.startswith(STRICT) or (p.startswith("powers/") and "/addons/" in p)
allow_f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "known_missing_images.txt")
allow = set()
if os.path.exists(allow_f):
    allow = {l.strip() for l in open(allow_f, encoding="utf-8") if l.strip() and not l.startswith("#")}
missing = set()
for p in sorted(set(expected) - have):
    missing.add(p)
    if not is_strict(p): warns.append(f"missing image: {p}")
    elif p not in allow:
        errors.append(f"images/{p}: record '{expected[p]}' exists in data/ but has no image file. "
                      f"Add the image, or remove the record. (Known gaps: scripts/known_missing_images.txt)")
for p in sorted(allow - missing):
    errors.append(f"scripts/known_missing_images.txt: '{p}' is listed but is no longer missing (or has no record); remove the line")
for p in sorted(allow & missing): warns.append(f"missing image (known gap): {p}")

# image dimensions (warnings only): larger is fine; warn only if width or height is below the minimum.
# Minimums sit just under what the bulk of each category uses, so trimmed/cropped art does not trigger.
# First matching rule wins.
MIN_SIZES = [(r"^perks/", (256, 256)), (r"^offerings/", (256, 256)), (r"^powers/", (256, 256)), (r"^items/", (256, 256)),
             (r"^(killers/portrait|survivors/portrait)/", (400, 800))]
for p in sorted(have):
    want = next((sz for rx, sz in MIN_SIZES if re.match(rx, p)), None)
    if want is None or not p.endswith(".webp"): continue
    with Image.open(f"{ROOT}/images/{p}") as im: got = im.size
    if got[0] < want[0] or got[1] < want[1]:
        warns.append(f"image too small: images/{p} is {got[0]}x{got[1]}, minimum {want[0]}x{want[1]}")

print(f"{len(errors)} errors, {len(warns)} warnings")
for e in errors: print("ERROR", e)
for w in warns: print("warn ", w)
sys.exit(1 if errors else 0)
