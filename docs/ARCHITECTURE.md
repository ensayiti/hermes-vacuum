# ARCHITECTURE hermes vacuum

Ponytail FULL shortest diff that works.

## 1. Flow Diagram (mermaid)

```mermaid
flowchart TD
    A[User: /safe-cleanup dry-run/quick/deep] --> B{Parse mode + --with}
    B --> C[Resolve allowlist expandvars + realpath + dedup ]
    C --> D{is_safe_path?}
    D, REJECT --> L[Log REJECT + skip]
    D, OK --> E{deep && not is_admin?}
    E, yes --> F[Block + provide elevation command powershell Start-Process -Verb RunAs / sudo]
    E, no --> G[Scan O(n) walk calculate size and age]
    G --> H{mode == dry-run?}
    H, yes --> I[Table preview + total reclaimable + confirm list >500MB]
    H, no --> J[Per file try: unlink except PermissionError/OSError: skipped.append]
    J --> K[Log DELETE/SKIP to cleanup.log + summary]
    K --> M[Return: Deleted X GB, N files, skip M, locked]
```

## 2. Components (3 core files)

```
SKILL.md              → prompt Hermes (when and how to use skill)
scripts/clean.py      → single file stdlib: is_admin, is_safe_path, scan, clean, log
$HERMES_HOME/hermes-vacuum/
  tracked.json        → last state (jobs, last_scan)
  cleanup.log         → audit append only
```

**Why 1 script?** Ladder rung 3 stdlib is enough. `os`, `pathlib`, `shutil`, `ctypes`, `json`, `subprocess` cover all. No `click`, no `rich`, no `send2trash`.

## 3. is_safe_path (safety core)

```python
import os, pathlib

ALLOWLIST_TEMPLATES = {
  "windows": ["%TEMP%", "%LOCALAPPDATA%/Temp", "C:/Windows/Temp", "C:/Windows/SoftwareDistribution/Download", "%LOCALAPPDATA%/hermes/cache"],
  "mac": ["~/Library/Caches", "~/Library/Logs", "~/.hermes/cache"],
  "linux": ["~/.cache", "/tmp", "~/.hermes/cache"],
}
# deep include dev cache + thumb by default (Deep Clean principle) + Hermes cache already in quick
DEEP_DEV = {"npm": ".../npm-cache", "pip": ".../pip/Cache", "cargo": ".../cargo/registry/cache", "uv": ".../cache/uv", "thumb": ".../Explorer/thumbcache_*.db"}
OPTIN_EXTRA = {"docker": "docker builder prune -f"}  # docker opt-in only, bahaya hapus image

def is_safe(path: pathlib.Path) -> bool:
    real = path.resolve()  # canonical
    for tmpl in all_resolved_allowlist():  # expandvars + expanduser + resolve
        try:
            real.relative_to(tmpl)  # inside allowlist?
            return True
        except ValueError:
            continue
    return False  # default REJECT

def is_admin() -> bool:
    try: return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except: return os.geteuid() == 0
```

## 4. Mitigation for Undeletable Files

```python
# ponytail: per-file try, O(n) scan, parallel walk if >50k files
skipped = []
reclaimed = 0
for f in files:  # files dari scan()
    if f.size > 500*1024*1024 and mode == "quick":
        skipped.append((f, "CONFIRM_NEEDED"))
        continue
    try:
        if f.is_dir(): shutil.rmtree(f, onerror=lambda *a: (_ for _ in ()).throw(OSError(*a)))
        else: f.unlink()
        reclaimed += f.size
        log("DELETE", f)
    except (PermissionError, OSError) as e:
        reason = "LOCKED" if "in use" in str(e).lower() else "ACCESS_DENIED"
        skipped.append((f, reason))
        log("SKIP", f, reason)
        continue  # jangan crash 1 folder
```

* Dedupe: `seen = set(realpath(expandvars(p)) for p in allowlist)` → `%TEMP%` vs `C:/Windows/Temp` if resolve to same path scan once only
* Native tool: `npm cache clean --force` via `subprocess.run` > `rm -rf`, `cleanmgr` > manual thumb delete

## 5. State and Log (similar to disk cleanup)

* Atomic write: `write .tmp → backup tracked.json.bak → rename`
* `cleanup.log` append only: `2026-08-30T13:18:00 DELETE /path size category`
* Never touch `logs/`, `memories/`, `sessions/`, `skills/` of Hermes

## 6. Platform Notes

* **Windows:** `%TEMP%` does not need Admin, `C:\Windows\Temp` needs it. `SoftwareDistribution\Download` → `net stop wuauserv` first then delete (only `deep` plus Admin)
* **Mac/Linux:** `sudo` for `journalctl --vacuum-time=7d`, not `rm /var/log`
* **Hermes Desktop:** stays as regular user, elevation only for `deep` command via OS UAC prompt

## 7. Skipped Next

* Weekly cron `hermes-vacuum quick` (use Hermes `cronjob`, not in skill)
* `--with` auto detect (check `npm --version` exists then offer `npm`)
* Parallel walk (`concurrent.futures`) if `>50k` files, add when scan exceeds 10s measured
