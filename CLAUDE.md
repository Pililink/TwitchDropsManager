# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **non-invasive web wrapper** for [Alorf/TwitchDropsBot](https://github.com/Alorf/TwitchDropsBot). The web interface does NOT modify the original C# bot - it only reads logs and configuration files.

### Components
- **TwitchDropsBot** (in `TwitchDropsBot/`): Original C# bot running in Docker - does the actual drop farming
- **Web Backend** (`web-backend/`): FastAPI service that monitors bot status by parsing log files
- **Web Frontend** (`web-frontend/`): Vue 3 interface for visualization and configuration

## Architecture - Non-Invasive Design

**Key Principle**: Web wrapper operates **completely outside** the C# bot. No code modifications to TwitchDropsBot.

### Shared Files (Communication Layer)
The web wrapper and C# bot communicate through the file system:
- **`/root/twitch/config.json`** - Bot configuration file (shared read/write)
  - C# bot: Creates structure, adds users, reads configuration
  - Web backend: Reads user list, modifies limited fields (Enabled, FavouriteGames)
- **`/root/twitch/logs/`** - Log directory (read-only for web)
  - C# bot: Writes `{username}.txt` log files
  - Web backend: Parses logs to determine bot status and display to users

### Data Flow
1. **C# Bot** (runs independently in Docker):
   - Writes to `config.json` and `logs/{username}.txt`
   - Exposes CLI commands like `--add-account`
2. **Web Backend**:
   - **Reads** `config.json` for user list and configuration
   - **Writes** limited fields in `config.json` (Enabled, FavouriteGames)
   - **Monitors** log files to determine bot status (Idle/Seeking/Watching/Error)
   - **Calls** C# bot CLI commands via Docker exec for operations like adding users
3. **Web Frontend**: Communicates with backend via REST API and WebSocket

### Key Components
- **Config Management**: `web-backend/app/services/config_service.py` handles `config.json` operations
- **Bot Monitoring**: `web-backend/app/services/bot_monitor.py` parses log files to determine bot status
- **User Addition**: Web backend calls C# bot's CLI command `docker compose exec drop dotnet TwitchDropsBot.Console.dll --add-account` to initiate Twitch OAuth, then C# bot automatically writes to `config.json`
- **Authentication**: JWT tokens for admin dashboard access
- **Real-time Updates**: WebSocket at `/ws` broadcasts bot status changes

## Common Development Commands

### Production Deployment
```bash
# 1. Build frontend
./build-frontend.sh

# 2. Start all services
docker compose up -d

# 3. Access at http://localhost:8000
```

### Development Mode

Backend:
```bash
cd web-backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend (with hot reload):
```bash
cd web-frontend
npm install
npm run dev  # Runs on http://localhost:8080
```

### Docker Operations
```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down

# Rebuild after frontend changes
./build-frontend.sh && docker compose restart web

# Add new Twitch account
./add_account.sh
# or: docker compose exec -it drop /bin/sh -c "dotnet TwitchDropsBot.Console.dll --add-account"

# Update bot to latest version (一键更新所有内容)
./auto_update.sh
```

### Auto Update Script (auto_update.sh)

自动更新脚本执行完整的更新流程，包括：

1. 停止所有服务
2. 更新 TwitchDropsBot 代码（git pull 或 git clone）
3. 构建前端（优先使用 Docker，回退到 npm）
4. 创建必要目录（logs、static 等）
5. 设置文件权限（config.json: 666, logs/: 777）
6. 清理未使用的 Docker 镜像
7. 重新构建所有容器
8. 启动所有服务

**使用场景：**
- Bot 版本更新
- Web 界面更新
- 文件权限修复
- 系统维护

**注意：** 脚本会停止服务，确保无重要任务运行时执行。

### Database Operations
- SQLite database at `web-backend/app.db` for admin accounts and sessions
- Schema auto-created on startup via SQLAlchemy models

### Scheduled Tasks (定时任务)

系统包含自动定时重启功能：

**位置：** `web-backend/app/services/scheduler_service.py`

**默认配置：**
- 重启时间：每天凌晨 4:00
- 自动重启 Bot 容器以确保稳定性

**修改定时重启时间：**

编辑 `scheduler_service.py` 中的配置：

```python
def __init__(self):
    # 每天凌晨4点重启（可配置）
    self.restart_hour = 4      # 修改这里：小时 (0-23)
    self.restart_minute = 0    # 修改这里：分钟 (0-59)
```

**手动触发重启：**
- Web 界面：管理员后台 → 系统管理 → 手动重启 Bot
- API：`POST /api/admin/bot/restart`
- 命令行：`docker compose restart drop`

**查看下次重启时间：**
- Web 界面：管理员后台 → 系统管理
- API：`GET /api/admin/bot/next-restart`

## Important Constraints

### Non-Invasive Design Rules
⚠️ **CRITICAL**: Web wrapper must NEVER modify TwitchDropsBot source code or interfere with its operation.

### config.json Management
⚠️ **CRITICAL**: The `config.json` structure is defined and owned by the C# bot. Web interface can only modify:
- `Users[].Enabled` - enable/disable users
- `Users[].FavouriteGames` - user's priority games list
- Global config fields like `waitingSeconds`, `OnlyFavouriteGames`

**Never manually create users in config.json** - must call C# bot's `--add-account` CLI command which handles Twitch OAuth and automatically updates config.json.

### Log File Format
- Location: `logs/{username}.txt`
- Format: `YYYY-MM-DD HH:mm:ss.fff +TZ [LEVEL] [username] : message`
- Bot status determined by parsing log patterns (Idle/Seeking/Watching/Error)

### File Permissions
- `config.json`: Must be writable by both web backend and C# bot (chmod 666)
- `logs/` directory: Writable by all services (chmod -R 777)

## API Structure

### Authentication Endpoints
- `POST /api/auth/admin/login` - Admin login with username/password
- `POST /api/auth/twitch/initiate` - Calls C# bot's `--add-account` command to start Twitch OAuth device flow
- `GET /api/auth/twitch/poll?device_code=xxx` - Monitors logs/config to check if C# bot completed user addition

### Admin Endpoints
- `GET /api/admin/users` - List all users
- `DELETE /api/admin/users/{user_id}` - Delete user
- `PATCH /api/admin/users/{user_id}/enable` - Enable/disable user

### User Endpoints
- `GET /api/user/dashboard` - User dashboard data
- `GET /api/user/config` - Get user config
- `PUT /api/user/config` - Update user config
- `GET /api/user/logs` - Get paginated user logs

### WebSocket
- `WS /ws` - Real-time status updates for all connected clients

## Environment Configuration

Key environment variables (see `.env` file):
- `ADMIN_USERNAME/PASSWORD` - Admin credentials
- `JWT_SECRET_KEY` - JWT signing key (change in production)
- `CONFIG_FILE_PATH` - Path to config.json (default: `./config.json`)
- `LOGS_DIRECTORY` - Logs directory path (default: `./logs`)
- `DATABASE_URL` - SQLite database URL (default: `sqlite:///./app.db`)
- `TWITCH_CLIENT_ID` - Uses Android app client ID by default

## Security Notes

1. **Authentication**: Admin dashboard uses username/password + JWT tokens
2. **Twitch OAuth**: Handled entirely by C# bot via `--add-account` command, web backend only calls this command
3. **File Access**: Backend reads config.json and logs but cannot modify bot core functionality
4. **CORS**: Configured for development ports (8080, 3000) - update for production
5. **Production**: Must use HTTPS and change default JWT secret