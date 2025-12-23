# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['CRT_Mixer.py'],
    pathex=[],
    binaries=[],
    datas=[('logo.svg', '.'), ('HelveticaNeue.ttc', '.')],
    hiddenimports=[
        'PIL._tkinter_finder',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.QtSvg',
        'numpy',
        'scipy',
        'scipy.ndimage',
        'scipy.signal',
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
    [],
    exclude_binaries=True,
    name='CRT_Mixer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Hide console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CRT_Mixer',
)

app = BUNDLE(
    coll,
    name='CRT Mixer.app',
    icon='icon.icns',
    bundle_identifier='com.lune.crtmixer',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'CFBundleDocumentTypes': [
            {
                'CFBundleTypeName': 'Image',
                'CFBundleTypeRole': 'Viewer',
                'LSItemContentTypes': ['public.image'],
                'LSHandlerRank': 'Alternate',
            }
        ],
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.13.0',
    },
)
