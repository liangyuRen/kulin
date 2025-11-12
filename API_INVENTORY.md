# Flask爬虫系统 - API接口清单

**系统概览**: VulSystem Crawler - 漏洞爬虫系统，用于从多个源爬取漏洞数据、解析项目依赖、利用LLM进行漏洞分析和修复建议

**基础信息**:
- 框架: Flask + Flask-CORS
- 项目路径: `/root/vulsystem-crawler/`
- 主应用文件: `app.py`
- 服务器模式: debug=True

---

## 1. 漏洞爬虫接口 (Vulnerabilities)

### 1.1 获取GitHub安全公告
**端点**: `/vulnerabilities/github`

**HTTP方法**: GET

**功能描述**: 从GitHub安全公告页面爬取最新漏洞数据。支持分页爬取，自动去重，包含CVE和GHSA编号

**请求参数**: 无（URL参数）

**返回值**: 
```json
[
  {
    "vulnerabilityName": "漏洞摘要",
    "cveId": "CVE-2024-XXXX 或 GHSA-XXXX-XXXX-XXXX",
    "disclosureTime": "YYYY-MM-DD",
    "description": "GitHub Security Advisory: ... CVE编号: ... GHSA编号: ... 风险等级: ...",
    "riskLevel": "High|Medium|Low",
    "referenceLink": "https://github.com/advisories/...",
    "affectsWhitelist": 0,
    "isDelete": 0
  }
]
```

**实现细节**:
- 目标爬取数量: 20,000条
- 最大页数: 2,000页
- 自动去重机制，跳过连续5页无新数据
- 风险等级标准化: Moderate→Medium, Critical→High
- 数据验证和清理: 通过data_validator模块

**源代码**: `/root/vulsystem-crawler/web_crawler/github.py`

---

### 1.2 获取阿里云漏洞库(AVD)
**端点**: `/vulnerabilities/avd`

**HTTP方法**: GET

**功能描述**: 从阿里云漏洞库(Aliyun Vulnerability Database)爬取漏洞数据。当前仅爬取第一页，可扩展

**请求参数**: 无

**返回值**:
```json
[
  {
    "vulnerabilityName": "漏洞名称",
    "cveId": "CVE-2024-XXXX 或 AVD-ID",
    "description": "阿里云漏洞库收录的XXX类型漏洞，CVE编号: ...",
    "disclosureTime": "YYYY-MM-DD",
    "riskLevel": "High|Medium|Low",
    "referenceLink": "https://avd.aliyun.com/...",
    "affectsWhitelist": 0,
    "isDelete": 0
  }
]
```

**风险等级规则**:
- 包含 "远程代码执行|代码执行|命令执行|提权" → High
- 包含 "信息泄漏|信息披露|拒绝服务" → Low
- 其他 → Medium(默认)

**源代码**: `/root/vulsystem-crawler/web_crawler/avd.py`

---

### 1.3 获取NVD(国家漏洞库)数据
**端点**: `/vulnerabilities/nvd`

**HTTP方法**: GET

**功能描述**: 通过NVD官方API获取最新漏洞数据。采用API方式而非网页爬虫，更稳定可靠

**请求参数**: 无

**返回值**:
```json
[
  {
    "vulnerabilityName": "CVE-XXXX-XXXX 或漏洞描述摘要",
    "cveId": "CVE-XXXX-XXXX",
    "description": "完整的漏洞描述(英文)",
    "disclosureTime": "YYYY-MM-DD",
    "riskLevel": "High|Medium|Low",
    "referenceLink": "https://nvd.nist.gov/vuln/detail/CVE-XXXX-XXXX",
    "affectsWhitelist": 0,
    "isDelete": 0
  }
]
```

**风险等级规则** (基于CVSS v3.1评分):
- baseScore >= 7.0 → High
- 4.0 <= baseScore < 7.0 → Medium
- baseScore < 4.0 → Low

**特点**:
- 自动获取3页数据(共60条)
- 包含CVSS评分信息
- 多语言描述支持(优先英文)
- API不可用时提供fallback示例数据

**源代码**: `/root/vulsystem-crawler/web_crawler/nvd.py`

---

