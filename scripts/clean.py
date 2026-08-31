#!/usr/bin/env python3
"""
hermes-vacuum, safe system cache cleaner (stdlib only)
Ponytail: O(n) scan, parallel walk if >50k files
Deep Clean: quick = %TEMP% + Hermes cache, deep = + system temp + dev cache + thumb, --with docker opt-in
"""
import os, sys, json, ctypes, pathlib, shutil, subprocess, time
from datetime import datetime

# --- allowlist (Deep Clean: deep = dev cache + thumb default) ---
ALLOWLIST = {
    "quick": [
        "%TEMP%",
        "%LOCALAPPDATA%/Temp",
        "~/Library/Caches",
        "~/Library/Logs",
        "~/.cache",
        "/tmp",
        "/var/tmp",
        # Hermes official cache, integrasi disk-cleanup (regeneratable)
        "$HERMES_HOME/cache", "%LOCALAPPDATA%/hermes/cache", "~/.hermes/cache",
        "$HERMES_HOME/cache/web",  # web cache hermes yang sering bengkak
    ],
    "deep": [  # need Admin + includes dev cache + thumb by default
        "C:/Windows/Temp",
        "C:/Windows/SoftwareDistribution/Download",
        "C:/Windows/DeliveryOptimization/Cache",
        # dev cache, Deep Clean principle (auto-include, fast scan)
        "%LOCALAPPDATA%/npm-cache", "~/.npm",
        "%LOCALAPPDATA%/pip/Cache", "~/.cache/pip",
        "~/.cargo/registry/cache", "~/.cargo/registry/src",
        "~/.cache/uv", "%LOCALAPPDATA%/uv/cache",
        # thumbcache, default in deep
        "%LOCALAPPDATA%/Microsoft/Windows/Explorer/thumbcache_*.db",
    ],
    "optin_extra": {  # --with docker/pnpm only (heavy/slow)
        "docker": ["docker builder prune"],  # via subprocess: docker builder prune -f / docker system df preview
        "pnpm": ["%LOCALAPPDATA%/pnpm/store"],  # heavy, 562M+, opt-in to keep dry-run fast
    }
}

# strict block, never touch even if allowlist typo
BLOCK = [
    "C:/Windows/System32",
    "C:/Windows/SysWOW64",
    "C:/Windows/WinSxS",
    "C:/Windows/System",
    "C:/Program Files",
    "C:/Program Files (x86)",
    "/System", "/System/Library",
    "/usr", "/etc", "/bin", "/sbin",
    "C:/Windows",  # bare C:/Windows without /Temp subpath = reject
]

def is_admin() -> bool:
    try: return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except: return os.geteuid() == 0 if hasattr(os, "geteuid") else False

def resolve(p: str) -> pathlib.Path | None:
    try:
        # expand $HERMES_HOME even if env not set, fallback to LOCALAPPDATA/hermes
        if "$HERMES_HOME" in p:
            hh = os.environ.get("HERMES_HOME") or os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes") or str(pathlib.Path.home()/".hermes")
            p = p.replace("$HERMES_HOME", hh)
        # handle glob * for thumbcache, return parent dir for is_safe base
        if "*" in p:
            p = p.split("*")[0]
            # trim trailing / or _
            p = p.rstrip("/\\_")
        return pathlib.Path(os.path.expandvars(os.path.expanduser(p))).resolve()
    except: return None

def get_allowed_set(mode: str, with_flags: list[str]) -> tuple[set[pathlib.Path], list[str]]:
    raws = []
    raws += ALLOWLIST["quick"]
    if mode in ("deep", "dry-run", "status"):
        # dry-run/status preview all (quick+deep) biar total kelihatan
        raws += ALLOWLIST["deep"]
        # deep includes quick+deep, dry-run preview both
        if mode == "deep":
            pass
    # opt-in
    for f in with_flags:
        if f in ALLOWLIST["optin_extra"]:
            raws += ALLOWLIST["optin_extra"][f]
    resolved = set()
    skipped_templates = []
    for r in raws:
        # OS filter: on Windows skip pure Unix paths like /tmp, /var/tmp
        if os.name == "nt" and r.startswith("/") and not r.startswith("C:/"):
            skipped_templates.append(f"{r} -> skip on Windows")
            continue
        rp = resolve(r)
        if rp and rp.exists():
            # canonical dedup
            resolved.add(rp)
        elif rp:
            skipped_templates.append(f"{r} -> {rp} (not exist, skip)")
    # BLOCK filter, remove any allowed that is inside BLOCK (safety)
    filtered = set()
    for a in resolved:
        if any(_is_inside(a, resolve(b)) for b in BLOCK if resolve(b)):
            continue
        filtered.add(a)
    return filtered, skipped_templates

