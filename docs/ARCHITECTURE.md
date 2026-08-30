# ARCHITECTURE, hermes-vacuum

Ponytail FULL, shortest diff that works.

## 1. Diagram Alir (mermaid)

```mermaid
flowchart TD
    A[User: /safe-cleanup dry-run/quick/deep] --> B{Parse mode + --with}
    B --> C[Resolve allowlist\n expandvars + realpath + dedup ]
    C --> D{is_safe_path?}
    D, REJECT --> L[Log REJECT + skip]
    D, OK --> E{deep && not is_admin?}
    E, yes --> F[Block + kasih command elevasi\n powershell Start-Process -Verb RunAs / sudo]
    E, no --> G[Scan O(n) walk\n hitung size+age]
    G --> H{mode == dry-run?}
    H, yes --> I[Tabel preview + total reclaimable\n + confirm list >500MB]
    H, no --> J[Per-file try: unlink\n except PermissionError/OSError: skipped.append]
    J --> K[Log DELETE/SKIP ke cleanup.log\n + ringkasan]
    K --> M[Return: Dihapus X GB, N file, skip M, locked]
```

## 2. Komponen (3 file inti)

```
SKILL.md              → prompt Hermes (kapan & gimana pakai skill)
scripts/clean.py      → satu file stdlib: is_admin, is_safe_path, scan, clean, log
$HERMES_HOME/hermes-vacuum/
  tracked.json        → state terakhir (jobs, last_scan)
  cleanup.log         → audit append-only
```

**Kenapa 1 script?** Ladder rung 3, stdlib cukup. `os`, `pathlib`, `shutil`, `ctypes`, `json`, `subprocess` cover semua. No `click`, no `rich`, no `send2trash`.

## 3. is_safe_path (jantung safety)

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

## 4. Mitigasi File Tidak Bisa Dihapus

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

* Dedupe: `seen = set(realpath(expandvars(p)) for p in allowlist)` → `%TEMP%` vs `C:/Windows/Temp` kalau resolve sama cuma scan sekali
* Native tool: `npm cache clean --force` via `subprocess.run` > `rm -rf`, `cleanmgr` > manual thumb delete

## 5. State & Log (mirip disk-cleanup)

- Atomic write: `write .tmp → backup tracked.json.bak → rename`
- `cleanup.log` append-only: `2026-08-30T13:18:00 DELETE /path size category`
- Tidak pernah sentuh `logs/`, `memories/`, `sessions/`, `skills/` Hermes

## 6. Platform Notes

- **Windows:** `%TEMP%` tidak butuh Admin, `C:\Windows\Temp` butuh. `SoftwareDistribution\Download` → `net stop wuauserv` dulu baru hapus (hanya `deep` + Admin)
- **Mac/Linux:** `sudo` untuk `journalctl --vacuum-time=7d`, bukan `rm /var/log`
- **Hermes Desktop:** tetap user biasa, elevasi hanya untuk command `deep` via UAC prompt OS

## 7. Skipped Next

- Cron `hermes-vacuum quick` mingguan (pakai `cronjob` Hermes, bukan di skill)
- `--with` auto-detect (cek `npm --version` ada baru tawarin `npm`)
- Parallel walk (`concurrent.futures`) kalau >50k file, add when scan >10s terukur
