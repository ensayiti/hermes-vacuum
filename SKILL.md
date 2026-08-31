---
name: hermes-vacuum
description: "Safe deep clean cache system without touching OS, dry run default, allowlist only, per file skip on lock."
version: 0.1.4
metadata:
  hermes:
    tags: [system, cleaner, cache, disk, windows, macos, linux, safe]
    category: productivity
---

# hermes-vacuum

## When to Use

- User wants to clean cache or temp files that fill up disk
- User says "clean", "vacuum", "clean cache", "deep clean"
- User wants to preview what is safe to delete before execution

## Procedure

1. **Parse intent**, `dry-run` (default) | `quick` | `deep` | `status`. `deep` **includes dev cache and thumb by default** (npm/pip/cargo/uv plus thumbcache), `--with` flag is only for extra `docker`
2. **Resolve allowlist**, expand `%TEMP%`, `~`, canonicalize via `realpath`, dedup `%TEMP%` vs `C:\Windows\Temp`, filter by OS
3. **Check admin**, if `deep` and `not is_admin()` then stop, show elevation command `powershell Start-Process -Verb RunAs` or `sudo`, do not auto elevate
4. **Scan**, walk allowlist, calculate size and age per file, `# ponytail: O(n) scan, parallel walk if >50k files`
5. **Report dry run**, table per category plus total reclaimable plus `skipped` preview
6. **Execute (if not dry run)**, per file `try: unlink() except (PermissionError, OSError): skipped.append`, continue to next folder, do not crash
7. **Log**, append to `$HERMES_HOME/hermes-vacuum/cleanup.log` and `tracked.json` like `disk-cleanup`, show summary "Deleted X GB (N files), skipped M files (locked)"

## Allowlist (do not add without discussion)

- **quick (no Admin, includes Hermes cache):** `%TEMP%`, `%LOCALAPPDATA%\Temp`, `~/Library/Caches`, `~/Library/Logs`, `~/.cache`, `/tmp` **plus `$HERMES_HOME/cache` (`%LOCALAPPDATA%\hermes\cache`, `~/.hermes/cache`), official disk cleanup integration, regeneratable**
- **deep (requires Admin, includes dev cache and thumb by default):** `C:\Windows\Temp`, `SoftwareDistribution\Download` (stop wuauserv first), `journalctl --vacuum` **plus npm/pip/cargo/uv cache** (`npm cache clean --force` native) **plus thumbcache** (`cleanmgr` native)
- **opt in extra (`--with`):** `docker` (`docker builder prune -f` or `docker system df` preview), not default because it may delete images still in use

## Pitfalls

- Locked file then skip, not fail. Do not use `shutil.rmtree` without `onerror`
- `%TEMP%` vs `C:\Windows\Temp` then dedup via `realpath(expandvars())`, if identical scan only once
- Greater than 500MB or older than 30 days then include in `deep` confirm list, do not auto delete in `quick`
- Do not use `send2trash` or new dependencies, stdlib only (ladder rung 3)
- Always `dry-run` first for `deep`, do not delete immediately

## Slash

- `/hermes-vacuum dry-run`              # preview all tiers
- `/hermes-vacuum quick`                # no Admin, includes Hermes cache, excludes dev cache and thumb
- `/hermes-vacuum deep`                 # Deep Clean: system temp plus dev cache plus thumb plus Hermes cache by default
- `/hermes-vacuum deep --with docker`   # plus docker builder prune extra
- `/hermes-vacuum status`
- Alias `/safe-cleanup` also works via `hermes chat -q` and natural language
