# VulSystem Crawler

Python Flask 爬虫服务，负责漏洞数据爬取、解析和处理。

## 📋 项目结构

```
vulsystem-crawler/
├── web_crawler/          # 网页爬虫模块
│   ├── __init__.py
│   ├── crawler.py        # 爬虫主逻辑
│   ├── spider.py         # 蜘蛛类
│   └── handlers/         # 各平台处理器
│
├── parase/              # 数据解析模块
│   ├── __init__.py
│   ├── parser.py        # 解析器基类
│   ├── extractors/      # 数据提取器
│   └── validators/      # 数据验证器
│
├── llm/                 # LLM 模型集成
│   ├── __init__.py
│   ├── llm_client.py    # LLM 客户端
│   └── prompts/         # 提示词模板
│
├── VulLibGen/           # 漏洞库生成
│   ├── __init__.py
│   └── generator.py     # 库生成器
│
├── utils/               # 工具函数
│   ├── __init__.py
│   ├── logger.py        # 日志模块
│   ├── request.py       # HTTP 请求
│   └── cache.py         # 缓存模块
│
├── app.py               # Flask 应用主文件
├── config.py            # 配置文件
├── requirements.txt     # Python 依赖
├── Dockerfile           # Docker 镜像定义
└── README.md
```

## 🚀 本地开发

### 前置要求

- Python 3.8+
- pip / conda
- Redis (可选，用于缓存)

### 安装依赖

```bash
cd /root/vulsystem-crawler

# 使用 pip
pip install -r requirements.txt

# 或使用 conda
conda create -n vulsystem python=3.8
conda activate vulsystem
pip install -r requirements.txt
```

### 配置文件

编辑 `config.py`:

```python
class Config:
    DEBUG = False
    LOG_LEVEL = 'INFO'

    # 爬虫配置
    CRAWLER_TIMEOUT = 30
    CRAWLER_RETRY = 3

    # 数据库配置
    DATABASE_URL = 'mysql://root:password@localhost:3306/kulin'

    # LLM 配置
    LLM_API_KEY = 'your_api_key'
    LLM_MODEL = 'gpt-3.5-turbo'

    # Redis 配置
    REDIS_URL = 'redis://localhost:6379/0'

class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    DEBUG = False
```

### 本地运行

```bash
# 开发模式
export FLASK_ENV=development
export FLASK_APP=app.py
flask run --port 5000

# 生产模式（使用 gunicorn）
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

应用将在 `http://localhost:5000` 启动。

## 🐳 Docker 运行

### 构建镜像

```bash
cd /root/vulsystem-orchestration
docker compose build vulsystem-flask-crawler
```

### 运行容器

```bash
docker compose up -d vulsystem-flask-crawler
```

### 查看日志

```bash
docker compose logs -f vulsystem-flask-crawler
```

## 📡 API 接口

### 爬虫管理

- `POST /crawler/start` - 启动爬虫任务
  ```json
  {
    "source": "github",
    "keywords": ["sql injection", "xss"]
  }
  ```

- `POST /crawler/stop` - 停止爬虫任务

- `GET /crawler/status` - 获取爬虫状态

- `GET /crawler/progress` - 获取进度

### 数据解析

- `POST /parse` - 解析漏洞数据
  ```json
  {
    "raw_data": "...",
    "format": "json"
  }
  ```

- `GET /parse/result/{task_id}` - 获取解析结果

### 漏洞库生成

- `POST /vulgen/generate` - 生成漏洞库

- `GET /vulgen/status` - 获取生成状态

## 🔧 配置说明

### 环境变量

创建 `.env` 文件或在 docker-compose.yml 中设置：

```env
# 日志配置
LOG_LEVEL=INFO
LOG_DIR=/app/logs

# 爬虫配置
CRAWLER_TIMEOUT=30
CRAWLER_RETRY=3
CONCURRENT_TASKS=5

# 数据库配置
MYSQL_HOST=vulsystem-mysql
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=changeme
MYSQL_DB=kulin

# LLM 配置
LLM_API_KEY=your_key
LLM_PROVIDER=openai

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379

# Flask 配置
FLASK_ENV=production
DEBUG=False
```

## 📊 主要模块说明

### web_crawler 模块

**功能**: 从各大安全平台爬取漏洞信息

**支持源**:
- GitHub Security Advisories
- NVD (National Vulnerability Database)
- Exploit-DB
- CVE 信息库
- 自定义源

