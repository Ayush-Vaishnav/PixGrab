# 📸 PixGrab for macOS

PixGrab is a lightweight macOS utility that eliminates the need to repeatedly trigger `Command + Shift + 4` by enabling continuous, precision-based area screenshots in a single workflow.

---

## ✨ Features

* **Continuous Capture:** Take multiple area screenshots in one uninterrupted flow
* **Precision Overlay:** Custom crosshair with screen dimming for accurate selection
* **Instant Save:** Each screenshot is automatically saved to the desktop
* **Simple Exit:** Press `Escape` anytime to stop capturing
* **Native macOS App:** Packaged as a standalone `.app` (no Python required for users)
* **Efficient & Minimal:** Designed for performance and simplicity using native macOS capabilities

---

## 🎯 Why PixGrab?

On macOS, capturing specific screen areas requires pressing `Command + Shift + 4` repeatedly.

While simple, this becomes inefficient for tasks like extracting multiple questions from documents or working with repeated selections.

PixGrab removes this friction by allowing a continuous screenshot workflow without restarting the tool each time.

---

## 🚀 How to Install & Run

Since PixGrab is an open-source, unsigned utility, macOS requires a few one-time steps to trust the application.

### 1. Download

* Go to the **Releases** section of this repository
* Download `PixGrab.zip` and extract it
* Drag `PixGrab.app` into your **Applications** folder

---

### 2. First-Time Setup (Permissions)

macOS requires manual permission for screen capture and input monitoring:

1. Open **System Settings** → **Privacy & Security**
2. Go to **Screen Recording** → Enable PixGrab
3. Go to **Input Monitoring** → Enable PixGrab
4. If already running, force quit (`Cmd + Option + Esc`) and restart

---

## 💻 Technical Details

For developers who want to explore or modify the project:

* **Language:** Python 3.13+
* **Main Logic:** `main.py`
* **Framework:** Tkinter + native macOS APIs

---

## ⚙️ Build Instructions

To build the `.app` locally:

```bash
pyinstaller --windowed --icon=icon.icns --name="PixGrab" main.py
```

---

## 📌 Note

PixGrab is currently in its initial version. Feedback, suggestions, and improvements are welcome.

---

## 👤 Author

Ayush Vaishnav
