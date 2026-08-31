# Changelog

All notable changes to `hermes-vacuum` are documented here. Format follows Keep a Changelog, versioning follows Semantic Versioning.

## [0.1.4] 2026-08-31

### Added

* One line installer. `install.ps1` for Windows `irm | iex` and `install.sh` for macOS and Linux `curl | bash`, handles `git` or zip fallback and copies to `productivity/hermes-vacuum`, fixes `Could not fetch` on Windows

### Changed

* README Installation now shows 1 liner as primary, manual `git clone` as fallback

## [0.1.3] 2026-08-31

### Fixed

* Privacy, remove PII from docs and scripts. Replace `C:/Users/XEM/...` and `D:/Code/hermes-vacuum` with generic `$HERMES_HOME`, `%TEMP%` and `./scripts/clean.py` in `README.md`, `CHANGELOG.md`, `docs/PRD.md`, `scripts/clean.py`

## [0.1.2] 2026-08-31

### Added

* Loading indicator for scan. `Scanning, please wait...` with per base progress `Scanning 1/9 .cache...` via carriage return, replaces verbose per file logs
* English i18n. All docs `README.md`, `SKILL.md`, `docs/PRD.md`, `docs/ARCHITECTURE.md`, `docs/ERD.md`, `docs/TASKS.md`, `AGENTS.md`, `CHANGELOG.md` and CLI messages in `scripts/clean.py` translated to English, structure and code blocks kept verbatim

### Changed

* CLI messages use English. `Deleted`, `Skipped`, `No files deleted`, `Disk free before` and `gain`, `requires Admin` replaces Indonesian strings
* Zero dash enforced across all files. Only hyphens inside words kept such as `hermes-vacuum`, `dry-run`, `allowlist-only`

## [0.1.1] 2026-08-30

### Added

* Hermes cache included in `quick` default. `$HERMES_HOME/cache` and `~/.hermes/cache` are now included in preview and deletion in `quick` without Admin, integrated with official `disk-cleanup`
* Preview total reclaimable, breakdown per base, top 10 largest, and skip report `LOCKED` versus `ACCESS_DENIED`
* Disk report `free before` and `free after` plus `gain`

### Changed

* Zero dash total. All dashes with spaces replaced by commas, only hyphens inside words are kept as normal such as `hermes-vacuum` and `deep-clean`
* `deep` now includes dev caches `npm`, `pip`, `cargo`, `uv` plus `thumbcache` by default following Deep Clean principle
* `pnpm store` moved to opt in `--with pnpm` because it is heavy at 562MB and slows `dry-run` from 10 seconds to 40 seconds
* `docker` stays opt in `--with docker` using `docker builder prune -f` with preview `docker system df`
* Scan optimized. `os.walk` with `followlinks=False`, skip symlinks, cache `BLOCK` resolution, and per base progress so it never hangs on `pnpm store`

### Fixed

* Canonical dedup for `%TEMP%` versus its resolved path to avoid double scanning
* OS filter. `/tmp` and `/var/tmp` are skipped automatically on Windows to avoid scanning `D:/tmp` which is irrelevant
* `is_safe()` uses lower case string prefix for speed across 50 thousand files, still strict allowlist only

## [0.1.0] 2026-08-30

### Added

* Initial release of `hermes-vacuum` as a Hermes Skill
* Repo structure. `SKILL.md`, `scripts/clean.py` stdlib only, `docs/PRD.md`, `docs/ERD.md`, `docs/ARCHITECTURE.md`, `docs/TASKS.md`, `AGENTS.md`
* Three modes. `dry-run` default preview without deletion, `quick` without Admin, `deep` requires Admin with `is_admin()` and UAC
* Initial allowlist. `quick` for `%TEMP%` and `~/Library/Caches`, `deep` for `C:/Windows/Temp` and `SoftwareDistribution/Download`
* Handling for undeletable files. Per file `try/except`, `skipped` with reason `LOCKED` and `ACCESS_DENIED`, scan continues without crash
* State and log. `tracked.json` atomic write plus `tracked.json.bak` and `cleanup.log` append only in `$HERMES_HOME/hermes-vacuum`
* Self check. `assert is_safe` for `%TEMP%` and rejection of `System32` in `__main__`

### Security

* `is_safe_path()` allowlist only, default `REJECT`
* Hard block for `System32`, `WinSxS`, `Program Files`, `/System`, `/usr`
* Threshold `>500MB` goes to confirmation list, no auto deletion in `quick`

[0.1.4]: https://github.com/ensayiti/hermes-vacuum/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/ensayiti/hermes-vacuum/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/ensayiti/hermes-vacuum/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/ensayiti/hermes-vacuum/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/ensayiti/hermes-vacuum/releases/tag/v0.1.0
