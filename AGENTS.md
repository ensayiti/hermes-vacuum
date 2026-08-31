# AGENTS.md, hermes-vacuum

Ponytail FULL active. Ladder enforced.

## Rules for agents working here

- Stdlib only. No new dependency for what 10 lines can do.
- `is_safe_path()` allowlist only. Reject anything outside allowlist, even if path looks like cache.
- Per file `try/except`, never crash whole scan because one file is locked.
- `dry-run` default. `deep` requires `is_admin()` check plus explicit UAC/sudo.
- Dedupe canonical paths (`realpath(expandvars())`) before scan.
- Native tool over manual rm: `npm cache clean --force` over `rm -rf npm-cache`, `cleanmgr` over manual thumbcache delete.

## Where to look

- `SKILL.md`, single source skill behavior
- `scripts/clean.py`, main logic (not yet created, will be built next)
- `docs/PRD.md`, requirements
- `docs/ERD.md`, state schema (not an RDBMS, JSON state)
- `docs/ARCHITECTURE.md`, arch

## Do not

- Add GUI installer (YAGNI)
- Add registry cleaner
- Add auto elevate without UAC prompt
- Delete >500MB without confirmation list in `deep`
