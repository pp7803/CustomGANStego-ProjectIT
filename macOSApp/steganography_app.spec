# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for CustomGANStego macOS App
This builds a standalone macOS application bundle.
"""

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, copy_metadata

# Get paths
spec_dir = Path(SPECPATH)
project_dir = spec_dir.parent

# Check if model directory exists and collect .dat files
model_dir = project_dir / 'results' / 'model'
model_datas = []
if model_dir.exists():
    # Include all .dat model files
    for dat_file in model_dir.glob('*.dat'):
        model_datas.append((str(dat_file), 'results/model'))
    print(f"Found {len(model_datas)} model files to include in bundle")
else:
    print("Warning: No model directory found at results/model/")

# Collect metadata for packages that need it
metadata_datas = []
metadata_datas += copy_metadata('imageio')
metadata_datas += copy_metadata('Pillow')
metadata_datas += copy_metadata('numpy')
metadata_datas += copy_metadata('torch')

# Collect data files
imageio_datas = collect_data_files('imageio')

# Block cipher (optional encryption)
block_cipher = None

# Analysis - collect all scripts and dependencies
a = Analysis(
    ['steganography_app.py'],
    pathex=[
        str(spec_dir),
        str(project_dir),  # Parent directory for imports
    ],
    binaries=[],
    datas=model_datas + metadata_datas + imageio_datas + [
        # Add other data files here if needed
    ],
    hiddenimports=[
        'PIL._tkinter_finder',
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'torch',
        'torchvision',
        'numpy',
        'imageio',
        'imageio.core',
        'imageio.plugins',
        'Crypto',
        'Crypto.PublicKey',
        'Crypto.PublicKey.RSA',
        'Crypto.Cipher',
        'Crypto.Cipher.AES',
        'Crypto.Cipher.PKCS1_OAEP',
        'Crypto.Random',
        'Crypto.Util.Padding',
        'reedsolo',
        'zlib',
        'skimage',
        'skimage.metrics',
        'skimage._shared',
        'skimage._shared.utils',
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.backends',
        'matplotlib.backends.backend_agg',
        'psutil',
        'encoder',
        'decoder',
        'reverse_decoder',
        'critic',
        'enhancedstegan',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib.tests',
        'numpy.tests',
        'PIL.tests',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# PYZ - Python zip archive
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# EXE - Executable
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CustomGANStego',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# COLLECT - Collect all files
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CustomGANStego',
)

# BUNDLE - Create macOS app bundle
app = BUNDLE(
    coll,
    name='CustomGANStego.app',
    icon=None,  # Add icon file path here if you have one
    bundle_identifier='com.customganstego.app',
    info_plist={
        'CFBundleName': 'CustomGANStego',
        'CFBundleDisplayName': 'CustomGANStego',
        'CFBundleGetInfoString': 'GAN-based Steganography Application',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': 'True',
        'NSRequiresAquaSystemAppearance': 'False',
    },
)
