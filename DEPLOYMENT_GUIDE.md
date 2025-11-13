# 🚀 Kuling 部署指南

本文档详细说明如何将 Kuling 项目部署到生产环境。

---

## 📋 目录

1. [本地开发环境](#本地开发环境)
2. [Linux 服务器部署](#linux-服务器部署)
3. [Docker 容器部署](#docker-容器部署)
4. [生产环境配置](#生产环境配置)
5. [监控与维护](#监控与维护)

---

## 本地开发环境

### 快速启动

```bash
# 1. 克隆项目
git clone https://github.com/your-username/kuling.git
cd kuling

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 API Keys

# 5. 启动开发服务器
python app.py
```

访问 `http://127.0.0.1:5000` 即可使用。

---

## Linux 服务器部署

### 前置要求

- Ubuntu 20.04+ 或 CentOS 8+
- Python 3.8+
- Nginx
- 4GB+ 内存
- sudo 权限

### 详细步骤

#### 1. 系统准备

```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 安装 Python 和依赖
sudo apt install -y python3.9 python3.9-venv python3.9-dev
sudo apt install -y nginx supervisor

# 创建应用用户
sudo useradd -m -s /bin/bash kuling
sudo usermod -aG sudo kuling
```

#### 2. 部署应用

```bash
# 切换到 kuling 用户
sudo su - kuling

# 克隆项目
git clone https://github.com/your-username/kuling.git
cd kuling

# 创建虚拟环境
python3.9 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install gunicorn

# 配置环境变量
cp .env.example .env
nano .env  # 填入你的 API Keys
```

#### 3. 配置 Gunicorn

创建 `/home/kuling/kuling/gunicorn_config.py`:
```python
import multiprocessing

# Gunicorn 配置
bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
```

#### 4. 配置 Supervisor

创建 `/etc/supervisor/conf.d/kuling.conf`:
```ini
[program:kuling]
directory=/home/kuling/kuling
command=/home/kuling/kuling/venv/bin/gunicorn -c gunicorn_config.py app:app
user=kuling
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/kuling/kuling/logs/gunicorn.log
environment=PATH="/home/kuling/kuling/venv/bin"
```

启动服务：
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start kuling
sudo supervisorctl status kuling
```

#### 5. 配置 Nginx

创建 `/etc/nginx/sites-available/kuling`:
```nginx
upstream kuling {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://kuling;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    location /static/ {
        alias /home/kuling/kuling/static/;
    }
}
```

启用站点：
```bash
sudo ln -s /etc/nginx/sites-available/kuling /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 6. SSL 证书（可选但推荐）

使用 Let's Encrypt：
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
sudo systemctl restart nginx
```

#### 7. 日志管理

创建日志目录：
```bash
mkdir -p /home/kuling/kuling/logs
chmod 755 /home/kuling/kuling/logs
```

---

## Docker 容器部署

### Dockerfile 示例

创建 `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制需求文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建日志目录
RUN mkdir -p logs

# 暴露端口
EXPOSE 5000

# 启动应用
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  kuling:
    build: .
    ports:
      - "5000:5000"
    environment:
      - ALI_API_KEY=${ALI_API_KEY}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - FLASK_ENV=production
    volumes:
      - ./logs:/app/logs
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/vulnerabilities/test"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - kuling
    restart: always
```

### 部署命令

```bash
# 构建镜像
docker-compose build

# 启动容器
docker-compose up -d

# 查看日志
docker-compose logs -f kuling

# 停止容器
docker-compose down
```

---

## 生产环境配置

### 1. 环境变量

必须设置的环境变量：
```bash
# API Keys（必须）
ALI_API_KEY=sk-xxxxxxxxxxxxx
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxx

# Flask 配置（必须）
FLASK_ENV=production
DEBUG=False
FLASK_SECRET_KEY=your-production-secret-key

# 服务器配置
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=/var/log/kuling
```

### 2. 性能优化

#### Gunicorn 优化
```python
# gunicorn_config.py
workers = multiprocessing.cpu_count() * 2 + 1  # CPU 密集型应用
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
timeout = 120
```

#### Nginx 优化
```nginx
# /etc/nginx/nginx.conf
worker_processes auto;
worker_connections 2000;

gzip on;
gzip_types text/plain text/css application/json application/javascript;
gzip_min_length 1000;

# 缓存配置
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=kuling_cache:10m;
```

### 3. 备份策略

```bash
# 每日备份脚本
#!/bin/bash
BACKUP_DIR="/backups/kuling"
DATE=$(date +%Y%m%d_%H%M%S)

# 备份数据库（如果有）
mysqldump -u root -p kuling_db > $BACKUP_DIR/kuling_$DATE.sql

# 备份配置
tar -czf $BACKUP_DIR/config_$DATE.tar.gz /home/kuling/kuling/.env /etc/nginx/sites-available/kuling

# 保留最近 30 天的备份
find $BACKUP_DIR -type f -mtime +30 -delete
```

### 4. 安全加固

```bash
# 1. 防火墙配置
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# 2. 限制 SSH 登陆
sudo nano /etc/ssh/sshd_config
# 设置: PermitRootLogin no, PasswordAuthentication no

# 3. 更新系统安全补丁
sudo apt update && sudo apt upgrade -y

# 4. 配置 fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

---

## 监控与维护

### 1. 日志监控

```bash
# 查看 Gunicorn 日志
tail -f /home/kuling/kuling/logs/gunicorn.log

# 查看 Nginx 日志
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log

# 查看系统日志
journalctl -u supervisor -f
```

### 2. 性能监控

使用 top 或 htop：
```bash
# 实时监控系统资源
top

# 或使用更友好的界面
sudo apt install htop
htop
```

### 3. 自动化监控脚本

创建 `/home/kuling/kuling/monitor.sh`:
```bash
#!/bin/bash
# 检查应用健康状况

HEALTH_URL="http://127.0.0.1:5000/vulnerabilities/test"
LOG_FILE="/home/kuling/kuling/logs/monitor.log"

# 发送健康检查请求
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $RESPONSE -ne 200 ]; then
    echo "[$(date)] Health check failed. Response code: $RESPONSE" >> $LOG_FILE
    # 重启服务
    sudo supervisorctl restart kuling
else
    echo "[$(date)] Health check passed." >> $LOG_FILE
fi
```

添加到 crontab：
```bash
crontab -e
# 每 5 分钟检查一次
*/5 * * * * /home/kuling/kuling/monitor.sh
```

### 4. 定期维护

```bash
# 每周更新依赖包
pip install --upgrade -r requirements.txt

# 每月重启应用
sudo supervisorctl restart kuling

# 检查磁盘空间
df -h

# 清理日志文件（保留最近 30 天）
find /home/kuling/kuling/logs -name "*.log" -mtime +30 -delete
```

---

## 故障排除

### 应用无法启动

```bash
# 1. 检查日志
tail -f /home/kuling/kuling/logs/gunicorn.log

# 2. 检查端口占用
sudo lsof -i :8000

# 3. 手动启动测试
source /home/kuling/kuling/venv/bin/activate
cd /home/kuling/kuling
python app.py
```

### 内存使用过高

```bash
# 1. 减少 Gunicorn workers
# 编辑 gunicorn_config.py，降低 workers 数量

# 2. 监控进程
ps aux | grep gunicorn

# 3. 重启应用
sudo supervisorctl restart kuling
```

### API 响应缓慢

```bash
# 1. 检查 LLM API 连接
curl -X GET "http://127.0.0.1:5000/llm/query?query=test&model=qwen"

# 2. 检查网络延迟
ping bailian.console.aliyun.com

# 3. 查看解析器性能
python test_all_parsers.py
```

---

## 清单

部署前检查清单：

- [ ] Python 3.8+ 已安装
- [ ] 所有依赖包已安装 (`pip install -r requirements.txt`)
- [ ] `.env` 文件已配置，包含有效的 API Keys
- [ ] Nginx 已正确配置并测试
- [ ] SSL 证书已安装（生产环境）
- [ ] 日志目录已创建
- [ ] 备份策略已部署
- [ ] 监控脚本已添加到 crontab
- [ ] 防火墙规则已配置
- [ ] 定期备份已测试

---

## 获取帮助

如遇到问题，请：

1. 查看日志文件
2. 检查 [常见问题](README.md#-常见问题)
3. 提交 [GitHub Issue](https://github.com/your-username/kuling/issues)
4. 联系技术支持：support@kuling.io

---

**更新时间**: 2025-11-13
**版本**: 1.2.0
