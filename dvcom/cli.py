#!/usr/bin/env python3
"""
dvcom - compress PDFs and images from your terminal.

Usage:
  dvcom file.pdf
  dvcom file.pdf 2MB
  dvcom photo.jpg 500KB
  dvcom *.pdf 1MB
  dvcom file.pdf 2MB --output ~/Desktop
  dvcom file.pdf --output ~/Desktop/compressed.pdf
"""

import sys
import os
import argparse
import glob
from pathlib import Path

from dvcom.core import (
    compress_pdf,
    compress_image,
    check_deps,
    parse_target,
    human_size,
)

# ── ANSI colours ──────────────────────────────────────────────────────────────

def _supports_color():
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

USE_COLOR = _supports_color()

def green(s):  return f"\033[32m{s}\033[0m" if USE_COLOR else s
def yellow(s): return f"\033[33m{s}\033[0m" if USE_COLOR else s
def red(s):    return f"\033[31m{s}\033[0m" if USE_COLOR else s
def dim(s):    return f"\033[2m{s}\033[0m"  if USE_COLOR else s
def bold(s):   return f"\033[1m{s}\033[0m"  if USE_COLOR else s
def cyan(s):   return f"\033[36m{s}\033[0m" if USE_COLOR else s


# ── Logger ────────────────────────────────────────────────────────────────────

def make_logger(verbose):
    def log(msg, level="info"):
        if level == "info" and not verbose:
            return
        if level == "info":
            print(dim(f"    {msg}"))
        elif level == "ok":
            print(green(f"  {msg}"))
        elif level == "warning":
            print(yellow(f"  ⚠  {msg}"))
        elif level == "err":
            print(red(f"  ✗  {msg}"))
        else:
            print(f"  {msg}")
    return log


# ── Resolve output path ───────────────────────────────────────────────────────

def resolve_output(src: Path, output_arg: str | None, multiple: bool) -> Path:
    """
    Work out where to save the compressed file.
    - If --output is a directory (or multiple files): save inside that dir
    - If --output is a full path and single file: use it directly
    - Default: same directory as source, _compressed suffix
    """
    stem   = src.stem
    suffix = src.suffix

    if output_arg:
        out = Path(output_arg).expanduser()
        if out.is_dir() or multiple or not out.suffix:
            out.mkdir(parents=True, exist_ok=True)
            return out / f"{stem}_compressed{suffix}"
        else:
            out.parent.mkdir(parents=True, exist_ok=True)
            return out

    return src.parent / f"{stem}_compressed{suffix}"


# ── Size string detector ──────────────────────────────────────────────────────

def is_size_string(s):
    """Return True if s looks like a size: 2MB, 500kb, 1.5mb, 300KB etc."""
    lo = s.lower().strip()
    if lo.endswith("mb") or lo.endswith("kb"):
        try:
            float(lo[:-2].strip())
            return True
        except ValueError:
            return False
    # bare number = treat as MB
    try:
        float(lo)
        return True
    except ValueError:
        return False


# ── Banner ────────────────────────────────────────────────────────────────────

