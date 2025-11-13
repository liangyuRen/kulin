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

from async_tasks import task_manager

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

@app.route('/llm/repair/suggestion', methods=['POST'])  # 异步修复建议接口
@cross_origin()
def get_repair_suggestion():
    # 获取参数
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

    # 定义后台任务函数
    def generate_repair_advice():
        # 构造优化的查询内容
        prompt_parts = []
        if vulnerability_name:
            prompt_parts.append(f"漏洞: {vulnerability_name}")
        if vulnerability_desc:
            prompt_parts.append(f"描述: {vulnerability_desc}")
        if related_code:
            code_preview = related_code[:500] + ("..." if len(related_code) > 500 else "")
            prompt_parts.append(f"代码: {code_preview}")

        prompt_parts.append("请提供简洁的修复建议（3-5点）：")
        full_query = "\n".join(prompt_parts)

        try:
            # 获取对应的模型客户端
            client = model_clients[model]
            # 调用模型生成建议
            result = client.Think([{"role": "user", "content": full_query}])
            return {
                "code": 200,
                "message": "success",
                "obj": {
                    "fix_advise": result
                }
            }
        except KeyError:
            raise Exception(f"不支持的模型：{model}，可用模型：{list(model_clients.keys())}")
        except Exception as e:
            raise Exception(f"生成建议时出错：{str(e)}")

    # 提交异步任务
    task_id = task_manager.create_task(generate_repair_advice)

    # 立即返回任务 ID 和轮询地址
    return jsonify({
        "code": 202,
        "message": "Task submitted",
        "task_id": task_id,
        "status_url": f"/llm/repair/suggestion/status/{task_id}",
        "result_url": f"/llm/repair/suggestion/result/{task_id}"
    }), 202


@app.route('/llm/repair/suggestion/status/<task_id>', methods=['GET'])
@cross_origin()
def get_repair_suggestion_status(task_id):
    """获取修复建议任务状态"""
    task_status = task_manager.get_task_status(task_id)

    if task_status['status'] == 'not_found':
        return jsonify(task_status), 404

    return jsonify({
        "code": 200,
        "task_id": task_id,
        "status": task_status['status'],
        "created_at": task_status['created_at'],
        "completed_at": task_status['completed_at']
    }), 200


@app.route('/llm/repair/suggestion/result/<task_id>', methods=['GET'])
@cross_origin()
def get_repair_suggestion_result(task_id):
    """获取修复建议任务结果"""
    task_status = task_manager.get_task_status(task_id)

    if task_status['status'] == 'not_found':
        return jsonify({
            "code": 404,
            "message": f"Task {task_id} not found"
        }), 404

    if task_status['status'] != 'completed':
        return jsonify({
            "code": 202,
            "message": f"Task still {task_status['status']}, please check status endpoint",
            "task_id": task_id,
            "status": task_status['status'],
            "status_url": f"/llm/repair/suggestion/status/{task_id}"
        }), 202

    if task_status['error']:
        return jsonify({
            "code": 500,
            "message": "Task failed",
            "error": task_status['error']
        }), 500

    # 返回任务结果
    result = task_status['result']
    result['task_id'] = task_id
    result['completed_at'] = task_status['completed_at']
    return jsonify(result), 200


@app.route('/parse/pom_parse', methods=['GET'])
def pom_parse():
    # project_folder = request.args.get("project_folder")
    project_folder = urllib.parse.unquote(request.args.get("project_folder"))
    return process_projects(project_folder)

# @app.route('/parse/c_parse',methods=['GET'])
# def c_parse():
#     project_folder = urllib.parse.unquote(request.args.get("project_folder"))
#     return  collect_dependencies(project_folder)

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

