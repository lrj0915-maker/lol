# -*- mode: python ; coding: utf-8 -*-
"""
兼容入口：保留 build.spec，实际委托到 build_config/lol-assistant.spec。
推荐命令：pyinstaller build_config/lol-assistant.spec
"""

from pathlib import Path

delegate_spec = Path(SPECPATH) / 'build_config' / 'lol-assistant.spec'
if not delegate_spec.exists():
    raise SystemExit('未找到 build_config/lol-assistant.spec，请检查仓库文件是否完整。')

print('[build.spec] 已切换到 build_config/lol-assistant.spec')

# 委托执行时，使用目标 spec 的目录作为 SPECPATH，避免相对路径解析错误。
SPECPATH = str(delegate_spec.parent)
__file__ = str(delegate_spec)
exec(compile(delegate_spec.read_text(encoding='utf-8'), str(delegate_spec), 'exec'), globals(), globals())
