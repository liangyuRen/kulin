import os
import re

from parase.pom_parse import llm_communicate

system_prompt = """Generate technical descriptions in English for Ruby gem dependencies following these rules:
1. For each dependency in format 'gem-name version' (e.g. rails 7.0.0)
2. Describe core functionality and typical use cases in Ruby development
3. Include key features and popular usage scenarios
4. Use concise technical language (80-120 words)
5. Output JSON array format:
[{
    "name": "gem identifier with version",
    "description": "generated text"
},...]

Example:
[{
    "name": "rails 7.0.0",
    "description": "A full-stack web application framework that includes everything needed to create database-backed web applications. Follows the MVC pattern, includes Active Record ORM, Action View templating, and Action Controller. Convention over configuration philosophy..."
},{
    "name": "devise 4.9.0",
    "description": "A flexible authentication solution for Rails based on Warden. Provides complete user authentication with features like password encryption, email confirmation, account locking, and password recovery. Highly modular and customizable..."
}]"""

def parse_gemfile(gemfile_path):
    """解析Gemfile并提取依赖信息"""
    try:
        dependencies = []
        with open(gemfile_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 跳过注释和空行
                if not line or line.startswith('#'):
                    continue

                # 匹配gem声明: gem 'rails', '~> 7.0.0'
                match = re.match(r"gem\s+['\"]([^'\"]+)['\"](?:\s*,\s*['\"]([^'\"]+)['\"])?", line)
                if match:
                    gem_name = match.group(1)
                    version = match.group(2) if match.group(2) else None

                    if version:
                        # 清理版本号
                        clean_version = version.lstrip('~><=')
                        dependencies.append(f"{gem_name} {clean_version}")
                    else:
                        dependencies.append(gem_name)

        return dependencies

    except Exception as e:
        print(f"处理Gemfile失败 ({gemfile_path}): {str(e)}")
        return []

def parse_gemfile_lock(gemfile_lock_path):
    """解析Gemfile.lock并提取依赖信息"""
    try:
        dependencies = []
        in_specs = False

        with open(gemfile_lock_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()

                # 检测specs部分
                if line == 'specs:':
                    in_specs = True
                    continue
                elif line.startswith('PLATFORMS') or line.startswith('DEPENDENCIES'):
                    in_specs = False
                    continue

                if in_specs and line:
                    # 匹配格式: gem-name (version)
                    match = re.match(r'^([a-zA-Z0-9_-]+)\s+\(([^)]+)\)', line)
                    if match:
                        gem_name, version = match.groups()
                        dependencies.append(f"{gem_name} {version}")

        return dependencies

    except Exception as e:
        print(f"处理Gemfile.lock失败 ({gemfile_lock_path}): {str(e)}")
        return []

def find_gemfiles(root_dir):
    """递归查找所有Gemfile"""
    gemfiles = []
    for dirpath, _, filenames in os.walk(root_dir):
        # 优先使用Gemfile.lock（版本更精确）
        if 'Gemfile.lock' in filenames:
            gemfiles.append(('lock', os.path.join(dirpath, 'Gemfile.lock')))
        elif 'Gemfile' in filenames:
            gemfiles.append(('gemfile', os.path.join(dirpath, 'Gemfile')))
        # 也接受小写
        elif 'gemfile.lock' in filenames:
            gemfiles.append(('lock', os.path.join(dirpath, 'gemfile.lock')))
        elif 'gemfile' in filenames:
            gemfiles.append(('gemfile', os.path.join(dirpath, 'gemfile')))

    return gemfiles

def collect_ruby_dependencies(project_path):
    """收集Ruby项目的所有依赖"""
    gemfiles = find_gemfiles(project_path)

    if not gemfiles:
        print(f"No Gemfile or Gemfile.lock files found in {project_path}")
        return []

    unique_dependencies = set()

    for file_type, file_path in gemfiles:
        if file_type == 'lock':
            dependencies = parse_gemfile_lock(file_path)
        else:
            dependencies = parse_gemfile(file_path)

        unique_dependencies.update(dependencies)

    print(f"Found {len(unique_dependencies)} unique Ruby dependencies")
    return llm_communicate(unique_dependencies, system_prompt, 10)


if __name__ == "__main__":
    project_path = input("请输入Ruby项目文件夹路径: ").strip()

    if not os.path.isdir(project_path):
        print("错误：输入的项目路径不存在或不是目录")
    else:
        result = collect_ruby_dependencies(project_path)
        print(f"处理完成，共 {len(result)} 个依赖")
