"""Slug rule (see docs/naming.md)."""
import re, unicodedata

def slug(name: str) -> str:
    s = re.sub(r"[™®©]", "", name)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

def file_slug(filename: str) -> str:
    """Normalise a legacy filename (Detective_S-Hunch.png) to a slug."""
    import os
    return slug(os.path.splitext(os.path.basename(filename))[0])

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*(/[a-z0-9]+(-[a-z0-9]+)*)?$")
