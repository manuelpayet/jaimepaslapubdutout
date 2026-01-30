# -*- mode: python ; coding: utf-8 -*-

import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all whisper data files and submodules
whisper_datas = collect_data_files('whisper')
whisper_hiddenimports = collect_submodules('whisper')

# Additional hidden imports
hiddenimports = whisper_hiddenimports + [
    'sklearn.utils._cython_blas',
    'sklearn.neighbors.typedefs',
    'sklearn.neighbors.quad_tree',
    'sklearn.tree._utils',
    'numpy.core._dtype_ctypes',
    'tiktoken_ext.openai_public',
    'tiktoken_ext',
]

a = Analysis(
    ['src/radio_listener/main.py'],
    pathex=[],
    binaries=[],
    datas=whisper_datas + [
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
    name='radio-listener',
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
