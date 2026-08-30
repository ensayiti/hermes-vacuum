# Changelog

Semua perubahan penting di `hermes-vacuum` dicatat di sini. Format ikut Keep a Changelog, versi ikut Semantic Versioning.

## [0.1.1] 2026-08-30

### Ditambah
* Hermes cache masuk `quick` default. `$HERMES_HOME/cache` dan `~/.hermes/cache` sekarang ikut preview dan hapus di `quick` tanpa Admin, integrasi dengan `disk-cleanup` official
* Preview total reclaimable, breakdown per base, top 10 terbesar, dan laporan skip `LOCKED` vs `ACCESS_DENIED`
* Laporan disk `free before` dan `free after` plus `gain`

### Diubah
* Zero dash total. Semua dash dengan spasi diganti koma, hanya hyphen di dalam kata normal yang dipertahankan seperti `hermes-vacuum` dan `deep-clean`
* `deep` sekarang include dev cache `npm`, `pip`, `cargo`, `uv` plus `thumbcache` by default sesuai prinsip Deep Clean
* `pnpm store` dipindah ke opt in `--with pnpm` karena heavy 562MB dan bikin `dry-run` lambat dari 10 detik jadi 40 detik
* `docker` tetap opt in `--with docker` pakai `docker builder prune -f` dengan preview `docker system df`
* Scan dioptimalkan. `os.walk` dengan `followlinks=False`, skip symlink, cache `BLOCK` resolve, dan progress per base biar tidak hang di `pnpm store`

### Diperbaiki
* Dedup canonical `%TEMP%` vs `C:/Users/XEM/AppData/Local/Temp` biar tidak dobel scan
* Filter OS. `/tmp` dan `/var/tmp` di skip otomatis di Windows biar tidak scan `D:/tmp` yang tidak relevan
* `is_safe()` pakai string prefix lower case biar cepat untuk 50 ribu file, tetap strict allowlist only

## [0.1.0] 2026-08-30

### Ditambah
* Rilis awal `hermes-vacuum` sebagai Hermes Skill
* Struktur repo. `SKILL.md`, `scripts/clean.py` stdlib only, `docs/PRD.md`, `docs/ERD.md`, `docs/ARCHITECTURE.md`, `docs/TASKS.md`, `AGENTS.md`
* Tiga mode. `dry-run` default preview tanpa hapus, `quick` tanpa Admin, `deep` butuh Admin dengan `is_admin()` dan UAC
* Allowlist awal. `quick` untuk `%TEMP%` dan `~/Library/Caches`, `deep` untuk `C:/Windows/Temp` dan `SoftwareDistribution/Download`
* Mitigasi file tidak bisa dihapus. Per file `try/except`, `skipped` dengan reason `LOCKED` dan `ACCESS_DENIED`, lanjut scan tidak crash
* State dan log. `tracked.json` atomic write plus `tracked.json.bak` dan `cleanup.log` append only di `$HERMES_HOME/hermes-vacuum`
* Self check. `assert is_safe` untuk `%TEMP%` dan reject `System32` di `__main__`

### Keamanan
* `is_safe_path()` allowlist only, default `REJECT`
* Hard block `System32`, `WinSxS`, `Program Files`, `/System`, `/usr`
* Threshold `>500MB` masuk confirm list, tidak auto hapus di `quick`

[0.1.1]: https://github.com/xem/hermes-vacuum/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/xem/hermes-vacuum/releases/tag/v0.1.0