### 1.4 漏洞检测/标签识别
**端点**: `/vulnerabilities/detect`

**HTTP方法**: POST

**功能描述**: 使用TF-IDF和LLM技术检测漏洞与项目依赖库的关联关系，为漏洞添加标签

**请求头**: 
```
Content-Type: application/json
```

**请求参数** (JSON Body):
```json
{
  "language": "java|c",
  "white_list": [
    {
      "name": "库名称",
      "desc": "库描述"
    }
  ],
  "detect_strategy": "TinyModel|TinyModel-lev|TinyModel-cos|TinyModel-lcs|LLM|LLM-lev|LLM-cos|LLM-lcs|TinyModel-whiteList|LLM-whiteList",
  "cve_id": "CVE-XXXX-XXXX",
  "desc": "漏洞描述文本",
  "company": "公司名称(可选)",
  "similarityThreshold": 0.0-1.0
}
```

**返回值**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "cve_id": "CVE-XXXX-XXXX",
    "matched_libraries": [
      {
        "name": "库名称",
        "similarity": 0.85,
        "match_type": "TF-IDF|LLM"
      }
    ]
  }
}
```

**检测策略说明**:
- **TinyModel**: 轻量级TF-IDF匹配算法
- **TinyModel-lev**: TinyModel + 编辑距离(Levenshtein)混合
- **TinyModel-cos**: TinyModel + 余弦相似度(Cosine)混合  
- **TinyModel-lcs**: TinyModel + 最长公共子序列(LCS)混合
- **LLM**: 使用大语言模型进行智能匹配(默认Qwen)
- **LLM-lev/cos/lcs**: LLM结合相似度算法
- **TinyModel-whiteList**: TinyModel仅匹配白名单库
- **LLM-whiteList**: LLM仅匹配白名单库

**源代码**: `/root/vulsystem-crawler/VulLibGen/getLabels.py`

---

### 1.5 服务健康检查
**端点**: `/vulnerabilities/test`

**HTTP方法**: POST, GET

**功能描述**: 测试服务是否正常运行

**请求参数**: 无

**返回值**:
```json
{
  "code": 200,
  "message": "Server is running normally",
  "status": "OK"
}
```

---

## 2. LLM智能分析接口 (LLM)

### 2.1 LLM查询接口
**端点**: `/llm/query`

**HTTP方法**: GET

**功能描述**: 发送任意查询到大语言模型，获取AI分析结果。支持多个LLM模型

**请求参数** (URL查询字符串):
```
query=<查询文本>  (必需)
model=qwen|deepseek  (可选，默认qwen)
```

**返回值** (成功200):
```json
{
  "message": "SUCCESS",
  "obj": "LLM模型的回复文本",
  "code": 200
}
```

**返回值** (参数错误400):
```json
{
  "code": 400,
  "message": "Missing required parameter 'query'"
}
```

**返回值** (模型不存在400):
```json
{
  "code": 400,
  "message": "不支持的模型: xxx，可用模型: ['qwen', 'deepseek']"
}
```

**支持的模型**:
- **qwen**: Qwen-Max (通义千问)
- **deepseek**: DeepSeek-R1 (深度求索)

**使用示例**:
```
GET /llm/query?query=如何修复SQL注入漏洞&model=qwen
```

**源代码**: `/root/vulsystem-crawler/llm/llm.py`

---

### 2.2 获取漏洞修复建议
**端点**: `/llm/repair/suggestion`

**HTTP方法**: POST

**功能描述**: 根据漏洞信息(名称、描述、相关代码)，使用LLM生成修复建议

**请求头**:
```
Content-Type: application/x-www-form-urlencoded
```

**请求参数** (表单数据):
```
vulnerability_name=漏洞名称(可选)
vulnerability_desc=漏洞描述(可选)
related_code=相关代码段(可选)
model=qwen|deepseek(可选，默认qwen)
```

**参数约束**:
- 至少需要提供: vulnerability_name、vulnerability_desc、related_code 之一
- 否则返回400错误

**返回值** (成功200):
```json
{
  "code": 200,
  "message": "success",
  "obj": {
    "fix_advise": "LLM生成的修复建议文本"
  }
}
```

**返回值** (参数不足400):
```json
{
  "code": 400,
  "message": "至少需要提供漏洞名称、描述或相关代码之一"
}
```

**返回值** (模型不存在400):
```json
{
  "code": 400,
  "message": "不支持的模型: xxx，可用模型: ['qwen', 'deepseek']"
}
```

**返回值** (处理错误400):
```json
{
  "code": 400,
  "message": "生成建议时出错: <错误信息>"
}
```

**构造的完整查询格式**:
```
漏洞名称: XXX