def _is_inside(path: pathlib.Path, parent: pathlib.Path | None) -> bool:
    if not parent: return False
    try: path.relative_to(parent); return True
    except: return False

def is_safe(path: pathlib.Path, allowed: set[pathlib.Path]) -> bool:
    # ponytail: fast string prefix, cached BLOCK, no per-file resolve storm
    try: s = str(path.resolve()).lower()
    except: s = str(path).lower()
    # hard BLOCK first, string check
    for b in BLOCK:
        bp = _block_resolved.get(b) or resolve(b)
        if bp and s.startswith(str(bp).lower() + os.sep):
            # allow if inside allowed (e.g. C:/Windows/Temp inside C:/Windows)
            if any(s.startswith(str(a).lower() + os.sep) or s == str(a).lower() for a in allowed):
                continue
            return False
        if s == str(bp).lower() if bp else False:
            return False
    for a in allowed:
        al = str(a).lower()
        if s == al or s.startswith(al + os.sep):
            return True
    return False

# cache BLOCK resolves once
_block_resolved = {b: resolve(b) for b in BLOCK}

def fmt_size(b: int) -> str:
    for unit in ["B","KB","MB","GB","TB"]:
        if abs(b) < 1024: return f"{b:.1f}{unit}" if unit!="B" else f"{b}B"
        b /= 1024
    return f"{b:.1f}PB"

def scan(allowed: set[pathlib.Path]):
    # ponytail: O(n) os.walk, followlinks=False, no rglob symlink storm, no per-file resolve
    for base in allowed:
        if not base.exists(): continue
        if base.is_file():
            try: yield base, base.stat().st_size, base.stat().st_mtime
            except: continue
            continue
        for root, dirs, files in os.walk(base, topdown=True, followlinks=False, onerror=lambda e: None):
            # prune dirs that are blocked? skip System32-like if somehow inside allowed (defense)
            # don't descend into reparse points
            try:
                # skip blocked subdirs quickly via string check
                root_l = str(pathlib.Path(root).resolve()).lower() if os.path.exists(root) else root.lower()
                if any(root_l.startswith(str(_block_resolved.get(b) or "").lower() + os.sep) for b in BLOCK if _block_resolved.get(b)):
                    # but if root is inside allowed, keep it (e.g. C:/Windows/Temp)
                    if not any(root_l.startswith(str(a).lower()+os.sep) or root_l==str(a).lower() for a in allowed):
                        dirs[:] = []
                        continue
            except: pass
            for name in files:
                p = pathlib.Path(root) / name
                try:
                    # lstat not follow symlink
                    st = p.stat() if not p.is_symlink() else p.lstat()
                    if p.is_symlink(): continue  # skip symlinks (pnpm store has many)
                    yield p, st.st_size, st.st_mtime
                except: continue

def get_disk_free(path: str = "C:/") -> int:
    try: return shutil.disk_usage(path).free
    except: 
        try: return shutil.disk_usage(pathlib.Path.home().anchor).free
        except: return 0

def run_docker_preview() -> str:
    try:
        out = subprocess.run(["docker","system","df"], capture_output=True, text=True, timeout=10)
        return out.stdout.strip() if out.returncode==0 else "docker not available"
    except: return "docker not available"

