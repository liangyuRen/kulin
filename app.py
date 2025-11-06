# app.py
import os
import urllib
import json
from datetime import datetime

import requests
from flask import Flask, jsonify, request
from flask import Flask, jsonify
# from crypt import methods

from flask import Flask
from flask import request, jsonify
from flask_cors import CORS

from flask import Flask
from flask_cors import CORS, cross_origin

app = Flask(__name__)
# r'/*' 是通配符，让本服务器所有的 URL 都允许跨域请求
CORS(app)
from llm.llm import QwenClient, DeepSeekClient, LlamaClient
from parase.c_parse import collect_dependencies
from parase.pom_parse import process_projects
from parase.go_parse import collect_go_dependencies
from parase.javascript_parse import collect_javascript_dependencies
from parase.python_parse import collect_python_dependencies
from parase.php_parse import collect_php_dependencies
from parase.ruby_parse import collect_ruby_dependencies
from parase.rust_parse import collect_rust_dependencies
from parase.erlang_parse import collect_erlang_dependencies
from parase.unified_parser import UnifiedProjectParser
from web_crawler import github
from web_crawler.avd import avd
from web_crawler.nvd import nvd
from VulLibGen.getLabels import getLabels


model_clients = {
    "qwen": QwenClient(model_name="qwen-max"),
    "deepseek": DeepSeekClient(model_name="deepseek-r1"),
    # "llama": LlamaClient(model_name="llama3.3-70b-instruct")
}

app = Flask(__name__)
CORS(app)


@app.route('/vulnerabilities/github', methods=['GET'])
def get_github_vulnerabilities():
    data = github.github()
    return jsonify(data)

@app.route('/vulnerabilities/avd', methods=['GET'])
def get_avd_vulnerabilities():
    data = avd()
    return jsonify(data)

@app.route('/vulnerabilities/nvd', methods=['GET'])
def get_nvd_vulnerabilities():
    data = nvd()
    return jsonify(data)


@app.route('/llm/query', methods=['GET'])
@cross_origin()
def get_llm_query():
    query = request.args.get("query")
    model = request.args.get("model")
    if model=='':
        model='qwen'

    if not query:
        return jsonify({"error": "Missing required parameter 'query'"}), 400
    if not model:
        return jsonify({"error": "Missing required parameter 'model'"}), 400

    try:
        client = model_clients[model]
        result = client.Think([{"role": "user", "content": query}])
        return jsonify({
            "message": "SUCCESS",
            "obj": result,
            "code":200
        })
    except Exception as e:
        return jsonify({
            "code": 400,
            "message": str(e)
        })

@app.route('/llm/repair/suggestion', methods=['POST'])  # 修正接口路径
@cross_origin()
def get_repair_suggestion():
    # 获取图片中要求的四个参数
    vulnerability_name = request.form.get("vulnerability_name")
    vulnerability_desc = request.form.get("vulnerability_desc")
    related_code = request.form.get("related_code")
    model = request.form.get("model", "qwen")  # 设置默认模型

    # 参数校验（至少需要漏洞相关信息）
    if not any([vulnerability_name, vulnerability_desc, related_code]):
        return jsonify({
            "code": 400,
            "message": "至少需要提供漏洞名称、描述或相关代码之一"
        }), 400

    # 构造完整的查询内容
    query_content = []
    if vulnerability_name:
        query_content.append(f"漏洞名称：{vulnerability_name}")
    if vulnerability_desc:
        query_content.append(f"漏洞描述：{vulnerability_desc}")
    if related_code:
        query_content.append(f"相关代码：\n{related_code}")
    query_content.append("\n根据以上信息，生成修复建议：")
    full_query = "\n\n".join(query_content)

    try:
        # 获取对应的模型客户端
        client = model_clients[model]
        # 调用模型生成建议
        result = client.Think([{"role": "user", "content": full_query}])

        # 按照接口要求构造响应格式
        return jsonify({
            "code": 200,
            "message": "success",
            "obj": {
                "fix_advise": result
            }
        })
    except KeyError:
        return jsonify({
            "code": 400,
            "message": f"不支持的模型：{model}，可用模型：{list(model_clients.keys())}"
        }), 400
    except Exception as e:
        return jsonify({
            "code": 400,
            "message": f"生成建议时出错：{str(e)}"
        }), 400


