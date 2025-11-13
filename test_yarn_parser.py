#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试优化后的yarn.lock解析器
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from parase.javascript_parse import parse_yarn_lock

# 测试yarn.lock文件
yarn_lock_path = r"D:\kuling\upload\144f2b8f-f4c8-4479-b714-428fa87c19d1\phpmyadmin-master\yarn.lock"

print("="*70)
print("测试优化后的yarn.lock解析器")
print("="*70)
print(f"文件: {yarn_lock_path}")
print()

# 解析
dependencies = parse_yarn_lock(yarn_lock_path)

print(f"[OK] 解析成功！")
print(f"[OK] 找到 {len(dependencies)} 个依赖")
print()

# 显示前20个
print("前20个依赖:")
for i, dep in enumerate(dependencies[:20], 1):
    print(f"  [{i:2d}] {dep}")

if len(dependencies) > 20:
    print(f"  ... 还有 {len(dependencies) - 20} 个依赖")

# 统计
scoped_count = sum(1 for dep in dependencies if dep.startswith('@'))
normal_count = len(dependencies) - scoped_count

print(f"\n统计:")
print(f"  Scoped packages (@scope/package): {scoped_count}")
print(f"  普通packages: {normal_count}")
print(f"  总计: {len(dependencies)}")
