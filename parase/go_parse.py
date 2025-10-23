import os
import re

from parase.pom_parse import llm_communicate

system_prompt = """Generate technical descriptions in English for Go module dependencies following these rules:
1. For each dependency in format 'module-path version' (e.g. github.com/gin-gonic/gin v1.9.0)
2. Describe core functionality and typical use cases in Go programming
3. Include key features and popular usage scenarios
4. Use concise technical language (80-120 words)
5. Output JSON array format:
[{
    "name": "module identifier with version",
    "description": "generated text"
},...]

Example:
[{
    "name": "github.com/gin-gonic/gin v1.9.0",
    "description": "A high-performance HTTP web framework for Go, featuring a martini-like API with much better performance. Provides routing, middleware support, JSON validation, error management, and rendering capabilities. Widely used for building RESTful APIs and web services..."
},{
    "name": "gorm.io/gorm v1.25.0",
    "description": "A full-featured ORM library for Go, supporting associations, hooks, preloading, transactions, and auto-migrations. Compatible with MySQL, PostgreSQL, SQLite, and SQL Server. Enables developers to interact with databases using Go structs and chainable API..."
}]"""

def parse_go_mod_file(go_mod_path):
    """解析go.mod文件并提取依赖信息"""
    try:
        dependencies = []
        with open(go_mod_path, 'r', encoding='utf-8') as f:
            in_require_block = False

            for line in f:
                line = line.strip()

                # 检测require块的开始
                if line.startswith('require ('):
                    in_require_block = True
                    continue

                # 检测require块的结束
                if in_require_block and line == ')':
                    in_require_block = False
                    continue

                # 处理单行require语句: require github.com/xxx v1.0.0
                if line.startswith('require ') and not line.endswith('('):
                    match = re.match(r'require\s+(\S+)\s+(\S+)', line)
                    if match:
                        module_path, version = match.groups()
                        # 过滤掉indirect依赖（可选）
                        if '// indirect' not in line:
                            dependencies.append(f"{module_path} {version}")
                    continue

                # 处理require块内的依赖
                if in_require_block and line:
                    # 匹配格式: github.com/xxx v1.0.0 或 github.com/xxx v1.0.0 // indirect
                    match = re.match(r'(\S+)\s+(\S+)', line)
                    if match:
                        module_path, version = match.groups()
                        # 可选：过滤掉indirect依赖
                        if '// indirect' not in line:
                            dependencies.append(f"{module_path} {version}")

        return dependencies

    except Exception as e:
        print(f"处理go.mod文件失败 ({go_mod_path}): {str(e)}")
        return []

def find_go_mod_files(root_dir):
    """递归查找所有go.mod文件"""
    go_mod_files = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename == 'go.mod':
                go_mod_files.append(os.path.join(dirpath, filename))
    return go_mod_files

def collect_go_dependencies(project_path):
    """收集Go项目的所有依赖"""
    go_mod_files = find_go_mod_files(project_path)

    if not go_mod_files:
        print(f"No go.mod files found in {project_path}")
        return []

    unique_dependencies = set()
    for go_mod_path in go_mod_files:
        dependencies = parse_go_mod_file(go_mod_path)
        unique_dependencies.update(dependencies)

    print(f"Found {len(unique_dependencies)} unique Go dependencies")
    return llm_communicate(unique_dependencies, system_prompt, 10)


# 使用示例
if __name__ == "__main__":
    # 测试代码
    project_path = input("请输入Go项目文件夹路径: ").strip()

    if not os.path.isdir(project_path):
        print("错误：输入的项目路径不存在或不是目录")
    else:
        result = collect_go_dependencies(project_path)
        print(f"处理完成，共 {len(result)} 个依赖")