漏洞描述: YYY

相关代码:
ZZZ

根据以上信息，生成修复建议：
```

**源代码**: `/root/vulsystem-crawler/app.py` (lines 92-142)

---

## 3. 项目解析接口 (Parse)

### 3.1 Java项目解析(Maven/Gradle)
**端点**: `/parse/pom_parse`

**HTTP方法**: GET

**功能描述**: 解析Java项目的pom.xml文件，提取所有Maven依赖及版本号

**请求参数** (URL查询字符串):
```
project_folder=<项目文件夹路径>  (必需，需要URL编码)
```

**返回值**:
```json
{
  "code": 200,
  "data": [
    {
      "name": "org.apache.commons:commons-lang3",
      "version": "3.12.0",
      "group": "org.apache.commons",
      "artifact": "commons-lang3"
    }
  ]
}
```

**处理逻辑**:
- 递归查找所有pom.xml文件
- 提取<dependency>标签中的版本号
- 解析Maven依赖树结构
- 处理URL编码的路径

**源代码**: `/root/vulsystem-crawler/parase/pom_parse.py`

---

### 3.2 C/C++项目解析
**端点**: `/parse/c_parse`

**HTTP方法**: GET

**功能描述**: 解析C/C++项目的依赖文件，提取库依赖信息(支持CMake, pkg-config等)

**请求参数**:
```
project_folder=<项目路径>  (必需，URL编码)
```

**返回值**:
```json
{
  "code": 200,
  "data": [
    {
      "name": "zlib",
      "version": "1.2.11",
      "type": "library"
    }
  ]
}
```

**源代码**: `/root/vulsystem-crawler/parase/c_parse.py`

---

### 3.3 Go项目解析
**端点**: `/parse/go_parse`

**HTTP方法**: GET

**功能描述**: 解析Go项目的go.mod文件，提取所有Go模块依赖

**请求参数**:
```
project_folder=<项目路径>  (必需，URL编码)
```

**返回值**:
```json
{
  "code": 200,
  "data": [
    {
      "name": "github.com/user/repo",
      "version": "v1.0.0",
      "direct": true
    }
  ]
}
```

**源代码**: `/root/vulsystem-crawler/parase/go_parse.py`

---

### 3.4 JavaScript/Node.js项目解析
**端点**: `/parse/javascript_parse`

**HTTP方法**: GET

**功能描述**: 解析JavaScript/Node.js项目的package.json和package-lock.json，提取NPM/Yarn依赖

**请求参数**:
```
project_folder=<项目路径>  (必需，URL编码)
```

**返回值**:
```json
{
  "code": 200,
  "data": [
    {
      "name": "lodash",
      "version": "4.17.21",
      "dev": false
    }
  ]
}
```

**源代码**: `/root/vulsystem-crawler/parase/javascript_parse.py`

---

### 3.5 Python项目解析
**端点**: `/parse/python_parse`

**HTTP方法**: GET

**功能描述**: 解析Python项目的requirements.txt和setup.py，提取PyPI依赖

**请求参数**:
```
project_folder=<项目路径>  (必需，URL编码)
```

**返回值**:
```json
{
  "code": 200,
  "data": [
    {
      "name": "requests",
      "version": "2.28.1",
      "extras": []
    }
  ]
}
```

**源代码**: `/root/vulsystem-crawler/parase/python_parse.py`

---

### 3.6 PHP项目解析
**端点**: `/parse/php_parse`

**HTTP方法**: GET

**功能描述**: 解析PHP项目的composer.json和composer.lock，提取Composer依赖

**请求参数**:
```
project_folder=<项目路径>  (必需，URL编码)
```

**返回值**:
```json
{
  "code": 200,
  "data": [
    {
      "name": "monolog/monolog",
      "version": "2.3.5"
    }
  ]
}
```

**源代码**: `/root/vulsystem-crawler/parase/php_parse.py`

---

### 3.7 Ruby项目解析
**端点**: `/parse/ruby_parse`

**HTTP方法**: GET

**功能描述**: 解析Ruby项目的Gemfile和Gemfile.lock，提取RubyGems依赖

**请求参数**:
```
project_folder=<项目路径>  (必需，URL编码)
```

**返回值**:
```json
{
  "code": 200,
  "data": [
    {
      "name": "rails",
      "version": "6.1.4"
    }
  ]
}
```

**源代码**: `/root/vulsystem-crawler/parase/ruby_parse.py`

---

### 3.8 Rust项目解析
**端点**: `/parse/rust_parse`

**HTTP方法**: GET

**功能描述**: 解析Rust项目的Cargo.toml和Cargo.lock，提取Crates.io依赖

**请求参数**:
```
project_folder=<项目路径>  (必需，URL编码)
```

**返回值**:
```json
{
  "code": 200,
  "data": [
    {
      "name": "serde",
      "version": "1.0.130",
      "features": ["derive"]
    }
  ]
}
```

**源代码**: `/root/vulsystem-crawler/parase/rust_parse.py`

---

### 3.9 Erlang项目解析
**端点**: `/parse/erlang_parse`

**HTTP方法**: GET

**功能描述**: 解析Erlang项目的rebar.config和rebar.lock，提取依赖

**请求参数**:
```
project_folder=<项目路径>  (必需，URL编码)
```

**返回值**:
```json
{
  "code": 200,
  "data": [
    {
      "name": "cowboy",
      "version": "2.8.0"
    }
  ]
}
```

**源代码**: `/root/vulsystem-crawler/parase/erlang_parse.py`

---

### 3.10 统一项目解析 (多语言自动检测)
**端点**: `/parse/unified_parse`

**HTTP方法**: GET

**功能描述**: 智能检测项目中的编程语言，自动调用对应的解析器，统一返回所有依赖数据，无需指定语言

**请求参数** (URL查询字符串):
```
project_folder=<项目文件夹路径>  (必需，URL编码)
project_id=<项目在数据库中的ID>   (可选，整数)
```

**返回值** (成功200):
```json
{
  "code": 200,
  "message": "SUCCESS",
  "summary": {
    "project_path": "/path/to/project",
    "project_id": 123,
    "detected_languages": ["java", "go", "python"],
    "primary_language": "java",
    "total_dependencies": 206,
    "parse_results": {
      "java": {
        "status": "success",
        "count": 25
      },
      "go": {
        "status": "success",
        "count": 181
      },
      "python": {
        "status": "success",
        "count": 5
      }
    },
    "timestamp": "2024-11-10T12:34:56.789123"
  },
  "dependencies": [
    {
      "name": "org.apache.commons:commons-lang3",
      "version": "3.12.0",
      "language": "java",
      "package_manager": "maven",
      "project_id": 123
    },
    {
      "name": "github.com/user/repo",
      "version": "v1.0.0",
      "language": "go",
      "package_manager": "go_modules"
    }
  ],
  "obj": {
    "summary": {...},
    "dependencies": [...],
    "total_dependencies": 206
  }
}
```

**返回值** (路径不存在400):
```json
{
  "code": 400,
  "message": "Project folder does not exist: /invalid/path",
  "summary": null,
  "dependencies": []
}
```

**返回值** (无任何语言检测到200):
```json
{
  "code": 200,
  "message": "No programming languages detected",
  "summary": {
    "project_path": "/path/to/project",
    "project_id": null,
    "detected_languages": [],
    "primary_language": null,
    "total_dependencies": 0,
    "parse_results": {}
  },
  "dependencies": []
}
```

**返回值** (解析出错500):
```json
{
  "code": 500,
  "message": "Error during unified parsing: <错误信息>",
  "summary": null,
  "dependencies": [],
  "error": "<详细错误信息>"
}
```

**语言优先级** (按检测的语言优先级依次解析):
1. Java (Maven/Gradle)
2. Go
3. JavaScript/TypeScript (Node.js)
4. Python
5. PHP
6. Ruby
7. Rust
8. Erlang
9. C/C++

**特点**:
- 自动检测项目中的所有编程语言
- 为每个依赖添加语言和包管理器标签
- 解析失败时继续处理其他语言，不中断整个流程
- 详细的解析结果统计
- 支持关联到数据库中的项目ID

**源代码**: `/root/vulsystem-crawler/app.py` (lines 191-393)

---

## 4. API通用信息

### 4.1 跨域请求 (CORS)
所有接口都支持跨域请求，已启用CORS中间件:
```python
CORS(app)
```

### 4.2 异常处理规范
所有接口遵循统一的错误响应格式:
```json
{
  "code": <HTTP状态码>,
  "message": "错误描述信息",
  "data": null 或 错误详情
}
```

### 4.3 调用示例

#### cURL示例

**GitHub漏洞爬取**:
```bash
curl http://localhost:5000/vulnerabilities/github
```

**LLM查询**:
```bash
curl "http://localhost:5000/llm/query?query=如何修复XSS漏洞&model=qwen"
```

**漏洞修复建议**:
```bash
curl -X POST http://localhost:5000/llm/repair/suggestion \
  -d "vulnerability_name=SQL注入" \
  -d "vulnerability_desc=用户输入未过滤" \
  -d "related_code=SELECT * FROM users WHERE id=\$_GET['id']" \
  -d "model=deepseek"
