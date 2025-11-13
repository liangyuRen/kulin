#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试优化版检测器
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


def test_optimized_detector():
    """测试优化的检测器"""
    from parase.optimized_project_detector import OptimizedProjectDetector

    upload_dir = "D:\\kuling\\upload"

    print("\n" + "="*80)
    print("优化检测器测试")
    print("="*80 + "\n")

    if not os.path.exists(upload_dir):
        print(f"错误: 文件夹不存在: {upload_dir}")
        return

    # 获取所有项目
    projects = [d for d in os.listdir(upload_dir) if os.path.isdir(os.path.join(upload_dir, d))][:10]

    print(f"测试项目数: {len(projects)}\n")

    for i, proj in enumerate(projects, 1):
        proj_path = os.path.join(upload_dir, proj)

        try:
            # 测试优化检测器
            detector = OptimizedProjectDetector(proj_path)
            detector.detect()

            primary = detector.get_primary_language() or "other"
            summary = detector.get_detailed_summary()

            # 显示前3种语言
            top_langs = summary['languages'][:3] if summary['languages'] else []
            lang_str = ", ".join(f"{l[0]}({l[1]:.0f})" for l in top_langs)

            print(f"[{i:2d}] {proj:40s} | 主要: {primary:12s} | 候选: {lang_str}")

        except Exception as e:
            print(f"[{i:2d}] {proj:40s} | 错误: {str(e)[:40]}")

    print("\n" + "="*80)
    print("测试完成")
    print("="*80 + "\n")


if __name__ == "__main__":
    test_optimized_detector()