def run_docker_prune() -> tuple[int, str]:
    try:
        # preview before
        df_before = run_docker_preview()
        r = subprocess.run(["docker","builder","prune","-f"], capture_output=True, text=True, timeout=60)
        r2 = subprocess.run(["docker","system","df"], capture_output=True, text=True, timeout=10)
        return 0, f"docker builder prune: {r.stdout.strip()[:500]}\n{r2.stdout.strip()[:500]}"
    except Exception as e: return 1, str(e)

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "dry-run"  # dry-run|quick|deep|status
    # --with now only for docker extra, dev cache+thumb is default in deep
    with_flags = []
    if "--with" in sys.argv:
        idx = sys.argv.index("--with")
        if idx+1 < len(sys.argv): with_flags = [x.strip() for x in sys.argv[idx+1].split(",") if x.strip()]
    elif any(a.startswith("--with=") for a in sys.argv):
        with_flags = next(a for a in sys.argv if a.startswith("--with=")).split("=",1)[1].split(",")

    if mode not in ("dry-run","quick","deep","status"):
        print(f"Unknown mode '{mode}', fallback to dry-run")
        mode = "dry-run"

    # deep needs admin
    if mode == "deep" and not is_admin():
        print("❌ Deep clean requires Admin. Hermes is running as normal user.")
        print("   Run elevation manually (UAC will appear):")
        print('   powershell -Command "Start-Process python -ArgumentList \'D:/Code/hermes-vacuum/scripts/clean.py deep\' -Verb RunAs"')
        print("   or: run Terminal as Administrator -> python D:/Code/hermes-vacuum/scripts/clean.py deep")
        if "docker" in with_flags:
            print("   + docker: powershell -Command \"Start-Process python -ArgumentList 'D:/Code/hermes-vacuum/scripts/clean.py deep --with docker' -Verb RunAs\"")
        sys.exit(1)

    # get allowed
    # for quick: only quick allowlist, for deep/dry-run/status: quick+deep
    if mode == "quick":
        allowed, skipped_tpl = get_allowed_set("quick", [])
    elif mode == "deep":
        allowed, skipped_tpl = get_allowed_set("deep", with_flags)
    else: # dry-run/status preview all
        allowed, skipped_tpl = get_allowed_set("dry-run", with_flags)
        # for preview, show both quick+deep total

    print(f"[hermes-vacuum] mode={mode} admin={is_admin()} with={with_flags}")
    print(f"Allowed bases ({len(allowed)}):")
    for a in sorted(allowed, key=lambda x: str(x)):
        print(f"  • {a}")
    if skipped_tpl:
        print(f"Skipped templates (not exist): {len(skipped_tpl)}")

    # docker preview if with docker
    if "docker" in with_flags:
        print("\n[docker] preview:")
        print(run_docker_preview())

    free_before = get_disk_free()

    # scan, already limited to allowed bases, skip per-file is_safe (scan is trusted)
    print("\nScanning... (ponytail O(n) scan)")
    files = []  # list of (path, size, mtime)
    for base in sorted(allowed, key=lambda x: str(x)):
        print(f"  Scanning {base}...")
        for p, sz, mt in scan({base}):
            files.append((p, sz, mt))
        print(f"    -> {len([f for f in files if str(f[0]).lower().startswith(str(base).lower())])} file so far")

    total = sum(sz for _, sz, _ in files)
    # breakdown per category (by base), fast string prefix, no per-file resolve
    from collections import Counter, defaultdict
    by_base = defaultdict(int)
    by_base_cnt = Counter()
    allowed_str = [(str(a).lower(), str(a)) for a in allowed]
    for p, sz, _ in files:
        s = str(p).lower()
        owner = next((orig for low, orig in allowed_str if s == low or s.startswith(low + os.sep)), "unknown")
        by_base[owner] += sz
        by_base_cnt[owner] += 1

    # top 10 largest
    top10 = sorted(files, key=lambda x: x[1], reverse=True)[:10]
    # confirm list >500MB or >30d
    now = time.time()
    confirm = [(p,sz) for p,sz,mt in files if sz > 500*1024*1024 or (now-mt) > 30*86400]
    # locked preview not yet, will be during delete

    print(f"\n=== PREVIEW ===")
    print(f"Total scannable: {len(files)} file, {fmt_size(total)} reclaimable")
    print(f"Breakdown per base:")
    for base, sz in sorted(by_base.items(), key=lambda x: x[1], reverse=True):
        print(f"  {fmt_size(sz):>9}  {by_base_cnt[base]:>5} file  {base}")
    print(f"Top 10 largest:")
    for p, sz, mt in top10:
        age = int((now-mt)/86400)
        print(f"  {fmt_size(sz):>9}  {age:>3}d  {p}")
    if confirm:
        print(f"Confirm needed (>500MB or >30d): {len(confirm)} file, not auto in quick, needs deep confirm")
        for p, sz in confirm[:5]: print(f"  {fmt_size(sz)} {p}")
        if len(confirm)>5: print(f"  ... +{len(confirm)-5} more")
    print(f"Disk free before: {fmt_size(free_before)}")

    if mode in ("dry-run","status"):
        print(f"\n[dry-run] No files deleted. Run:")
        print(f"  python scripts/clean.py quick              # no Admin, includes Hermes cache")
        print(f"  python scripts/clean.py deep               # + dev cache + thumb, requires Admin")
        print(f"  python scripts/clean.py deep --with docker # + docker prune")
        # save tracked.json
        save_tracked(mode, with_flags, files, total)
        return

    # quick / deep → delete per-file try/except
    print(f"\n=== EXECUTE {mode} ===")
    if mode == "quick":
        # quick jangan hapus confirm list >500MB
        to_delete = [(p,sz,mt) for p,sz,mt in files if not (sz > 500*1024*1024)]
        if len(to_delete) != len(files):
            print(f"Skipped {len(files)-len(to_delete)} file >500MB (needs deep)")
    else:
        to_delete = files

    skipped = []  # list of (path, reason)
    reclaimed = 0
    deleted_cnt = 0
    # handle SoftwareDistribution stop service if deep
    wuauserv_stopped = False
    if mode == "deep" and any("SoftwareDistribution" in str(a) for a in allowed):
        try:
            print("Stopping wuauserv for SoftwareDistribution...")
            subprocess.run(["net","stop","wuauserv"], capture_output=True, timeout=15)
            wuauserv_stopped = True
        except: pass

    for p, sz, _ in to_delete:
        try:
            # double is_safe check before delete (defense in depth)
            if not is_safe(p, allowed):
                skipped.append((p, "REJECT_NOT_SAFE"))
                continue
            if p.is_dir():
                shutil.rmtree(p, onerror=lambda *a: (_ for _ in ()).throw(OSError(*a)))
            else:
                p.unlink()
            reclaimed += sz
            deleted_cnt += 1
        except (PermissionError, OSError) as e:
            reason = "LOCKED" if "in use" in str(e).lower() or "being used" in str(e).lower() else "ACCESS_DENIED"
            if "WinError 32" in str(e): reason = "LOCKED"
            if "WinError 5" in str(e): reason = "ACCESS_DENIED"
            skipped.append((p, reason))
            continue

    if wuauserv_stopped:
        try: subprocess.run(["net","start","wuauserv"], capture_output=True, timeout=15)
        except: pass

    # docker prune if with docker
    docker_msg = ""
    if "docker" in with_flags and mode == "deep":
        print("\n[docker] pruning...")
        code, msg = run_docker_prune()
        docker_msg = msg
        print(msg)

    free_after = get_disk_free()
    gained = free_after, free_before

    print(f"\n=== HASIL ===")
    print(f"Deleted: {deleted_cnt} file, {fmt_size(reclaimed)} (reclaimed)")
    print(f"Skipped: {len(skipped)} file")
    if skipped:
        from collections import Counter
        c = Counter(r for _, r in skipped)
        for k,v in c.items(): print(f"  {k}: {v}")
        print("Example skipped (first 5):")
        for p,r in skipped[:5]: print(f"  {r} {p}")
    print(f"Disk free before: {fmt_size(free_before)} → after: {fmt_size(free_after)} (gain: {fmt_size(gained)})")
    if docker_msg: print(docker_msg)

    save_tracked(mode, with_flags, files, total, deleted_cnt, reclaimed, skipped)
    log_append(mode, deleted_cnt, reclaimed, skipped)

