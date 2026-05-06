"""测试野怪监控自动启动配置"""
import sys
import os

# 添加 backend 目录到路径
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

from config import config
from services.jungle_monitor import jungle_monitor

print("=" * 50)
print("野怪监控自动启动配置测试")
print("=" * 50)

# 检查配置
auto_start_config = config.get('jungle_monitor.auto_start', None)
print(f"配置文件中的 auto_start: {auto_start_config}")

# 检查实例
print(f"jungle_monitor.auto_start: {jungle_monitor.auto_start}")
print(f"jungle_monitor.is_running(): {jungle_monitor.is_running()}")

# 检查完整配置
jungle_config = config.get('jungle_monitor', {})
print(f"\n完整的 jungle_monitor 配置:")
for key, value in jungle_config.items():
    print(f"  {key}: {value}")

print("\n" + "=" * 50)
print("测试完成")
print("=" * 50)
