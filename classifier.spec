# -*- mode: python ; coding: utf-8 -*-

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect rich library data files
rich_datas = collect_data_files('rich')

# Additional hidden imports for classifier
hiddenimports = [
    'pygame',
    'pygame.mixer',
    'rich.console',
    'rich.table',
    'rich.panel',
    'rich.text',
    'rich.markdown',
    'sqlite3',
]

a = Analysis(
    ['src/classifier/main.py'],
    pathex=[],
    binaries=[],
    datas=rich_datas + [
        ('src', 'src'),
    ],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='classifier',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
