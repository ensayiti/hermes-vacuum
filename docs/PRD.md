# PRD, hermes-vacuum

**Version:** 0.1.0, 2026-08-30
**Owner:** XEM, Hermes Agent Skill
**Status:** Draft to Ready for dev
**Ponytail:** full, deletion over addition, stdlib first

***

## 1. Overview

`hermes-vacuum` is a Hermes Skill for **safe deep clean of cache and temp** on Windows, Mac and Linux without touching OS files or important user data. Unlike `disk-cleanup` which only covers `HERMES_HOME`, this skill covers **system user cache** with **allowlist only** plus default `dry-run` plus explicit elevation for `deep`.

> One liner: *CCleaner but ponytail, only removes regeneratable files, never touches System32.*

***

## 2. Problem and Goals

**Problem:**
* Disk full due to `%TEMP%`, `~/Library/Caches`, `~/.cache`, `npm/pip/cargo` cache, `thumbcache`, `SoftwareDistribution\Download`
* `disk-cleanup` does not cover these areas
* General cleaner tools like CCleaner are too aggressive, require an installer, and touch the registry

**Goals (G):**
* G1: Reclaim 1 to 10GB safely across 3 OS via 1 Hermes skill
* G2: Zero incidents of deleted OS files or user data via allowlist plus audit log
* G3: 10 second UX: `/safe-cleanup dry-run` to preview then `/safe-cleanup quick` to finish

**Non Goals (NG):**
* NG1: Registry cleaner, defrag, driver update, YAGNI
* NG2: GUI installer `.exe`, Hermes chat is the GUI
* NG3: Silent auto elevation without UAC, forbidden for security

***

## 3. User Persona

* **Solo Dev (primary, you):** D:/Code full of cache, wants daily `quick` without Admin
* **Power User:** Wants monthly `deep`, understands UAC, `deep` directly includes dev cache plus thumb, `docker` as extra when requested (`--with docker`)
* **Non tech (future):** Only comfortable with `dry-run` plus `status`

***

## 4. User Stories

* US1: As a dev, I want `/safe-cleanup dry-run` to see what can be deleted plus how many GB, so I am not surprised
* US2: As a dev, I want `/safe-cleanup quick` to delete `%TEMP%` without Admin and skip locked files without crashing
* US3: As a power user, I want `/safe-cleanup deep` to clean `C:\Windows\Temp` but it **must** go through UAC, not silently
* US4: As a power user, I want `/safe-cleanup deep` to automatically clean dev cache (npm/pip/cargo) plus thumbcache natively without extra flags, Deep Clean by default
* US5: As a user, I want `/safe-cleanup status` to see breakdown per category plus top 10 largest files
* US6: As a user, I want `cleanup.log` so I can audit what was deleted and when

***

## 5. Functional Requirements

| ID | Requirement | Priority | Mode |
|----|-------------|----------|------|
| F1 | `dry-run` by default, scan allowlist, calculate size and age, show table, **do not delete** | P0 | all |
| F2 | `quick`, delete allowlist user cache (`%TEMP%`, `~/Library/Caches`, `~/.cache`, `/tmp`) without Admin, per file `try/except`, skip locked | P0 | quick |
| F3 | `deep`, F2 plus `C:\Windows\Temp` plus `SoftwareDistribution\Download` plus `journalctl --vacuum` **plus dev cache (npm/pip/cargo/uv) plus thumbcache by default**, **requires `is_admin()`**, if false then show elevation command and stop | P0 | deep |
| F4 | `--with` extra, `docker` (`docker builder prune -f`, `docker system df` preview) via native, opt in because it can delete images still in use | P1 | deep |
| F5 | `status`, breakdown per category plus top 10 largest plus total reclaimable | P0 | all |
| F6 | Canonical dedup, `realpath(expandvars())` before scan, `%TEMP%` vs `C:\Windows\Temp` if same then scan once | P0 | all |
| F7 | Per file skip mitigation, `PermissionError`/`OSError` goes to `skipped[]`, continue, at end report "Deleted X (N files), skipped M (locked or access denied)" | P0 | quick/deep |
| F8 | `is_safe_path()`, allowlist only, reject `System32`, `WinSxS`, `Program Files`, `/System`, `/usr`, `Application Support` indiscriminately | P0 | all |
| F9 | Audit, append `cleanup.log` plus `tracked.json` in `$HERMES_HOME/hermes-vacuum/` | P1 | quick/deep |
| F10 | Threshold, files larger than 500MB or older than 30 days go to confirm list in `deep`, do not auto delete in `quick` | P1 | deep |

