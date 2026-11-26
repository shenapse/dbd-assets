# Naming rules

The **slug** is the only ID. It is also the file/folder name.

```
slug    := segment | segment "/" segment      # second form only for add-ons: <parent>/<leaf>
segment := [a-z0-9]+ ( "-" [a-z0-9]+ )*
```

- Source is the English display name: fold accents (NFKD), remove ™ ® ©, replace every other run of
  non-alphanumerics with `-`, lowercase, trim `-`. (`Bonnie's` -> `bonnie-s`, `Matias'` -> `matias`.)
  Implementation: `scripts/lib/slug.py`.
- A slug is **frozen** once created. Renames change `name`, not the slug or the file.
- Slugs are unique per type (killer perks, survivor perks, power add-ons, item add-ons are separate types).
- Add-on identity includes its parent: `the-nurse/pocket-watch` != `the-dark-lord/pocket-watch`.

## Where things live

| Record | Data | Image |
|---|---|---|
| killer | `data/entities/killers.json` | `images/killers/{portrait,lore}/<slug>.webp` |
| killer power | (same killer slug) | `images/powers/<killer>/icon.webp` |
| power add-on `<killer>/<leaf>` | `data/entities/addons-power.json` | `images/powers/<killer>/addons/<leaf>.webp` |
| item | `data/entities/items.json` (variants nested as a field) | none (items have no representative icon) |
| item variant `<item>/<variant>` | `items.json -> variants` | `images/items/<item>/variants/<variant>.webp`; a variant whose slug equals the item slug (flashlight, toolbox, firecracker) is `images/items/<item>/icon.webp` instead |
| item add-on `<item>/<leaf>` | `data/entities/addons-item.json` | `images/items/<item>/addons/<leaf>.webp` |
| killer / survivor perk | `perks-killer.json` / `perks-survivor.json` | `images/perks/{killer,survivor}/<slug>.webp` |
| survivor | `survivors.json` | `images/survivors/portrait/<slug>.webp` |
| offering | `offerings.json` | `images/offerings/<slug>.webp` |
| map (optional icon) | `maps.json` | `images/maps/<slug>.webp` |
| realm (optional artwork) | `realms.json` | `images/realms/<slug>.webp` |
| empty-slot UI art | none (generic UI art, not a record) | `images/ui/empty-slot/<slot>.webp`, slot = `perk`\|`item`\|`addon`\|`offering`; fixed allow-list in `validate.py` |

Map artwork import sources, dimensions, and SHA-256 checksums are recorded in `docs/map-image-sources.json`.

Translations: `data/i18n/<lang>/<type>.json`, keyed by the same slugs (`item-variants` keyed `<item>/<variant>`).
Aliases/abbreviations: `data/aliases/<type>.json` (currently `killers`, `maps`, `perks-killer`, `perks-survivor`), keyed by slug:
`{"<slug>": {"aliases": [...], "abbreviations": [...]}}` (either field optional). `abbreviations` are short capitalised tokens
without spaces (`DS`, `CoH`); everything else (`Pebble`) is an `aliases` entry. Do not list a perk's own `name` or `renamed_from.name`
as an alias: they already resolve. `validate.py` checks perk alias files: keys must be slugs of the matching perks file, entries must be
non-empty strings, and no alias may collide (case/space/punctuation-insensitive: lowercase, strip `[\s\-_'.&"]`) with another perk's
name, `renamed_from.name` or alias on the same side (killer and survivor perks are resolved separately).

## Renamed perks
When BHVR renames a perk, the record gets the new slug/`name` and keeps its old image file untouched:
`"renamed_from": {"slug": "decisive-strike", "name": "Decisive Strike"}` -> image stays at `images/perks/survivor/decisive-strike.webp`.
`validate.py` resolves the image through `renamed_from.slug` and errors if that slug is also a live record or its file is claimed twice.
Currently supported for killer/survivor perks only.

## Scripts
- `scripts/validate.py` — slug format, referential integrity, image <-> record mapping, image dimensions (errors fail; known-gap missing images and images smaller than the per-category minimum warn). Run with `uv run python scripts/validate.py`.
- `scripts/build_index.py` — writes `dist/index/*.json` and `dist/manifest.json` (slug path, size, sha1). Generated, git-ignored.
