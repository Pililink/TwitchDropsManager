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

# Update bot to latest version
./auto_update.sh
```

### Database Operations
- SQLite database at `web-backend/app.db` for admin accounts and sessions
- Schema auto-created on startup via SQLAlchemy models

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