import os
import re

from parase.pom_parse import llm_communicate

system_prompt = """Generate technical descriptions in English for Rust crate dependencies following these rules:
1. For each dependency in format 'crate-name version' (e.g. tokio 1.28.0)
2. Describe core functionality and typical use cases in Rust development
3. Include key features and popular usage scenarios
4. Use concise technical language (80-120 words)
5. Output JSON array format:
[{
    "name": "crate identifier with version",
    "description": "generated text"
},...]

Example:
[{
    "name": "tokio 1.28.0",
    "description": "An asynchronous runtime for Rust providing async/await support, multi-threaded work-stealing scheduler, and non-blocking I/O. Essential for building concurrent applications, network services, and async tasks. Powers many production systems..."
},{
    "name": "serde 1.0.163",
    "description": "A framework for serializing and deserializing Rust data structures efficiently and generically. Supports JSON, YAML, TOML, and many other formats. Widely used for data exchange, configuration files, and API communication..."
}]"""

def parse_cargo_toml(cargo_toml_path):
    """解析Cargo.toml并提取依赖信息"""
    try:
        dependencies = []
        in_dependencies = False

        with open(cargo_toml_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()

                # 检测[dependencies]或[dev-dependencies]部分
                if line.startswith('[dependencies]') or line.startswith('[dev-dependencies]'):
                    in_dependencies = True
                    continue
                elif line.startswith('['):
                    in_dependencies = False
                    continue

                if in_dependencies and '=' in line:
                    # 简单格式: crate = "1.0.0"
                    simple_match = re.match(r'^([a-zA-Z0-9_-]+)\s*=\s*"([^"]+)"', line)
                    if simple_match:
                        crate_name, version = simple_match.groups()
                        # 清理版本号
                        clean_version = version.lstrip('^~>=<')
                        dependencies.append(f"{crate_name} {clean_version}")
                        continue

                    # 复杂格式: crate = { version = "1.0.0", ... }
                    complex_match = re.match(r'^([a-zA-Z0-9_-]+)\s*=\s*\{', line)
                    if complex_match:
                        crate_name = complex_match.group(1)
                        # 尝试在同一行中找到version
                        version_match = re.search(r'version\s*=\s*"([^"]+)"', line)
                        if version_match:
                            version = version_match.group(1)
                            clean_version = version.lstrip('^~>=<')
                            dependencies.append(f"{crate_name} {clean_version}")
                        else:
                            dependencies.append(crate_name)

        return dependencies

    except Exception as e:
        print(f"处理Cargo.toml失败 ({cargo_toml_path}): {str(e)}")
        return []

def parse_cargo_lock(cargo_lock_path):
    """解析Cargo.lock并提取依赖信息"""
    try:
        dependencies = []
        current_package = None

        with open(cargo_lock_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()

                # 检测package块
                if line == '[[package]]':
                    current_package = {}
                    continue

                if current_package is not None:
                    # 提取name
                    name_match = re.match(r'name\s*=\s*"([^"]+)"', line)
                    if name_match:
                        current_package['name'] = name_match.group(1)

                    # 提取version
                    version_match = re.match(r'version\s*=\s*"([^"]+)"', line)
                    if version_match:
                        current_package['version'] = version_match.group(1)

                    # 如果遇到空行或新的section，保存当前package
                    if line == '' or line.startswith('['):
                        if 'name' in current_package and 'version' in current_package:
                            dependencies.append(
                                f"{current_package['name']} {current_package['version']}"
                            )
                        current_package = None if line.startswith('[') and line != '[[package]]' else current_package

        return dependencies

    except Exception as e:
        print(f"处理Cargo.lock失败 ({cargo_lock_path}): {str(e)}")
        return []

def find_cargo_files(root_dir):
    """递归查找所有Cargo文件"""
    cargo_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        # 优先使用Cargo.lock（版本更精确）
        if 'Cargo.lock' in filenames:
            cargo_files.append(('lock', os.path.join(dirpath, 'Cargo.lock')))
        elif 'Cargo.toml' in filenames:
            cargo_files.append(('toml', os.path.join(dirpath, 'Cargo.toml')))

    return cargo_files

def collect_rust_dependencies(project_path):
    """收集Rust项目的所有依赖"""
    cargo_files = find_cargo_files(project_path)

    if not cargo_files:
        print(f"No Cargo.toml or Cargo.lock files found in {project_path}")
        return []

    unique_dependencies = set()

    for file_type, file_path in cargo_files:
        if file_type == 'lock':
            dependencies = parse_cargo_lock(file_path)
        else:
            dependencies = parse_cargo_toml(file_path)

        unique_dependencies.update(dependencies)

    print(f"Found {len(unique_dependencies)} unique Rust dependencies")
    return llm_communicate(unique_dependencies, system_prompt, 10)


if __name__ == "__main__":
    project_path = input("请输入Rust项目文件夹路径: ").strip()

    if not os.path.isdir(project_path):
        print("错误：输入的项目路径不存在或不是目录")
    else:
        result = collect_rust_dependencies(project_path)
        print(f"处理完成，共 {len(result)} 个依赖")
