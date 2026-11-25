# dbd-assets

Dead by Daylight vocabulary data and icon/art assets.

- `data/` — vocabulary: `entities/` (canonical records), `i18n/<lang>/`, `aliases/` (killers, maps, killer/survivor perks)
- `images/` — WebP masters, laid out by slug (see `docs/naming.md`); `images/ui/` holds generic UI art that is not a record
- `scripts/` — `validate.py`, `build_index.py`
- `dist/` — generated indexes + manifest (git-ignored)

Slug is the only ID and doubles as file/folder name. Start with `docs/naming.md`.