**使用示例**:
```python
from web_crawler import Crawler

crawler = Crawler()
vulnerabilities = crawler.crawl(
    sources=['github', 'nvd'],
    keywords=['sql injection'],
    limit=100
)
```

### parase 模块

**功能**: 解析和规范化爬取的漏洞数据

**支持格式**:
- JSON
- XML
- HTML
- CSV
- 自定义格式

**使用示例**:
```python
from parase import Parser

parser = Parser()
normalized = parser.parse(
    raw_data=data,
    source_type='github'
)
```

### llm 模块

**功能**: 使用 LLM 进行智能分析和增强

**功能**:
- 漏洞描述生成
- 影响范围分析
- 修复建议生成
- 严重程度评估

**使用示例**:
```python
from llm import LLMClient

llm = LLMClient()
analysis = llm.analyze_vulnerability(
    vuln_data=vuln,
    analysis_type='comprehensive'
)
```

### VulLibGen 模块

**功能**: 将处理后的漏洞数据生成结构化的漏洞库

**输出格式**:
- SQLite 数据库
- JSON 文件
- 自定义格式

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_crawler.py

# 运行并生成覆盖率报告
pytest --cov=. --cov-report=html
```

### 测试示例

```python
# tests/test_crawler.py
import unittest
from web_crawler import Crawler

class TestCrawler(unittest.TestCase):
    def setUp(self):
        self.crawler = Crawler()

    def test_crawl_github(self):
        result = self.crawler.crawl(sources=['github'], limit=1)
        self.assertGreater(len(result), 0)
```

## 📈 性能优化

### 1. 并发控制

```python
# config.py
CONCURRENT_TASKS = 5  # 并发任务数
BATCH_SIZE = 100      # 批处理大小
```

### 2. 缓存机制

```python
from utils import cache

@cache.cached(timeout=3600)
def get_vulnerability_data(source):
    # 缓存 1 小时
    pass
```

### 3. 异步处理

```python
from celery import Celery

celery = Celery()

@celery.task
def crawl_async(source):
    # 异步爬虫任务
    pass
```

## 🔐 安全配置

### 1. 请求头设置

```python
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...',
    'Referer': 'https://github.com'
}
```

### 2. IP 轮换

```python
PROXIES = [
    'http://proxy1:8080',
    'http://proxy2:8080',
    # ...
]
```

### 3. 速率限制

```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=get_remote_address)

@app.route('/crawl', methods=['POST'])
@limiter.limit("10 per hour")
def start_crawl():
    pass
```

## 🐛 常见问题

### 1. 连接超时

**错误**: `requests.exceptions.ConnectTimeout`

**解决方案**:
```python
# 增加超时时间
CRAWLER_TIMEOUT = 60

# 或添加重试机制
CRAWLER_RETRY = 5
```

### 2. 内存溢出

**错误**: `MemoryError`

**解决方案**:
```python
# 减少并发任务数
CONCURRENT_TASKS = 2

# 使用流式处理
def process_large_file():
    with open('file.json') as f:
        for line in f:
            yield json.loads(line)
```

### 3. 数据库连接失败

**错误**: `pymysql.err.OperationalError`

**解决方案**:
```bash
# 检查 MySQL 服务
docker compose ps | grep mysql

# 检查连接字符串
echo $MYSQL_HOST  # 应该是 vulsystem-mysql
```

## 📝 日志配置

### 日志输出

```
日志文件位置: /root/vulsystem-data/logs/flask/
├── crawler.log       # 爬虫日志
├── parser.log        # 解析器日志
└── error.log         # 错误日志
```

### 日志级别

```python
# 在 config.py 中设置
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

## 🔗 相关链接

- [Flask 官方文档](https://flask.palletsprojects.com/)
- [Scrapy 官方文档](https://docs.scrapy.org/)
- [BeautifulSoup 文档](https://www.crummy.com/software/BeautifulSoup/)
- [Requests 文档](https://requests.readthedocs.io/)

## 📚 依赖包说明

主要依赖：

```
flask>=2.0.0              # Web 框架
requests>=2.26.0          # HTTP 库
beautifulsoup4>=4.9.0     # HTML 解析
pymysql>=1.0.0            # MySQL 驱动
redis>=3.5.0              # 缓存
celery>=5.0.0             # 异步任务队列
openai>=0.10.0            # LLM 集成
python-dotenv>=0.19.0     # 环境变量管理
```

---

**最后更新**: 2025-11-07
**技术栈**: Python 3.8+, Flask, Crawling, NLP