```

**Java项目解析**:
```bash
curl "http://localhost:5000/parse/pom_parse?project_folder=%2Fhome%2Fuser%2Fmy-app"
```

**统一项目解析**:
```bash
curl "http://localhost:5000/parse/unified_parse?project_folder=%2Fhome%2Fuser%2Fmy-project&project_id=123"
```

#### Python示例

```python
import requests
import json

# 1. 获取GitHub漏洞
url = "http://localhost:5000/vulnerabilities/github"
response = requests.get(url)
print(response.json())

# 2. LLM查询
params = {
    "query": "CVE-2024-1234的修复方案",
    "model": "qwen"
}
response = requests.get("http://localhost:5000/llm/query", params=params)
print(response.json())

# 3. 修复建议
data = {
    "vulnerability_name": "SQL注入漏洞",
    "vulnerability_desc": "用户输入未经验证直接拼接SQL语句",
    "related_code": "query = f\"SELECT * FROM users WHERE id={user_id}\"",
    "model": "deepseek"
}
response = requests.post("http://localhost:5000/llm/repair/suggestion", data=data)
print(response.json())

# 4. Java项目解析
import urllib.parse
project_path = "/home/user/my-maven-project"
encoded_path = urllib.parse.quote(project_path)
url = f"http://localhost:5000/parse/pom_parse?project_folder={encoded_path}"
response = requests.get(url)
print(response.json())

