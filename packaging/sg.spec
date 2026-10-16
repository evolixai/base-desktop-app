# PyInstaller spec for the Sg desktop app (macOS + Windows).
#
# Usage:
#   uv run pyinstaller packaging/sg.spec --noconfirm
#
# On macOS this produces dist/Sg.app; on Windows dist/Sg/Sg.exe.

import sys
from pathlib import Path

ROOT = Path(SPECPATH).parent  # noqa: F821

block_cipher = None

datas = []
if (ROOT / "resources").exists():
    datas.append((str(ROOT / "resources"), "resources"))

hiddenimports = [
    "PySide6.QtSvg",
    "PySide6.QtNetwork",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineQuick",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuickWidgets",
]

excludes = [
    "tkinter",
]

a = Analysis(  # noqa: F821
    [str(ROOT / "src" / "sg" / "__main__.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=excludes,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)  # noqa: F821

win_icon = ROOT / "resources" / "icon.ico"

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Sg",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    icon=str(win_icon) if win_icon.exists() else None,
)

coll = COLLECT(  # noqa: F821
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Sg",
)

if sys.platform == "darwin":
    app = BUNDLE(  # noqa: F821
        coll,
        name="Sg.app",
        icon=str(ROOT / "resources" / "icon.icns")
        if (ROOT / "resources" / "icon.icns").exists()
        else None,
        bundle_identifier="com.example.sg",
        info_plist={
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "11.0",
            "NSRequiresAquaSystemAppearance": False,
        },
    )
