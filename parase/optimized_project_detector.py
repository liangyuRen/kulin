#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优化版项目语言检测器 - 提升准确率
加强了源代码检测、项目结构分析、配置文件识别
"""

import os
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import Counter
import re


class OptimizedProjectDetector:
    """优化的项目语言检测器 - 更高准确率"""

    # 扩展的语言特征文件映射
    LANGUAGE_SIGNATURES = {
        'java': {
            'files': ['pom.xml', 'build.gradle', 'build.gradle.kts', 'gradle.properties'],
            'source_files': {'.java'},
            'dir_patterns': ['src/main/java', 'src/test/java', 'target/classes'],
            'priority': 1,
            'package_manager': 'maven'
        },
        'python': {
            'files': ['requirements.txt', 'setup.py', 'setup.cfg', 'pyproject.toml',
                     'Pipfile', 'poetry.lock', 'tox.ini', '.python-version'],
            'source_files': {'.py'},
            'dir_patterns': ['venv', 'env', '__pycache__', '.eggs', 'site-packages'],
            'priority': 1,
            'package_manager': 'pip'
        },
        'go': {
            'files': ['go.mod', 'go.sum', 'Gopkg.toml', 'go.yml', '.go-version'],
            'source_files': {'.go'},
            'dir_patterns': ['vendor', 'go.sum'],
            'priority': 1,
            'package_manager': 'go'
        },
        'javascript': {
            'files': ['package.json', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
                     '.npmrc', '.yarnrc', 'tsconfig.json', 'jest.config.js'],
            'source_files': {'.js', '.jsx', '.ts', '.tsx', '.mjs'},
            'dir_patterns': ['node_modules', '.next', 'dist', 'build'],
            'priority': 2,
            'package_manager': 'npm'
        },
        'typescript': {
            'files': ['tsconfig.json', 'tsconfig.app.json', 'tsconfig.spec.json'],
            'source_files': {'.ts', '.tsx'},
            'dir_patterns': ['dist', '.next'],
            'priority': 2,
            'package_manager': 'npm'
        },
        'php': {
            'files': ['composer.json', 'composer.lock', 'phpunit.xml', '.php-version',
                     'php.ini', 'wp-config.php'],
            'source_files': {'.php'},
            'dir_patterns': ['vendor', 'node_modules', 'wp-content'],
            'priority': 1,
            'package_manager': 'composer'
        },
        'ruby': {
            'files': ['Gemfile', 'Gemfile.lock', '.ruby-version', 'config.ru'],
            'source_files': {'.rb', '.rake'},
            'dir_patterns': ['vendor', 'bundle'],
            'priority': 1,
            'package_manager': 'bundler'
        },
        'rust': {
            'files': ['Cargo.toml', 'Cargo.lock', 'rustfmt.toml'],
            'source_files': {'.rs'},
            'dir_patterns': ['target', 'src/bin'],
            'priority': 1,
            'package_manager': 'cargo'
        },
        'csharp': {
            'files': ['.csproj', '.sln', 'packages.config', 'app.config', 'web.config',
                     '.csharpierrc', 'stylecop.json'],
            'source_files': {'.cs'},
            'dir_patterns': ['bin', 'obj', 'packages'],
            'priority': 1,
            'package_manager': 'nuget'
        },
        'kotlin': {
            'files': ['build.gradle.kts', 'gradle.properties'],
            'source_files': {'.kt', '.kts'},
            'dir_patterns': ['src/main/kotlin', 'src/test/kotlin'],
            'priority': 2,
            'package_manager': 'gradle'
        },
        'swift': {
            'files': ['Package.swift', 'Podfile', 'Cartfile'],
            'source_files': {'.swift'},
            'dir_patterns': ['Pods', '.build', 'Carthage'],
            'priority': 1,
            'package_manager': 'swift'
        },
        'c': {
            'files': ['CMakeLists.txt', 'Makefile', 'conanfile.txt', 'makefile'],
            'source_files': {'.c', '.h'},
            'dir_patterns': ['build', 'dist'],
            'priority': 3,
            'package_manager': 'conan'
        },
        'cpp': {
            'files': ['CMakeLists.txt', 'vcpkg.json', 'conanfile.txt'],
            'source_files': {'.cpp', '.cc', '.cxx', '.h', '.hpp', '.hxx'},
            'dir_patterns': ['build', 'dist'],
            'priority': 2,
            'package_manager': 'vcpkg'
        },
        'erlang': {
            'files': ['rebar.config', 'rebar.lock', 'rebar3.config'],
            'source_files': {'.erl'},
            'dir_patterns': ['_build', 'ebin'],
            'priority': 1,
            'package_manager': 'rebar3'
        },
        'scala': {
            'files': ['build.sbt', 'project/build.properties'],
            'source_files': {'.scala'},
            'dir_patterns': ['target', 'project'],
            'priority': 2,
            'package_manager': 'sbt'
        },
        'groovy': {
            'files': ['build.gradle', 'gradle.properties'],
            'source_files': {'.groovy', '.gradle'},
            'dir_patterns': ['build', 'gradle'],
            'priority': 2,
            'package_manager': 'gradle'
        },
        'android': {
            'files': ['AndroidManifest.xml', 'build.gradle', 'local.properties'],
            'source_files': {'.java', '.kt'},
            'dir_patterns': ['src/main/res', 'src/androidTest'],
            'priority': 1,
            'package_manager': 'gradle'
        },
    }

    # 需要跳过的目录
    SKIP_DIRS = {
        '.git', '.svn', '__pycache__', '.pytest_cache',
        'node_modules', '.idea', '.vscode', 'venv',
        'env', '.env', 'dist', 'build', 'target',
        'vendor', '.gradle', '.m2', '.tox',
        'eggs', '.eggs', '*.egg-info', 'bower_components',
        '.angular', 'coverage', '.next', '.nuxt', 'Pods',
        'Carthage', '.bundle'
    }

    def __init__(self, project_path: str):
        """初始化优化的项目检测器"""
        self.project_path = Path(project_path)
        self.detected_languages = {}
        self.source_files_count = Counter()
        self.config_files_count = Counter()
        self.dir_patterns_count = Counter()
        self.source_file_depths = {}  # 源代码文件的目录深度

    def detect(self) -> Dict[str, Dict]:
        """检测项目中的所有语言"""
        if not self.project_path.exists():
            raise ValueError(f"Project path does not exist: {self.project_path}")

        # 阶段1: 扫描特征文件
        self._scan_feature_files()

        # 阶段2: 扫描源代码文件
        self._scan_source_files()

        # 阶段3: 扫描目录结构
        self._scan_directory_patterns()

        # 阶段4: 综合判断
        self._aggregate_results()

        return self.detected_languages

    def _scan_feature_files(self):
        """扫描特征文件 (高优先级)"""
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]

            for language, config in self.LANGUAGE_SIGNATURES.items():
                for feature_file in config['files']:
                    if feature_file in files:
                        file_path = os.path.join(root, feature_file)

                        if language not in self.detected_languages:
                            self.detected_languages[language] = {
                                'files': [],
                                'package_manager': config['package_manager'],
                                'priority': config['priority'],
                                'confidence': 'high',
                                'feature_files': 0,
                                'source_file_count': 0,
                                'matched_patterns': 0
                            }

                        if file_path not in self.detected_languages[language]['files']:
                            self.detected_languages[language]['files'].append(file_path)
                            self.detected_languages[language]['feature_files'] += 1

                        self.config_files_count[language] += 1

    def _scan_source_files(self):
        """扫描源代码文件 (中等优先级)"""
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]

            # 计算目录深度
            depth = root.replace(str(self.project_path), '').count(os.sep)

            for file in files:
                file_ext = Path(file).suffix.lower()
                if file_ext:
                    self.source_files_count[file_ext] += 1

                    # 检查源代码文件
                    for language, config in self.LANGUAGE_SIGNATURES.items():
                        if file_ext in config.get('source_files', set()):
                            if language not in self.source_file_depths:
                                self.source_file_depths[language] = []
                            self.source_file_depths[language].append(depth)

    def _scan_directory_patterns(self):
        """扫描目录结构模式"""
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]

            for language, config in self.LANGUAGE_SIGNATURES.items():
                for pattern in config.get('dir_patterns', []):
                    if pattern in dirs or pattern in root:
                        self.dir_patterns_count[language] += 1

    def _aggregate_results(self):
        """综合判断语言"""
        # 处理已有特征文件的语言
        for language in list(self.detected_languages.keys()):
            continue  # 已经设置了 high confidence

        # 处理源代码文件较多的语言
        for ext, count in self.source_files_count.most_common():
            for language, config in self.LANGUAGE_SIGNATURES.items():
                if ext in config.get('source_files', set()):
                    if language in self.detected_languages:
                        # 更新源代码计数
                        self.detected_languages[language]['source_file_count'] = count
                    elif count >= 5:  # 提高阈值到 5 个
                        # 新增该语言
                        self.detected_languages[language] = {
                            'files': [],
                            'package_manager': config['package_manager'],
                            'priority': config['priority'] + 1,
                            'confidence': 'medium',
                            'feature_files': 0,
                            'source_file_count': count,
                            'matched_patterns': self.dir_patterns_count.get(language, 0)
                        }

    def get_detected_languages(self) -> List[str]:
        """获取检测到的所有语言列表"""
        return list(self.detected_languages.keys())

    def get_primary_language(self) -> str:
        """获取主要语言（改进的排序）"""
        if not self.detected_languages:
            return None

        def score_language(lang_name):
            info = self.detected_languages[lang_name]

            # 计算综合得分
            score = 0

            # 特征文件权重: 100
            score += info.get('feature_files', 0) * 100

            # 源文件数权重: 5
            score += info.get('source_file_count', 0) * 5

            # 目录模式权重: 50
            score += info.get('matched_patterns', 0) * 50

            # 置信度权重
            if info.get('confidence') == 'high':
                score += 500
            elif info.get('confidence') == 'medium':
                score += 200

            # 优先级权重 (低优先级号更好)
            score += (10 - info.get('priority', 0)) * 50

            return score

        # 按得分排序
        sorted_langs = sorted(
            self.detected_languages.items(),
            key=lambda x: score_language(x[0]),
            reverse=True
        )

        return sorted_langs[0][0] if sorted_langs else None

    def get_languages_by_score(self) -> List[Tuple[str, float]]:
        """按得分获取语言列表"""
        def score_language(lang_name):
            info = self.detected_languages[lang_name]
            score = (
                info.get('feature_files', 0) * 100 +
                info.get('source_file_count', 0) * 5 +
                info.get('matched_patterns', 0) * 50
            )

            if info.get('confidence') == 'high':
                score += 500
            elif info.get('confidence') == 'medium':
                score += 200

            return score

        scored = [
            (lang, score_language(lang))
            for lang in self.detected_languages
        ]
        return sorted(scored, key=lambda x: x[1], reverse=True)

    def get_package_manager(self, language: str) -> str:
        """获取包管理器"""
        if language in self.detected_languages:
            return self.detected_languages[language]['package_manager']
        return 'unknown'

    def get_detailed_summary(self) -> Dict:
        """获取详细的检测摘要"""
        summary = {
            'languages': self.get_languages_by_score(),
            'primary_language': self.get_primary_language(),
            'confidence_distribution': self._get_confidence_distribution(),
            'detection_stats': {
                'total_languages': len(self.detected_languages),
                'high_confidence': sum(
                    1 for l in self.detected_languages.values()
                    if l.get('confidence') == 'high'
                ),
                'medium_confidence': sum(
                    1 for l in self.detected_languages.values()
                    if l.get('confidence') == 'medium'
                ),
            }
        }
        return summary

    def _get_confidence_distribution(self) -> Dict[str, int]:
        """获取置信度分布"""
        dist = {'high': 0, 'medium': 0, 'low': 0}
        for lang_info in self.detected_languages.values():
            conf = lang_info.get('confidence', 'low')
            if conf in dist:
                dist[conf] += 1
        return dist

    def get_summary(self) -> str:
        """获取人类可读的检测摘要"""
        if not self.detected_languages:
            return "未检测到已知的项目类型"

        lines = ["检测到以下项目类型:"]
        for lang, score in self.get_languages_by_score():
            info = self.detected_languages[lang]
            conf = info.get('confidence', 'unknown')
            feature_count = info.get('feature_files', 0)
            source_count = info.get('source_file_count', 0)

            details = []
            if feature_count > 0:
                details.append(f"{feature_count} 个特征文件")
            if source_count > 0:
                details.append(f"{source_count} 个源文件")

            detail_str = f" ({', '.join(details)})" if details else ""
            lines.append(f"  - {lang}: {conf} 置信度 [得分: {score}]{detail_str}")

        return "\n".join(lines)


# 测试代码
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python3 optimized_project_detector.py <project_path>")
        sys.exit(1)

    project_path = sys.argv[1]
    detector = OptimizedProjectDetector(project_path)

    print("=" * 70)
    print("优化的项目语言检测器")
    print("=" * 70)

    result = detector.detect()
    print("\n检测结果:")
    print(detector.get_summary())

    print("\n\n详细统计:")
    summary = detector.get_detailed_summary()
    print(f"检测到的语言数: {summary['detection_stats']['total_languages']}")
    print(f"高置信度: {summary['detection_stats']['high_confidence']}")
    print(f"中置信度: {summary['detection_stats']['medium_confidence']}")
    print(f"主要语言: {summary['primary_language']}")

    print("\n\n按得分排序:")
    for lang, score in summary['languages']:
        info = detector.detected_languages[lang]
        print(f"\n{lang}:")
        print(f"  得分: {score:.0f}")
        print(f"  置信度: {info.get('confidence')}")
        print(f"  特征文件: {info.get('feature_files')} 个")
        print(f"  源代码文件: {info.get('source_file_count')} 个")
        print(f"  目录匹配: {info.get('matched_patterns')} 个")