# 5. 统一项目解析(多语言)
project_path = "/home/user/mixed-language-project"
encoded_path = urllib.parse.quote(project_path)
url = f"http://localhost:5000/parse/unified_parse?project_folder={encoded_path}&project_id=123"
response = requests.get(url)
print(response.json())
```

### 4.4 性能与限制

| 接口 | 超时时间 | 最大数据量 | 注意事项 |
|------|--------|----------|--------|
| /vulnerabilities/github | 无限制 | 20,000条 | 爬虫速率受GitHub限制，需要1.5秒/页延迟 |
| /vulnerabilities/avd | 15秒 | 单页 | 当前仅支持第一页，可扩展 |
| /vulnerabilities/nvd | 30秒 | 3页(60条) | 使用官方API，稳定可靠 |
| /llm/query | 无限制 | 无限制 | 取决于LLM服务响应时间 |
| /llm/repair/suggestion | 无限制 | 无限制 | 取决于LLM服务响应时间 |
| /parse/* | 无限制 | 无限制 | 大型项目可能耗时较长 |
| /parse/unified_parse | 无限制 | 无限制 | 多语言解析，按语言依次处理 |

### 4.5 数据验证
爬虫接口数据会自动进行验证和清理:
- 必填字段检查
- 数据类型验证
- 危险字符过滤(HTML标签等)
- 去重处理

验证器位置: `/root/vulsystem-crawler/web_crawler/data_validator.py`

---

## 5. 系统架构

### 5.1 核心模块结构
```
vulsystem-crawler/
├── app.py                          # Flask主应用，所有路由定义
├── web_crawler/                    # 网页爬虫模块
│   ├── github.py                   # GitHub安全公告爬虫
│   ├── nvd.py                      # NVD漏洞库爬虫/API调用
│   ├── avd.py                      # 阿里云漏洞库爬虫
│   └── data_validator.py           # 数据验证和清理
├── parase/                         # 项目依赖解析模块
│   ├── pom_parse.py                # Java/Maven解析
│   ├── c_parse.py                  # C/C++解析
│   ├── go_parse.py                 # Go解析
│   ├── javascript_parse.py         # JavaScript解析
│   ├── python_parse.py             # Python解析
│   ├── php_parse.py                # PHP解析
│   ├── ruby_parse.py               # Ruby解析
│   ├── rust_parse.py               # Rust解析
│   ├── erlang_parse.py             # Erlang解析
│   ├── project_detector.py         # 语言检测模块
│   └── unified_parser.py           # 统一解析器
├── llm/                            # LLM集成模块
│   └── llm.py                      # 多模型LLM客户端(Qwen, DeepSeek等)
├── VulLibGen/                      # 漏洞库生成和标签识别
│   ├── getLabels.py                # 漏洞-库匹配标签识别
│   └── tf_idf/                     # TF-IDF匹配算法
│       ├── tf_idf.py               # 核心TF-IDF实现
│       ├── threshold_cal.py        # 相似度阈值计算
│       ├── clean_text.py           # 文本清理
│       └── ...
└── requirements.txt                # Python依赖

