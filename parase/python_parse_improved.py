"""
改进的Python依赖解析器 - 支持版本约束和extras

支持解析：
- requirements.txt (多个文件)
- setup.py / setup.cfg
- pyproject.toml (Poetry和PEP 517)
- Pipfile / Pipfile.lock
- poetry.lock
"""

import os
import re
import json
import ast
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging

from parase.version_parser import VersionParser, VersionRange

logger = logging.getLogger(__name__)


class PythonDependency:
    """Python依赖对象"""

    def __init__(self, name: str, version_range: VersionRange = None,
                 extras: List[str] = None, dependency_type: str = 'production',
                 markers: str = None):
        self.name = name
        self.version_range = version_range or VersionRange([], "")
        self.extras = extras or []
        self.dependency_type = dependency_type  # production, development, optional
        self.markers = markers  # PEP 508环境标记

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'version_range': str(self.version_range) if self.version_range else '(unspecified)',
            'min_version': self.version_range.get_min_version(),
            'max_version': self.version_range.get_max_version(),
            'exact_version': self.version_range.get_exact_version(),
            'extras': self.extras,
            'type': self.dependency_type,
            'markers': self.markers
        }

    def __repr__(self):
        return f"PythonDep({self.name}[{self.version_range}])"


class PythonParser:
    """改进的Python项目解析器"""

    def __init__(self, project_path: str):
        self.project_path = project_path
        self.version_parser = VersionParser()
        self.dependencies: List[PythonDependency] = []
        self.errors: List[str] = []

    def parse(self) -> Dict:
        """
        解析Python项目的所有依赖

        返回格式:
        {
            'status': 'success'/'error',
            'dependencies': [...],
            'errors': [...],
            'metadata': {
                'total_found': int,
                'with_constraints': int,
                'with_extras': int,
                'files_parsed': [...]
            }
        }
        """
        self.dependencies.clear()
        self.errors.clear()
        parsed_files = []

        # 优先级顺序尝试解析不同文件类型
        file_checkers = [
            (self._parse_poetry_lock, 'poetry.lock'),
            (self._parse_pipfile_lock, 'Pipfile.lock'),
            (self._parse_requirements_txt, 'requirements.txt'),
            (self._parse_setup_py, 'setup.py'),
            (self._parse_pyproject_toml, 'pyproject.toml'),
            (self._parse_pipfile, 'Pipfile'),
        ]

        for checker_func, file_name in file_checkers:
            file_path = os.path.join(self.project_path, file_name)
            if os.path.exists(file_path):
                try:
                    logger.info(f"解析 {file_name}")
                    deps = checker_func(file_path)
                    if deps:
                        self.dependencies.extend(deps)
                        parsed_files.append(file_name)
                except Exception as e:
                    logger.error(f"解析 {file_name} 失败: {e}")
                    self.errors.append(f"{file_name}: {str(e)}")

        # 如果有lock文件，跳过txt文件（lock文件更准确）
        has_lock = any('lock' in f.lower() for f in parsed_files)
        if has_lock:
            self.dependencies = [d for d in self.dependencies
                               if 'requirements' not in parsed_files]

        # 去重（同一个包可能在多个文件中）
        unique_deps = {}
        for dep in self.dependencies:
            key = (dep.name.lower(), dep.dependency_type)
            if key not in unique_deps:
                unique_deps[key] = dep

        self.dependencies = list(unique_deps.values())

        return {
            'status': 'success' if self.dependencies or not self.errors else 'error',
            'dependencies': [d.to_dict() for d in self.dependencies],
            'errors': self.errors,
            'metadata': {
                'total_found': len(self.dependencies),
                'with_constraints': sum(1 for d in self.dependencies
                                       if not d.version_range.is_unconstrained()),
                'with_extras': sum(1 for d in self.dependencies if d.extras),
                'files_parsed': parsed_files
            }
        }

    def _parse_requirements_txt(self, file_path: str) -> List[PythonDependency]:
        """解析requirements.txt文件"""
        dependencies = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # 跳过注释和空行
                    if not line or line.startswith('#'):
                        continue

                    # 跳过选项行 (-r, -f, --index-url等)
                    if line.startswith('-'):
                        continue

                    try:
                        # 解析PEP 508格式: name[extras]>=version ; markers
                        dep = self._parse_pep508_requirement(line)
                        if dep:
                            dependencies.append(dep)
                    except Exception as e:
                        logger.warning(f"{file_path}:{line_num} 解析失败: {line} - {e}")
                        self.errors.append(
                            f"{os.path.basename(file_path)}:{line_num} - {str(e)}"
                        )

        except Exception as e:
            logger.error(f"读取 {file_path} 失败: {e}")
            raise

        return dependencies

    def _parse_setup_py(self, file_path: str) -> List[PythonDependency]:
        """解析setup.py文件"""
        dependencies = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 使用AST解析setup()调用
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # 查找setup()调用
                    if isinstance(node.func, ast.Name) and node.func.id == 'setup':
                        # 提取关键字参数
                        for keyword in node.keywords:
                            if keyword.arg == 'install_requires':
                                deps = self._extract_list_from_ast(keyword.value)
                                for dep_str in deps:
                                    dep = self._parse_pep508_requirement(dep_str)
                                    if dep:
                                        dependencies.append(dep)

                            elif keyword.arg == 'extras_require':
                                # extras_require是字典: {'dev': [...], 'test': [...]}
                                extras_dict = self._extract_dict_from_ast(keyword.value)
                                for extra_name, dep_list in extras_dict.items():
                                    for dep_str in dep_list:
                                        dep = self._parse_pep508_requirement(dep_str)
                                        if dep:
                                            dep.dependency_type = f'optional[{extra_name}]'
                                            dependencies.append(dep)

                            elif keyword.arg == 'tests_require':
                                deps = self._extract_list_from_ast(keyword.value)
                                for dep_str in deps:
                                    dep = self._parse_pep508_requirement(dep_str)
                                    if dep:
                                        dep.dependency_type = 'test'
                                        dependencies.append(dep)

        except SyntaxError as e:
            logger.warning(f"setup.py 语法错误: {e}")
        except Exception as e:
            logger.error(f"解析 setup.py 失败: {e}")
            raise

        return dependencies

    def _parse_pyproject_toml(self, file_path: str) -> List[PythonDependency]:
        """解析pyproject.toml (Poetry/PEP 517)"""
        dependencies = []

        try:
            # 简单的TOML解析（如果有toml库则更好）
            import configparser
            config = configparser.ConfigParser()
            config.read(file_path)

            # 查找[project] dependencies部分 (PEP 517)
            if config.has_section('project'):
                if config.has_option('project', 'dependencies'):
                    deps_str = config.get('project', 'dependencies')
                    # 通常是多行JSON数组
                    try:
                        deps_list = json.loads(deps_str)
                        for dep_str in deps_list:
                            dep = self._parse_pep508_requirement(dep_str)
                            if dep:
                                dependencies.append(dep)
                    except:
                        pass

            # 查找[tool.poetry] dependencies部分
            if config.has_section('tool.poetry'):
                for option in ['dependencies', 'dev-dependencies']:
                    if config.has_option('tool.poetry', option):
                        deps_str = config.get('tool.poetry', option)
                        # Poetry格式通常是字典
                        pass

        except Exception as e:
            logger.error(f"解析 pyproject.toml 失败: {e}")

        return dependencies

    def _parse_pipfile(self, file_path: str) -> List[PythonDependency]:
        """解析Pipfile"""
        dependencies = []

        try:
            # 简单的INI解析
            import configparser
            config = configparser.ConfigParser()
            config.read(file_path)

            for section in ['packages', 'dev-packages']:
                if config.has_section(section):
                    dep_type = 'development' if 'dev' in section else 'production'
                    for pkg_name in config.options(section):
                        version_spec = config.get(section, pkg_name)
                        # Pipfile格式: {"requests": ">=2.28.0"}
                        dep = PythonDependency(
                            name=pkg_name,
                            version_range=self.version_parser.parse(version_spec),
                            dependency_type=dep_type
                        )
                        dependencies.append(dep)

        except Exception as e:
            logger.error(f"解析 Pipfile 失败: {e}")

        return dependencies

    def _parse_poetry_lock(self, file_path: str) -> List[PythonDependency]:
        """解析poetry.lock文件 (TOML格式)"""
        dependencies = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 查找[[package]]部分
            package_pattern = r'\[\[package\]\]\s*\nname\s*=\s*"([^"]+)"\s*\nversion\s*=\s*"([^"]+)"'
            matches = re.finditer(package_pattern, content)

            for match in matches:
                pkg_name = match.group(1)
                version = match.group(2)

                dep = PythonDependency(
                    name=pkg_name,
                    version_range=self.version_parser.parse(version),
                    dependency_type='production'
                )
                dependencies.append(dep)

        except Exception as e:
            logger.error(f"解析 poetry.lock 失败: {e}")

        return dependencies

    def _parse_pipfile_lock(self, file_path: str) -> List[PythonDependency]:
        """解析Pipfile.lock (JSON格式)"""
        dependencies = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lock_data = json.load(f)

            for dep_type in ['default', 'develop']:
                if dep_type in lock_data:
                    pkg_type = 'development' if dep_type == 'develop' else 'production'

                    for pkg_name, pkg_info in lock_data[dep_type].items():
                        version = pkg_info.get('version', '').lstrip('=')

                        dep = PythonDependency(
                            name=pkg_name,
                            version_range=self.version_parser.parse(version),
                            dependency_type=pkg_type
                        )
                        dependencies.append(dep)

        except Exception as e:
            logger.error(f"解析 Pipfile.lock 失败: {e}")

        return dependencies

    def _parse_pep508_requirement(self, requirement_str: str) -> Optional[PythonDependency]:
        """
        解析PEP 508格式的依赖字符串

        格式: name[extras]>=version ; markers

        例: requests[security]>=2.28.0,<3.0.0 ; python_version>="3.6"
        """
        requirement_str = requirement_str.strip()

        if not requirement_str:
            return None

        # 分离markers: ; 后面的部分
        markers = None
        if ';' in requirement_str:
            requirement_str, markers = requirement_str.split(';', 1)
            markers = markers.strip()
            requirement_str = requirement_str.strip()

        # 解析包名和extras: package[extra1,extra2]
        pkg_name, extras, constraint_str = self.version_parser.parse_extras(requirement_str)

        # 验证包名有效性
        if not re.match(r'^[a-zA-Z0-9_\-\.]+$', pkg_name):
            logger.warning(f"无效的包名: {pkg_name}")
            return None

        # 解析版本约束
        version_range = self.version_parser.parse(constraint_str) if constraint_str else VersionRange([], '')

        return PythonDependency(
            name=pkg_name,
            version_range=version_range,
            extras=extras,
            markers=markers,
            dependency_type='production'
        )

    def _extract_list_from_ast(self, node) -> List[str]:
        """从AST节点提取字符串列表"""
        items = []

        if isinstance(node, ast.List):
            for element in node.elts:
                if isinstance(element, ast.Str):  # Python < 3.8
                    items.append(element.s)
                elif isinstance(element, ast.Constant) and isinstance(element.value, str):  # Python >= 3.8
                    items.append(element.value)
                elif isinstance(element, ast.BinOp):  # 字符串拼接
                    # 简单处理: a + b
                    if isinstance(element.left, ast.Constant):
                        items.append(str(element.left.value))

        return items

    def _extract_dict_from_ast(self, node) -> Dict[str, List[str]]:
        """从AST节点提取字典"""
        result = {}

        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if isinstance(key, ast.Str):  # Python < 3.8
                    dict_key = key.s
                elif isinstance(key, ast.Constant):  # Python >= 3.8
                    dict_key = key.value
                else:
                    continue

                items = self._extract_list_from_ast(value)
                if items:
                    result[dict_key] = items

        return result


# 使用示例
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        project_path = sys.argv[1]
    else:
        project_path = "."

    parser = PythonParser(project_path)
    result = parser.parse()

    print(json.dumps(result, indent=2, ensure_ascii=False))
