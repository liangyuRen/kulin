#!/usr/bin/env python3
"""
统一的项目解析器 - 支持自动语言检测和多语言解析

功能：
1. 基于项目检测器自动识别项目语言
2. 调用相应的语言特定解析器
3. 聚合所有依赖信息
4. 保存到数据库的white_list表
5. 更新项目的元数据（language, component_count, analysis_status）
"""

import os
import sys
import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path

# 添加到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from parase.project_detector import ProjectDetector

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UnifiedProjectParser:
    """统一的项目解析器"""

    def __init__(self, project_path: str, project_id: Optional[int] = None):
        """
        初始化项目解析器

        Args:
            project_path: 项目路径
            project_id: 数据库中的项目ID（用于后续保存）
        """
        self.project_path = Path(project_path)
        self.project_id = project_id
        self.detector = ProjectDetector(str(project_path))
        self.detected_languages = {}
        self.all_dependencies = []
        self.parse_results = {}  # {language: {status: 'success'|'failed', dependencies: [...], error: ...}}

    def detect_languages(self) -> Dict[str, Dict]:
        """检测项目中的所有语言"""
        logger.info(f"检测项目语言: {self.project_path}")
        self.detected_languages = self.detector.detect()

        if not self.detected_languages:
            logger.warning("未检测到任何已知的项目类型")
            return {}

        logger.info(f"检测到语言: {list(self.detected_languages.keys())}")
        logger.info(self.detector.get_summary())

        return self.detected_languages

    def parse_all_languages(self) -> List[Dict]:
        """解析所有检测到的语言，并聚合依赖"""
        if not self.detected_languages:
            self.detect_languages()

        logger.info(f"开始解析 {len(self.detected_languages)} 种语言")

        # 按优先级遍历语言
        for language in self.detector.get_languages_by_priority():
            try:
                logger.info(f"正在解析 {language} 项目...")
                deps = self._parse_language(language)
                self.parse_results[language] = {
                    'status': 'success',
                    'dependencies': deps,
                    'count': len(deps)
                }
                self.all_dependencies.extend(deps)
                logger.info(f"✓ {language}: 找到 {len(deps)} 个依赖")
            except Exception as e:
                logger.error(f"✗ {language}: 解析失败 - {str(e)}")
                self.parse_results[language] = {
                    'status': 'failed',
                    'dependencies': [],
                    'error': str(e),
                    'count': 0
                }

        logger.info(f"解析完成: 共找到 {len(self.all_dependencies)} 个依赖")
        return self.all_dependencies

    def _parse_language(self, language: str) -> List[Dict]:
        """
        解析特定语言的项目

        Args:
            language: 编程语言 (java, python, go, etc.)

        Returns:
            依赖列表
        """
        # 动态导入相应的解析器
        parser_module = self._get_parser_module(language)
        if not parser_module:
            raise ValueError(f"不支持的语言: {language}")

        # 调用解析器
        dependencies = parser_module.parse(str(self.project_path))

        # 添加语言和包管理器信息
        package_manager = self.detector.get_package_manager(language)
        for dep in dependencies:
            dep['language'] = language
            dep['package_manager'] = package_manager

        return dependencies

    def _get_parser_module(self, language: str):
        """动态加载语言特定的解析器"""
        # 特殊的语言-模块映射（某些语言有不同的模块名称）
        language_module_mapping = {
            'java': 'pom_parse',  # Java使用pom_parse而不是java_parse
        }

        parser_name = language_module_mapping.get(language, f"{language}_parse")

        try:
            # 尝试导入优化版本的解析器（如果存在）
            try:
                module = __import__(f'parase.{parser_name}_improved', fromlist=[parser_name])
                logger.debug(f"使用改进版本的{language}解析器 ({parser_name}_improved)")
                return module
            except ImportError:
                # 回退到原始版本
                module = __import__(f'parase.{parser_name}', fromlist=[parser_name])
                logger.debug(f"使用原始版本的{language}解析器 ({parser_name})")
                return module
        except ImportError as e:
            logger.warning(f"无法导入 {language} 解析器 (尝试: {parser_name}): {e}")
            return None

    def get_summary(self) -> Dict:
        """获取解析结果摘要"""
        return {
            'project_path': str(self.project_path),
            'project_id': self.project_id,
            'detected_languages': list(self.detected_languages.keys()),
            'primary_language': self.detector.get_primary_language(),
            'parse_results': self.parse_results,
            'total_dependencies': len(self.all_dependencies),
            'timestamp': datetime.now().isoformat()
        }

    def print_summary(self):
        """打印解析结果摘要"""
        summary = self.get_summary()

        print("\n" + "=" * 70)
        print("项目解析结果摘要")
        print("=" * 70)
        print(f"项目路径: {summary['project_path']}")
        print(f"项目ID: {summary['project_id']}")
        print(f"检测到的语言: {', '.join(summary['detected_languages'])}")
        print(f"主要语言: {summary['primary_language']}")
        print(f"总依赖数: {summary['total_dependencies']}")
        print()

        print("按语言的解析结果:")
        for language, result in summary['parse_results'].items():
            status = "✓ 成功" if result['status'] == 'success' else "✗ 失败"
            print(f"  {language:12} {status:8} ({result['count']} 个依赖)", end="")
            if result['status'] == 'failed':
                print(f" - 错误: {result['error']}")
            else:
                print()

        print("\n示例依赖 (前10个):")
        for i, dep in enumerate(self.all_dependencies[:10], 1):
            print(f"  {i}. {dep['name']} ({dep['version']}) - {dep['language']}")

        if len(self.all_dependencies) > 10:
            print(f"  ... 还有 {len(self.all_dependencies) - 10} 个依赖")

        print("\n" + "=" * 70)

    def get_dependencies_for_database(self) -> List[Dict]:
        """
        获取格式化后的依赖列表，用于保存到数据库

        Returns:
            标准化的依赖字典列表
        """
        formatted_deps = []

        for dep in self.all_dependencies:
            formatted_dep = {
                'project_id': self.project_id,
                'name': dep.get('name', ''),
                'version': dep.get('version', 'unknown'),
                'language': dep.get('language', 'unknown'),
                'package_manager': dep.get('package_manager', 'unknown'),
                'file_path': dep.get('file_path', ''),
                'description': f"Dependency: {dep.get('name')} v{dep.get('version', 'unknown')}",
                'created_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'isdelete': 0
            }
            formatted_deps.append(formatted_dep)

        return formatted_deps


def parse_project(project_path: str, project_id: Optional[int] = None) -> Dict:
    """
    单一函数用于解析项目

    Args:
        project_path: 项目路径
        project_id: 数据库项目ID

    Returns:
        解析结果字典
    """
    parser = UnifiedProjectParser(project_path, project_id)
    parser.detect_languages()
    parser.parse_all_languages()
    parser.print_summary()

    return {
        'summary': parser.get_summary(),
        'dependencies': parser.get_dependencies_for_database(),
        'all_dependencies': parser.all_dependencies
    }


# 测试代码
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 unified_parser.py <project_path> [project_id]")
        print("例: python3 unified_parser.py /path/to/project 9")
        sys.exit(1)

    project_path = sys.argv[1]
    project_id = int(sys.argv[2]) if len(sys.argv) > 2 else None

    print(f"\n开始解析项目: {project_path}")
    print(f"项目ID: {project_id}")

    try:
        result = parse_project(project_path, project_id)
        print("\n\n解析结果JSON:")
        print(json.dumps(result['summary'], indent=2, ensure_ascii=False))
    except Exception as e:
        logger.error(f"解析失败: {e}", exc_info=True)
        sys.exit(1)
