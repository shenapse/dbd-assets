#!/usr/bin/env python3
"""Generate dist/index/*.json (entities merged with names) and dist/manifest.json (slug -> path, size, sha1)."""
import hashlib, json, os, sys, glob
sys.path.insert(0, os.path.dirname(__file__))
from lib.paths import ROOT
out = f"{ROOT}/dist"; os.makedirs(f"{out}/index", exist_ok=True)
for f in glob.glob(f"{ROOT}/data/entities/*.json"):
    n = os.path.basename(f)
    data = json.load(open(f, encoding="utf-8"))
    json.dump(data, open(f"{out}/index/{n}", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
man = {}
for p in sorted(glob.glob(f"{ROOT}/images/**/*.webp", recursive=True)):
    rel = os.path.relpath(p, f"{ROOT}/images"); b = open(p, "rb").read()
    man[rel] = {"size": len(b), "sha1": hashlib.sha1(b).hexdigest()}
json.dump(man, open(f"{out}/manifest.json", "w"), indent=1)
print(f"index: {len(glob.glob(out + '/index/*'))} files; manifest: {len(man)} images")
