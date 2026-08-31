# hermes-vacuum

Safe deep cache cleaning for Hermes Agent. Remove system junk without touching OS files. Stdlib only, allowlist only, preview before deletion.

> Ponytail style Deep Clean. `quick` needs no Admin, `deep` prompts for UAC. Hermes cache is included.

![Hermes](https://img.shields.io/badge/Hermes-Skill-blue) ![Python](https://img.shields.io/badge/Python-stdlib%20only-green) ![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

## Why hermes-vacuum

Disk fills up from `Temp`, `npm-cache`, `cargo`, `thumbcache`, `Hermes cache` piling up. The built-in Hermes `disk-cleanup` only cleans Hermes files. `hermes-vacuum` goes further to clean safe system caches, with preview of total reclaimable and a skip report if files are in use.

## Features

* Preview first, delete later. `dry-run` is default, no file is deleted without confirmation
* Three clear modes. `quick`, `deep`, `status`. Total files and total GB are always visible
* Safe by default. Only deletes inside allowlist, OS files like `System32` and `WinSxS` are always rejected
* Hermes cache included. `$HERMES_HOME/cache` is part of `quick`, so bloated Hermes web cache is counted
* Real Deep Clean. `deep` includes dev caches `npm`, `pip`, `cargo`, `uv` plus `thumbcache` with no extra flag
* Skip, not fail. Files in use are skipped, 1 locked file does not fail 1 folder
* Runs on every surface. CLI, Desktop, Dashboard use the same skill

## Security

* `is_safe_path()` allowlist only. Any path not in allowlist is automatically `REJECT`, never `DELETE`
* OS core blocked. `C:/Windows/System32`, `WinSxS`, `Program Files`, `/System`, `/usr` are hard rejected
* Canonical dedup. `%TEMP%` and its resolved path are deduped via `realpath` first to avoid double scanning
* No silent Admin. `deep` checks `is_admin()`, if false it immediately returns the elevation command `powershell Start-Process -Verb RunAs`, no auto elevation

## Installation

```bash
hermes skills install https://raw.githubusercontent.com/ensayiti/hermes-vacuum/main/SKILL.md --name hermes-vacuum
# or local
hermes skills install ./hermes-vacuum --name hermes-vacuum
hermes skills list  # ensure hermes-vacuum appears
```

Update:

```bash
hermes skills update hermes-vacuum
```

Remove:

```bash
hermes skills remove hermes-vacuum
```

## How to Use

### Hermes CLI

```bash
hermes
> /safe-cleanup dry-run
> /safe-cleanup quick
> /safe-cleanup deep
> /safe-cleanup deep --with docker
> /safe-cleanup status

# one shot without entering chat
hermes chat -q "/safe-cleanup dry-run"
hermes chat -q "/safe-cleanup status"
```

Natural language also works:

```
clean cache please
vacuum deep please, preview first
```

### Hermes Desktop

1. Open `hermes desktop`, select profile `default`
2. In the center chat type `/safe-cleanup dry-run` then press Enter
3. Or press `Ctrl+K` then type `safe-cleanup`
4. Preview table output and `Deleted X GB` summary streams in, same as CLI
5. Log file is in the left File Browser at `$HERMES_HOME/hermes-vacuum/cleanup.log`

CLI and Desktop share the same `tracked.json`, so `dry-run` in CLI is visible as `status` in Desktop.

### Hermes Dashboard Web UI

```bash
hermes dashboard
# buka http://localhost:3000
```

* Skills tab: see `hermes-vacuum` installed
* Chat tab: type `/safe-cleanup dry-run` in the embedded chat, result is identical
* No dedicated Vacuum tab with buttons yet. This is intentional ponytail, chat is enough. A dedicated tab will only be added on request.

## Commands

| Command | Requires Admin | What gets deleted |
| --- | --- | --- |
| `/safe-cleanup dry-run` | No | Preview all tiers, no deletion. Per base breakdown, total reclaimable, top 10 largest |
| `/safe-cleanup quick` | No | `%TEMP%`, `%LOCALAPPDATA%/Temp`, `~/Library/Caches`, `~/.cache`, `/tmp` plus `$HERMES_HOME/cache` |
| `/safe-cleanup deep` | Yes | `quick` plus `C:/Windows/Temp`, `SoftwareDistribution/Download`, dev caches `npm`, `pip`, `cargo`, `uv` plus `thumbcache` |
| `/safe-cleanup deep --with docker` | Yes | `deep` plus `docker builder prune` |
| `/safe-cleanup deep --with pnpm` | Yes | `deep` plus `pnpm store` (heavy, 562MB, opt in to keep dry run fast) |
| `/safe-cleanup status` | No | Same as dry run, reads from latest `tracked.json` |

## Example Preview and Result

**Preview:**

```
/safe-cleanup dry-run
Total scannable: 50689 file, 4.5GB reclaimable
Breakdown per base:
  3.2GB  10726 file  %TEMP%
  407MB  28263 file  npm-cache
Top 10:
  447MB  huggingface model
Disk free before: 25.8GB
[dry-run] No files deleted.
```

**Result after `quick`:**

```
/safe-cleanup quick
Deleted: 805 file, 1.1GB
Skip: 37 file
  LOCKED: 32
  ACCESS_DENIED: 5
Disk free before: 25.8GB after: 26.9GB (gain: 1.1GB)
Log: $HERMES_HOME/hermes-vacuum/cleanup.log
```

## Allowlist Details

**quick without Admin, includes Hermes cache:**
* Windows: `%TEMP%`, `%LOCALAPPDATA%/Temp`, `%LOCALAPPDATA%/Microsoft/Windows/INetCache` plus `%LOCALAPPDATA%/hermes/cache`
* macOS: `~/Library/Caches`, `~/Library/Logs`
* Linux: `~/.cache`, `/tmp`, `/var/tmp` plus `~/.hermes/cache`

**deep requires Admin, Deep Clean plus dev cache plus thumb by default:**
* Windows: `C:/Windows/Temp`, `C:/Windows/SoftwareDistribution/Download` plus `npm-cache`, `pip Cache`, `cargo`, `uv` plus `thumbcache`
* Linux: `journalctl --vacuum-time=7d`
* macOS: `DerivedData`, `CoreSimulator`

**Opt in extra `--with`:**
* `docker` uses `docker builder prune -f` with `docker system df` preview, opt in because it can remove images still in use
* `pnpm` uses `%LOCALAPPDATA%/pnpm/store`, opt in because it is heavy and makes dry run slow

**Never touched:**
`C:/Windows/System32`, `WinSxS`, `Program Files`, `~/Library/Application Support` random, `/System`, `/usr`, `/etc`

## FAQ

**Will files that are in use cause an error?**
No. Per file uses `try/except`, if `LOCKED` or `ACCESS_DENIED` it is skipped and reported at the end. 1 locked file does not fail 1 folder.

**Will `Temp` and `%TEMP%` be double counted?**
No. Both are resolved via `realpath` first, if they resolve to the same path they are scanned once.

**Do I need to Run as Administrator every time?**
No. `quick` and `dry-run` need no Admin. Only `deep` needs Admin and will trigger UAC. Hermes keeps running as a regular user.

**Does it work on every model?**
Yes. The LLM only parses intent `quick` or `deep`, the actual deletion is done by `scripts/clean.py` deterministically. So even lower ranked models that sometimes misread SKILL.md are still blocked by `is_safe()`.

**Is Hermes cache already included?**
Yes. `$HERMES_HOME/cache` has been part of `quick` since v0.1.1, so Hermes web cache that was 8MB is now counted.

## Further Documentation

* `docs/PRD.md` Product Requirements
* `docs/ERD.md` Entity Relationship plus `tracked.json` schema
* `docs/ARCHITECTURE.md` Ponytail design, `O(n)` scan plus lock mitigation
* `docs/TASKS.md` Dev checklist

## License

MIT