BANNER = f"""{bold(cyan('dvcom'))}  {dim('local file compressor · no cloud · no nonsense')}"""


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="dvcom",
        description="Compress PDFs and images locally. Nothing leaves your machine.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  dvcom report.pdf                    compress PDF to 60% of original size
  dvcom report.pdf -t 2MB             compress PDF to target 2 MB
  dvcom report.pdf -t 2mb             same, lowercase works too
  dvcom photo.jpg -t 500kb            compress image to target 500 KB
  dvcom *.pdf -t 1mb                  batch compress all PDFs in folder
  dvcom scan.pdf -t 2mb -o ~/Desktop  save to Desktop
  dvcom report.pdf -v                 verbose output (show compression steps)
        """,
    )

    parser.add_argument(
        "files",
        nargs="+",
        help="file(s) to compress -- PDF or image (jpg, png, webp, bmp, tiff)",
    )
    parser.add_argument(
        "-t", "--target",
        default="",
        metavar="SIZE",
        help="target size: '2MB', '500kb', '1.5mb', or blank for -40%%",
    )
    parser.add_argument(
        "-o", "--output",
        metavar="PATH",
        help="output file or directory",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="show compression steps",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="dvcom 1.0.0",
    )

    args = parser.parse_args()

    # ── Print banner ──────────────────────────────────────────────────────────
    print()
    print(BANNER)
    print()

    # ── Expand globs (Windows doesn't auto-expand) ────────────────────────────
    raw_files = []
    for pattern in args.files:
        expanded = glob.glob(pattern)
        if expanded:
            raw_files.extend(expanded)
        else:
            raw_files.append(pattern)   # let it fail naturally below

    # ── Get target string ─────────────────────────────────────────────────────
    target_str = args.target

    # ── Validate files ────────────────────────────────────────────────────────
    SUPPORTED = {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}
    files = []
    has_pdf = False
    has_img = False

    for f in raw_files:
        p = Path(f)
        if not p.exists():
            print(red(f"  not found: {f}"))
            continue
        ext = p.suffix.lower()
        if ext not in SUPPORTED:
            print(yellow(f"  unsupported type: {f}  (supported: pdf, jpg, png, webp, bmp, tiff)"))
            continue
        files.append(p)
        if ext == ".pdf":
            has_pdf = True
        else:
            has_img = True

    if not files:
        print(red("  no valid files to compress."))
        sys.exit(1)

    # ── Check deps dynamically based on input file types ──────────────────────
    missing = check_deps()
    missing_req = []
    if has_pdf and "ghostscript" in missing:
        missing_req.append("ghostscript")
    if has_img and "imagemagick" in missing:
        missing_req.append("imagemagick")

    if missing_req:
        print(red("  missing dependencies for requested file type(s):"))
        for m in missing_req:
            print(red(f"    · {m}"))
        print()
        print("  install them:")
        print(dim("    mac:    brew install " + " ".join(missing_req)))
        print(dim("    linux:  sudo apt install " + " ".join(missing_req)))
        print()
        sys.exit(1)

    # ── Run compression ───────────────────────────────────────────────────────
    log      = make_logger(args.verbose)
    multiple = len(files) > 1
    success  = 0
    total_saved = 0

    for src in files:
        orig_size  = os.path.getsize(src)
        target_b   = parse_target(target_str, orig_size)

        if target_b is None:
            print(red(f"  invalid target '{target_str}' -- use format like 2MB or 500KB"))
            sys.exit(1)

        dst = resolve_output(src, args.output, multiple)

        print(f"  {bold(src.name)}")
        print(dim(f"    {human_size(orig_size)} → target {human_size(target_b)}"))

        suffix = src.suffix.lower()
        if suffix == ".pdf":
            ok, new_size, warn = compress_pdf(str(src), str(dst), target_b, log)
        else:
            ok, new_size, warn = compress_image(str(src), str(dst), target_b, log)

        if ok and dst.exists():
            new_size = os.path.getsize(dst)
            saved    = orig_size - new_size
            pct      = (saved / orig_size * 100) if orig_size else 0
            total_saved += max(saved, 0)
            success += 1
            size_arrow = f"{human_size(orig_size)} → {bold(human_size(new_size))}"
            print(green(f"  ✓  {size_arrow}  (saved {pct:.1f}%)"))
            print(dim(f"     saved to: {dst}"))
            if warn:
                print(yellow(f"  ⚠  {warn}"))
        else:
            print(red(f"  ✗  failed"))

        print()

    # ── Summary ───────────────────────────────────────────────────────────────
    if multiple:
        status = green(f"{success}/{len(files)} files compressed") if success == len(files) \
                 else yellow(f"{success}/{len(files)} files compressed")
        print(f"  {status}  ·  total saved: {bold(human_size(total_saved))}")
        print()

    sys.exit(0 if success > 0 else 1)


if __name__ == "__main__":
    main()