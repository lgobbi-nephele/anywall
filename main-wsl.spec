# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path
import subprocess
import sys


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path.cwd()  # Usa la directory corrente come base


try:
    python_exe_path = subprocess.check_output(['which', 'python']).decode('utf-8').strip()
except Exception:
    python_exe_path = sys.executable

# Ottieni la versione di Python corrente
python_version = '.'.join(map(str, sys.version_info[:2]))

# Usa il percorso corretto dell'ambiente virtuale
env_path = Path(sys.prefix)
print(f"Percorso dell'ambiente virtuale: {env_path}")
site_packages_dir = env_path / f'lib64/python{python_version}' / 'site-packages'

a = Analysis(
    ['./dev/monitor.py'],
    pathex=[ os.path.join(BASE_DIR, 'django/anywall'), site_packages_dir],
    binaries=[],
    datas=[(os.path.join(BASE_DIR, 'django/anywall'), './python/anywall'), (os.path.join(site_packages_dir, 'rest_framework/templates/rest_framework'), './django/contrib/admin/templates/rest_framework'), (os.path.join(site_packages_dir, 'rest_framework/static/rest_framework'), './django/contrib/admin/static/rest_framework')],
    hiddenimports=['anywall', 'anywall.settings', 'anywall.urls', 'anywall.wsgi', 'anywall_app.urls', 'dotenv', 'rest_framework', 'rest_framework.authentication', 'rest_framework.permissions', 'rest_framework.parsers', 'rest_framework.negotiation', 'rest_framework.metadata', 'drf_yasg', 'drf_yasg.generators', 'numpy'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
 
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Anywall',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)