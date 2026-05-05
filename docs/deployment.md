# 部署指南

## 环境要求

### 开发环境
- Node.js 18+
- Python 3.9+
- npm 或 yarn

### 生产环境
- Node.js 18+
- Python 3.9+
- Nginx (用于前端静态文件托管)
- Gunicorn + Uvicorn workers (用于后端部署)
- PostgreSQL 或 MySQL (推荐)

## 开发环境部署

### 1. 克隆项目

```bash
git clone <repository-url>
cd stock_fund_analysis
```

### 2. 后端部署

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python init_db.py

# 启动开发服务器
python main.py
```

### 3. 前端部署

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问 http://localhost:5173 即可看到应用。

## 生产环境部署

### 1. 后端部署

#### 使用 Gunicorn

```bash
cd backend

# 安装生产依赖
pip install gunicorn

# 使用 Gunicorn 启动
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

#### 使用 Systemd (Linux)

创建服务文件 `/etc/systemd/system/admin-backend.service`:

```ini
[Unit]
Description=Admin Dashboard Backend
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/backend
ExecStart=/path/to/backend/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl start admin-backend
sudo systemctl enable admin-backend
```

### 2. 前端部署

#### 构建生产版本

```bash
cd frontend

# 安装依赖
npm install

# 构建
npm run build
```

构建产物在 `dist/` 目录。

#### Nginx 配置

创建 Nginx 配置文件 `/etc/nginx/sites-available/admin-dashboard`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;

        # 缓存静态资源
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # API 代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

启用站点：

```bash
sudo ln -s /etc/nginx/sites-available/admin-dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### HTTPS 配置

使用 Let's Encrypt 免费证书：

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Docker 部署 (可选)

### Dockerfile (后端)

创建 `backend/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - SECRET_KEY=your-production-secret-key
    depends_on:
      - db

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=admin
      - POSTGRES_PASSWORD=admin123
      - POSTGRES_DB=stock_fund_analysis
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

启动：

```bash
docker-compose up -d
```

## 环境变量

### 后端环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| SECRET_KEY | (代码中定义) | JWT 签名密钥 |
| DATABASE_URL | sqlite+aiosqlite:///./admin.db | 数据库连接字符串 |
| ACCESS_TOKEN_EXPIRE_MINUTES | 60 | Token 过期时间(分钟) |

### 前端环境变量

在 `frontend/.env` 文件中配置：

```
VITE_API_BASE_URL=http://localhost:8000
```

## 数据库迁移

### 使用 Alembic

```bash
cd backend

# 初始化 Alembic
pip install alembic
alembic init alembic

# 创建迁移
alembic revision --autogenerate -m "Add field"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

## 性能优化

### 后端
- 使用 Gunicorn + Uvicorn workers 处理并发
- 启用数据库连接池
- 使用 Redis 缓存（可选）

### 前端
- 启用 gzip 压缩
- 静态资源 CDN 加速
- 图片优化和懒加载

## 监控和日志

### 日志配置

在 `backend/main.py` 中配置日志：

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 健康检查

- 后端健康检查: `GET /health`
- API 文档: `GET /docs`

## 备份

### 数据库备份

```bash
# SQLite
cp backend/admin.db backup/admin.db.$(date +%Y%m%d)

# PostgreSQL
pg_dump -U admin -d stock_fund_analysis > backup/$(date +%Y%m%d).sql
```

## 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # Windows
   netstat -ano | findstr :8000
   taskkill /PID <pid> /F

   # Linux
   lsof -i :8000
   kill -9 <pid>
   ```

2. **依赖安装失败**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt --no-cache-dir
   ```

3. **前端构建失败**
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

4. **CORS 错误**
   - 检查后端 CORS 配置中的 allowed_origins
   - 确认前端请求的 Origin 与配置匹配
