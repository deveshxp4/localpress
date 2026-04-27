# ── Stage 1: base image ───────────────────────────────────────────────────────
FROM python:3.12-slim

# ── System deps: Ghostscript + ImageMagick + qpdf ────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    ghostscript \
    imagemagick \
    qpdf \
    && rm -rf /var/lib/apt/lists/*

# ── ImageMagick policy fix ────────────────────────────────────────────────────
# Default ImageMagick policy blocks PDF operations. Fix it.
RUN sed -i 's/rights="none" pattern="PDF"/rights="read|write" pattern="PDF"/' \
    /etc/ImageMagick-6/policy.xml || true

# ── App setup ─────────────────────────────────────────────────────────────────
WORKDIR /app

# Install Python deps first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy dvcom package (shared compression core)
COPY dvcom/ ./dvcom/
COPY pyproject.toml .

# Install dvcom package so app.py can import from it
RUN pip install --no-cache-dir -e .

# Copy Flask app
COPY localpress/ ./localpress/

# ── Tmp dirs ──────────────────────────────────────────────────────────────────
RUN mkdir -p /tmp/localpress/uploads /tmp/localpress/outputs

# ── Run ───────────────────────────────────────────────────────────────────────
COPY start.py .

EXPOSE 5000
CMD ["python", "start.py"]