# AGENTS.md, hermes-vacuum

Ponytail FULL active. Ladder enforced.

## Rules for agents working here

- Stdlib only. No new dependency for what 10 lines can do.
- `is_safe_path()` allowlist-only. Reject anything outside allowlist, even if path looks like cache.
- Per-file `try/except`, never crash whole scan because 1 file locked.
- `dry-run` default. `deep` requires `is_admin()` check + explicit UAC/sudo.
- Dedupe canonical paths (`realpath(expandvars())`) before scan.
- Native tool over manual rm: `npm cache clean --force` > `rm -rf npm-cache`, `cleanmgr` > manual thumbcache delete.

## Where to look

- `SKILL.md`, single source skill behavior
- `scripts/clean.py`, main logic (belum ada, akan dibuat next)
- `docs/PRD.md`, requirements
- `docs/ERD.md`, state schema (bukan DB RDBMS, tapi JSON state)
- `docs/ARCHITECTURE.md`, arch

## Do not

- Add GUI installer (YAGNI)
- Add registry cleaner
- Add auto-elevate without UAC prompt
- Delete >500MB without confirm list in `deep`
