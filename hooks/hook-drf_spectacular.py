# Create this file as: hooks/hook-drf_spectacular.py

from PyInstaller.utils.hooks import collect_all, collect_submodules

# Collect all drf_spectacular modules
datas, binaries, hiddenimports = collect_all('drf_spectacular')

# Additional hidden imports that might be missed
hiddenimports += [
    'drf_spectacular.openapi',
    'drf_spectacular.utils',
    'drf_spectacular.views',
    'drf_spectacular.contrib',
    'drf_spectacular.authentication',
    'drf_spectacular.extensions',
    'drf_spectacular.generators',
    'drf_spectacular.inspectors',
    'drf_spectacular.plumbing',
    'drf_spectacular.serializers',
    'drf_spectacular.settings',
    'drf_spectacular.types',
]

# Collect contrib modules
contrib_modules = collect_submodules('drf_spectacular.contrib')
hiddenimports += contrib_modules