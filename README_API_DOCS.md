# Flask爬虫系统 - API文档总索引

## 项目信息

**系统名称**: VulSystem Crawler (漏洞爬虫系统)  
**框架**: Flask + Flask-CORS  
**项目路径**: `/root/vulsystem-crawler/`  
**基础URL**: `http://localhost:5000`  
**文档生成时间**: 2024-11-10

---

## 快速开始

### 系统特性
- ✓ 3个数据源漏洞爬虫 (GitHub、AVD、NVD)
- ✓ 2个LLM模型集成 (Qwen、DeepSeek)
- ✓ 9种编程语言依赖解析
- ✓ 智能漏洞-库关联检测
- ✓ CORS跨域支持

### 总接口数: 17个

| 分类 | 接口数 | 功能 |
|-----|-------|------|
| 漏洞爬虫 | 5个 | GitHub、AVD、NVD爬虫及漏洞检测 |
| LLM服务 | 2个 | 智能查询和修复建议生成 |
| 依赖解析 | 10个 | 9种语言+统一解析 |

---

## 文档文件说明

### 1. **API_INVENTORY.md** (详细文档 - 21KB)
最完整的API文档，包含：
- 所有17个接口的详细说明
- 请求/响应示例和格式
- 参数详细说明
- cURL和Python调用示例
- 系统架构说明

**推荐用途**: 
- API开发和集成
- 功能详细了解
- 完整参考查阅

**查看方式**: 文本编辑器打开

---

### 2. **API_QUICK_REFERENCE.html** (可视化指南 - 30KB)
交互式HTML文档，包含：
- 分类导航界面
- 接口快速查询
- 代码示例高亮
- 响应式设计，支持手机访问

**推荐用途**:
- 快速查看接口列表
- 代码示例参考
- 在线浏览查阅

**查看方式**: 浏览器打开 (Chrome/Firefox/Edge)

---

### 3. **API_REFERENCE.json** (机器可读 - 12KB)
结构化的JSON格式API定义，包含：
- 端点元数据
- 参数类型和必需性
- HTTP方法
- 响应状态码
- 语言和包管理器列表

**推荐用途**:
- 自动化工具集成
- API网关配置
- 代码生成
- 文档自动化

**查看方式**: 任何文本编辑器或JSON查看器

---

### 4. **API_ENDPOINTS.csv** (表格汇总 - 4KB)
Excel/表格友好的格式，包含：
- 功能分类
- 端点路径
- HTTP方法
- 功能名称和描述
- 请求参数
- 响应码和数据源

**推荐用途**:
- 在Excel中导入和分析
- 创建API矩阵表
- 快速对比查看
- 项目规划

**查看方式**: Excel、Google Sheets 或 LibreOffice Calc

---

### 5. **API_DOCUMENTATION_SUMMARY.txt** (总结报告 - 17KB)
完整的技术文档报告，包含：
- 17个部分的详细分析
- 系统架构说明
- 性能指标
- 常见问题解答
- 技术栈说明
- 扩展建议

**推荐用途**:
- 系统整体了解
- 性能评估
- 故障排查
- 技术决策

**查看方式**: 文本编辑器或终端命令 (cat/less)

---

## 接口快速导航

### 漏洞爬虫接口

| 接口 | 方法 | 功能 | 数据源 |
|-----|------|------|--------|
| `/vulnerabilities/github` | GET | GitHub安全公告爬虫 | GitHub Advisories |
| `/vulnerabilities/avd` | GET | 阿里云漏洞库 | Aliyun AVD |
| `/vulnerabilities/nvd` | GET | 国家漏洞库 | NVD Official API |
| `/vulnerabilities/detect` | POST | 漏洞检测和标签识别 | TF-IDF + LLM |
| `/vulnerabilities/test` | GET/POST | 服务健康检查 | 本地 |

### LLM服务接口

| 接口 | 方法 | 功能 | 模型 |
|-----|------|------|------|
| `/llm/query` | GET | 通用LLM查询 | Qwen/DeepSeek |
| `/llm/repair/suggestion` | POST | 漏洞修复建议 | Qwen/DeepSeek |

### 项目解析接口

| 语言 | 接口 | 包管理器 | 配置文件 |
|-----|------|---------|---------|
| Java | `/parse/pom_parse` | Maven/Gradle | pom.xml |
| Go | `/parse/go_parse` | Go Modules | go.mod |
| JavaScript | `/parse/javascript_parse` | NPM/Yarn | package.json |
| Python | `/parse/python_parse` | pip/PyPI | requirements.txt |
| PHP | `/parse/php_parse` | Composer | composer.json |
| Ruby | `/parse/ruby_parse` | RubyGems | Gemfile |
| Rust | `/parse/rust_parse` | Cargo | Cargo.toml |
| Erlang | `/parse/erlang_parse` | Rebar | rebar.config |
| C/C++ | `/parse/c_parse` | CMake | CMakeLists.txt |
| 多语言 | `/parse/unified_parse` | 自动检测 | 自动检测 |

---

## 使用场景指南

### 场景1: 我需要获取最新漏洞信息
**推荐接口**:
- `/vulnerabilities/github` - 最全面(20000条)
- `/vulnerabilities/nvd` - 官方权威
- `/vulnerabilities/avd` - 国内数据源

**推荐文档**: `API_INVENTORY.md` 第1章节

---

### 场景2: 我需要分析某个漏洞的修复方案
**推荐接口**:
- `/llm/query` - 通用查询分析
- `/llm/repair/suggestion` - 生成修复建议

**推荐文档**: `API_QUICK_REFERENCE.html` LLM服务章节

---

