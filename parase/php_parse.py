import os
import json

from parase.pom_parse import llm_communicate

system_prompt = """Generate technical descriptions in English for PHP Composer dependencies following these rules:
1. For each dependency in format 'vendor/package version' (e.g. laravel/framework 10.0.0)
2. Describe core functionality and typical use cases in PHP development
3. Include key features and popular usage scenarios
4. Use concise technical language (80-120 words)
5. Output JSON array format:
[{
    "name": "package identifier with version",
    "description": "generated text"
},...]

Example:
[{
    "name": "laravel/framework 10.0.0",
    "description": "A comprehensive PHP web application framework with expressive, elegant syntax. Provides routing, middleware, authentication, ORM (Eloquent), templating (Blade), and artisan CLI. Widely used for building modern web applications..."
},{
    "name": "symfony/http-foundation 6.2.0",
    "description": "Defines an object-oriented layer for the HTTP specification. Provides Request and Response objects with a clean API for working with HTTP headers, cookies, sessions, and file uploads. Core component of many PHP frameworks..."
}]"""

def parse_composer_json(composer_json_path):
    """解析composer.json文件并提取依赖信息"""
    try:
        with open(composer_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        dependencies = []

        # 提取require中的依赖
        if 'require' in data and isinstance(data['require'], dict):
            for pkg, version in data['require'].items():
                # 跳过PHP自身和扩展
                if pkg.startswith('php') or pkg.startswith('ext-'):
                    continue
                # 清理版本号
                clean_version = version.lstrip('^~>=<*')
                if clean_version:
                    dependencies.append(f"{pkg} {clean_version}")
                else:
                    dependencies.append(pkg)

        # 提取require-dev中的依赖（可选）
        if 'require-dev' in data and isinstance(data['require-dev'], dict):
            for pkg, version in data['require-dev'].items():
                if pkg.startswith('php') or pkg.startswith('ext-'):
                    continue
                clean_version = version.lstrip('^~>=<*')
                if clean_version:
                    dependencies.append(f"{pkg} {clean_version}")
                else:
                    dependencies.append(pkg)

        return dependencies

    except json.JSONDecodeError as e:
        print(f"JSON解析错误 ({composer_json_path}): {str(e)}")
        return []
    except Exception as e:
        print(f"处理composer.json文件失败 ({composer_json_path}): {str(e)}")
        return []

def parse_composer_lock(composer_lock_path):
    """解析composer.lock文件并提取依赖信息"""
    try:
        with open(composer_lock_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        dependencies = []

        # 提取packages
        if 'packages' in data and isinstance(data['packages'], list):
            for package in data['packages']:
                name = package.get('name', '')
                version = package.get('version', '').lstrip('v')
                if name and version:
                    dependencies.append(f"{name} {version}")

        # 提取packages-dev
        if 'packages-dev' in data and isinstance(data['packages-dev'], list):
            for package in data['packages-dev']:
                name = package.get('name', '')
                version = package.get('version', '').lstrip('v')
                if name and version:
                    dependencies.append(f"{name} {version}")

        return dependencies

    except json.JSONDecodeError as e:
        print(f"JSON解析错误 ({composer_lock_path}): {str(e)}")
        return []
    except Exception as e:
        print(f"处理composer.lock文件失败 ({composer_lock_path}): {str(e)}")
        return []

def find_composer_files(root_dir):
    """递归查找所有composer文件"""
    composer_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        # 优先使用composer.lock（版本更精确）
        if 'composer.lock' in filenames:
            composer_files.append(('lock', os.path.join(dirpath, 'composer.lock')))
        elif 'composer.json' in filenames:
            composer_files.append(('json', os.path.join(dirpath, 'composer.json')))

    return composer_files

def collect_php_dependencies(project_path):
    """收集PHP项目的所有依赖"""
    composer_files = find_composer_files(project_path)

    if not composer_files:
        print(f"No composer.json or composer.lock files found in {project_path}")
        return json.dumps([])

    unique_dependencies = set()

    for file_type, file_path in composer_files:
        if file_type == 'lock':
            dependencies = parse_composer_lock(file_path)
        else:
            dependencies = parse_composer_json(file_path)

        unique_dependencies.update(dependencies)

    print(f"Found {len(unique_dependencies)} unique PHP dependencies")
    return llm_communicate(unique_dependencies, system_prompt, 10)


if __name__ == "__main__":
    project_path = input("请输入PHP项目文件夹路径: ").strip()

    if not os.path.isdir(project_path):
        print("错误：输入的项目路径不存在或不是目录")
    else:
        result = collect_php_dependencies(project_path)
        print(f"处理完成，共 {len(result)} 个依赖")
