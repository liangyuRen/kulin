import os
import re
import ast
import json

from parase.pom_parse import llm_communicate

system_prompt = """Generate technical descriptions in English for Python package dependencies following these rules:
1. For each dependency in format 'package-name version' (e.g. django 4.2.0)
2. Describe core functionality and typical use cases in Python development
3. Include key features and popular usage scenarios
4. Use concise technical language (80-120 words)
5. Output JSON array format:
[{
    "name": "package identifier with version",
    "description": "generated text"
},...]

Example:
[{
    "name": "django 4.2.0",
    "description": "A high-level Python web framework that encourages rapid development and clean, pragmatic design. Includes ORM, templating engine, admin interface, authentication, and URL routing. Widely used for building scalable web applications..."
},{
    "name": "requests 2.31.0",
    "description": "An elegant and simple HTTP library for Python. Provides intuitive methods for making HTTP requests with features like automatic content decoding, connection pooling, and SSL verification. Essential for API integration..."
}]"""

def parse_requirements_txt(requirements_path):
    """解析requirements.txt文件并提取依赖信息"""
    try:
        dependencies = []
        with open(requirements_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if not line or line.startswith('#'):
                    continue

                # 处理各种格式：
                # package==1.0.0
                # package>=1.0.0
                # package~=1.0.0
                # package
                match = re.match(r'^([a-zA-Z0-9_-]+)\s*([=~><!]+)\s*([0-9.]+)', line)
                if match:
                    pkg_name, _, version = match.groups()
                    dependencies.append(f"{pkg_name} {version}")
                else:
                    # 没有版本号的包
                    pkg_match = re.match(r'^([a-zA-Z0-9_-]+)', line)
                    if pkg_match:
                        dependencies.append(pkg_match.group(1))

        return dependencies

    except Exception as e:
        print(f"处理requirements.txt文件失败 ({requirements_path}): {str(e)}")
        return []

def parse_pipfile(pipfile_path):
    """解析Pipfile并提取依赖信息"""
    try:
        dependencies = []
        with open(pipfile_path, 'r', encoding='utf-8') as f:
            in_packages = False
            for line in f:
                line = line.strip()

                # 检测[packages]或[dev-packages]部分
                if line.startswith('[packages]') or line.startswith('[dev-packages]'):
                    in_packages = True
                    continue
                elif line.startswith('['):
                    in_packages = False
                    continue

                if in_packages and '=' in line:
                    # 格式: package = "==1.0.0" 或 package = "*"
                    match = re.match(r'^([a-zA-Z0-9_-]+)\s*=\s*"([^"]+)"', line)
                    if match:
                        pkg_name, version = match.groups()
                        # 清理版本号
                        clean_version = version.lstrip('=~><!* ')
                        if clean_version and clean_version != '*':
                            dependencies.append(f"{pkg_name} {clean_version}")
                        else:
                            dependencies.append(pkg_name)

        return dependencies

    except Exception as e:
        print(f"处理Pipfile失败 ({pipfile_path}): {str(e)}")
        return []

def parse_setup_py_ast(setup_py_path):
    """使用AST解析setup.py以支持更复杂的依赖定义"""
    try:
        dependencies = []
        with open(setup_py_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 尝试使用AST解析
        try:
            tree = ast.parse(content)

            # 查找setup()函数调用
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # 检查是否是setup()函数
                    if isinstance(node.func, ast.Name) and node.func.id == 'setup':
                        # 遍历所有关键字参数
                        for keyword in node.keywords:
                            if keyword.arg in ('install_requires', 'requires', 'extras_require'):
                                dependencies.extend(_extract_deps_from_ast_value(keyword.value))
                    # 或者可能是setuptools.setup()
                    elif isinstance(node.func, ast.Attribute) and node.func.attr == 'setup':
                        for keyword in node.keywords:
                            if keyword.arg in ('install_requires', 'requires', 'extras_require'):
                                dependencies.extend(_extract_deps_from_ast_value(keyword.value))
        except SyntaxError:
            # 如果AST解析失败，回退到正则表达式
            dependencies = _parse_setup_py_regex(content)
            return dependencies

        return list(set(dependencies))  # 去重

    except Exception as e:
        print(f"AST解析setup.py失败 ({setup_py_path}): {str(e)}")
        # 回退到正则表达式解析
        try:
            with open(setup_py_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return _parse_setup_py_regex(content)
        except Exception as e2:
            print(f"正则表达式解析也失败: {str(e2)}")
            return []

def _extract_deps_from_ast_value(value):
    """从AST节点值提取依赖列表"""
    dependencies = []

    if isinstance(value, ast.List):
        # install_requires = [...]
        for element in value.elts:
            if isinstance(element, ast.Constant):
                dep = element.value
                if isinstance(dep, str):
                    dependencies.append(dep.strip())
            elif isinstance(element, ast.Str):  # Python 3.7及更早版本
                dependencies.append(element.s.strip())
    elif isinstance(value, ast.Dict):
        # extras_require = {...}
        for val in value.values:
            if isinstance(val, ast.List):
                for element in val.elts:
                    if isinstance(element, ast.Constant) and isinstance(element.value, str):
                        dependencies.append(element.value.strip())
                    elif isinstance(element, ast.Str):
                        dependencies.append(element.s.strip())

    return dependencies

def _parse_setup_py_regex(content):
    """使用正则表达式解析setup.py"""
    dependencies = []

    # 查找install_requires部分
    install_requires_match = re.search(
        r'install_requires\s*=\s*\[(.*?)\]',
        content,
        re.DOTALL
    )

    if install_requires_match:
        requires_str = install_requires_match.group(1)
        # 提取所有引号中的内容
        for match in re.finditer(r'["\']([^"\']+)["\']', requires_str):
            dep = match.group(1)
            # 解析格式: package==1.0.0 或 package>=1.0.0
            dep_match = re.match(r'^([a-zA-Z0-9_.-]+)\s*([=~><!]+)\s*([0-9.]+)', dep)
            if dep_match:
                pkg_name, _, version = dep_match.groups()
                dependencies.append(f"{pkg_name} {version}")
            else:
                pkg_match = re.match(r'^([a-zA-Z0-9_.-]+)', dep)
                if pkg_match:
                    dependencies.append(pkg_match.group(1))

    return dependencies

def parse_setup_py(setup_py_path):
    """解析setup.py并提取依赖信息（AST + 正则混合）"""
    return parse_setup_py_ast(setup_py_path)

def parse_poetry_lock(poetry_lock_path):
    """解析poetry.lock文件"""
    try:
        dependencies = []
        with open(poetry_lock_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # poetry.lock格式：[[package]]部分包含name和version
        package_pattern = r'\[\[package\]\]\s*\nname\s*=\s*"([^"]+)"\s*\nversion\s*=\s*"([^"]+)"'
        for match in re.finditer(package_pattern, content):
            pkg_name, version = match.groups()
            dependencies.append(f"{pkg_name} {version}")

        return dependencies

    except Exception as e:
        print(f"处理poetry.lock失败 ({poetry_lock_path}): {str(e)}")
        return []

def parse_pyproject_toml(pyproject_path):
    """解析pyproject.toml文件（支持poetry）"""
    try:
        dependencies = []
        with open(pyproject_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 查找[tool.poetry.dependencies]部分
        poetry_deps_match = re.search(
            r'\[tool\.poetry\.dependencies\](.*?)(?=\[|$)',
            content,
            re.DOTALL
        )

        if poetry_deps_match:
            deps_section = poetry_deps_match.group(1)
            # 匹配: package = "^1.0.0" 或 package = {version = "^1.0.0"}
            # 简单的版本提取
            for line in deps_section.split('\n'):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # 格式1: package = "^1.0.0"
                match1 = re.match(r'^([a-zA-Z0-9_-]+)\s*=\s*"([^"]+)"', line)
                if match1:
                    pkg_name, version_spec = match1.groups()
                    # 清理版本号 (^1.0.0 -> 1.0.0)
                    clean_version = re.sub(r'^[\^~>=<!]*', '', version_spec)
                    if clean_version:
                        dependencies.append(f"{pkg_name} {clean_version}")
                    continue

                # 格式2: package = {version = "^1.0.0"}
                match2 = re.match(r'^([a-zA-Z0-9_-]+)\s*=\s*\{', line)
                if match2:
                    pkg_name = match2.group(1)
                    # 从当前行及后续行中提取version
                    version_match = re.search(r'version\s*=\s*"([^"]+)"', line)
                    if version_match:
                        version_spec = version_match.group(1)
                        clean_version = re.sub(r'^[\^~>=<!]*', '', version_spec)
                        if clean_version:
                            dependencies.append(f"{pkg_name} {clean_version}")

        return dependencies

    except Exception as e:
        print(f"处理pyproject.toml失败 ({pyproject_path}): {str(e)}")
        return []

def parse_pipfile_lock(pipfile_lock_path):
    """解析Pipfile.lock文件"""
    try:
        dependencies = []
        with open(pipfile_lock_path, 'r', encoding='utf-8') as f:
            content = f.read()

        try:
            # Pipfile.lock是JSON格式
            data = json.loads(content)

            # 获取default和develop依赖
            for section in ['default', 'develop']:
                if section in data:
                    for pkg_name, pkg_info in data[section].items():
                        if isinstance(pkg_info, dict) and 'version' in pkg_info:
                            version = pkg_info['version']
                            # 移除版本前的==
                            clean_version = version.lstrip('=')
                            if clean_version:
                                dependencies.append(f"{pkg_name} {clean_version}")
                        else:
                            dependencies.append(pkg_name)
        except json.JSONDecodeError:
            # 如果JSON解析失败，使用正则
            # 简单的[[package]] 式Pipfile.lock
            package_pattern = r'\[\[package\]\]\s*\nname\s*=\s*"([^"]+)"\s*\nversion\s*=\s*"([^"]+)"'
            for match in re.finditer(package_pattern, content):
                pkg_name, version = match.groups()
                dependencies.append(f"{pkg_name} {version}")

        return dependencies

    except Exception as e:
        print(f"处理Pipfile.lock失败 ({pipfile_lock_path}): {str(e)}")
        return []

def find_python_dependency_files(root_dir):
    """递归查找所有Python依赖文件"""
    files = []
    for dirpath, _, filenames in os.walk(root_dir):
        # 优先级（按精准度）:
        # 1. poetry.lock (最精确，包含所有resolved版本)
        # 2. Pipfile.lock (Pipenv的lock文件，精确)
        # 3. requirements.txt (标准格式)
        # 4. pyproject.toml (Poetry配置，可能版本约束宽泛)
        # 5. Pipfile (Pipenv配置)
        # 6. setup.py (通常使用版本约束)

        if 'poetry.lock' in filenames:
            files.append(('poetry_lock', os.path.join(dirpath, 'poetry.lock')))
        elif 'Pipfile.lock' in filenames:
            files.append(('pipfile_lock', os.path.join(dirpath, 'Pipfile.lock')))
        elif 'requirements.txt' in filenames:
            files.append(('requirements', os.path.join(dirpath, 'requirements.txt')))
        elif 'pyproject.toml' in filenames:
            files.append(('pyproject', os.path.join(dirpath, 'pyproject.toml')))
        elif 'Pipfile' in filenames:
            files.append(('pipfile', os.path.join(dirpath, 'Pipfile')))
        elif 'setup.py' in filenames:
            files.append(('setup', os.path.join(dirpath, 'setup.py')))

    return files

def collect_python_dependencies(project_path):
    """收集Python项目的所有依赖"""
    dep_files = find_python_dependency_files(project_path)

    if not dep_files:
        print(f"No Python dependency files found in {project_path}")
        return []

    unique_dependencies = set()

    for file_type, file_path in dep_files:
        print(f"Processing {file_type}: {file_path}")

        if file_type == 'requirements':
            dependencies = parse_requirements_txt(file_path)
        elif file_type == 'pipfile':
            # Pipfile使用TOML格式解析
            dependencies = parse_pipfile(file_path)
        elif file_type == 'pipfile_lock':
            # Pipfile.lock使用JSON格式解析
            dependencies = parse_pipfile_lock(file_path)
        elif file_type == 'poetry_lock':
            # poetry.lock是TOML格式，包含所有resolved版本
            dependencies = parse_poetry_lock(file_path)
        elif file_type == 'pyproject':
            # pyproject.toml支持Poetry配置
            dependencies = parse_pyproject_toml(file_path)
        elif file_type == 'setup':
            # setup.py使用AST解析
            dependencies = parse_setup_py(file_path)
        else:
            continue

        if dependencies:
            print(f"  Found {len(dependencies)} dependencies from {file_type}")
            unique_dependencies.update(dependencies)

    print(f"Found {len(unique_dependencies)} unique Python dependencies in total")
    return llm_communicate(unique_dependencies, system_prompt, 10)


if __name__ == "__main__":
    project_path = input("请输入Python项目文件夹路径: ").strip()

    if not os.path.isdir(project_path):
        print("错误：输入的项目路径不存在或不是目录")
    else:
        result = collect_python_dependencies(project_path)
        print(f"处理完成，共 {len(result)} 个依赖")
