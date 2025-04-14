# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['entry_point.py'],
    pathex=[],
    binaries=[],
    datas=[('visual_transcripts.py', '.'), ('.streamlit', './.streamlit'), ('database', './database'), ('mock_data', './mock_data'), ('src', './src'), ('utils', './utils'), ('visual_transcription', './visual_transcription'), ('.cursor', './.cursor')],
    hiddenimports=[],
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
    [],
    exclude_binaries=True,
    name='VisualTranscriptsApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VisualTranscriptsApp',
)