### 场景3: 我需要解析项目的依赖
**推荐接口**:
- `/parse/unified_parse` - 推荐，自动检测所有语言
- 或各个语言的专用接口

**推荐文档**: `API_INVENTORY.md` 第3章节

---

### 场景4: 我需要检测漏洞与依赖的关联
**推荐接口**:
- `/vulnerabilities/detect` - POST接口，支持10种检测策略

**推荐文档**: `API_DOCUMENTATION_SUMMARY.txt` 第七章节

---

### 场景5: 我需要集成到自动化工具
**推荐文件**:
- `API_REFERENCE.json` - 机器可读格式
- `API_ENDPOINTS.csv` - 表格格式

**推荐文档**: `API_DOCUMENTATION_SUMMARY.txt` 第十一章节

---

## 常用命令示例

### 使用cURL测试接口

```bash
# 1. 健康检查
curl http://localhost:5000/vulnerabilities/test

# 2. 获取GitHub漏洞(需要等待较长时间)
curl http://localhost:5000/vulnerabilities/github

# 3. LLM查询
curl "http://localhost:5000/llm/query?query=如何修复SQL注入&model=qwen"

# 4. 获取修复建议
curl -X POST http://localhost:5000/llm/repair/suggestion \
  -d "vulnerability_name=SQL注入" \
  -d "vulnerability_desc=用户输入未过滤" \
  -d "related_code=SELECT * FROM users WHERE id=\$_GET['id']"

# 5. 解析项目依赖(替换路径)
curl "http://localhost:5000/parse/unified_parse?project_folder=%2Fhome%2Fuser%2Fmy-project&project_id=123"
```

### 使用Python调用API

```python
import requests
import urllib.parse

# 1. 获取GitHub漏洞
response = requests.get("http://localhost:5000/vulnerabilities/github")
print(response.json())

# 2. LLM查询
params = {"query": "CVE-2024-1234的修复方案", "model": "qwen"}
response = requests.get("http://localhost:5000/llm/query", params=params)
print(response.json())

# 3. 修复建议
data = {
    "vulnerability_name": "SQL注入漏洞",
    "vulnerability_desc": "用户输入未经验证",
    "related_code": "query = f\"SELECT * FROM users WHERE id={user_id}\"",
    "model": "deepseek"
}
response = requests.post("http://localhost:5000/llm/repair/suggestion", data=data)
print(response.json())

# 4. 统一项目解析
project_path = "/home/user/my-project"
encoded_path = urllib.parse.quote(project_path)
url = f"http://localhost:5000/parse/unified_parse?project_folder={encoded_path}"
response = requests.get(url)
print(response.json())
```

---

## 关键参数说明

### URL路径参数必须进行URL编码

**原始路径**: `/home/user/my-project`  
**编码后**: `%2Fhome%2Fuser%2Fmy-project`

**Python编码方法**:
```python
import urllib.parse
encoded = urllib.parse.quote("/home/user/my-project")
# 结果: %2Fhome%2Fuser%2Fmy-project
```

### LLM模型选择

- **Qwen-Max** (`model=qwen`) - 默认，推荐通用使用
- **DeepSeek-R1** (`model=deepseek`) - 推荐复杂推理

### 检测策略选择

- **TinyModel系列** - 轻量级，速度快，资源占用少
- **LLM系列** - 准确度高，需要LLM服务
- **whiteList后缀** - 只匹配白名单库

---

## 文件大小对比

| 文档 | 大小 | 格式 | 适合场景 |
|-----|------|------|---------|
| API_INVENTORY.md | 21KB | Markdown | 完整参考 |
| API_QUICK_REFERENCE.html | 30KB | HTML | 快速查阅 |
| API_REFERENCE.json | 12KB | JSON | 自动化集成 |
| API_ENDPOINTS.csv | 4KB | CSV | Excel分析 |
| API_DOCUMENTATION_SUMMARY.txt | 17KB | Text | 技术总结 |

**总计**: 84KB 完整API文档

---

## 文件位置

所有文档都位于项目根目录:
```
/root/vulsystem-crawler/
├── API_INVENTORY.md                  (详细文档)
├── API_QUICK_REFERENCE.html          (可视化指南)
├── API_REFERENCE.json                (机器可读)
├── API_ENDPOINTS.csv                 (表格汇总)
├── API_DOCUMENTATION_SUMMARY.txt     (总结报告)
└── README_API_DOCS.md               (本文件)
```

---

## 如何选择文档

### 情景1: "我想快速了解有哪些接口"
→ 打开 **API_QUICK_REFERENCE.html** 在浏览器中查看

### 情景2: "我需要详细的API文档进行开发"
→ 阅读 **API_INVENTORY.md**

### 情景3: "我需要在项目规划中整理接口"
→ 在Excel中导入 **API_ENDPOINTS.csv**

### 情景4: "我需要理解系统架构和性能指标"
→ 阅读 **API_DOCUMENTATION_SUMMARY.txt**

### 情景5: "我要集成到自动化工具"
→ 使用 **API_REFERENCE.json**

---

## 更新日志

**2024-11-10** - 初始版本
- 完整扫描17个Flask路由
- 生成5种格式的文档
- 总计超过80KB的详细文档

---

## 支持和反馈

**问题排查**: 查看 `API_DOCUMENTATION_SUMMARY.txt` 第十五章节 "常见问题解决"

**技术栈**: 查看 `API_DOCUMENTATION_SUMMARY.txt` 第十六章节 "技术栈"

**扩展建议**: 查看 `API_DOCUMENTATION_SUMMARY.txt` 第十七章节 "扩展建议"

---

**Generated by Claude Code**  
**2024-11-10**
