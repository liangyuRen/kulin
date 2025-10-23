import os
import re

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

def parse_setup_py(setup_py_path):
    """解析setup.py并提取依赖信息（简化版）"""
    try:
        dependencies = []
        with open(setup_py_path, 'r', encoding='utf-8') as f:
            content = f.read()

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
                dep_match = re.match(r'^([a-zA-Z0-9_-]+)\s*([=~><!]+)\s*([0-9.]+)', dep)
                if dep_match:
                    pkg_name, _, version = dep_match.groups()
                    dependencies.append(f"{pkg_name} {version}")
                else:
                    pkg_match = re.match(r'^([a-zA-Z0-9_-]+)', dep)
                    if pkg_match:
                        dependencies.append(pkg_match.group(1))

        return dependencies

    except Exception as e:
        print(f"处理setup.py失败 ({setup_py_path}): {str(e)}")
        return []

def find_python_dependency_files(root_dir):
    """递归查找所有Python依赖文件"""
    files = []
    for dirpath, _, filenames in os.walk(root_dir):
        # 优先级: Pipfile.lock > requirements.txt > Pipfile > setup.py
        if 'Pipfile.lock' in filenames:
            files.append(('pipfile', os.path.join(dirpath, 'Pipfile.lock')))
        elif 'requirements.txt' in filenames:
            files.append(('requirements', os.path.join(dirpath, 'requirements.txt')))
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
        if file_type == 'requirements':
            dependencies = parse_requirements_txt(file_path)
        elif file_type == 'pipfile':
            # Pipfile和Pipfile.lock使用相同的解析器（简化处理）
            dependencies = parse_pipfile(file_path)
        elif file_type == 'setup':
            dependencies = parse_setup_py(file_path)
        else:
            continue

        unique_dependencies.update(dependencies)

    print(f"Found {len(unique_dependencies)} unique Python dependencies")
    return llm_communicate(unique_dependencies, system_prompt, 10)


if __name__ == "__main__":
    project_path = input("请输入Python项目文件夹路径: ").strip()

    if not os.path.isdir(project_path):
        print("错误：输入的项目路径不存在或不是目录")
    else:
        result = collect_python_dependencies(project_path)
        print(f"处理完成，共 {len(result)} 个依赖")
