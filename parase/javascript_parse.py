import os
import json
import re
import yaml

from parase.pom_parse import llm_communicate

system_prompt = """Generate technical descriptions in English for JavaScript/Node.js dependencies following these rules:
1. For each dependency in format 'package-name version' (e.g. express 4.18.2)
2. Describe core functionality and typical use cases in JavaScript/Node.js development
3. Include key features and popular usage scenarios
4. Use concise technical language (80-120 words)
5. Output JSON array format:
[{
    "name": "package identifier with version",
    "description": "generated text"
},...]

Example:
[{
    "name": "express 4.18.2",
    "description": "A fast, unopinionated, minimalist web framework for Node.js. Provides robust routing, HTTP helpers, middleware support, and template engine integration. Widely used for building web applications and RESTful APIs..."
},{
    "name": "lodash 4.17.21",
    "description": "A modern JavaScript utility library delivering modularity, performance, and extras. Provides helper functions for common programming tasks like manipulating arrays, objects, strings, and more..."
}]"""

def parse_package_json(package_json_path):
    """解析package.json文件并提取依赖信息"""
    try:
        with open(package_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        dependencies = []

        # 提取dependencies
        if 'dependencies' in data and isinstance(data['dependencies'], dict):
            for pkg, version in data['dependencies'].items():
                # 清理版本号（移除^, ~, >=等前缀）
                clean_version = version.lstrip('^~>=<')
                dependencies.append(f"{pkg} {clean_version}")

        # 提取devDependencies（可选）
        if 'devDependencies' in data and isinstance(data['devDependencies'], dict):
            for pkg, version in data['devDependencies'].items():
                clean_version = version.lstrip('^~>=<')
                dependencies.append(f"{pkg} {clean_version}")

        return dependencies

    except json.JSONDecodeError as e:
        print(f"JSON解析错误 ({package_json_path}): {str(e)}")
        return []
    except Exception as e:
        print(f"处理package.json文件失败 ({package_json_path}): {str(e)}")
        return []

def parse_package_lock_json(package_lock_path):
    """解析package-lock.json文件并提取依赖信息"""
    try:
        with open(package_lock_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        dependencies = []

        # package-lock.json v2/v3 格式
        if 'packages' in data:
            for pkg_path, pkg_info in data['packages'].items():
                if pkg_path and pkg_path != '':  # 排除根包
                    pkg_name = pkg_path.replace('node_modules/', '')
                    version = pkg_info.get('version', '')
                    if version:
                        dependencies.append(f"{pkg_name} {version}")
        # package-lock.json v1 格式
        elif 'dependencies' in data:
            for pkg, info in data['dependencies'].items():
                version = info.get('version', '')
                if version:
                    dependencies.append(f"{pkg} {version}")

        return dependencies

    except json.JSONDecodeError as e:
        print(f"JSON解析错误 ({package_lock_path}): {str(e)}")
        return []
    except Exception as e:
        print(f"处理package-lock.json文件失败 ({package_lock_path}): {str(e)}")
        return []

def parse_yarn_lock(yarn_lock_path):
    """解析yarn.lock文件并提取依赖信息"""
    try:
        dependencies = []
        with open(yarn_lock_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # yarn.lock格式: "package@^version":
        # 匹配所有的包定义行
        package_pattern = r'^"([^"@]+)@(?:[^"]+)":.*\n\s+version\s+"([^"]+)"'
        for match in re.finditer(package_pattern, content, re.MULTILINE):
            pkg_name, version = match.groups()
            # 确保包名不包含 @scope 前缀的处理
            dependencies.append(f"{pkg_name} {version}")

        # 处理 scoped packages (@scope/package)
        scoped_pattern = r'^"(@[^"@]+/[^"@]+)@(?:[^"]+)":.*\n\s+version\s+"([^"]+)"'
        for match in re.finditer(scoped_pattern, content, re.MULTILINE):
            pkg_name, version = match.groups()
            dependencies.append(f"{pkg_name} {version}")

        # 去重
        return list(set(dependencies))

    except Exception as e:
        print(f"处理yarn.lock失败 ({yarn_lock_path}): {str(e)}")
        return []

def parse_pnpm_lock_yaml(pnpm_lock_path):
    """解析pnpm-lock.yaml文件并提取依赖信息"""
    try:
        dependencies = []
        with open(pnpm_lock_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # pnpm-lock.yaml是YAML格式，packages字段包含所有包
        try:
            data = yaml.safe_load(content)

            if 'packages' in data and isinstance(data['packages'], dict):
                for pkg_path, pkg_info in data['packages'].items():
                    # pkg_path的格式: 'node_modules/package@version'
                    # 提取包名和版本
                    if pkg_info and isinstance(pkg_info, dict):
                        version = pkg_info.get('version', '')
                        # 从路径中提取包名
                        if 'node_modules/' in pkg_path:
                            pkg_name = pkg_path.replace('node_modules/', '')
                            # 分离包名和版本路径
                            if '@' in pkg_name and not pkg_name.startswith('@'):
                                # 非scoped包
                                pkg_name = pkg_name.split('@')[0]
                            elif pkg_name.startswith('@'):
                                # scoped包
                                parts = pkg_name.rsplit('@', 1)
                                if len(parts) == 2:
                                    pkg_name = parts[0] + '/' + parts[1].split('@')[0] if '@' in parts[1] else parts[1]

                            if version:
                                dependencies.append(f"{pkg_name} {version}")
        except yaml.YAMLError:
            # 如果YAML解析失败，使用正则
            dependencies = _parse_pnpm_lock_regex(content)

        return list(set(dependencies))

    except Exception as e:
        print(f"处理pnpm-lock.yaml失败 ({pnpm_lock_path}): {str(e)}")
        return []

def _parse_pnpm_lock_regex(content):
    """使用正则表达式解析pnpm-lock.yaml"""
    dependencies = []

    # 简单的正则模式匹配 version: 'x.y.z' 行
    # 这是一个简化版本，因为YAML结构复杂
    version_pattern = r'\s+version:\s+[\'"]?([0-9.]+[^\'"\n]*)[\'"]?'
    for match in re.finditer(version_pattern, content):
        # 这不太精确，但对于基本提取还是可以的
        pass

    return dependencies

def find_javascript_lock_files(root_dir):
    """递归查找所有JavaScript包管理器的lock文件"""
    lock_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        # 优先级（按精准度）:
        # 1. pnpm-lock.yaml (pnpm)
        # 2. yarn.lock (yarn)
        # 3. package-lock.json (npm)
        # 4. package.json (fallback)

        if 'pnpm-lock.yaml' in filenames:
            lock_files.append(('pnpm', os.path.join(dirpath, 'pnpm-lock.yaml')))
        elif 'yarn.lock' in filenames:
            lock_files.append(('yarn', os.path.join(dirpath, 'yarn.lock')))
        elif 'package-lock.json' in filenames:
            lock_files.append(('npm_lock', os.path.join(dirpath, 'package-lock.json')))
        elif 'package.json' in filenames:
            lock_files.append(('npm', os.path.join(dirpath, 'package.json')))

    return lock_files

def find_npm_files(root_dir):
    """递归查找所有package.json和lock文件（向后兼容）"""
    return find_javascript_lock_files(root_dir)

def collect_javascript_dependencies(project_path):
    """收集JavaScript/Node.js项目的所有依赖（支持npm、yarn、pnpm）"""
    npm_files = find_npm_files(project_path)

    if not npm_files:
        print(f"No JavaScript lock files or package.json found in {project_path}")
        return []

    unique_dependencies = set()

    for file_type, file_path in npm_files:
        print(f"Processing {file_type}: {file_path}")

        if file_type == 'pnpm':
            # pnpm-lock.yaml
            dependencies = parse_pnpm_lock_yaml(file_path)
        elif file_type == 'yarn':
            # yarn.lock
            dependencies = parse_yarn_lock(file_path)
        elif file_type == 'npm_lock':
            # package-lock.json (npm)
            dependencies = parse_package_lock_json(file_path)
        elif file_type == 'npm':
            # package.json (fallback)
            dependencies = parse_package_json(file_path)
        else:
            continue

        if dependencies:
            print(f"  Found {len(dependencies)} dependencies from {file_type}")
            unique_dependencies.update(dependencies)

    print(f"Found {len(unique_dependencies)} unique JavaScript dependencies in total")
    return llm_communicate(unique_dependencies, system_prompt, 10)


if __name__ == "__main__":
    project_path = input("请输入JavaScript/Node.js项目文件夹路径: ").strip()

    if not os.path.isdir(project_path):
        print("错误：输入的项目路径不存在或不是目录")
    else:
        result = collect_javascript_dependencies(project_path)
        print(f"处理完成，共 {len(result)} 个依赖")
