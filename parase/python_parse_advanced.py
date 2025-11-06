#!/usr/bin/env python3
"""
改进的Python项目依赖解析器 - 支持多种格式

支持的格式：
- requirements.txt
- setup.py (setuptools)
- pyproject.toml (PEP 518)
- Pipfile / Pipfile.lock
- poetry.lock
"""

import os
import re
import json
import toml
from pathlib import Path
from typing import List, Dict, Optional


def parse_pyproject_toml(pyproject_path: str) -> List[Dict]:
    """
    解析pyproject.toml文件

    支持：
    - [project] dependencies
    - [project.optional-dependencies]
    - [tool.poetry] packages/dependencies（如果是Poetry格式）
    """
    dependencies = []

    try:
        with open(pyproject_path, 'r', encoding='utf-8') as f:
            data = toml.load(f)

        # 标准PEP 518格式：[project] dependencies
        if 'project' in data and 'dependencies' in data['project']:
            for dep_spec in data['project']['dependencies']:
                dep = _parse_dependency_spec(dep_spec)
                if dep:
                    dependencies.append(dep)

        # 可选依赖
        if 'project' in data and 'optional-dependencies' in data['project']:
            for group, deps in data['project']['optional-dependencies'].items():
                for dep_spec in deps:
                    dep = _parse_dependency_spec(dep_spec)
                    if dep:
                        dependencies.append(dep)

        # Poetry格式：[tool.poetry] dependencies
        if 'tool' in data and 'poetry' in data['tool'] and 'dependencies' in data['tool']['poetry']:
            for pkg_name, version_spec in data['tool']['poetry']['dependencies'].items():
                if pkg_name.lower() == 'python':  # 跳过Python版本规范
                    continue

                version = 'unknown'
                if isinstance(version_spec, str):
                    version = version_spec
                elif isinstance(version_spec, dict):
                    version = version_spec.get('version', 'unknown')

                dependencies.append({
                    'name': pkg_name,
                    'version': version,
                    'file_path': pyproject_path,
                    'language': 'python',
                    'package_manager': 'poetry'
                })

        return dependencies

    except Exception as e:
        print(f"[Python] 解析pyproject.toml失败 {pyproject_path}: {e}")
        return []


