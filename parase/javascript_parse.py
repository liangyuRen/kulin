import os
import json

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

def find_npm_files(root_dir):
    """递归查找所有package.json和package-lock.json文件"""
    package_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        # 优先使用package-lock.json（版本更精确）
        if 'package-lock.json' in filenames:
            package_files.append(('lock', os.path.join(dirpath, 'package-lock.json')))
        elif 'package.json' in filenames:
            package_files.append(('json', os.path.join(dirpath, 'package.json')))

    return package_files

def collect_javascript_dependencies(project_path):
    """收集JavaScript/Node.js项目的所有依赖"""
    npm_files = find_npm_files(project_path)

    if not npm_files:
        print(f"No package.json or package-lock.json files found in {project_path}")
        return []

    unique_dependencies = set()

    for file_type, file_path in npm_files:
        if file_type == 'lock':
            dependencies = parse_package_lock_json(file_path)
        else:
            dependencies = parse_package_json(file_path)

        unique_dependencies.update(dependencies)

    print(f"Found {len(unique_dependencies)} unique JavaScript dependencies")
    return llm_communicate(unique_dependencies, system_prompt, 10)


if __name__ == "__main__":
    project_path = input("请输入JavaScript/Node.js项目文件夹路径: ").strip()

    if not os.path.isdir(project_path):
        print("错误：输入的项目路径不存在或不是目录")
    else:
        result = collect_javascript_dependencies(project_path)
        print(f"处理完成，共 {len(result)} 个依赖")
