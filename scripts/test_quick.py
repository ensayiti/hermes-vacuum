#!/usr/bin/env python3
"""
test_quick - validasi step 1 hermes-vacuum
Ponytail: one runnable check, no framework
"""
import pathlib, os, tempfile, time

# import from clean.py
import importlib.util, sys
spec = importlib.util.spec_from_file_location("clean", pathlib.Path(__file__).parent / "clean.py")
clean = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clean)

def test_is_safe():
    tmp = clean.resolve("%TEMP%")
    assert tmp and tmp.exists(), "TEMP not found"
    # allow %TEMP%/test.tmp
    assert clean.is_safe(tmp / "test.tmp", {tmp}), "is_safe should allow TEMP/test.tmp"
    # reject System32
    sys32 = pathlib.Path("C:/Windows/System32/notepad.exe")
    assert not clean.is_safe(sys32, {tmp}), "is_safe should reject System32"
    # reject Windows root
    assert not clean.is_safe(pathlib.Path("C:/Windows/notepad.exe"), {tmp}), "reject C:/Windows"
    print("is_safe OK")

def test_quick_dummy():
    tmp = pathlib.Path(os.environ.get("TEMP", tempfile.gettempdir()))
    testdir = tmp / "hermes-vacuum-test-step1"
    if testdir.exists():
        import shutil
        shutil.rmtree(testdir, ignore_errors=True)
    testdir.mkdir(parents=True, exist_ok=True)
    # buat 3 file dummy
    (testdir / "a.txt").write_text("hello", encoding="utf-8")
    (testdir / "c.log").write_text("log", encoding="utf-8")
    b = testdir / "b-locked.txt"
    b.write_text("locked", encoding="utf-8")
    # lock b dengan hold handle open (Windows: file open bikin unlink gagal)
    fh = open(b, "r", encoding="utf-8")
    try:
        # simulasi quick delete hanya untuk testdir, pakai allowed = {testdir}
        allowed = {testdir.resolve()}
        files = list(clean.scan(allowed))
        print(f"scanned {len(files)} file di {testdir}")
        assert len(files) >= 3, f"expected 3 file, got {len(files)}"
        # cek is_safe untuk tiap file
        for p, sz, mt in files:
            assert clean.is_safe(p, allowed), f"is_safe fail for {p}"
        # coba delete per file try/except seperti clean.py quick
        skipped = []
        reclaimed = 0
        for p, sz, mt in files:
            try:
                # defense in depth
                assert clean.is_safe(p, allowed)
                p.unlink()
                reclaimed += sz
            except (PermissionError, OSError) as e:
                # di Windows, file yang masih open akan WinError 32
                reason = "LOCKED" if "32" in str(e) or "in use" in str(e).lower() else "ACCESS_DENIED"
                skipped.append((p, reason))
        # di Windows, b yang masih open harusnya gagal, di Linux mungkin tetap kehapus (unlink while open allowed)
        # jadi cek: kalau Windows, b harus di skipped atau sudah terhapus tapi fh masih handle
        remaining = list(testdir.glob("*"))
        print(f"remaining after delete: {[x.name for x in remaining]}")
        print(f"skipped: {skipped}")
        print(f"reclaimed: {clean.fmt_size(reclaimed)}")
        # validasi: a.txt dan c.log harus hilang
        assert not (testdir / "a.txt").exists(), "a.txt harus terhapus"
        assert not (testdir / "c.log").exists(), "c.log harus terhapus"
        # b mungkin masih ada kalau Windows lock, atau hilang kalau Linux
        if os.name == "nt":
            # Windows: b harus skipped LOCKED dan masih ada
            if (testdir / "b-locked.txt").exists():
                assert any("LOCKED" in r for _, r in skipped), "b should be LOCKED"
                print("LOCKED handling OK di Windows")
            else:
                print("b terhapus walau open, Windows allow delete while open di env ini, skip LOCKED check")
        print("quick dummy OK")
    finally:
        fh.close()
        # cleanup testdir
        import shutil
        shutil.rmtree(testdir, ignore_errors=True)
        print("cleanup testdir done")

if __name__ == "__main__":
    test_is_safe()
    test_quick_dummy()
    print("STEP 1 PASS")