***

## 6. Non Functional

* **Safety:** 100 percent allowlist, never blocklist. Windows mounts outside allowlist equal reject.
* **Perf:** `# ponytail: O(n) scan, parallel walk if more than 50k files`, target less than 5s for 10k files
* **Compat:** Windows 10 and 11 as primary, macOS 13 plus, Linux Ubuntu. Python stdlib only (os, pathlib, shutil, ctypes, json, time)
* **No deps:** `npm cache clean` via `subprocess`, not a lib. `cleanmgr` native.
* **Idempotent:** `dry-run` many times gives same result, second `quick` equals 0 files

***

## 7. Allowlist Detail

**quick (no Admin, includes Hermes cache):**
* Win: `%TEMP%`, `%LOCALAPPDATA%\Temp`, `%LOCALAPPDATA%\Microsoft\Windows\INetCache` **plus `%LOCALAPPDATA%\hermes\cache` (`$HERMES_HOME/cache`), official disk cleanup integration**
* Mac: `~/Library/Caches`, `~/Library/Logs`, `/private/var/folders`
* Linux: `~/.cache`, `/tmp`, `/var/tmp` **plus `~/.hermes/cache` and `$HERMES_HOME/cache`**

**deep (needs Admin, Deep Clean equals dev cache plus thumb by default):**
* Win: `C:\Windows\Temp`, `C:\Windows\SoftwareDistribution\Download` (stop `wuauserv` first), `DeliveryOptimization\Cache` **plus `%LOCALAPPDATA%\npm-cache`, `%LOCALAPPDATA%\pip\Cache`, `~/.cargo/registry/cache`, `~/.cache/uv` plus `Explorer\thumbcache_*.db` via `cleanmgr`**
* Linux: `journalctl --vacuum-time=7d`, `/var/log` (only `*.log.*` older than 14 days, not active logs)
* Mac: `~/Library/Caches` stays in quick, but `DerivedData` plus `CoreSimulator` belong to deep

**opt in extra (`--with`):**
* `docker` to `docker builder prune -f` or `docker system prune` (preview `docker system df`), opt in because it can delete images or containers still in use

**Never (reject):** `C:\Windows\System32`, `WinSxS`, `Program Files*`, `~/Library/Application Support` except for clearly designated sub cache, `/System`, `/usr`, `/etc`

***

## 8. UX Flow

```
User: /safe-cleanup dry-run  (or natural language "please clean up")
Agent: scan allowlist to table [Category | File | Size | Age] plus Total 2.4GB reclaimable (includes dev cache plus thumb in deep)
User: /safe-cleanup quick
Agent: delete per file, skip locked to "Deleted 1.1GB (842 files), skipped 37 (locked). Log: .../cleanup.log"
User: /safe-cleanup deep                 # auto includes npm/pip/cargo plus thumb
Agent: if not admin to "Need Admin. Run: powershell Start-Process hermes -Verb RunAs ..."
       if admin then clean system temp plus dev cache plus thumb to confirm list larger than 500MB then delete then report
User: /safe-cleanup deep --with docker   # plus docker builder prune extra
```

***

## 9. Success Metrics

* Reclaim at least 1GB on dev machine without `skipped` above 20 percent
* Zero OS files deleted verified via audit `cleanup.log`
* `dry-run` less than 3s for 5k files, `quick` less than 10s
* User understands without reading docs, only 3 commands

***

## 10. Out of Scope v0.1

* Cron scheduler auto clean (can use Hermes `cronjob` later, not in skill)
* GUI, tray icon, installer
* Cloud and user Documents (`Documents`, `Downloads`), too risky

***

## 11. Open Questions

* Q1: For `thumbcache` is `cleanmgr` or `rm` plus `ie4uinit -show` better? Leaning to `cleanmgr` as native
* Q2: Does `SoftwareDistribution\Download` need service stop with `net stop wuauserv`? Yes, but only in `deep` plus Admin