@app.route('/parse/get_primary_language', methods=['GET'])
@cross_origin()
def get_primary_language():
    """
    获取项目的主要编程语言 - 简化版本，仅返回单一语言
    使用优化的检测器以获得更高的准确率 (精准识别 PHP、JavaScript 等)

    Parameters:
        project_folder: 项目文件夹路径 (必需)
        use_optimized: 是否使用优化检测器 (可选, 默认 true)

    Returns:
        {
            "code": 200,
            "message": "SUCCESS",
            "project_path": "...",
            "language": "java",
            "confidence": "high",
            "detection_score": 1000.5,
            "timestamp": "..."
        }
    """
    try:
        # 获取参数
        project_folder = request.args.get("project_folder")
        use_optimized = request.args.get("use_optimized", "true").lower() == "true"

        if not project_folder:
            return jsonify({
                "code": 400,
                "message": "Missing required parameter 'project_folder'",
                "language": "other"
            }), 400

        project_folder = urllib.parse.unquote(project_folder)

        # 验证项目路径是否存在
        if not os.path.isdir(project_folder):
            return jsonify({
                "code": 400,
                "message": f"Project folder does not exist: {project_folder}",
                "language": "other"
            }), 400

        print(f"[获取主要语言] 开始检测项目: {project_folder}")
        print(f"[获取主要语言] 使用优化检测器: {use_optimized}")

        # 选择检测器
        if use_optimized:
            from parase.optimized_project_detector import OptimizedProjectDetector
            detector = OptimizedProjectDetector(project_folder)
        else:
            from parase.project_detector import ProjectDetector
            detector = ProjectDetector(project_folder)

        detected_languages = detector.detect()

        # 获取主要语言，如果没有检测到则返回 "other"
        primary_language = detector.get_primary_language() or "other"

        print(f"[获取主要语言] 检测到的主要语言: {primary_language}")

        # 获取检测得分 (仅优化检测器有)
        detection_score = 0
        if use_optimized and hasattr(detector, 'get_detailed_summary'):
            summary = detector.get_detailed_summary()
            if summary['languages']:
                detection_score = summary['languages'][0][1]

        # 支持的语言列表
        supported_languages = [
            'java', 'go', 'python', 'javascript', 'php', 'ruby', 'rust', 'erlang',
            'kotlin', 'scala', 'swift', 'csharp', 'typescript', 'cpp', 'c', 'groovy', 'android'
        ]

        # 如果检测到的语言不在支持列表中，返回 "other"
        if primary_language != "other" and primary_language not in supported_languages:
            primary_language = "other"

        # 获取置信度
        confidence = "low"
        if use_optimized:
            # 根据得分判断置信度
            if detection_score >= 500:
                confidence = "high"
            elif detection_score >= 200:
                confidence = "medium"
            else:
                confidence = "low"
        elif hasattr(detector, '_get_overall_confidence'):
            confidence = detector._get_overall_confidence()

        # 构造返回结果
        result = {
            "code": 200,
            "message": "SUCCESS",
            "project_path": project_folder,
            "language": primary_language,
            "confidence": confidence,
            "detection_score": detection_score,
            "supported_languages": supported_languages,
            "timestamp": datetime.now().isoformat()
        }

        return jsonify(result), 200

    except Exception as e:
        print(f"[获取主要语言] 错误: {str(e)}")
        import traceback
        traceback.print_exc()

        return jsonify({
            "code": 500,
            "message": f"Error during language detection: {str(e)}",
            "language": "other"
        }), 500


@app.route('/parse/detect_languages', methods=['GET'])
@cross_origin()
def detect_languages():
    """
    语言检测接口 - 检测项目中使用的编程语言

    Parameters:
        project_folder: 项目文件夹路径 (必需)

    Returns:
        {
            "code": 200,
            "message": "SUCCESS",
            "project_path": "...",
            "detected_languages": ["java", "go"],
            "primary_language": "java",
            "language_details": {
                "java": {
                    "files": ["/path/to/pom.xml"],
                    "package_manager": "maven",
                    "priority": 1
                },
                "go": {
                    "files": ["/path/to/go.mod"],
                    "package_manager": "go",
                    "priority": 1
                }
            }
        }
    """
    try:
        # 获取参数
        project_folder = request.args.get("project_folder")

        if not project_folder:
            return jsonify({
                "code": 400,
                "message": "Missing required parameter 'project_folder'"
            }), 400

        project_folder = urllib.parse.unquote(project_folder)

        # 验证项目路径是否存在
        if not os.path.isdir(project_folder):
            return jsonify({
                "code": 400,
                "message": f"Project folder does not exist: {project_folder}"
            }), 400

        print(f"[语言检测] 开始检测项目: {project_folder}")

        # 创建ProjectDetector进行语言检测
        from parase.project_detector import ProjectDetector
        detector = ProjectDetector(project_folder)
        detected_languages = detector.detect()

        if not detected_languages:
            return jsonify({
                "code": 200,
                "message": "No programming languages detected",
                "project_path": project_folder,
                "detected_languages": [],
                "primary_language": None,
                "language_details": {}
            }), 200

        print(f"[语言检测] 检测到语言: {list(detected_languages.keys())}")

        # 构造返回结果
        result = {
            "code": 200,
            "message": "SUCCESS",
            "project_path": project_folder,
            "detected_languages": detector.get_detected_languages(),
            "primary_language": detector.get_primary_language(),
            "language_details": detected_languages,
            "timestamp": datetime.now().isoformat()
        }

        return jsonify(result), 200

    except Exception as e:
        print(f"[语言检测] 错误: {str(e)}")
        import traceback
        traceback.print_exc()

        return jsonify({
            "code": 500,
            "message": f"Error during language detection: {str(e)}"
        }), 500


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
    # 使用 Flask 开发服务器，禁用调试以避免自动重加载
    # 使用 threaded=True 支持并发请求
    app.run(debug=False, threaded=True, host='127.0.0.1', port=5000)
