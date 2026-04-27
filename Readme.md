# LocalPress

```
your files. your machine. your rules.
```

> **Because your internet is slow, your files are sensitive, and you refuse to upload your documents to some random cloud server you don't control.**

---

## The Problem

You have a 10MB PDF you need to send over email.

Your options:
- Upload it to some random online compressor *(and hope they're not logging your documents)*
- Pay for Adobe *(lol)*
- Suffer through a 45-minute upload on your slow connection just to compress it somewhere else, then download it back

**There is a better option.**

---

## What is LocalPress?

LocalPress is a **local-first file compressor** for PDFs and images.

It runs entirely on your machine. You open it in a browser, drop your files in, and it compresses them. No internet required after setup. No files leave your computer. No accounts. No cloud. No nonsense.

It is built for people who:

- Have **slow upload speeds** and can't afford to send large files to a cloud service
- Handle **sensitive documents** -- medical records, legal papers, private photos -- and refuse to let them touch someone else's server
- Are **nerdy enough** to run a local web app and appreciate how it works under the hood

Under the hood it uses **Ghostscript** and **ImageMagick** -- the same battle-tested Unix tools professionals have used for decades. LocalPress wraps them in a clean, drag-and-drop web UI so you don't have to touch the command line every time you need to shrink a file.

---

## How it works

```
You drop a file
      ↓
LocalPress tries to compress it 3 ways (smartest first):
      ↓
  [1] Strip redundant fonts & streams       ← fast, no quality loss
  [2] Repack compressed objects (qpdf)      ← medium effort
  [3] Binary search best DPI / quality      ← hits your target size
      ↓
Compressed file saved on your machine
      ↓
Download it. Done.
```

You can set a **target size** (e.g. `2MB`, `500KB`) or leave it blank for a sensible −40% default. LocalPress figures out the rest.

---

## Installation

Pick your OS below. The setup takes about 5 minutes.

---

### macOS

**Step 1 -- Install Homebrew** (skip if you already have it)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Step 2 -- Install dependencies**

```bash
brew install ghostscript imagemagick python
```

**Step 3 -- Run LocalPress**

```bash
cd localpress
pip3 install flask
python3 app.py
```

Your browser will open automatically at `http://localhost:5000`

> **Note:** macOS Gatekeeper may block `gs` or `convert` on first run. Go to **System Settings → Privacy & Security** and click Allow.

---

### Windows

**Step 1 -- Install Python**

Download from [python.org](https://python.org) and run the installer.
**Check the box: "Add Python to PATH"** before clicking Install.

**Step 2 -- Install Ghostscript**

Download the 64-bit installer from [ghostscript.com](https://www.ghostscript.com/releases/gsdnld.html) and run it.

**Step 3 -- Install ImageMagick**

Download from [imagemagick.org](https://imagemagick.org/script/download.php#windows).
During install, **check "Install legacy utilities (e.g. convert)"**.

**Step 4 -- Run LocalPress**

Open Command Prompt or PowerShell in the project folder:

```bash
pip install flask
python app.py
```

Your browser will open automatically at `http://localhost:5000`

> **Note:** Windows has a built-in tool also called `convert`. If ImageMagick's `convert` doesn't work, try using the full path: `C:\Program Files\ImageMagick-*\convert.exe`

---

### Linux (Ubuntu / Debian)

```bash
sudo apt install ghostscript imagemagick python3 python3-pip
cd localpress
pip3 install flask --break-system-packages
python3 app.py
```

Your browser will open automatically at `http://localhost:5000`

**Fedora / RHEL:**
```bash
sudo dnf install ghostscript ImageMagick python3 python3-pip
```

**Arch:**
```bash
sudo pacman -S ghostscript imagemagick python python-pip
```

---

### Recommended: Virtual Environment (all platforms)

Keeps Flask isolated from your system Python. Good practice.

```bash
# Create
python3 -m venv venv

# Activate (Mac / Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install and run
pip install flask
python app.py
```

---

## Verify everything installed correctly

```bash
gs --version        # expect: 9.x or 10.x
convert --version   # expect: ImageMagick 7.x.x
python3 --version   # expect: 3.8 or higher
```

LocalPress also checks for missing tools on startup and shows a warning banner in the UI if anything is missing.

---

## Supported file types

| Type | Extensions |
|------|-----------|
| Documents | `.pdf` |
| Images | `.jpg` `.jpeg` `.png` `.webp` `.bmp` `.tiff` |

---

## Privacy

- **Zero network requests.** Nothing is sent anywhere.
- Files are processed in `/tmp/localpress/` and stay on your machine.
- The app binds to `127.0.0.1` only -- it is not accessible from other devices on your network.
- Compressed files are saved wherever you tell it to save them.

---

## Requirements

| Dependency | Purpose |
|-----------|---------|
| Python 3.8+ | Runs the web server |
| Flask | Web framework |
| Ghostscript (`gs`) | PDF compression |
| ImageMagick (`convert`) | Image compression |
| qpdf *(optional)* | Extra PDF compression pass |

---

## License

Do whatever you want with it. It's yours.

---

```
built for slow connections, private files, and people who read READMEs.
```
