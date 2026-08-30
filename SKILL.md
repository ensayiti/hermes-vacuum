---
name: hermes-vacuum
description: "Safe deep-clean cache sistem tanpa sentuh OS, dry-run default, allowlist-only, per-file skip on lock."
version: 0.1.0
metadata:
  hermes:
    tags: [system, cleaner, cache, disk, windows, macos, linux, safe]
    category: productivity
---

# hermes-vacuum

## When to Use

- User mau bersihin cache/temp yang bikin disk penuh
- User bilang "bersihin", "vacuum", "clean cache", "deep clean"
- User mau lihat apa yang aman dihapus sebelum eksekusi

## Procedure

1. **Parse intent**, `dry-run` (default) | `quick` | `deep` | `status`. `deep` **include dev cache + thumb by default** (npm/pip/cargo/uv + thumbcache), flag `--with` cuma untuk extra `docker`
2. **Resolve allowlist**, expand `%TEMP%`, `~`, canonicalize via `realpath`, dedup `%TEMP%` vs `C:\Windows\Temp`, filter by OS
3. **Check admin**, jika `deep` dan `not is_admin()` → stop, kasih command elevasi `powershell Start-Process -Verb RunAs` / `sudo`, jangan auto-elevate
4. **Scan**, walk allowlist, hitung size+age per file, `# ponytail: O(n) scan, parallel walk if >50k files`
5. **Report dry-run**, tabel per kategori + total reclaimable + `skipped` preview
6. **Execute (jika bukan dry-run)**, per-file `try: unlink() except (PermissionError, OSError): skipped.append`, lanjutkan folder, jangan crash
7. **Log**, append ke `$HERMES_HOME/hermes-vacuum/cleanup.log` + `tracked.json` ala `disk-cleanup`, tampilkan ringkasan "Dihapus X GB (N file), skip M file (locked)"

## Allowlist (jangan tambah tanpa diskusi)

- **quick (no Admin, include Hermes cache):** `%TEMP%`, `%LOCALAPPDATA%\Temp`, `~/Library/Caches`, `~/Library/Logs`, `~/.cache`, `/tmp` **+ `$HERMES_HOME/cache` (`%LOCALAPPDATA%\hermes\cache`, `~/.hermes/cache`), integrasi disk-cleanup official, regeneratable**
- **deep (need Admin, include dev cache + thumb by default):** `C:\Windows\Temp`, `SoftwareDistribution\Download` (stop wuauserv dulu), `journalctl --vacuum` **+ npm/pip/cargo/uv cache** (`npm cache clean --force` native) **+ thumbcache** (`cleanmgr` native)
- **opt-in extra (`--with`):** `docker` (`docker builder prune -f` / `docker system df` preview), tidak default karena bisa hapus image yang masih dipakai

## Pitfalls

- File ke-lock → skip, bukan fail. Jangan `shutil.rmtree` tanpa `onerror`
- `%TEMP%` vs `C:\Windows\Temp` → dedup via `realpath(expandvars())`, kalau sama cuma scan sekali
- >500MB / >30 hari → masuk `deep` confirm list, jangan auto-hapus di `quick`
- Jangan pakai `send2trash` / dependency baru, stdlib only (ladder rung 3)
- Selalu `dry-run` dulu untuk `deep`, jangan langsung hapus

## Slash

- `/safe-cleanup dry-run`              # preview semua tier
- `/safe-cleanup quick`                # tanpa Admin, include Hermes cache, tanpa dev cache/thumb
- `/safe-cleanup deep`                 # Deep Clean: system temp + dev cache + thumb + Hermes cache default
- `/safe-cleanup deep --with docker`   # + docker builder prune extra
- `/safe-cleanup status`
