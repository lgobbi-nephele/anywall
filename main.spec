# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path
import platform
import re
import sys

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

a = Analysis(
    ['./dev/monitor.py'],
    pathex=[os.path.join(BASE_DIR, 'django/anywall'), os.path.join(BASE_DIR, 'dev')],
    binaries=[],
    datas=[
        # (os.path.join(BASE_DIR, 'django/anywall/anywall'), './anywall'),
        # (os.path.join(BASE_DIR, 'django/anywall/anywall_app'), './anywall_app'),
        (os.path.join(BASE_DIR, 'dev'), './dev'),
        (os.path.join(BASE_DIR, 'django/anywall/templates'), './templates'),
        (os.path.join(BASE_DIR, 'django/anywall/static'), './static'), # da generare con python .\django\anywall\manage.py collectstatic
        # (os.path.join(BASE_DIR, 'django/anywall/static'), './static'),
        # (os.path.join(site_packages_dir, 'rest_framework/templates/rest_framework'), './django/contrib/admin/templates/rest_framework'),
        # (os.path.join(site_packages_dir, 'rest_framework/static/rest_framework'), './django/contrib/admin/static/rest_framework')
    ],
    hiddenimports=['anywall', 
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
    'drf_yasg', 
    'drf_yasg.generators', 
    'numpy', 
    'drf_spectacular'
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
    'anywall_app.middleware.CustomHeadersMiddleware'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    distpath=output_dir,
    icon=icon_path
)
