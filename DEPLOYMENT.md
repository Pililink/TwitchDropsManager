# 部署指南

## 概述

本项目采用**前后端分离开发，统一部署**的模式：
- **开发环境**：前端（8080）和后端（8000）独立运行
- **生产环境**：后端服务前端静态文件，只需访问 8000 端口

---

## 快速部署

### 1. 构建前端

```bash
./build-frontend.sh
```

这个脚本会：
1. 安装前端依赖（npm install）
2. 构建前端项目（npm run build）
3. 将 `web-frontend/dist/` 复制到 `web-backend/static/`

### 2. 启动服务

```bash
docker compose up -d
```

### 3. 访问

打开浏览器访问：`http://localhost:8000`

---

## 工作原理

### 后端静态文件服务

`web-backend/app/main.py` 中配置了静态文件服务：

```python
# 挂载静态资源
app.mount("/assets", StaticFiles(directory="/app/static/assets"), name="assets")

# SPA路由回退
@app.get("/{full_path:path}")
async def serve_spa(request: Request, full_path: str):
    return FileResponse("/app/static/index.html")
```

### 路由优先级

1. **API路由** (`/api/*`) - 最高优先级
2. **WebSocket** (`/ws`) - 第二优先级
3. **静态资源** (`/assets/*`) - 第三优先级
4. **SPA回退** - 其他所有路径返回 `index.html`

### Docker Compose 配置

```yaml
volumes:
  - ./web-backend/static:/app/static  # 挂载前端构建文件
```

---

## 文件结构

```
/root/twitch/
├── build-frontend.sh          # 前端构建脚本
├── web-frontend/
│   ├── dist/                  # 构建输出（gitignore）
│   ├── src/
│   └── vite.config.ts
└── web-backend/
    ├── static/                # 前端静态文件（gitignore）
    │   ├── index.html
    │   └── assets/
    └── app/
        └── main.py            # 服务静态文件
```

---

## 开发 vs 生产

### 开发模式

```bash
# 终端 1: 后端
cd web-backend
python -m venv venv
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# 终端 2: 前端
cd web-frontend
npm run dev  # 运行在 http://localhost:8080
```

**特点**：
- 前端有热重载
- 前端通过 Vite proxy 访问后端 API
- 两个端口：8080（前端）+ 8000（后端）

### 生产模式

```bash
./build-frontend.sh
docker compose up -d
```

**特点**：
- 单一端口：8000
- 后端统一服务前端和API
- 无需 CORS（同源）

---

## 更新前端

当前端代码有变化时：

```bash
# 1. 重新构建前端
./build-frontend.sh

# 2. 重启后端容器（如果已运行）
docker compose restart web
```

---

## 环境变量

确保 `.env` 文件配置正确：

```env
# 管理员账户
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_password

# JWT配置
JWT_SECRET_KEY=your-secret-key-here

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# 文件路径
CONFIG_FILE_PATH=./config.json
LOGS_DIRECTORY=./logs
```

---

## 故障排除

### 问题：访问 8000 端口显示 "Frontend not built"

**解决**：
```bash
./build-frontend.sh
docker compose restart web
```

### 问题：前端路由 404

**原因**：SPA回退未生效

**检查**：
1. 确认 `web-backend/static/index.html` 存在
2. 确认 `docker-compose.yml` 中挂载了 static 目录
3. 重启容器

### 问题：API 请求 404

**原因**：API路由配置错误

**检查**：
1. 确认API路径以 `/api/` 开头
2. 检查 `web-backend/app/main.py` 中的路由注册

---

## 性能优化

### Gzip 压缩

可以在 uvicorn 启动时添加 gzip 中间件：

```python
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### 缓存策略

前端构建文件自带 hash，可以配置长期缓存：

```python
app.mount("/assets", StaticFiles(directory="/app/static/assets"), name="assets")
# 添加缓存头
```

---

## 安全注意事项

1. **生产环境必须**：
   - 使用 HTTPS
   - 修改默认管理员密码
   - 更换 JWT_SECRET_KEY

2. **CORS 配置**：
   生产环境下前后端同源，无需 CORS

3. **文件权限**：
   - `config.json`: 666（bot和web都能写）
   - `logs/`: 777（bot写入，web读取）
