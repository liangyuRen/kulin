import os
import re
import json

from parase.pom_parse import llm_communicate

system_prompt = """Generate technical descriptions in English for Erlang/OTP library dependencies following these rules:
1. For each dependency in format 'library-name version' (e.g. cowboy 2.9.0)
2. Describe core functionality and typical use cases in Erlang/OTP development
3. Include key features and popular usage scenarios
4. Use concise technical language (80-120 words)
5. Output JSON array format:
[{
    "name": "library identifier with version",
    "description": "generated text"
},...]

Example:
[{
    "name": "cowboy 2.9.0",
    "description": "A small, fast, and modern HTTP server for Erlang/OTP. Provides support for HTTP/1.1, HTTP/2, WebSocket protocols with routing, middleware, and streaming capabilities. Widely used for building REST APIs and real-time web applications..."
},{
    "name": "ranch 1.8.0",
    "description": "A socket acceptor pool for TCP protocols in Erlang. Handles connection pooling, protocol upgrades, and worker supervision. Used as the foundation for Cowboy and other network servers..."
}]"""

def parse_rebar_lock(rebar_lock_path):
    """解析rebar.lock文件并提取依赖信息"""
    try:
        dependencies = []

        with open(rebar_lock_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # rebar.lock是Erlang term格式
        # 匹配模式: {<<"package_name">>,{pkg,<<"package_name">>,<<"version">>},0}
        pattern = r'\{<<"([^"]+)">>,\{[^,]+,<<"[^"]+">>,<<"([^"]+)">>\}'
        matches = re.findall(pattern, content)

        for pkg_name, version in matches:
            dependencies.append(f"{pkg_name} {version}")

        return dependencies

    except Exception as e:
        print(f"处理rebar.lock失败 ({rebar_lock_path}): {str(e)}")
        return []

def parse_rebar_config(rebar_config_path):
    """解析rebar.config文件并提取依赖信息"""
    try:
        dependencies = []

        with open(rebar_config_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 查找deps部分
        # 匹配模式: {package, "version"} 或 {package, {git, ...}}
        # 简化处理，主要匹配版本格式
        pattern = r'\{([a-zA-Z0-9_]+),\s*"([^"]+)"\}'
        matches = re.findall(pattern, content)

        for pkg_name, version in matches:
            # 过滤掉看起来不像版本号的
            if re.match(r'^\d+\.\d+', version):
                dependencies.append(f"{pkg_name} {version}")
            else:
                dependencies.append(pkg_name)

        return dependencies

    except Exception as e:
        print(f"处理rebar.config失败 ({rebar_config_path}): {str(e)}")
        return []

def find_rebar_files(root_dir):
    """递归查找所有rebar文件"""
    rebar_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        # 优先使用rebar.lock（版本更精确）
        if 'rebar.lock' in filenames:
            rebar_files.append(('lock', os.path.join(dirpath, 'rebar.lock')))
        elif 'rebar.config' in filenames:
            rebar_files.append(('config', os.path.join(dirpath, 'rebar.config')))

    return rebar_files

def collect_erlang_dependencies(project_path):
    """收集Erlang项目的所有依赖"""
    rebar_files = find_rebar_files(project_path)

    if not rebar_files:
        print(f"No rebar.lock or rebar.config files found in {project_path}")
        return json.dumps([])

    unique_dependencies = set()

    for file_type, file_path in rebar_files:
        if file_type == 'lock':
            dependencies = parse_rebar_lock(file_path)
        else:
            dependencies = parse_rebar_config(file_path)

        unique_dependencies.update(dependencies)

    print(f"Found {len(unique_dependencies)} unique Erlang dependencies")
    return llm_communicate(unique_dependencies, system_prompt, 10)


if __name__ == "__main__":
    project_path = input("请输入Erlang项目文件夹路径: ").strip()

    if not os.path.isdir(project_path):
        print("错误：输入的项目路径不存在或不是目录")
    else:
        result = collect_erlang_dependencies(project_path)
        print(f"处理完成，共 {len(result)} 个依赖")
