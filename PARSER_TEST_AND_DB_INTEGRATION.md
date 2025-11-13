# 解析器接口测试与数据库集成指南

## 概述

本文档说明如何测试项目中的解析接口，验证返回格式的一致性，以及如何将解析结果存储到数据库中。

## 标准返回格式

所有解析器（pom_parse, go_parse, python_parse等）都应该返回统一的JSON格式：

```json
[
  {
    "name": "dependency-name version",
    "description": "LLM生成的依赖描述"
  }
]
```

### 字段说明

| 字段 | 类型 | 说明 | 示例 |
|-----|------|------|------|
| name | string | 依赖包名称和版本号（空格分隔） | "express 4.18.2" |
| description | string | LLM生成的功能描述（80-120词） | "A fast web framework for Node.js..." |

## 可用的测试脚本

### 1. test_parser_apis.py （推荐）

通过HTTP请求测试Flask API接口，最接近实际使用场景。

**使用步骤:**

```bash
# 1. 启动Flask服务器
python app.py

# 2. 在另一个终端运行测试
python test_parser_apis.py
```

**配置测试项目:**

编辑脚本中的 `TEST_PROJECTS` 字典：

```python
TEST_PROJECTS = {
    "pom_parse": r"C:\path\to\java\project",
    "go_parse": r"C:\path\to\go\project",
    # ...
}
```

**优点:**
- 测试真实的HTTP接口
- 验证URL编码和网络传输
- 检查HTTP响应头和状态码

### 2. test_parser_format_quick.py （快速测试）

快速验证工具，自动检测项目类型。

**使用方法:**

```bash
python test_parser_format_quick.py

# 选择:
# 1 - 测试指定项目
# 2 - 测试当前项目
# 3 - 查看标准格式
```

**优点:**
- 无需手动配置
- 自动检测项目类型
- 快速验证单个项目

### 3. test_parsers_consistency.py （全面测试）

直接测试解析器函数，无需启动服务器。

**使用方法:**

```bash
python test_parsers_consistency.py
```

**优点:**
- 不依赖Flask服务器
- 直接测试解析器逻辑
- 适合开发调试

## API接口列表

### 解析接口

| 接口路径 | 支持语言 | 依赖文件 |
|---------|---------|---------|
| `/parse/pom_parse` | Java | pom.xml |
| `/parse/go_parse` | Go | go.mod |
| `/parse/python_parse` | Python | requirements.txt, setup.py, pyproject.toml |
| `/parse/javascript_parse` | JavaScript | package.json, yarn.lock, pnpm-lock.yaml |
| `/parse/php_parse` | PHP | composer.json |
| `/parse/ruby_parse` | Ruby | Gemfile |
| `/parse/rust_parse` | Rust | Cargo.toml |
| `/parse/erlang_parse` | Erlang | rebar.config |

### 请求格式

```http
GET /parse/{parser_name}?project_folder=/path/to/project
```

**参数:**
- `project_folder`: 项目文件夹路径（需要URL编码）

**示例:**

```python
import requests
import urllib.parse

project_path = r"C:\Users\user\project"
encoded_path = urllib.parse.quote(project_path)

response = requests.get(
    f"http://127.0.0.1:5000/parse/go_parse?project_folder={encoded_path}"
)

dependencies = response.json()
```

## 数据库集成

### 推荐表结构

```sql
CREATE TABLE dependencies (
    id INT PRIMARY KEY AUTO_INCREMENT,
    project_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    version VARCHAR(100),
    description TEXT,
    language VARCHAR(50),
    package_manager VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_project (project_id),
    INDEX idx_language (language),
    INDEX idx_name (name),
    UNIQUE KEY uk_project_dep (project_id, name, version)
);
```

### 字段说明

| 字段 | 类型 | 说明 | 来源 |
|-----|------|------|------|
| project_id | INT | 项目ID | 从业务系统传入 |
| name | VARCHAR(255) | 依赖包名称 | 从 API 返回的 name 字段分离 |
| version | VARCHAR(100) | 版本号 | 从 API 返回的 name 字段分离 |
| description | TEXT | 功能描述 | 直接使用 API 返回的 description |
| language | VARCHAR(50) | 编程语言 | 根据解析器类型设定 |
| package_manager | VARCHAR(50) | 包管理器 | 根据解析器类型设定 |

### Python存储示例

```python
import requests
import json
import urllib.parse

def parse_and_store_dependencies(project_id, project_path, language):
    """
    解析项目依赖并存储到数据库

    Args:
        project_id: 项目ID
        project_path: 项目路径
        language: 编程语言 (java, go, python, javascript等)
    """
    # 1. 确定解析器和包管理器
    parser_map = {
        'java': ('pom_parse', 'maven'),
        'go': ('go_parse', 'go'),
        'python': ('python_parse', 'pip'),
        'javascript': ('javascript_parse', 'npm'),
        'php': ('php_parse', 'composer'),
        'ruby': ('ruby_parse', 'bundler'),
        'rust': ('rust_parse', 'cargo'),
        'erlang': ('erlang_parse', 'rebar')
    }

    if language not in parser_map:
        raise ValueError(f"不支持的语言: {language}")

    parser_name, package_manager = parser_map[language]

    # 2. 调用解析API
    encoded_path = urllib.parse.quote(project_path)
    url = f"http://127.0.0.1:5000/parse/{parser_name}"

    response = requests.get(url, params={'project_folder': encoded_path})
    response.raise_for_status()

    # 3. 解析响应
    dependencies = response.json()

    # 4. 存储到数据库
    stored_count = 0

    for dep in dependencies:
        name_full = dep['name']
        description = dep['description']

        # 分离包名和版本号
        parts = name_full.rsplit(' ', 1)
        package_name = parts[0]
        version = parts[1] if len(parts) > 1 else None

        # 插入数据库（使用你的数据库连接）
        cursor.execute('''
            INSERT INTO dependencies
            (project_id, name, version, description, language, package_manager)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                description = VALUES(description),
                updated_at = CURRENT_TIMESTAMP
        ''', (project_id, package_name, version, description, language, package_manager))

        stored_count += 1

    conn.commit()
    print(f"✓ 成功存储 {stored_count} 个依赖")
    return stored_count


# 使用示例
if __name__ == "__main__":
    import pymysql

    # 连接数据库
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='password',
        database='your_database'
    )
    cursor = conn.cursor()

    try:
        # 解析并存储Go项目依赖
        count = parse_and_store_dependencies(
            project_id=123,
            project_path=r'C:\path\to\go\project',
            language='go'
        )
        print(f"存储了 {count} 个依赖")

    finally:
        cursor.close()
        conn.close()
```

