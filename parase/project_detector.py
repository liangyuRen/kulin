#!/usr/bin/env python3
"""
项目语言自动检测模块

功能：
1. 扫描项目目录，检测存在的特征文件
2. 自动识别项目使用的编程语言和包管理器
3. 支持多语言项目（一个项目可能有多种语言）
4. 返回检测到的所有语言及其对应的文件路径
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple, Set


class ProjectDetector:
    """项目语言自动检测器"""

    # 定义各语言的特征文件映射
    LANGUAGE_SIGNATURES = {
        'java': {
            'files': ['pom.xml', 'build.gradle', 'build.gradle.kts'],
            'priority': 1,
            'package_manager': 'maven'  # 默认使用maven
        },
        'go': {
            'files': ['go.mod', 'go.sum'],
            'priority': 1,
            'package_manager': 'go'
        },
        'rust': {
            'files': ['Cargo.toml', 'Cargo.lock'],
            'priority': 1,
            'package_manager': 'cargo'
        },
        'python': {
            'files': ['requirements.txt', 'setup.py', 'setup.cfg', 'pyproject.toml', 'Pipfile', 'poetry.lock'],
            'priority': 1,
            'package_manager': 'pip'
        },
        'javascript': {
            'files': ['package.json', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml'],
            'priority': 2,
            'package_manager': 'npm'
        },
        'ruby': {
            'files': ['Gemfile', 'Gemfile.lock'],
            'priority': 1,
            'package_manager': 'bundler'
        },
        'php': {
            'files': ['composer.json', 'composer.lock'],
            'priority': 1,
            'package_manager': 'composer'
        },
        'csharp': {
            'files': ['.csproj', '.sln', 'packages.config'],
            'priority': 1,
            'package_manager': 'nuget'
        },
        'c': {
            'files': ['CMakeLists.txt', 'Makefile', 'conanfile.txt', 'conanfile.py'],
            'priority': 3,
            'package_manager': 'conan'
        },
        'cpp': {
            'files': ['CMakeLists.txt', 'vcpkg.json'],
            'priority': 3,
            'package_manager': 'vcpkg'
        },
        'erlang': {
            'files': ['rebar.config', 'rebar.lock'],
            'priority': 1,
            'package_manager': 'rebar3'
        }
    }

    # 需要跳过的目录
    SKIP_DIRS = {
        '.git', '.svn', '__pycache__', '.pytest_cache',
        'node_modules', '.idea', '.vscode', 'venv',
        'env', '.env', 'dist', 'build', 'target',
        'vendor', '.gradle', '.m2'
    }

    def __init__(self, project_path: str):
        """
        初始化项目检测器

        Args:
            project_path: 项目根目录路径
        """
        self.project_path = Path(project_path)
        self.detected_languages = {}  # {language: {files: [...], package_manager: ...}}

    def detect(self) -> Dict[str, Dict]:
        """
        检测项目中存在的所有语言

        Returns:
            检测结果字典，格式为：
            {
                'java': {
                    'files': ['/path/to/pom.xml'],
                    'package_manager': 'maven',
                    'priority': 1
                },
                'python': {
                    'files': ['/path/to/requirements.txt', '/path/to/setup.py'],
                    'package_manager': 'pip',
                    'priority': 1
                }
            }
        """
        if not self.project_path.exists():
            raise ValueError(f"Project path does not exist: {self.project_path}")

        # 扫描项目目录
        self._scan_project()

        return self.detected_languages

    def _scan_project(self):
        """递归扫描项目目录，查找特征文件"""
        for root, dirs, files in os.walk(self.project_path):
            # 过滤掉不需要的目录
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]

            # 检查当前目录的文件
            for language, config in self.LANGUAGE_SIGNATURES.items():
                for feature_file in config['files']:
                    if feature_file in files:
                        file_path = os.path.join(root, feature_file)

                        if language not in self.detected_languages:
                            self.detected_languages[language] = {
                                'files': [],
                                'package_manager': config['package_manager'],
                                'priority': config['priority']
                            }

                        if file_path not in self.detected_languages[language]['files']:
                            self.detected_languages[language]['files'].append(file_path)

    def get_detected_languages(self) -> List[str]:
        """获取检测到的所有语言列表"""
        return list(self.detected_languages.keys())

    def get_primary_language(self) -> str:
        """获取主要语言（按优先级排序）"""
        if not self.detected_languages:
            return None

        # 按优先级排序
        sorted_langs = sorted(
            self.detected_languages.items(),
            key=lambda x: x[1]['priority']
        )
        return sorted_langs[0][0]

    def get_languages_by_priority(self) -> List[str]:
        """获取按优先级排序的语言列表"""
        sorted_langs = sorted(
            self.detected_languages.items(),
            key=lambda x: x[1]['priority']
        )
        return [lang for lang, _ in sorted_langs]

    def get_package_manager(self, language: str) -> str:
        """获取指定语言的包管理器"""
        if language in self.detected_languages:
            return self.detected_languages[language]['package_manager']
        return 'unknown'

    def get_feature_files(self, language: str) -> List[str]:
        """获取指定语言的特征文件列表"""
        if language in self.detected_languages:
            return self.detected_languages[language]['files']
        return []

    def get_summary(self) -> str:
        """获取检测结果的人类可读摘要"""
        if not self.detected_languages:
            return "未检测到已知的项目类型"

        lines = ["检测到以下项目类型:"]
        for lang in self.get_languages_by_priority():
            files = self.detected_languages[lang]['files']
            lines.append(f"  ✓ {lang}: {len(files)} 个特征文件")
            for f in files[:3]:  # 只显示前3个文件
                lines.append(f"    - {os.path.basename(f)}")
            if len(files) > 3:
                lines.append(f"    ... 还有 {len(files) - 3} 个文件")

        return "\n".join(lines)


# 测试代码
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python3 project_detector.py <project_path>")
        sys.exit(1)

    project_path = sys.argv[1]
    detector = ProjectDetector(project_path)

    print("=" * 60)
    print("项目语言检测器")
    print("=" * 60)

    result = detector.detect()
    print("\n检测结果:")
    print(detector.get_summary())

    print("\n\n详细信息:")
    print(f"检测到的语言: {detector.get_detected_languages()}")
    print(f"主要语言: {detector.get_primary_language()}")
    print(f"按优先级排序: {detector.get_languages_by_priority()}")

    print("\n\n完整检测结果 (JSON):")
    import json
    for lang, info in result.items():
        print(f"\n{lang}:")
        print(f"  package_manager: {info['package_manager']}")
        print(f"  priority: {info['priority']}")
        print(f"  files:")
        for f in info['files']:
            print(f"    - {f}")
