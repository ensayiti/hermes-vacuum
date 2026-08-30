# TASKS, hermes-vacuum v0.1

> Ponytail: fewest files, shortest diff. Checklist ini urutan dev yang paling lazy.

## Milestone v0.1 (ship)

- [ ] **P0** `scripts/clean.py`, `dry-run` + `status` (scan + tabel, tanpa hapus)
- [ ] **P0** `is_safe_path()` allowlist-only + `is_admin()` guard
- [ ] **P0** `quick`, per-file `try/except`, skip locked, lanjut
- [ ] **P0** dedup canonical `%TEMP%` vs `C:\Windows\Temp` (`realpath(expandvars)`)
- [ ] **P0** `deep`, block jika `not admin`, kasih command elevasi UAC/sudo
- [ ] **P1** `cleanup.log` + `tracked.json` atomic write (`.tmp` → `.bak` → rename)
- [ ] **P1** `--with npm,pip,cargo,thumb` via native tool (`npm cache clean --force`, `cleanmgr`)
- [ ] **P1** threshold >500MB / >30d → confirm list di `deep`

## Milestone v0.2 (kalau needed)

- [ ] `cronjob` mingguan `hermes-vacuum quick` via `cronjob` tool Hermes
- [ ] `--with` auto-detect (cek `npm --version` ada baru tawarin)
- [ ] Parallel walk jika scan >50k file / >10s

## Done

- [x] PRD, ERD, ARCHITECTURE, SKILL.md, AGENTS.md, README.md
- [x] `.gitignore` + `scripts/clean.py` stub + self-check

## How to run

```bash
python scripts/clean.py dry-run
python scripts/clean.py status
python scripts/clean.py quick          # tanpa Admin
python scripts/clean.py deep           # butuh Admin
python scripts/clean.py deep --with npm,thumb
```
