# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

icon_file  = 'condor.ico'  if os.path.exists('condor.ico')  else None
prompt_file = 'prompt.txt' if os.path.exists('prompt.txt') else None
minip_file  = 'minip.txt'  if os.path.exists('minip.txt')  else None

datas = []
if icon_file:   datas.append((icon_file,   '.'))
if prompt_file: datas.append((prompt_file, '.'))
if minip_file:  datas.append((minip_file,  '.'))

try:
    import tkinterdnd2
    datas.append((os.path.dirname(tkinterdnd2.__file__), 'tkinterdnd2'))
except ImportError:
    pass

a = Analysis(
    ['condor.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'pystray',
        'pystray._win32',
        'PIL',
        'PIL.Image',
        'tkinterdnd2',
        'core',
        'core.config',
        'core.process',
        'core.cmd',
        'core.files',
        'core.parser',
        'core.executor',
        'ui',
        'ui.app',
        'ui.toolbar',
        'ui.sidebar',
        'ui.statusbar',
        'ui.editor',
        'ui.scripts',
        'ui.styles',
    ],
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
    a.datas,
    [],
    name='KONDOR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)
