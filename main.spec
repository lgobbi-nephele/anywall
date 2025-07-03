# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path
import platform
import re
import sys
import drf_yasg

def remove_last_decimal(s):
    last_dot_index = s.rfind('.')
    if last_dot_index == -1:
        return s
    return s[:last_dot_index]

current_dir = os.getcwd()
BASE_DIR = Path(current_dir)

python_exe_path = sys.executable
print(f"python_exe_path: {python_exe_path}")

path_obj = Path(python_exe_path)
env_path = str(path_obj.parent.parent)
print(f"env_path: {env_path}")
python_version = platform.python_version()
python_version = re.sub(r'\.\d+$', '', python_version)

drf_yasg_path = os.path.dirname(drf_yasg.__file__)

a = Analysis(
    ['./dev/monitor.py'],
    pathex=[os.path.join(BASE_DIR, 'django/anywall'), os.path.join(BASE_DIR, 'django/anywall/anywall_app'), os.path.join(BASE_DIR, 'dev')],
    binaries=[],
    datas=[
        (os.path.join(BASE_DIR, 'dev'), './dev'),
        (os.path.join(BASE_DIR, 'django/anywall/templates'), 'templates'),
        (os.path.join(BASE_DIR, 'django/anywall/static'), 'static'),
        (drf_yasg_path, 'drf_yasg'),
    ],
    hiddenimports=[
        'anywall', 
        'anywall.settings', 
        'anywall.urls', 
        'anywall.wsgi', 
        'anywall_app.urls', 
        'anywall_app.middleware',
        'dotenv', 
        'dev',
        'rest_framework', 
        'rest_framework.authentication', 
        'rest_framework.permissions', 
        'rest_framework.parsers', 
        'rest_framework.negotiation', 
        'rest_framework.metadata',
        'rest_framework.schemas',
        'rest_framework.schemas.coreapi',
        'drf_yasg', 
        'drf_yasg.generators', 
        'numpy', 
        'whitenoise', 
        'whitenoise.middleware', 
        'whitenoise.runserver_nostatic', 
        'whitenoise.storage', 
        'mnemonic', 
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'whitenoise.middleware.WhiteNoiseMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
        'anywall_app.middleware.CustomHeadersMiddleware'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Explicitly exclude drf_spectacular to avoid import issues
    excludes=[
        'drf_spectacular',
        'drf_spectacular.openapi',
        'drf_spectacular.utils',
        'drf_spectacular.views',
        'drf_spectacular.contrib',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# Ensure the output directory exists
output_dir = os.path.join(BASE_DIR, 'out/anywall/lib')
icon_path = os.path.join(BASE_DIR, 'out/anywall/resources/anywall.ico')
os.makedirs(output_dir, exist_ok=True)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='anywall',
    debug=True,  # Enable debug mode
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    distpath=output_dir,
    icon=icon_path
)