```

### 5.2 配置信息
**模型配置** (app.py lines 39-43):
```python
model_clients = {
    "qwen": QwenClient(model_name="qwen-max"),
    "deepseek": DeepSeekClient(model_name="deepseek-r1"),
}
```

**可用LLM模型**:
- Qwen-Max (阿里通义千问)
- DeepSeek-R1 (深度求索)
- 可扩展支持: Llama3.3-70b-instruct (已注释)

---

## 6. 快速参考表

| 功能分类 | 端点 | 方法 | 功能简述 |
|---------|------|------|--------|
| **漏洞爬虫** | `/vulnerabilities/github` | GET | GitHub安全公告爬虫 |
| | `/vulnerabilities/avd` | GET | 阿里云漏洞库爬虫 |
| | `/vulnerabilities/nvd` | GET | NVD官方API数据获取 |
| | `/vulnerabilities/detect` | POST | 漏洞-库关联检测 |
| | `/vulnerabilities/test` | GET/POST | 服务健康检查 |
| **LLM服务** | `/llm/query` | GET | 通用LLM查询接口 |
| | `/llm/repair/suggestion` | POST | 漏洞修复建议生成 |
| **Java依赖解析** | `/parse/pom_parse` | GET | Maven/Gradle依赖解析 |
| **C/C++依赖解析** | `/parse/c_parse` | GET | C/C++依赖解析 |
| **Go依赖解析** | `/parse/go_parse` | GET | Go模块依赖解析 |
| **JavaScript依赖解析** | `/parse/javascript_parse` | GET | NPM/Yarn依赖解析 |
| **Python依赖解析** | `/parse/python_parse` | GET | PyPI依赖解析 |
| **PHP依赖解析** | `/parse/php_parse` | GET | Composer依赖解析 |
| **Ruby依赖解析** | `/parse/ruby_parse` | GET | RubyGems依赖解析 |
| **Rust依赖解析** | `/parse/rust_parse` | GET | Cargo依赖解析 |
| **Erlang依赖解析** | `/parse/erlang_parse` | GET | Rebar依赖解析 |
| **统一项目解析** | `/parse/unified_parse` | GET | 多语言自动检测与解析 |

---

**生成时间**: 2024-11-10  
**系统**: VulSystem Crawler Flask应用  
**维护者**: VulSystem Team
