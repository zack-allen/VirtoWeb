# VirtoWeb Desktop Builder (prototype)

This is a lightweight prototype desktop application that lets you visually compose pages by dragging components onto a page canvas and export a VirtoWeb-compatible JSON schema.

Technology
- PyQt6 (Qt6) — cross-platform GUI toolkit. Can be packaged to executables with PyInstaller.

Quick start (Windows PowerShell):

```powershell
# from repo root
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r builders/desktop_builder/requirements.txt
python builders/desktop_builder/main.py
```

Packaging (one example using PyInstaller):

```powershell
pip install pyinstaller
pyinstaller --onefile builders/desktop_builder/main.py --name virtoweb-builder
```

Notes & next steps
- This is a prototype. Next improvements I'd implement:
  - multi-region page editing (not just a single "main" region)
  - richer property editors (forms for common props instead of raw JSON)
  - undo/redo and copy/paste
  - project templates and built-in component palette management
