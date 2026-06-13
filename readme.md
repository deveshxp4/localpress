# 🔒 LocalPress

> Secure, 100% offline PDF & image compression right in your browser. No uploads. No servers. Zero network footprint.

LocalPress is a privacy-first utility tool designed to compress documents and images using **client-side hardware**. It runs entirely in the user's browser sandbox, making it 100% private, compliant with regulations (GDPR/HIPAA), and completely serverless.

It also includes a local Python CLI tool (`dvcom`) and developer Flask backend for high-performance server-side processing using Ghostscript and ImageMagick.

---

## 🚀 Deployed Web App (100% Local / Static)

You can host this project as a **static-only website** (e.g., on Cloudflare Pages, Vercel, or GitHub Pages) for zero cost and infinite scalability.

*   **Zero Installs**: Visitors do not need to install Python, Ghostscript, or ImageMagick. Everything runs in the browser.
*   **Offline First**: Loads core engines locally. Works even when disconnected from the internet.
*   **Privacy Guaranteed**: Files never leave the browser. You can verify this by checking your browser's Network tab (F12).

---

## 🛠️ CLI & Local Server Setup (`dvcom`)

For power users who prefer the terminal or want to run the full high-performance server engine locally using **Ghostscript** and **ImageMagick**:

### 1. Install System Dependencies

**macOS**
```bash
brew install ghostscript imagemagick qpdf
```

**Ubuntu / Debian**
```bash
sudo apt install ghostscript imagemagick qpdf
```

**Windows**
1. Download and install **Ghostscript** from [ghostscript.com](https://www.ghostscript.com/releases/gsdnld.html)
2. Download and install **ImageMagick** from [imagemagick.org](https://imagemagick.org/script/download.php#windows) *(check "Install legacy utilities (e.g. convert)" during setup)*.

### 2. Install the CLI Package

Create and activate your virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### 3. Use the CLI

```bash
dvcom report.pdf               # Compress to -40% default size
dvcom report.pdf -t 2MB        # Target exactly 2 MB
dvcom photo.jpg -t 500KB       # Works on images with EXIF stripping
dvcom *.pdf -t 1MB             # Batch compress documents
dvcom report.pdf -o ~/Desktop  # Save output to a custom directory
```

### 4. Run the Developer Flask App

Start the developer server:
```bash
python start.py
```
Open `http://localhost:5000` in your browser. The app will detect the server backend and display both **Privacy Mode (Local)** and **Server Mode (Ghostscript/ImageMagick)**.

---

## 🐋 Run via Docker

You can spin up the full backend server container instantly:
```bash
docker build -t localpress .
docker run -p 5000:5000 localpress
```
Access the dashboard at `http://localhost:5000`.

---

## ⚙️ Under the Hood (How it Works)

### Image Compression
*   **Client-Side**: Images are loaded into an offscreen HTML5 `<canvas>`. We downscale extremely high-res images to save device memory and run a **binary search** on WebP/JPEG quality (tuning `canvas.toBlob()`) to hit the target size with the best visual clarity.
*   **Server-Side**: Uses **ImageMagick** with progressive encoding (`-interlace Plane`) and lossless metadata stripping (`-strip`), saving 10-100KB of metadata bloat with zero quality loss.

### PDF Compression
*   **Client-Side**: Uses Mozilla's `pdf.js` to render vector document pages onto high-DPI canvases at 130 DPI (ideal for screens). The rasterized canvases are converted to compressed JPEGs and compiled into a new PDF stream using `pdf-lib`.
*   **Server-Side**: Uses **Ghostscript** to execute advanced vector optimization, font subsetting, duplicate image detection, and DPI downsampling.

---

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.
