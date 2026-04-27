#!/usr/bin/env python3
"""
LocalPress - Local PDF & Image Compressor
Flask web UI. Runs on localhost:5000. Nothing leaves your machine.
"""

import os, threading, uuid, time
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_file
from dvcom.core import compress_pdf, compress_image, check_deps, parse_target, human_size

app = Flask(__name__)

UPLOAD_DIR = Path("/tmp/localpress/uploads")
OUTPUT_DIR = Path("/tmp/localpress/outputs")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# job_id -> {status, logs, files}
JOBS = {}


# ── Job runner ────────────────────────────────────────────────────────────────

def run_job(job_id, files_info, output_dir):
    job = JOBS[job_id]
    job["status"] = "running"
    total = len(files_info)
    success = 0
    total_saved = 0

    def log(msg, level="info"):
        job["logs"].append({"msg": msg, "level": level, "ts": time.time()})

    for i, fi in enumerate(files_info):
        src       = fi["src"]
        target_b  = fi["target"]
        orig_name = fi["name"]
        suffix    = Path(orig_name).suffix.lower()
        orig_size = os.path.getsize(src)
        dst       = Path(output_dir) / f"{Path(orig_name).stem}_compressed{suffix}"

        log(f"→ {orig_name}")
        log(f"  {human_size(orig_size)} → target {human_size(target_b)}", "info")

        if suffix == ".pdf":
            ok, new_size, err = compress_pdf(src, str(dst), target_b, log)
        else:
            ok, new_size, err = compress_image(src, str(dst), target_b, log)

        if ok and os.path.exists(dst):
            new_size  = os.path.getsize(dst)
            saved     = orig_size - new_size
            pct       = (saved / orig_size * 100) if orig_size else 0
            total_saved += max(saved, 0)
            success += 1
            log(f"  ✓ {human_size(orig_size)} → {human_size(new_size)} (saved {pct:.1f}%)", "ok")
            if err: log(f"  ⚠ {err}", "warning")
            job["outputs"].append({
                "name": dst.name,
                "path": str(dst),
                "orig": human_size(orig_size),
                "final": human_size(new_size),
                "saved": f"{pct:.1f}%"
            })
        else:
            log(f"  ✗ failed: {err[:120]}", "err")

        job["progress"] = int((i + 1) / total * 100)

    log("─" * 40, "info")
    log(f"Done: {success}/{total} files. Total saved: {human_size(total_saved)}",
        "ok" if success == total else "warning")
    job["status"] = "done"


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    missing = check_deps()
    return render_template("index.html", missing=missing)

@app.route("/upload", methods=["POST"])
def upload():
    """Upload files, get back file info (name + size)."""
    saved = []
    for f in request.files.getlist("files"):
        uid  = uuid.uuid4().hex
        dest = UPLOAD_DIR / f"{uid}_{f.filename}"
        f.save(str(dest))
        saved.append({
            "id":       uid,
            "name":     f.filename,
            "size":     os.path.getsize(str(dest)),
            "size_human": human_size(os.path.getsize(str(dest))),
            "path":     str(dest)
        })
    return jsonify(saved)

@app.route("/compress", methods=["POST"])
def compress():
    """Start compression job. Body: [{id, name, path, target_str}]"""
    data = request.json
    job_id = uuid.uuid4().hex
    files_info = []

    for item in data["files"]:
        orig_bytes = os.path.getsize(item["path"])
        target_b   = parse_target(item.get("target", ""), orig_bytes)
        if target_b is None:
            return jsonify({"error": f"Invalid target for {item['name']}"}), 400
        files_info.append({
            "src":    item["path"],
            "name":   item["name"],
            "target": target_b
        })

    out_dir = data.get("output_dir") or str(OUTPUT_DIR)
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    JOBS[job_id] = {
        "status":   "queued",
        "progress": 0,
        "logs":     [],
        "outputs":  []
    }
    threading.Thread(target=run_job, args=(job_id, files_info, out_dir), daemon=True).start()
    return jsonify({"job_id": job_id})

@app.route("/job/<job_id>")
def job_status(job_id):
    job = JOBS.get(job_id)
    if not job: return jsonify({"error": "not found"}), 404
    return jsonify(job)

@app.route("/download/<path:filename>")
def download(filename):
    p = Path(filename).resolve()
    allowed = Path(OUTPUT_DIR).resolve()
    if not str(p).startswith(str(allowed)):
        return "Forbidden", 403
    if not p.exists():
        return "Not found", 404
    return send_file(str(p), as_attachment=True, download_name=p.name)

if __name__ == "__main__":
    import webbrowser
    print("\n  LocalPress running at http://localhost:5000")
    print("  Press Ctrl+C to stop.\n")
    threading.Timer(1.2, lambda: webbrowser.open("http://localhost:5000")).start()
    app.run(host="127.0.0.1", port=5000, debug=False)