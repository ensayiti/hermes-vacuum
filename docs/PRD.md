# PRD, hermes-vacuum

**Version:** 0.1.0, 2026-08-30  
**Owner:** XEM, Hermes Agent Skill  
**Status:** Draft → Ready for dev  
**Ponytail:** full, deletion over addition, stdlib first

---

## 1. Ringkasan

`hermes-vacuum` adalah Hermes Skill untuk **deep clean cache/temp yang aman** di Windows/Mac/Linux tanpa menyentuh file OS atau data penting. Berbeda dengan `disk-cleanup` (hanya `HERMES_HOME`), skill ini meng-cover **system user-cache** dengan **allowlist-only** + `dry-run` default + elevasi eksplisit untuk `deep`.

> One-liner: *CCleaner tapi ponytail, cuma hapus yang regeneratable, gak pernah sentuh System32.*

---

## 2. Problem & Goals

**Problem:**
- Disk penuh karena `%TEMP%`, `~/Library/Caches`, `~/.cache`, `npm/pip/cargo` cache, `thumbcache`, `SoftwareDistribution\Download`
- `disk-cleanup` tidak cover area ini
- Tool cleaner umum (CCleaner) terlalu agresif / butuh installer / nyentuh registry

**Goals (G):**
- G1: Reclaim 1-10GB dengan aman di 3 OS via 1 skill Hermes
- G2: Zero insiden hapus file OS / data user (allowlist + audit log)
- G3: UX 10 detik: `/safe-cleanup dry-run` → lihat → `/safe-cleanup quick` → beres

**Non-Goals (NG):**
- NG1: Registry cleaner, defrag, driver update, YAGNI
- NG2: GUI installer `.exe`, Hermes chat adalah GUI-nya
- NG3: Auto-elevate silent tanpa UAC, dilarang security

---

## 3. User Persona

- **Solo Dev (primary, lo):** D:/Code penuh cache, mau `quick` harian tanpa Admin
- **Power User:** Mau `deep` bulanan, paham UAC, `deep` langsung include dev cache + thumb, `docker` kalau mau extra (`--with docker`)
- **Non-tech (future):** Cuma berani `dry-run` + `status`

---

## 4. User Stories

- US1: Sebagai dev, gue mau `/safe-cleanup dry-run` lihat apa aja yang bisa kehapus + berapa GB, biar gak kaget
- US2: Sebagai dev, gue mau `/safe-cleanup quick` hapus `%TEMP%` tanpa Admin, skip file yang ke-lock tanpa crash
- US3: Sebagai power user, gue mau `/safe-cleanup deep` yang bersihin `C:\Windows\Temp` tapi **harus** lewat UAC, bukan silent
- US4: Sebagai power user, gue mau `/safe-cleanup deep` otomatis bersihin dev cache (npm/pip/cargo) + thumbcache via native tanpa flag tambahan, Deep Clean default
- US5: Sebagai user, gue mau `/safe-cleanup status` lihat breakdown per kategori + top 10 file terbesar
- US6: Sebagai user, gue mau log `cleanup.log` biar bisa audit apa yang kehapus kapan

---

## 5. Functional Requirements

| ID | Requirement | Priority | Mode |
|----|-------------|----------|------|
| F1 | `dry-run` default, scan allowlist, hitung size+age, tampilkan tabel, **tidak hapus** | P0 | all |
| F2 | `quick`, hapus allowlist user-cache (`%TEMP%`, `~/Library/Caches`, `~/.cache`, `/tmp`) tanpa Admin, per-file `try/except`, skip locked | P0 | quick |
| F3 | `deep`, F2 + `C:\Windows\Temp` + `SoftwareDistribution\Download` + `journalctl --vacuum` **+ dev cache (npm/pip/cargo/uv) + thumbcache by default**, **require `is_admin()`**, jika false → kasih command elevasi, stop | P0 | deep |
| F4 | `--with` extra, `docker` (`docker builder prune -f`, `docker system df` preview) via native, opt-in karena bisa hapus image yang masih dipakai | P1 | deep |
| F5 | `status`, breakdown per kategori + top-10 terbesar + total reclaimable | P0 | all |
| F6 | Dedup canonical, `realpath(expandvars())` sebelum scan, `%TEMP%` vs `C:\Windows\Temp` kalau sama cuma sekali | P0 | all |
| F7 | Per-file skip mitigasi, `PermissionError`/`OSError` → `skipped[]`, lanjut, akhir lapor "Dihapus X (N file), skip M (locked/access)" | P0 | quick/deep |
| F8 | `is_safe_path()`, allowlist-only, reject `System32`, `WinSxS`, `Program Files`, `/System`, `/usr`, `Application Support` sembarangan | P0 | all |
| F9 | Audit, append `cleanup.log` + `tracked.json` di `$HERMES_HOME/hermes-vacuum/` | P1 | quick/deep |
| F10 | Threshold, file >500MB / >30 hari masuk confirm list di `deep`, jangan auto di `quick` | P1 | deep |

