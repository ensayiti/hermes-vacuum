# hermes-vacuum

Safe deep clean cache untuk Hermes Agent. Hapus sampah sistem tanpa sentuh file OS. Stdlib only, allowlist only, preview dulu sebelum hapus.

> Deep Clean versi ponytail. `quick` tanpa Admin, `deep` baru minta UAC. Hermes cache ikut kehitung.

![Hermes](https://img.shields.io/badge/Hermes-Skill-blue) ![Python](https://img.shields.io/badge/Python-stdlib%20only-green) ![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

## Kenapa hermes-vacuum

Disk penuh karena `Temp`, `npm-cache`, `cargo`, `thumbcache`, `Hermes cache` yang menumpuk. `disk-cleanup` bawaan Hermes cuma bersihin file Hermes. `hermes-vacuum` lanjut bersihin cache sistem yang aman, dengan preview total reclaimable dan laporan skip kalau file lagi dipakai.

## Fitur

* Preview dulu, hapus belakangan. `dry-run` default, tidak ada file terhapus tanpa konfirmasi
* Tiga mode jelas. `quick`, `deep`, `status`. Total file dan total GB selalu kelihatan
* Aman by default. Hanya hapus di allowlist, file OS seperti `System32` dan `WinSxS` selalu ditolak
* Hermes cache ikut. `$HERMES_HOME/cache` masuk `quick`, jadi cache web Hermes yang bengkak ikut kehitung
* Deep Clean beneran. `deep` include dev cache `npm`, `pip`, `cargo`, `uv` plus `thumbcache` tanpa flag tambahan
* Skip bukan gagal. File yang lagi dipakai di skip, 1 file ke lock tidak bikin 1 folder gagal
* Jalan di semua surface. CLI, Desktop, Dashboard pakai skill yang sama

## Keamanan

* `is_safe_path()` allowlist only. Path tidak ada di allowlist otomatis `REJECT`, tidak pernah `DELETE`
* Block OS core. `C:/Windows/System32`, `WinSxS`, `Program Files`, `/System`, `/usr` hard reject
* Canonical dedup. `%TEMP%` dan `C:/Users/XEM/AppData/Local/Temp` di `realpath` dulu biar tidak dobel scan
* Tanpa silent Admin. `deep` cek `is_admin()`, kalau false langsung kasih command elevasi `powershell Start-Process -Verb RunAs`, tidak auto elevate

## Instalasi

```bash
hermes skills install D:/Code/hermes-vacuum --name hermes-vacuum
hermes skills list  # pastikan hermes-vacuum muncul
```

Update:

```bash
hermes skills update hermes-vacuum
```

Hapus:

```bash
hermes skills remove hermes-vacuum
```

## Cara Pakai

### Hermes CLI

```bash
hermes
> /safe-cleanup dry-run
> /safe-cleanup quick
> /safe-cleanup deep
> /safe-cleanup deep --with docker
> /safe-cleanup status

# one shot tanpa masuk chat
hermes chat -q "/safe-cleanup dry-run"
hermes chat -q "/safe-cleanup status"
```

Natural language juga bisa:

```
bersihin cache dong
vacuum deep dong, preview dulu
```

### Hermes Desktop

1. Buka `hermes desktop`, pilih profile `default`
2. Di chat tengah ketik `/safe-cleanup dry-run` lalu Enter
3. Atau `Ctrl+K` lalu ketik `safe-cleanup`
4. Output tabel preview dan ringkasan `Dihapus X GB` muncul streaming, sama seperti CLI
5. File log ada di File Browser kiri di `$HERMES_HOME/hermes-vacuum/cleanup.log`

CLI dan Desktop pakai `tracked.json` yang sama, jadi `dry-run` di CLI terbaca `status` di Desktop.

### Hermes Dashboard Web UI

```bash
hermes dashboard
# buka http://localhost:3000
```

* Tab Skills: lihat `hermes-vacuum` terinstall
* Tab Chat: ketik `/safe-cleanup dry-run` di chat embedded, hasil sama persis
* Belum ada tab Vacuum khusus dengan tombol. Itu sengaja ponytail, chat sudah cukup. Tab khusus hanya ditambah kalau diminta.

## Perintah

| Perintah | Butuh Admin | Apa yang dihapus |
| --- | --- | --- |
| `/safe-cleanup dry-run` | Tidak | Preview semua tier, tidak hapus. Breakdown per base, total reclaimable, top 10 terbesar |
| `/safe-cleanup quick` | Tidak | `%TEMP%`, `%LOCALAPPDATA%/Temp`, `~/Library/Caches`, `~/.cache`, `/tmp` plus `$HERMES_HOME/cache` |
| `/safe-cleanup deep` | Ya | `quick` plus `C:/Windows/Temp`, `SoftwareDistribution/Download`, dev cache `npm`, `pip`, `cargo`, `uv` plus `thumbcache` |
| `/safe-cleanup deep --with docker` | Ya | `deep` plus `docker builder prune` |
| `/safe-cleanup deep --with pnpm` | Ya | `deep` plus `pnpm store` (heavy, 562MB, opt in biar dry run tetap cepat) |
| `/safe-cleanup status` | Tidak | Sama seperti dry run, baca dari `tracked.json` terakhir |

## Contoh Preview dan Hasil

**Preview:**

```
/safe-cleanup dry-run
Total scannable: 50689 file, 4.5GB reclaimable
Breakdown per base:
  3.2GB  10726 file  C:/Users/XEM/AppData/Local/Temp
  407MB  28263 file  npm-cache
Top 10:
  447MB  huggingface model
Disk free before: 25.8GB
[dry-run] Tidak ada file dihapus.
```

**Hasil setelah `quick`:**

```
/safe-cleanup quick
Dihapus: 805 file, 1.1GB
Skip: 37 file
  LOCKED: 32
  ACCESS_DENIED: 5
Disk free before: 25.8GB after: 26.9GB (gain: 1.1GB)
Log: C:/Users/XEM/AppData/Local/hermes/hermes-vacuum/cleanup.log
```

## Allowlist Detail

**quick tanpa Admin, include Hermes cache:**
* Windows: `%TEMP%`, `%LOCALAPPDATA%/Temp`, `%LOCALAPPDATA%/Microsoft/Windows/INetCache` plus `%LOCALAPPDATA%/hermes/cache`
* macOS: `~/Library/Caches`, `~/Library/Logs`
* Linux: `~/.cache`, `/tmp`, `/var/tmp` plus `~/.hermes/cache`

**deep butuh Admin, Deep Clean plus dev cache plus thumb default:**
* Windows: `C:/Windows/Temp`, `C:/Windows/SoftwareDistribution/Download` plus `npm-cache`, `pip Cache`, `cargo`, `uv` plus `thumbcache`
* Linux: `journalctl --vacuum-time=7d`
* macOS: `DerivedData`, `CoreSimulator`

**Opt in extra `--with`:**
* `docker` pakai `docker builder prune -f` dengan preview `docker system df`, opt in karena bisa hapus image yang masih dipakai
* `pnpm` pakai `%LOCALAPPDATA%/pnpm/store`, opt in karena heavy dan bikin dry run lambat

**Tidak pernah disentuh:**
`C:/Windows/System32`, `WinSxS`, `Program Files`, `~/Library/Application Support` sembarangan, `/System`, `/usr`, `/etc`

## FAQ

**Apakah file yang lagi dipakai bakal bikin error?**
Tidak. Per file pakai `try/except`, kalau `LOCKED` atau `ACCESS_DENIED` langsung di skip dan dilaporin di akhir. 1 file ke lock tidak bikin 1 folder gagal.

**Apakah `Temp` dan `%TEMP%` dobel kehitung?**
Tidak. Keduanya di `realpath` dulu, kalau resolve sama cuma scan sekali.

**Apakah perlu Run as Administrator terus?**
Tidak. Cukup `quick` dan `dry-run` tanpa Admin. `deep` saja yang butuh Admin dan akan muncul UAC. Hermes tetap jalan sebagai user biasa.

**Apakah jalan di semua model?**
Ya. LLM cuma parse intent `quick` atau `deep`, yang hapus itu `scripts/clean.py` yang deterministik. Jadi model ranking bawah yang kadang salah baca SKILL.md tetap ke block `is_safe()`.

**Apakah cache Hermes sudah ikut?**
Ya. `$HERMES_HOME/cache` masuk `quick` sejak v0.1.1, jadi cache web Hermes yang kemarin 8MB ikut kehitung.

## Dokumen Lanjutan

* `docs/PRD.md` Product Requirements
* `docs/ERD.md` Entity Relationship plus schema `tracked.json`
* `docs/ARCHITECTURE.md` Desain ponytail, scan `O(n)` plus mitigasi lock
* `docs/TASKS.md` Checklist dev

## Lisensi

MIT
