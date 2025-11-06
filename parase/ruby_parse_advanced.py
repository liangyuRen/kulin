#!/usr/bin/env python3
"""
改进的Ruby项目依赖解析器

支持的Gemfile格式：
- gem "package"
- gem "package", "~> 1.0"
- gem "package", ">= 1.0", require: false
- gem "package", path: "..."（本地依赖）
- group :production do ... end（分组声明）
"""

import os
import re
from typing import List, Dict, Optional


def parse_gemfile(gemfile_path: str) -> List[Dict]:
    """
    解析Gemfile文件，支持多种gem声明格式

    支持的格式：
    - gem "name"
    - gem "name", "version"
    - gem "name", ">= 1.0", "< 2.0"
    - gem "name", ">= 1.0", require: false
    - gem "name", path: "..."
    """
    dependencies = []

    try:
        with open(gemfile_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 移除注释
        lines = []
        for line in content.split('\n'):
            # 移除行尾注释
            if '#' in line:
                line = line[:line.index('#')]
            lines.append(line)

        # 重新加入所有行
        content = '\n'.join(lines)

        # 查找所有gem声明（跨行支持）
        # 更灵活的正则表达式：匹配gem "name" 及其后的参数
        gem_pattern = r'gem\s+["\']([^"\']+)["\']([^,\n]*(?:,[^,\n]*)*)?(?=\n|$)'

        for match in re.finditer(gem_pattern, content):
            gem_name = match.group(1).strip()
            params = match.group(2).strip() if match.group(2) else ""

            # 跳过路径依赖和git依赖
            if 'path:' in params or 'git:' in params or 'github:' in params:
                print(f"[Ruby] 跳过非标准依赖: {gem_name} (本地/git依赖)")
                continue

            # 提取版本信息
            version = _extract_version_from_params(params)

            dep = {
                'name': gem_name,
                'version': version,
                'file_path': gemfile_path,
                'language': 'ruby',
                'package_manager': 'bundler'
            }
            dependencies.append(dep)

        return dependencies

    except Exception as e:
        print(f"[Ruby] 解析Gemfile失败 {gemfile_path}: {e}")
        return []


def parse_gemfile_lock(gemfile_lock_path: str) -> List[Dict]:
    """
    解析Gemfile.lock文件（生成的依赖锁定文件）

    Gemfile.lock格式：
    GEM
      remote: https://rubygems.org/
      specs:
        actioncable (7.0.0)
          actionpack (= 7.0.0)
          ...
    """
    dependencies = []

    try:
        with open(gemfile_lock_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        in_specs = False
        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # 检测GEM部分开始
            if line_stripped == 'specs:':
                in_specs = True
                continue

            # 检测其他部分的开始（停止解析）
            if line and not line[0].isspace() and in_specs:
                if line_stripped and line_stripped[0].isupper():
                    in_specs = False

            if in_specs:
                # 格式: gem_name (version)
                # 与依赖相同的缩进（通常是4-6个空格）
                match = re.match(r'^\s{4,6}([a-zA-Z0-9_\-\.]+)\s+\(([^)]+)\)', line)
                if match:
                    gem_name = match.group(1).strip()
                    version = match.group(2).strip()

                    # 版本可能包含依赖信息，如 "7.0.0.rc2"
                    # 我们只取主版本号
                    version = version.split()[0] if version else 'unknown'

                    dep = {
                        'name': gem_name,
                        'version': version,
                        'file_path': gemfile_lock_path,
                        'language': 'ruby',
                        'package_manager': 'bundler'
                    }
                    dependencies.append(dep)

        return dependencies

    except Exception as e:
        print(f"[Ruby] 解析Gemfile.lock失败 {gemfile_lock_path}: {e}")
        return []


def _extract_version_from_params(params: str) -> str:
    """
    从gem参数字符串中提取版本号

    参数格式示例：
    - "~> 1.0.0"
    - ">= 1.0.0", "< 2.0.0"
    - "1.0.0"
    - "", require: false
    """
    if not params:
        return 'unknown'

    # 移除require: false等选项
    params = re.sub(r',\s*(?:require|path|git|github|group):\s*[^\s,]+', '', params)
    params = params.strip()

    if not params:
        return 'unknown'

    # 移除引号
    params = params.strip('"\' ,')

    # 查找版本号（数字开头）
    match = re.search(r'[\d\.]+', params)
    if match:
        return match.group(0)

    return 'unknown'


def parse(project_path: str) -> List[Dict]:
    """
    解析Ruby项目的所有依赖

    优先级：
    1. Gemfile（开发定义）
    2. Gemfile.lock（锁定版本）
    """
    dependencies = []
    seen = set()

    print(f"[Ruby] 扫描项目: {project_path}")

    # 查找Gemfile和Gemfile.lock
    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in ['.git', '.bundle', 'vendor', '.gradle']]

        for file in files:
            file_path = os.path.join(root, file)

            if file == 'Gemfile':
                print(f"[Ruby] 找到: Gemfile")
                for dep in parse_gemfile(file_path):
                    key = f"{dep['name']}:{dep['version']}"
                    if key not in seen:
                        dependencies.append(dep)
                        seen.add(key)

            elif file == 'Gemfile.lock':
                print(f"[Ruby] 找到: Gemfile.lock")
                for dep in parse_gemfile_lock(file_path):
                    key = f"{dep['name']}:{dep['version']}"
                    if key not in seen:
                        dependencies.append(dep)
                        seen.add(key)

    print(f"[Ruby] 找到 {len(dependencies)} 个依赖")
    return dependencies


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python3 ruby_parse_advanced.py <project_path>")
        sys.exit(1)

    project_path = sys.argv[1]
    deps = parse(project_path)

    print(f"\n总计: {len(deps)} 个依赖")
    for i, dep in enumerate(deps[:20], 1):
        print(f"{i}. {dep['name']} ({dep['version']})")

    if len(deps) > 20:
        print(f"... 还有 {len(deps) - 20} 个")
