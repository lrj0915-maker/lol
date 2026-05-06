# -*- mode: python ; coding: utf-8 -*-
"""
LOL 战绩助手 — PyInstaller 打包配置
用法：pyinstaller build_config/lol-assistant.spec
输出：dist/LOL战绩助手/
"""

import os
import sys

# 项目根目录（spec 文件在 build_config/ 下，所以上一级就是项目根）
PROJECT_ROOT = os.path.abspath(os.path.join(SPECPATH, '..'))

block_cipher = None

a = Analysis(
    [os.path.join(PROJECT_ROOT, 'backend', 'main.py')],
    pathex=[
        os.path.join(PROJECT_ROOT, 'backend'),
    ],
    binaries=[],
    datas=[
        # 前端构建产物（只读资源）
        (os.path.join(PROJECT_ROOT, 'frontend', 'dist'), os.path.join('frontend', 'dist')),
        # 英雄列表数据（供内嵌 fetch 使用）
        (os.path.join(PROJECT_ROOT, 'frontend', 'src', 'data', 'champions.js'),
         os.path.join('frontend', 'src', 'data')),
    ],
    hiddenimports=[
        # pywebview 及其后端
        'webview',
        'webview.platforms.edgechromium',
        'clr',
        'clr_loader',
        'pythonnet',
        # pywebview 内置 HTTP 服务
        'bottle',
        # 标准库中 PyInstaller 可能遗漏的模块
        'json',
        'ssl',
        'ctypes',
        'ctypes.wintypes',
        'threading',
        'concurrent.futures',
        'multiprocessing',
        'sqlite3',
        'email.mime.text',
        # 第三方依赖
        'requests',
        'urllib3',
        'charset_normalizer',
        'certifi',
        'idna',
        'websocket',
        'jwt',
        'psutil',
        'uiautomation',
        # 项目内部模块
        'paths',
        'logger',
        'config',
        'bridge',
        'lcu',
        'lcu.connection',
        'lcu.api',
        'lcu.events',
        'services',
        'services.auto_accept',
        'services.auto_select',
        'services.match_history',
        'services.team_analyzer',
        'services.chat_sender',
        'services.ingame_chat',
        'services.runes_data_service',
        'services.augments_updater',
        'services.login_service',
        'services.account_manager',
        'services.jungle_monitor',
        'services.audio_manager',
        # Full-feature dependencies (jungle monitor/audio/region selection)
        'cv2',
        'numpy',
        'pytesseract',
        'mss',
        'pygame',
        'PIL',
        'PIL.Image',
        'PIL.ImageOps',
        'tkinter',
        '_tkinter',
        'storage',
        'storage.database',
        'storage.models',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除当前未使用的重型依赖
        'pynput',
        'pyautogui',
        'matplotlib',
        'scipy',
        'pandas',
        'notebook',
        'IPython',
        'pytest',
    ],
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
    name='LOL战绩助手',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(PROJECT_ROOT, 'icon.ico'),
    uac_admin=True,
    version=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='LOL战绩助手',
)