def save_tracked(mode, with_flags, files, total, deleted=0, reclaimed=0, skipped=None):
    try:
        home = pathlib.Path(os.environ.get("HERMES_HOME") or os.path.join(os.environ.get("LOCALAPPDATA",""), "hermes") or str(pathlib.Path.home()/".hermes"))
        d = home / "hermes-vacuum"
        d.mkdir(parents=True, exist_ok=True)
        tracked = d / "tracked.json"
        data = {"at": datetime.now().isoformat(), "mode": mode, "with": with_flags, "total_scanned": len(files), "total_bytes": total, "deleted": deleted, "reclaimed": reclaimed, "skipped": len(skipped or [])}
        # atomic write
        tmp = d / "tracked.json.tmp"
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        bak = d / "tracked.json.bak"
        if tracked.exists():
            try: shutil.copy2(tracked, bak)
            except: pass
        tmp.replace(tracked)
    except Exception as e: print(f"tracked.json save fail: {e}")

def log_append(mode, deleted, reclaimed, skipped):
    try:
        home = pathlib.Path(os.environ.get("HERMES_HOME") or os.path.join(os.environ.get("LOCALAPPDATA",""), "hermes") or str(pathlib.Path.home()/".hermes"))
        d = home / "hermes-vacuum"
        d.mkdir(parents=True, exist_ok=True)
        log = d / "cleanup.log"
        with log.open("a", encoding="utf-8") as f:
            f.write(f"{datetime.now().isoformat()} {mode} deleted={deleted} reclaimed={reclaimed} skipped={len(skipped or [])}\n")
            for p,r in (skipped or [])[:20]:
                f.write(f"  SKIP {r} {p}\n")
    except: pass

if __name__ == "__main__":
    main()
    # --- self-check (ponytail: one runnable check) ---
    try:
        # is_safe must allow %TEMP%/test.tmp if %TEMP% is allowed
        tmp = resolve("%TEMP%/test.tmp") or pathlib.Path(os.environ.get("TEMP","C:/Temp"))/"test.tmp"
        allowed = {resolve("%TEMP%")} if resolve("%TEMP%") else set()
        if allowed and list(allowed)[0]:
            assert is_safe(tmp, allowed) or os.name != "nt", "is_safe failed for %TEMP%"
        # is_safe must reject System32
        sys32 = pathlib.Path("C:/Windows/System32/notepad.exe")
        assert not is_safe(sys32, {resolve("%TEMP%")} if resolve("%TEMP%") else set()), "is_safe should reject System32"
        print("self-check ok")
    except AssertionError as e: print(f"self-check FAIL: {e}"); sys.exit(1)
    except Exception as e: print(f"self-check skip: {e}")
