# -*- mode: python ; coding: utf-8 -*-

import os
from django.core.wsgi import get_wsgi_application
from django.conf import settings

settings.configure()

# Path to the parent directory of your Django application
django_app_path = os.path.join(os.getcwd(), '')

# Path to your Django settings file
django_settings = 'HagBot.settings'

# Additional data files and directories that PyInstaller should include
additional_files = [
    (os.path.join(django_app_path, 'app', 'templates'), 'app/templates'),
    (os.path.join(django_app_path, 'middleware'), 'middleware'),
    (os.path.join(django_app_path, 'HagBot'), 'HagBot'),
    (os.path.join(django_app_path, 'backend'), 'backend'),
]

# Specify the executable file name
exe_name = 'HagBot'

# Tell PyInstaller to use the WSGI application to start the Django app
wsgi_app = get_wsgi_application()

# PyInstaller configuration options
a = Analysis(['manage.py'],
             pathex=[django_app_path],
             binaries=[],
             datas=additional_files,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=None,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=None)

exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name=exe_name,
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          upx_debug_info=False,
          upx_compress_icons=True,
          upx_compress_overrides=None)

app = BUNDLE(exe,
             name=exe_name,
             icon=None,
             bundle_identifier=None,
             info_plist={},
             dylibs=[],
             frameworks=[],
             resources=[])

# Define the WSGI entry point for PyInstaller
def get_wsgi_entry_point():
    return wsgi_app
