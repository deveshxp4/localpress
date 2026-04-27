"""
dvcom - core compression logic
Ghostscript + ImageMagick wrappers. No network. No cloud.
"""

import os, shutil, subprocess
from pathlib import Path


# ── Helpers ───────────────────────────────────────────────────────────────────

def human_size(b):
    if b < 1024:      return f"{b} B"
    if b < 1024**2:   return f"{b/1024:.1f} KB"
    return f"{b/1024**2:.2f} MB"


def check_deps():
    missing = []
    if not shutil.which("gs"):       missing.append("ghostscript")
    if not shutil.which("convert"):  missing.append("imagemagick")
    return missing


def parse_target(text, orig_bytes):
    """
    Parse target size string -> bytes.
    '2MB' -> 2097152
    '500KB' -> 512000
    '' -> 60% of original
    """
    t = text.strip() if text else ""
    if not t:
        return int(orig_bytes * 0.6)
    lo = t.lower()
    try:
        if "kb" in lo:
            return int(float(lo.replace("kb", "").strip()) * 1024)
        if "mb" in lo:
            return int(float(lo.replace("mb", "").strip()) * 1024 * 1024)
        # bare number treated as MB
        return int(float(lo) * 1024 * 1024)
    except Exception:
        return None


# ── PDF compression ───────────────────────────────────────────────────────────

def _gs_compress_text(src, dst):
    cmd = [
        "gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
        "-dNOPAUSE", "-dQUIET", "-dBATCH",
        "-dSubsetFonts=true", "-dCompressFonts=true", "-dCompressPages=true",
        "-dDetectDuplicateImages=true", "-dOptimize=true", "-dFastWebView=false",
        "-dDownsampleColorImages=false", "-dDownsampleGrayImages=false",
        f"-sOutputFile={dst}", src,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode == 0, r.stderr


def _gs_compress_dpi(src, dst, dpi):
    cmd = [
        "gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4",
        "-dNOPAUSE", "-dQUIET", "-dBATCH",
        "-dSubsetFonts=true", "-dCompressFonts=true", "-dDetectDuplicateImages=true",
        f"-dColorImageResolution={dpi}", f"-dGrayImageResolution={dpi}",
        f"-dMonoImageResolution={dpi}",
        "-dColorImageDownsampleType=/Bicubic", "-dGrayImageDownsampleType=/Bicubic",
        "-dDownsampleColorImages=true", "-dDownsampleGrayImages=true",
        f"-sOutputFile={dst}", src,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode == 0, r.stderr


def _qpdf_compress(src, dst):
    if not shutil.which("qpdf"):
        return False, "qpdf not installed"
    cmd = [
        "qpdf", "--compress-streams=y", "--object-streams=generate",
        "--recompress-flate", "--compression-level=9", src, dst,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode == 0, r.stderr


def compress_pdf(src, dst, target_bytes, log=None):
    """
    Compress PDF using 3-strategy cascade.
    log: callable(msg, level) or None
    Returns (success, final_size, warning_msg)
    """
    def _log(msg, level="info"):
        if log: log(msg, level)

    orig = os.path.getsize(src)
    temps = []

    def tmp(tag):
        p = str(dst) + f".dvcom_{tag}.pdf"
        temps.append(p)
        return p

    def cleanup(*keep):
        for t in temps:
            if t not in keep and os.path.exists(t):
                os.remove(t)

    best_path, best_size = None, orig

    # Strategy 1: font/stream optimisation
    t1 = tmp("text")
    ok, _ = _gs_compress_text(src, t1)
    if ok and os.path.exists(t1):
        s1 = os.path.getsize(t1)
        _log(f"  [font/stream] {human_size(orig)} → {human_size(s1)}")
        if s1 < best_size:
            best_size, best_path = s1, t1
        if s1 <= target_bytes:
            shutil.move(t1, dst)
            cleanup(str(dst))
            return True, s1, ""

    # Strategy 2: qpdf repack
    t2 = tmp("qpdf")
    ok2, _ = _qpdf_compress(best_path or src, t2)
    if ok2 and os.path.exists(t2):
        s2 = os.path.getsize(t2)
        _log(f"  [qpdf repack] → {human_size(s2)}")
        if s2 < best_size:
            best_size, best_path = s2, t2
        if s2 <= target_bytes:
            shutil.move(t2, dst)
            cleanup(str(dst))
            return True, s2, ""

    # Strategy 3: DPI binary search
    dpi_src = best_path or src
    lo, hi = 20, 300
    _log(f"  [DPI search] target={human_size(target_bytes)} ...")
    for _ in range(8):
        mid = (lo + hi) // 2
        td = tmp(f"dpi{mid}")
        ok3, _ = _gs_compress_dpi(dpi_src, td, mid)
        if not ok3:
            if os.path.exists(td): os.remove(td)
            hi = mid - 10
            continue
        sd = os.path.getsize(td)
        _log(f"  [DPI={mid}] → {human_size(sd)}")
        if sd <= target_bytes:
            if sd > best_size or best_path is None:
                best_size, best_path = sd, td
            else:
                os.remove(td)
            lo = mid + 1
        else:
            if sd < best_size:
                best_size, best_path = sd, td
            else:
                os.remove(td)
            hi = mid - 1
        if lo > hi:
            break

    if best_path and os.path.exists(best_path):
        shutil.move(best_path, dst)
        cleanup(str(dst))
        final = os.path.getsize(dst)
        warn = "" if final <= target_bytes else "best effort -- target unreachable (text-only or already compressed)"
        return True, final, warn

    cleanup()
    return False, 0, "all strategies failed"


# ── Image compression ─────────────────────────────────────────────────────────

def compress_image(src, dst, target_bytes, log=None):
    """
    Binary search on ImageMagick quality level.
    Returns (success, final_size, warning_msg)
    """
    def _log(msg, level="info"):
        if log: log(msg, level)

    lo, hi = 5, 95
    best_path, best_size = None, None
    temps = []

    for _ in range(8):
        mid = (lo + hi) // 2
        t = str(dst) + f".dvcom_{mid}"
        temps.append(t)
        r = subprocess.run(
            ["convert", src, "-quality", str(mid), t],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            if os.path.exists(t): os.remove(t)
            hi = mid - 1
            continue
        size = os.path.getsize(t)
        _log(f"  [quality={mid}] → {human_size(size)}")
        if size <= target_bytes:
            if best_size is None or size > best_size:
                if best_path and os.path.exists(best_path): os.remove(best_path)
                best_path, best_size = t, size
            else:
                os.remove(t)
            lo = mid + 1
        else:
            os.remove(t)
            hi = mid - 1
        if lo > hi:
            break

    def cleanup():
        for t in temps:
            if t != best_path and os.path.exists(t):
                os.remove(t)

    if best_path and os.path.exists(best_path):
        shutil.move(best_path, dst)
        cleanup()
        return True, os.path.getsize(dst), ""

    # fallback: quality 5
    r = subprocess.run(
        ["convert", src, "-quality", "5", str(dst)],
        capture_output=True, text=True,
    )
    cleanup()
    if r.returncode == 0:
        return True, os.path.getsize(dst), "best effort -- target unreachable"
    return False, 0, r.stderr