---

## 6. Non-Functional

- **Safety:** 100% allowlist, never blocklist. Windows mounts outside allowlist = reject.
- **Perf:** `# ponytail: O(n) scan, parallel walk if >50k files`, target <5s untuk 10k file
- **Compat:** Windows 10/11 (utama), macOS 13+, Linux (Ubuntu). Python stdlib only (os, pathlib, shutil, ctypes, json, time)
- **No deps:** `npm cache clean` via `subprocess`, bukan lib. `cleanmgr` native.
- **Idempotent:** `dry-run` berkali-kali hasil sama, `quick` kedua kali = 0 file

---

## 7. Allowlist Detail

**quick (no Admin, include Hermes cache):**
- Win: `%TEMP%`, `%LOCALAPPDATA%\Temp`, `%LOCALAPPDATA%\Microsoft\Windows\INetCache` **+ `%LOCALAPPDATA%\hermes\cache` (`$HERMES_HOME/cache`), integrasi disk-cleanup official**
- Mac: `~/Library/Caches`, `~/Library/Logs`, `/private/var/folders`
- Linux: `~/.cache`, `/tmp`, `/var/tmp` **+ `~/.hermes/cache` / `$HERMES_HOME/cache`**

**deep (need Admin, Deep Clean = dev cache + thumb default):**
- Win: `C:\Windows\Temp`, `C:\Windows\SoftwareDistribution\Download` (stop `wuauserv` dulu), `DeliveryOptimization\Cache` **+ `%LOCALAPPDATA%\npm-cache`, `%LOCALAPPDATA%\pip\Cache`, `~/.cargo/registry/cache`, `~/.cache/uv` + `Explorer\thumbcache_*.db` (via `cleanmgr`)**
- Linux: `journalctl --vacuum-time=7d`, `/var/log` (hanya `*.log.*` >14 hari, bukan active log)
- Mac: `~/Library/Caches` tetap quick, tapi `DerivedData` + `CoreSimulator` masuk deep

**opt-in extra (`--with`):**
- `docker` → `docker builder prune -f` / `docker system prune` (preview `docker system df`), opt-in karena bisa hapus image/container yang masih dipakai

**Never (reject):** `C:\Windows\System32`, `WinSxS`, `Program Files*`, `~/Library/Application Support` (kecuali sub-cache jelas), `/System`, `/usr`, `/etc`

---

## 8. UX Flow

```
User: /safe-cleanup dry-run  (atau natural "bersihin dong")
Agent: scan allowlist → tabel [Kategori | File | Size | Age] + Total 2.4GB reclaimable (termasuk dev cache + thumb di deep)
User: /safe-cleanup quick
Agent: hapus per-file, skip locked → "✅ Dihapus 1.1GB (842 file), skip 37 (locked). Log: .../cleanup.log"
User: /safe-cleanup deep                 # auto include npm/pip/cargo + thumb
Agent: if not admin → "❌ Need Admin. Run: powershell Start-Process hermes -Verb RunAs ..."
       if admin → clean system temp + dev cache + thumb → confirm list >500MB → hapus → laporan
User: /safe-cleanup deep --with docker   # + docker builder prune extra
```

---

## 9. Success Metrics

- Reclaim ≥1GB di mesin dev tanpa `skipped` >20%
- Zero file OS terhapus (audit `cleanup.log`)
- `dry-run` <3s untuk 5k file, `quick` <10s
- User paham tanpa baca docs (3 command doang)

---

## 10. Out of Scope v0.1

- Scheduler cron auto-clean (bisa pakai Hermes `cronjob` nanti, bukan di skill)
- GUI, tray icon, installer
- Cloud/Dokumen user (`Documents`, `Downloads`), terlalu risky

---

## 11. Open Questions

- Q1: `thumbcache` mending `cleanmgr` atau `rm` + `ie4uinit -show`? → lean ke `cleanmgr` (native)
- Q2: `SoftwareDistribution\Download` butuh stop service, perlu `net stop wuauserv`? → yes, tapi cuma di `deep` + Admin