@app.route('/parse/pom_parse', methods=['GET'])
def pom_parse():
    # project_folder = request.args.get("project_folder")
    project_folder = urllib.parse.unquote(request.args.get("project_folder"))
    return process_projects(project_folder)

@app.route('/parse/c_parse',methods=['GET'])
def c_parse():
    project_folder = urllib.parse.unquote(request.args.get("project_folder"))
    return  collect_dependencies(project_folder)

@app.route('/parse/go_parse',methods=['GET'])
def go_parse():
    project_folder = urllib.parse.unquote(request.args.get("project_folder"))
    return collect_go_dependencies(project_folder)

@app.route('/parse/javascript_parse',methods=['GET'])
def javascript_parse():
    project_folder = urllib.parse.unquote(request.args.get("project_folder"))
    return collect_javascript_dependencies(project_folder)

@app.route('/parse/python_parse',methods=['GET'])
def python_parse():
    project_folder = urllib.parse.unquote(request.args.get("project_folder"))
    return collect_python_dependencies(project_folder)

@app.route('/parse/php_parse',methods=['GET'])
def php_parse():
    project_folder = urllib.parse.unquote(request.args.get("project_folder"))
    return collect_php_dependencies(project_folder)

@app.route('/parse/ruby_parse',methods=['GET'])
def ruby_parse():
    project_folder = urllib.parse.unquote(request.args.get("project_folder"))
    return collect_ruby_dependencies(project_folder)

@app.route('/parse/rust_parse',methods=['GET'])
def rust_parse():
    project_folder = urllib.parse.unquote(request.args.get("project_folder"))
    return collect_rust_dependencies(project_folder)

@app.route('/parse/erlang_parse',methods=['GET'])
def erlang_parse():
    project_folder = urllib.parse.unquote(request.args.get("project_folder"))
    return collect_erlang_dependencies(project_folder)

