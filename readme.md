# LocalPress

Compress PDFs and images locally. No cloud. No uploads. Nothing leaves your machine.

Uses Ghostscript and ImageMagick under the hood.

---

## Docker

```bash
docker build -t localpress .
docker run -p 5000:5000 localpress
```

Open `http://localhost:5000` — drag files in, set a target size, download.

---

## CLI — `dvcom`

### 1. Install system dependencies

**macOS**
```bash
brew install ghostscript imagemagick
```

**Ubuntu / Debian**
```bash
sudo apt install ghostscript imagemagick
```

**Fedora / RHEL**
```bash
sudo dnf install ghostscript ImageMagick
```

**Arch**
```bash
sudo pacman -S ghostscript imagemagick
```

**Windows**

1. Download and install **Ghostscript** from [ghostscript.com](https://www.ghostscript.com/releases/gsdnld.html)
2. Download and install **ImageMagick** from [imagemagick.org](https://imagemagick.org/script/download.php#windows) — check **"Install legacy utilities (e.g. convert)"** during setup

### 2. Install dvcom

```bash
pip install -e .
```

### 3. Use it

```bash
dvcom report.pdf               # compress to −40% default
dvcom report.pdf -t 2MB        # hit a target size
dvcom photo.jpg -t 500KB       # works on images too
dvcom *.pdf -t 1MB             # batch compress
dvcom report.pdf -o ~/Desktop  # save to a specific folder
```

---

## Supported Files

`.pdf` `.jpg` `.jpeg` `.png` `.webp` `.bmp` `.tiff`