def parse_requirements_txt(req_path: str) -> List[Dict]:
    """解析requirements.txt和类似文件"""
    dependencies = []

    try:
        with open(req_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                dep = _parse_requirement_line(line)
                if dep:
                    dep['file_path'] = req_path
                    dep['language'] = 'python'
                    dep['package_manager'] = 'pip'
                    dependencies.append(dep)

        return dependencies

    except Exception as e:
        print(f"[Python] 解析requirements.txt失败 {req_path}: {e}")
        return []


def parse_setup_py(setup_path: str) -> List[Dict]:
    """解析setup.py文件"""
    dependencies = []

    try:
        with open(setup_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 查找install_requires列表
        match = re.search(r'install_requires\s*=\s*\[(.*?)\]', content, re.DOTALL)
        if match:
            deps_str = match.group(1)
            # 提取引号中的依赖
            for dep_spec in re.findall(r'["\']([^"\']+)["\']', deps_str):
                dep = _parse_dependency_spec(dep_spec)
                if dep:
                    dep['file_path'] = setup_path
                    dep['language'] = 'python'
                    dep['package_manager'] = 'pip'
                    dependencies.append(dep)

        return dependencies

    except Exception as e:
        print(f"[Python] 解析setup.py失败 {setup_path}: {e}")
        return []


def parse_pipfile(pipfile_path: str) -> List[Dict]:
    """解析Pipfile文件"""
    dependencies = []

    try:
        import pipfile  # 需要pipfile库
        pf = pipfile.load(open(pipfile_path))

        # 解析packages
        for name, spec in pf.get('packages', {}).items():
            version = 'unknown'
            if isinstance(spec, str):
                version = spec
            elif isinstance(spec, dict):
                version = spec.get('version', 'unknown')

            dependencies.append({
                'name': name,
                'version': version,
                'file_path': pipfile_path,
                'language': 'python',
                'package_manager': 'pipenv'
            })

        # 解析dev-packages
        for name, spec in pf.get('dev-packages', {}).items():
            version = 'unknown'
            if isinstance(spec, str):
                version = spec
            elif isinstance(spec, dict):
                version = spec.get('version', 'unknown')

            dependencies.append({
                'name': name,
                'version': version,
                'file_path': pipfile_path,
                'language': 'python',
                'package_manager': 'pipenv'
            })

        return dependencies

    except Exception as e:
        print(f"[Python] 解析Pipfile失败 {pipfile_path}: {e}")
        return []


def _parse_dependency_spec(spec: str) -> Optional[Dict]:
    """
    解析PEP 508格式的依赖规范

    支持：
    - package
    - package[extra]
    - package>=1.0
    - package==1.0,<2.0
    - package; python_version>="3.6"
    """
    spec = spec.strip()
    if not spec:
        return None

    # 移除环境标记（semicolon后面的部分）
    if ';' in spec:
        spec = spec.split(';')[0].strip()

    # 提取包名
    match = re.match(r'^([a-zA-Z0-9_\-\.]+)(?:\[.*?\])?(.*)$', spec)
    if not match:
        return None

    name = match.group(1)
    version_part = match.group(2).strip()

    # 提取版本号
    version = 'unknown'
    if version_part:
        # 查找第一个数字
        version_match = re.search(r'([\d\.]+)', version_part)
        if version_match:
            version = version_match.group(1)

    return {
        'name': name,
        'version': version
    }


def _parse_requirement_line(line: str) -> Optional[Dict]:
    """解析requirements.txt中的单行"""
    line = line.strip()
    if not line or line.startswith('#'):
        return None

    # 移除URL和git依赖
    if line.startswith('http') or line.startswith('git+'):
        return None

    # 移除-r和-e选项
    if line.startswith('-'):
        return None

    return _parse_dependency_spec(line)


def parse(project_path: str) -> List[Dict]:
    """
    解析Python项目的所有依赖

    支持优先级：
    1. requirements*.txt 文件
    2. setup.py
    3. pyproject.toml
    4. Pipfile / Pipfile.lock
    5. poetry.lock
    """
    dependencies = []
    seen = set()  # 避免重复

    print(f"[Python] 扫描项目: {project_path}")

    # 1. 查找所有requirements*.txt文件
    for root, dirs, files in os.walk(project_path):
        dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.venv', 'venv', 'env']]

        for file in files:
            file_path = os.path.join(root, file)

            # requirements.txt和变体
            if re.match(r'requirements[^/]*\.txt$', file):
                print(f"[Python] 找到: {file}")
                for dep in parse_requirements_txt(file_path):
                    key = f"{dep['name']}:{dep['version']}"
                    if key not in seen:
                        dependencies.append(dep)
                        seen.add(key)

            # setup.py
            elif file == 'setup.py':
                print(f"[Python] 找到: setup.py")
                for dep in parse_setup_py(file_path):
                    key = f"{dep['name']}:{dep['version']}"
                    if key not in seen:
                        dependencies.append(dep)
                        seen.add(key)

            # pyproject.toml
            elif file == 'pyproject.toml':
                print(f"[Python] 找到: pyproject.toml")
                for dep in parse_pyproject_toml(file_path):
                    key = f"{dep['name']}:{dep['version']}"
                    if key not in seen:
                        dependencies.append(dep)
                        seen.add(key)

            # Pipfile / Pipfile.lock
            elif file in ['Pipfile', 'Pipfile.lock']:
                print(f"[Python] 找到: {file}")
                for dep in parse_pipfile(file_path):
                    key = f"{dep['name']}:{dep['version']}"
                    if key not in seen:
                        dependencies.append(dep)
                        seen.add(key)

    print(f"[Python] 找到 {len(dependencies)} 个依赖")
    return dependencies


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: python3 python_parse_advanced.py <project_path>")
        sys.exit(1)

    project_path = sys.argv[1]
    deps = parse(project_path)

    print(f"\n总计: {len(deps)} 个依赖")
    for i, dep in enumerate(deps[:10], 1):
        print(f"{i}. {dep['name']} ({dep['version']})")

    if len(deps) > 10:
        print(f"... 还有 {len(deps) - 10} 个")
