# 架构说明文档

## 系统架构

### 两种用户角色

#### 1. 管理员 (Admin)
- **登录方式**: 用户名密码 (JWT)
- **权限**:
  - 查看所有用户列表和状态
  - 启用/禁用用户
  - 删除用户
  - 调用Docker命令添加新用户到bot
- **API端点**: `/api/admin/*`

#### 2. 普通用户 (User)
- **登录方式**: Twitch OAuth (JWT)
- **权限**:
  - 查看自己的dashboard（bot状态、进度）
  - 修改自己的配置（优先游戏列表）
  - 查看自己的日志
- **API端点**: `/api/user/*`

---

## 关键业务流程

### 流程 1: 管理员添加用户到Bot

```
1. 管理员登录后台
2. 点击"添加用户"
3. 调用 POST /api/admin/users/add/initiate
   └─> 后端调用 docker compose exec drop dotnet TwitchDropsBot.Console.dll --add-account
4. C# bot 输出 Twitch OAuth 链接和代码
5. 管理员将链接和代码提供给待添加的用户
6. 用户访问链接并授权
7. C# bot 自动将用户信息写入 config.json
8. 管理员可通过 GET /api/admin/users/check/{username} 检查用户是否添加成功
```

**重要**: Web 界面不直接处理 Twitch OAuth，完全由 C# bot 处理

---

### 流程 2: 用户登录Web界面查看自己信息

```
1. 用户访问登录页面
2. 选择"通过Twitch登录"
3. 调用 POST /api/auth/user/twitch/initiate
   └─> 获取 device_code 和 verification_uri
4. 用户访问 verification_uri 并授权
5. 前端轮询调用 POST /api/auth/user/twitch/login (传递 device_code)
   └─> 后端验证用户的 Twitch username 是否存在于 config.json
   └─> 如果存在，颁发 JWT token
6. 用户使用 JWT token 访问 /api/user/* 端点
7. 后端从 token 中获取 username，从 config.json 读取用户数据，从 logs/ 读取日志
```

---

## 文件交互

### config.json
```json
{
  "Users": [
    {
      "Login": "twitch_username",  // Twitch用户名
      "Id": "123456789",           // Twitch用户ID
      "ClientSecret": "oauth_token",
      "UniqueId": "unique_id",
      "Enabled": true,             // Web可修改
      "FavouriteGames": []         // Web可修改
    }
  ],
  "FavouriteGames": [],
  "waitingSeconds": 300,
  ...
}
```

- **C# bot**: 创建结构，添加用户，读取配置
- **Web backend**: 读取用户列表，修改 Enabled 和 FavouriteGames

### logs/{username}.txt
```
2025-11-04 11:05:58.055 +08:00 [INF] [username] : Checking Albion Online...
```

- **C# bot**: 写入日志
- **Web backend**: 只读，解析状态

---

## 认证依赖关系

### 后端 Depends
```python
# 管理员认证
from app.routers.auth import get_current_admin

@router.get("/admin/users")
async def get_users(current_admin: Admin = Depends(get_current_admin)):
    ...

# 用户认证
from app.routers.auth import get_current_user

@router.get("/user/dashboard")
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    username = current_user["username"]  # Twitch username
    user_data = current_user["user_data"]  # config.json中的用户数据
    ...
```

---

## API 端点总结

### 认证端点
- `POST /api/auth/admin/login` - 管理员登录
- `POST /api/auth/user/twitch/initiate` - 用户发起Twitch登录
- `POST /api/auth/user/twitch/login` - 完成Twitch登录
- `POST /api/auth/logout` - 登出
- `GET /api/auth/me` - 获取当前用户信息

### 管理员端点
- `GET /api/admin/users` - 获取所有用户
- `DELETE /api/admin/users/{user_id}` - 删除用户
- `PATCH /api/admin/users/{user_id}/enable` - 启用/禁用用户
- `POST /api/admin/users/add/initiate` - 调用bot添加用户
- `GET /api/admin/users/check/{username}` - 检查用户是否添加成功

### 用户端点
- `GET /api/user/dashboard` - 获取仪表盘（需要认证）
- `GET /api/user/config` - 获取配置（需要认证）
- `PUT /api/user/config` - 更新配置（需要认证）
- `GET /api/user/logs` - 获取日志（需要认证）

---

## 数据库表

### admins (SQLite)
- 管理员账户信息
- 用户名、密码hash

### sessions (SQLite)
- 用户会话（admin和user共用）
- token、过期时间

---

## 非侵入式设计原则

✅ **正确做法**:
- Web 调用 Docker 命令让 C# bot 添加用户
- Web 读取 config.json 和 logs/
- Web 只修改 config.json 中允许的字段

❌ **错误做法**:
- Web 不应自己实现 Twitch OAuth 来添加用户到 bot
- Web 不应修改 C# bot 的代码
- Web 不应修改 config.json 的结构