### Java/Spring Boot 存储示例

```java
@Service
public class DependencyService {

    @Autowired
    private DependencyRepository dependencyRepository;

    @Autowired
    private RestTemplate restTemplate;

    public int parseAndStoreDependencies(Long projectId, String projectPath, String language) {
        // 1. 确定解析器
        Map<String, String[]> parserMap = Map.of(
            "java", new String[]{"pom_parse", "maven"},
            "go", new String[]{"go_parse", "go"},
            "python", new String[]{"python_parse", "pip"}
            // ...
        );

        String[] config = parserMap.get(language);
        if (config == null) {
            throw new IllegalArgumentException("不支持的语言: " + language);
        }

        String parserName = config[0];
        String packageManager = config[1];

        // 2. 调用解析API
        String encodedPath = URLEncoder.encode(projectPath, StandardCharsets.UTF_8);
        String url = String.format(
            "http://127.0.0.1:5000/parse/%s?project_folder=%s",
            parserName, encodedPath
        );

        // 3. 获取响应
        ResponseEntity<List<DependencyDto>> response = restTemplate.exchange(
            url,
            HttpMethod.GET,
            null,
            new ParameterizedTypeReference<List<DependencyDto>>() {}
        );

        List<DependencyDto> dependencies = response.getBody();

        // 4. 存储到数据库
        int count = 0;
        for (DependencyDto dep : dependencies) {
            String nameFull = dep.getName();
            String description = dep.getDescription();

            // 分离包名和版本号
            String[] parts = nameFull.split(" ");
            String packageName = parts[0];
            String version = parts.length > 1 ? parts[1] : null;

            // 创建实体
            Dependency dependency = new Dependency();
            dependency.setProjectId(projectId);
            dependency.setName(packageName);
            dependency.setVersion(version);
            dependency.setDescription(description);
            dependency.setLanguage(language);
            dependency.setPackageManager(packageManager);

            // 保存（如果存在则更新）
            dependencyRepository.save(dependency);
            count++;
        }

        return count;
    }
}

// DTO类
@Data
public class DependencyDto {
    private String name;
    private String description;
}
```

## 测试检查清单

在集成到生产环境之前，请确保完成以下测试：

- [ ] 所有解析器返回格式一致
- [ ] JSON格式正确，可以被解析
- [ ] 每个依赖项包含 name 和 description 字段
- [ ] name 字段格式为 "包名 版本号"
- [ ] description 字段内容合理（非空，有意义）
- [ ] HTTP接口返回 200 状态码
- [ ] URL编码正确处理中文路径和特殊字符
- [ ] 数据库插入成功
- [ ] 重复依赖处理正确（使用 UNIQUE KEY）
- [ ] 性能可接受（大项目测试）

## 常见问题

### Q1: 解析器返回空数组

**可能原因:**
- 项目中没有找到依赖文件
- 依赖文件格式不正确
- 依赖文件为空

**解决方法:**
检查项目路径和依赖文件是否存在。

### Q2: LLM调用超时

**可能原因:**
- 依赖数量太多
- LLM服务响应慢

**解决方法:**
- 增加HTTP请求超时时间
- 使用批处理（已在代码中实现，每批10个）
- 考虑使用异步任务

### Q3: 版本号分离错误

**问题:**
某些依赖名称中包含空格，导致分离错误。

**解决方法:**
使用 `rsplit(' ', 1)` 从右边分离，只分离最后一个空格：

```python
parts = name_full.rsplit(' ', 1)  # 从右边分离
package_name = parts[0]
version = parts[1] if len(parts) > 1 else None
```

### Q4: 数据库字段长度不够

**问题:**
某些依赖名称或描述超过字段长度。

**解决方法:**
- name: VARCHAR(255) 通常足够
- description: 使用 TEXT 类型
- version: VARCHAR(100) 足够

## 性能优化建议

1. **批量插入**: 使用批量INSERT而非逐条插入
2. **异步处理**: 对于大项目，使用异步任务
3. **缓存结果**: 缓存已解析的项目结果
4. **增量更新**: 只更新变化的依赖
5. **索引优化**: 在 project_id, name, language 上创建索引

## 维护与监控

- 定期运行测试脚本验证接口
- 监控解析失败率
- 记录解析耗时
- 定期更新LLM提示词以提高描述质量

## 联系与支持

如有问题，请查看：
- `API.md` - API完整文档
- `test_parsers_format.py` - 格式测试报告
- `错误分析与解决方案.md` - 常见错误
