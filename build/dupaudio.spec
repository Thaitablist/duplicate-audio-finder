# PyInstaller spec — builds a native app bundle for the current OS.
# Usage:  pyinstaller build/dupaudio.spec
# Build on Windows to get the .exe, on macOS to get the .app.

import os
import sys
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# Resolve paths from the spec's own location so the build works regardless of
# the current working directory. SPECPATH is injected by PyInstaller.
ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
SRC = os.path.join(ROOT, "src")
ASSETS = os.path.join(SRC, "dupaudio", "assets")

hidden = collect_submodules("mutagen") + ["send2trash"]

# Bundle the assets folder (app icon PNG, .icns, .ico).
datas = [(ASSETS, "dupaudio/assets")]

# Platform-native icon for the executable/bundle, if it has been generated
# (run `python build/make_icons.py` first).
_icns = os.path.join(ASSETS, "icon.icns")
_ico = os.path.join(ASSETS, "icon.ico")
exe_icon = None
if sys.platform == "darwin" and os.path.exists(_icns):
    exe_icon = _icns
elif sys.platform.startswith("win") and os.path.exists(_ico):
    exe_icon = _ico

a = Analysis(
    [os.path.join(SRC, "dupaudio", "__main__.py")],
    pathex=[SRC],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DuplicateAudioFinder",
    console=False,  # GUI app — no terminal window
    icon=exe_icon,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="DuplicateAudioFinder",
)

# On macOS, wrap the collected bundle into a .app package.
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Duplicate Audio Finder.app",
        icon=exe_icon,
        bundle_identifier="com.djlabsiam.dupaudio",
    )
