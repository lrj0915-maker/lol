# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# 收集 backend 目录下所有 Python 文件
backend_dir = os.path.join(os.getcwd(), 'backend')
backend_files = []
for root, dirs, files in os.walk(backend_dir):
    # 跳过 __pycache__
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for f in files:
        if f.endswith('.py'):
            src = os.path.join(root, f)
            # 计算相对路径
            rel_path = os.path.relpath(root, os.getcwd())
            backend_files.append((src, rel_path))

a = Analysis(
    ['backend/main.py'],
    pathex=['backend'],
    binaries=[],
    datas=[
        ('frontend/dist', 'frontend/dist'),
        ('backend', 'backend'),
    ],
    hiddenimports=[
        'bridge',
        'config',
        'lcu',
        'lcu.api',
        'lcu.connection',
        'lcu.events',
        'services',
        'services.auto_accept',
        'services.auto_select',
        'services.match_history',
        'services.team_analyzer',
        'services.chat_sender',
        'services.ingame_chat',
        'storage',
        'storage.database',
        'storage.models',
        'webview',
        'clr_loader',
        'pythonnet',
        'pyautogui',
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
    a.zipfiles,
    a.datas,
    [],
    name='LOL战绩助手',
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
)
