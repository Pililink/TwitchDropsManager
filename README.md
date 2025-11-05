# Twitch挂宝Web管理平台

基于 [Alorf/TwitchDropsBot](https://github.com/Alorf/TwitchDropsBot) 的Web管理界面，提供多用户管理、实时监控和配置管理功能。

## 项目简介

本项目为 C# 实现的 Twitch 挂宝机器人添加了现代化的 Web 管理界面，支持：

- 📊 **多用户管理**：管理员可以添加、删除、启用/禁用用户
- 📈 **实时监控**：实时查看每个用户的运行状态、进度和日志
- ⚙️ **配置管理**：用户可以管理个人配置（如优先游戏列表）
- 🔐 **双重认证**：管理员使用用户名/密码，用户使用 Twitch OAuth 登录

## 系统架构

```
┌─────────────────┐
│  Vue 前端       │
│  (Web界面)      │
└────────┬────────┘
         │ HTTP/WebSocket
┌────────▼────────┐
│  FastAPI 后端   │
│  (Python)       │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼──────┐
│Config │ │ Logs   │
│JSON   │ │ Files  │
└───┬───┘ └────────┘
    │
┌───▼──────────┐
│ C# Bot       │
│ (Docker)     │
└──────────────┘
```

### 技术栈

- **后端**: FastAPI (Python 3.10+)
- **前端**: Vue 3 + TypeScript + Vite
- **数据库**: SQLite（管理员账户、会话管理）
- **认证**: JWT tokens
- **实时通信**: WebSocket

## 功能特性

### 管理员功能

#### 系统概览
- ✅ 实时统计信息（总用户数、启用用户、禁用用户）
- ✅ 活跃Campaign统计
- ✅ 用户状态分布（Idle/Seeking/Watching/Error）
- ✅ 总观看进度和百分比
- ✅ 当前挂宝游戏列表

#### 用户管理
- ✅ 用户列表管理（查看所有用户实时状态）
- ✅ 添加新用户（通过 Twitch OAuth 设备流）
- ✅ 删除用户
- ✅ 启用/禁用用户
- ✅ 查看用户详细信息（状态、进度、最近日志）
- ✅ 显示用户当前观看的游戏

#### 系统管理
- ✅ 管理员账户管理（添加、删除、启用/禁用）
- ✅ 修改管理员密码
- ✅ 手动重启Bot容器
- ✅ 查看下次自动重启时间
- ✅ 定时自动重启（每天凌晨4点）

### 用户功能

- ✅ 个人仪表盘（实时状态、进度、Campaign信息）
- ✅ 配置管理（编辑优先游戏列表）
- ✅ 日志查看（分页、过滤）
- ✅ 通过 Twitch 账号登录

## 快速开始

### 前置要求

- Docker 和 Docker Compose
- Python 3.10+（本地开发）
- Node.js 18+（前端开发）

### 安装步骤

1. **克隆项目**（如果还没有）
```bash
cd /root/twitch
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，设置管理员账户等信息
```

3. **构建前端**
```bash
./build-frontend.sh
```
这个脚本会：
- 安装前端依赖
- 构建前端项目
- 将构建文件复制到 `web-backend/static/`

4. **启动服务**
```bash
docker compose up -d
```

5. **访问Web界面**
```
http://localhost:8000
```

**注意**：现在前端由后端统一服务，只需访问端口 8000

### 开发模式

开发时前端和后端分别运行（前端有热重载）：

#### 后端开发

```bash
cd web-backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### 前端开发

```bash
cd web-frontend
npm install
npm run dev  # 运行在 http://localhost:8080
```

开发模式下：
- 前端运行在 8080 端口（带热重载）
- 后端运行在 8000 端口
- Vite 自动代理 `/api` 和 `/ws` 请求到后端

生产模式下：
- 运行 `./build-frontend.sh` 构建前端
- 后端统一服务前端和API（只需 8000 端口）

## 项目结构

```
/
├── README.md                    # 本文档
├── CLAUDE.md                    # Claude Code 项目说明
├── compose.yml                  # Docker Compose配置
├── build-frontend.sh            # 前端构建脚本
├── add_account.sh               # 添加账户脚本
├── auto_update.sh               # 自动更新脚本
├── config.json                  # Bot配置文件（由C# bot管理）
├── logs/                        # 日志目录
│   └── {username}.txt          # 用户日志
├── TwitchDropsBot/              # C# Bot源代码
├── web-backend/                 # FastAPI后端
│   ├── app/
│   │   ├── main.py             # 主应用入口
│   │   ├── database.py         # 数据库配置
│   │   ├── config.py           # 应用配置
│   │   ├── models/             # 数据模型
│   │   │   └── admin.py        # 管理员模型
│   │   ├── routers/            # API路由
│   │   │   ├── auth.py         # 认证路由
│   │   │   ├── admin/          # 管理员路由
│   │   │   │   ├── users.py    # 用户管理
│   │   │   │   └── system.py   # 系统管理
│   │   │   └── user.py         # 用户路由
│   │   ├── services/           # 业务服务
│   │   │   ├── config_service.py      # 配置文件服务
│   │   │   ├── bot_monitor.py         # Bot监控服务
│   │   │   ├── docker_service.py      # Docker操作服务
│   │   │   └── scheduler_service.py   # 定时任务服务
│   │   └── utils/              # 工具函数
│   │       ├── jwt.py          # JWT处理
│   │       ├── password.py     # 密码加密
│   │       └── twitch_auth.py  # Twitch OAuth
│   ├── static/                 # 前端构建文件
│   ├── app.db                  # SQLite数据库
│   └── requirements.txt
└── web-frontend/                # Vue前端
    ├── src/
    │   ├── views/
    │   │   ├── Admin/          # 管理员页面
    │   │   │   ├── Dashboard.vue      # 管理员布局
    │   │   │   ├── Overview.vue       # 系统概览
    │   │   │   ├── UserManagement.vue # 用户管理
    │   │   │   └── SystemManagement.vue # 系统管理
    │   │   ├── User/           # 用户页面
    │   │   │   ├── Layout.vue         # 用户布局
    │   │   │   ├── Dashboard.vue      # 用户仪表盘
    │   │   │   ├── Config.vue         # 用户配置
    │   │   │   └── Logs.vue           # 用户日志
    │   │   ├── Login.vue       # 管理员登录
    │   │   └── TwitchLogin.vue # 用户登录
    │   ├── components/         # 组件
    │   ├── stores/             # Pinia状态管理
    │   │   └── auth.ts         # 认证状态
    │   ├── api/                # API客户端
    │   │   └── client.ts
    │   └── router/             # 路由配置
    │       └── index.ts
    └── package.json
```

## 配置说明

### 环境变量

创建 `.env` 文件：

```env
# 管理员账户
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password
ADMIN_PASSWORD_HASH=  # 自动生成，或使用 bcrypt 生成

# JWT配置
JWT_SECRET_KEY=your_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# 服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# 数据库
DATABASE_URL=sqlite:///./app.db

# 文件路径
CONFIG_FILE_PATH=./config.json
LOGS_DIRECTORY=./logs
```

### config.json 约束

⚠️ **重要**: `config.json` 的结构由 C# bot 项目定义，Web界面只能修改以下字段：

- `Users[].Enabled` - 启用/禁用用户
- `Users[].FavouriteGames` - 用户优先游戏列表
- 全局配置字段（如 `waitingSeconds`, `OnlyFavouriteGames` 等）

**不能手动创建用户**，必须通过 Twitch OAuth 认证流程添加。

## API 文档

### 认证端点

- `POST /api/auth/admin/login` - 管理员登录
- `POST /api/auth/user/twitch/initiate` - 启动用户 Twitch 登录流程
- `POST /api/auth/user/twitch/login` - 完成用户 Twitch 登录
- `GET /api/auth/me` - 获取当前用户信息
- `POST /api/auth/logout` - 登出

### 管理员端点

#### 统计与概览
- `GET /api/admin/stats` - 获取系统统计信息

#### 用户管理
- `GET /api/admin/users` - 获取用户列表（含实时状态）
- `GET /api/admin/users/{user_id}/detail` - 获取用户详细信息
- `DELETE /api/admin/users/{user_id}` - 删除用户
- `PATCH /api/admin/users/{user_id}/enable` - 启用/禁用用户
- `POST /api/admin/users/add/initiate` - 添加用户（调用C# bot）
- `GET /api/admin/users/check/{username}` - 检查用户是否已添加

#### 系统管理
- `GET /api/admin/admins` - 获取管理员列表
- `POST /api/admin/admins` - 创建新管理员
- `PATCH /api/admin/admins/{admin_id}` - 更新管理员状态
- `DELETE /api/admin/admins/{admin_id}` - 删除管理员
- `POST /api/admin/change-password` - 修改当前管理员密码
- `POST /api/admin/bot/restart` - 手动重启Bot容器
- `GET /api/admin/bot/next-restart` - 获取下次定时重启时间

### 用户端点

- `GET /api/user/dashboard` - 用户仪表盘数据
- `GET /api/user/config` - 获取用户配置
- `PUT /api/user/config` - 更新用户配置
- `GET /api/user/logs` - 获取用户日志（分页）

### WebSocket

- `WS /ws` - WebSocket连接，实时推送状态更新（每30秒）

## 日志格式

日志文件格式：`logs/{username}.txt`

日志行格式：
```
YYYY-MM-DD HH:mm:ss.fff +TZ [LEVEL] [username] : message
```

示例：
```
2025-11-04 11:05:58.055 +08:00 [INF] [pureol] : Checking Albion Online (AOCP Buttercup 9 - #1/7)...
```

## 状态说明

Bot 状态通过解析日志确定：

- **Idle**: 没有可用 Campaign，等待重试
- **Seeking**: 正在查找可用的 Campaign
- **Watching**: 正在观看直播，获取 Drops
- **Error**: 发生错误

## 自动化功能

### 定时重启
系统会在每天凌晨4点自动重启Bot容器，以确保稳定运行。可以在系统管理页面查看下次重启时间。

### 实时监控
- 后端每隔一定时间增量读取日志文件（避免重复读取）
- WebSocket每30秒向所有连接的客户端推送状态更新
- 前端自动刷新统计信息和用户列表

## 安全注意事项

1. **管理员密码**: 使用强密码，建议使用密码管理器生成
2. **JWT Secret**: 使用随机生成的强密钥
3. **HTTPS**: 生产环境必须使用 HTTPS
4. **文件权限**: 确保 `config.json` 和日志文件的权限设置正确
5. **CORS**: 配置适当的 CORS 策略

## 常用命令

### 服务管理
```bash
# 启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f
docker compose logs web -f      # 只查看web服务
docker compose logs drop -f     # 只查看bot服务

# 停止服务
docker compose down

# 重启服务
docker compose restart
docker compose restart web      # 只重启web服务
docker compose restart drop     # 只重启bot服务
```

### 构建与更新
```bash
# 构建前端
./build-frontend.sh

# 更新Bot到最新版本
./auto_update.sh

# 添加新账户（手动）
./add_account.sh
```

### 数据库操作
```bash
# 进入数据库（查看管理员账户）
sqlite3 web-backend/app.db
> SELECT * FROM admins;
> .exit
```

## 故障排除

### 常见问题

1. **无法读取 config.json**
   - 检查文件权限：`chmod 666 config.json`
   - 确保文件路径正确
   - 检查文件是否被 C# bot 锁定

2. **日志文件找不到**
   - 确认日志文件命名格式为 `{username}.txt`
   - 检查日志目录权限：`chmod -R 777 logs/`

3. **Twitch 认证失败**
   - 检查网络连接
   - 确认设备码未过期（通常15分钟）
   - 查看系统日志了解详细错误：`docker compose logs drop -f`

4. **管理员无法登录**
   - 确认环境变量配置正确
   - 检查数据库是否正常创建：`ls -la web-backend/app.db`
   - 查看后端日志：`docker compose logs web -f`

5. **前端页面无法加载**
   - 确认前端已构建：`ls web-backend/static/`
   - 重新构建前端：`./build-frontend.sh`
   - 重启web服务：`docker compose restart web`

6. **Bot重启失败**
   - 检查Docker权限（容器需要访问宿主机Docker）
   - 查看错误日志：`docker compose logs web -f`
   - 确认compose.yml路径正确

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

本项目基于 [Alorf/TwitchDropsBot](https://github.com/Alorf/TwitchDropsBot) 项目，遵循相同的 MIT 许可证。

## 免责声明

本项目仅供学习和个人使用。使用本工具时请遵守 Twitch 的服务条款。作者不对因使用本工具导致的账号封禁或限制负责。

## 参考项目

- [Alorf/TwitchDropsBot](https://github.com/Alorf/TwitchDropsBot) - 原始 C# Bot 项目
- [fireph/TwitchDropsFarmer](https://github.com/fireph/TwitchDropsFarmer) - Web界面设计参考