@app.route('/parse/unified_parse', methods=['GET'])
@cross_origin()
def unified_parse():
    """
    统一的项目解析端点 - 自动检测语言并进行多语言解析
    直接调用各种单语言解析函数

    Parameters:
        project_folder: 项目文件夹路径 (必需)
        project_id: 项目在数据库中的ID (可选)

    Returns:
        {
            "code": 200,
            "message": "SUCCESS",
            "summary": {
                "project_path": "...",
                "detected_languages": ["java", "go"],
                "primary_language": "java",
                "total_dependencies": 206,
                "parse_results": {
                    "java": {"status": "success", "count": 25},
                    "go": {"status": "success", "count": 181}
                }
            },
            "dependencies": [
                {
                    "name": "xxx",
                    "version": "1.0",
                    "language": "java",
                    "package_manager": "maven",
                    ...
                }
            ]
        }
    """
    try:
        # 获取参数
        project_folder = urllib.parse.unquote(request.args.get("project_folder"))
        project_id = request.args.get("project_id", type=int)

        if not project_folder:
            return jsonify({
                "code": 400,
                "message": "Missing required parameter 'project_folder'",
                "summary": None,
                "dependencies": []
            }), 400

        # 验证项目路径是否存在
        if not os.path.isdir(project_folder):
            return jsonify({
                "code": 400,
                "message": f"Project folder does not exist: {project_folder}",
                "summary": None,
                "dependencies": []
            }), 400

        print(f"[统一解析] 开始解析项目: {project_folder}")
        print(f"[统一解析] 项目ID: {project_id}")

        # 步骤1: 创建ProjectDetector进行语言检测
        from parase.project_detector import ProjectDetector
        detector = ProjectDetector(project_folder)
        detected_languages = detector.detect()

        if not detected_languages:
            return jsonify({
                "code": 200,
                "message": "No programming languages detected",
                "summary": {
                    "project_path": project_folder,
                    "project_id": project_id,
                    "detected_languages": [],
                    "primary_language": None,
                    "total_dependencies": 0,
                    "parse_results": {}
                },
                "dependencies": []
            }), 200

        print(f"[统一解析] 检测到语言: {list(detected_languages.keys())}")

        # 步骤2: 根据检测到的语言调用相应的解析函数
        all_dependencies = []
        parse_results = {}

        # 语言到解析函数的映射
        language_parsers = {
            'java': process_projects,
            'go': collect_go_dependencies,
            'javascript': collect_javascript_dependencies,
            'python': collect_python_dependencies,
            'php': collect_php_dependencies,
            'ruby': collect_ruby_dependencies,
            'rust': collect_rust_dependencies,
            'erlang': collect_erlang_dependencies,
            'c': collect_dependencies
        }

        # 按优先级遍历检测到的语言
        for language in detector.get_languages_by_priority():
            if language not in language_parsers:
                print(f"[统一解析] 跳过: {language} (无可用的解析器)")
                parse_results[language] = {
                    'status': 'skipped',
                    'count': 0,
                    'error': 'No parser available for this language'
                }
                continue

            try:
                print(f"[统一解析] 正在解析 {language}...")
                parser_func = language_parsers[language]

                # 调用解析函数
                result = parser_func(project_folder)

                # 解析结果可能是JSON字符串、jsonify返回值或字典/列表
                deps_list = []

                if isinstance(result, str):
                    # 如果是JSON字符串，先解析
                    try:
                        deps_data = json.loads(result)
                    except json.JSONDecodeError:
                        deps_data = result
                elif hasattr(result, 'get_json'):
                    # 如果是Flask Response对象
                    deps_data = result.get_json()
                else:
                    # 否则直接使用
                    deps_data = result

                # 提取依赖列表
                if isinstance(deps_data, dict):
                    deps_list = deps_data.get('obj', deps_data.get('data', []))
                elif isinstance(deps_data, list):
                    deps_list = deps_data
                else:
                    deps_list = []

                # 为每个依赖添加语言和包管理器标签
                package_manager = detector.get_package_manager(language)
                for dep in deps_list:
                    if isinstance(dep, dict):
                        dep['language'] = language
                        dep['package_manager'] = package_manager
                        if project_id:
                            dep['project_id'] = project_id

                all_dependencies.extend(deps_list)
                parse_results[language] = {
                    'status': 'success',
                    'count': len(deps_list)
                }
                print(f"[统一解析] ✓ {language}: 找到 {len(deps_list)} 个依赖")

            except Exception as e:
                print(f"[统一解析] ✗ {language}: 解析失败 - {str(e)}")
                parse_results[language] = {
                    'status': 'failed',
                    'count': 0,
                    'error': str(e)
                }

        print(f"[统一解析] 完成: 共找到 {len(all_dependencies)} 个依赖")

        # 步骤3: 构造返回结果
        summary = {
            "project_path": project_folder,
            "project_id": project_id,
            "detected_languages": list(detected_languages.keys()),
            "primary_language": detector.get_primary_language(),
            "total_dependencies": len(all_dependencies),
            "parse_results": parse_results,
            "timestamp": datetime.now().isoformat()
        }

        return jsonify({
            "code": 200,
            "message": "SUCCESS",
            "summary": summary,
            "dependencies": all_dependencies,
            "obj": {
                "summary": summary,
                "dependencies": all_dependencies,
                "total_dependencies": len(all_dependencies)
            }
        }), 200

    except Exception as e:
        print(f"[统一解析] 错误: {str(e)}")
        import traceback
        traceback.print_exc()

        return jsonify({
            "code": 500,
            "message": f"Error during unified parsing: {str(e)}",
            "summary": None,
            "dependencies": [],
            "error": str(e)
        }), 500

@app.route('/vulnerabilities/detect', methods=['POST'])
def detect_vulnerabilities():
    # 从请求体中获取JSON数据，添加null检查
    params = request.get_json()

    if params is None:
        params = {}

    # print(params)
    data = getLabels(params=params)
    try:
        print("data=")
        print(data)
    except UnicodeEncodeError:
        print("data with unicode encoding issues")
    return jsonify(data)

@app.route('/vulnerabilities/test', methods=['POST', 'GET'])
def test():
    return jsonify({
        "code": 200,
        "message": "Server is running normally",
        "status": "OK"
    })

if __name__ == '__main__':
    app.run(debug=True)
