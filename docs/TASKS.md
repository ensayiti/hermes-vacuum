# TASKS, hermes-vacuum v0.1

> Ponytail: fewest files, shortest diff. This checklist follows the laziest dev order.

## Milestone v0.1 (ship)

- [ ] **P0** `scripts/clean.py`, `dry-run` plus `status` (scan plus table, no deletion)
- [ ] **P0** `is_safe_path()` allowlist only plus `is_admin()` guard
- [ ] **P0** `quick`, per file `try/except`, skip locked files, continue
- [ ] **P0** dedupe canonical `%TEMP%` versus `C:\Windows\Temp` (`realpath(expandvars)`)
- [ ] **P0** `deep`, block if `not admin`, show UAC/sudo elevation command
- [ ] **P1** `cleanup.log` plus `tracked.json` atomic write (`.tmp` to `.bak` to rename)
- [ ] **P1** `--with npm,pip,cargo,thumb` via native tool (`npm cache clean --force`, `cleanmgr`)
- [ ] **P1** threshold >500MB / >30d to confirmation list in `deep`

## Milestone v0.2 (if needed)

- [ ] weekly `cronjob` for `hermes-vacuum quick` via Hermes `cronjob` tool
- [ ] `--with` auto detection (check `npm --version` exists before offering)
- [ ] parallel walk if scan exceeds 50k files / 10s

## Done

- [x] PRD, ERD, ARCHITECTURE, SKILL.md, AGENTS.md, README.md
- [x] `.gitignore` plus `scripts/clean.py` stub plus self check

## How to run

```bash
python scripts/clean.py dry-run
python scripts/clean.py status
python scripts/clean.py quick          # no Admin
python scripts/clean.py deep           # requires Admin
python scripts/clean.py deep --with npm,thumb
```
