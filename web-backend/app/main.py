"""FastAPI应用入口"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from app.config import settings
from app.database import engine, Base
from app.routers import auth, admin, user
import asyncio
import json

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Twitch Drops Bot Web API",
    description="Twitch挂宝机器人Web管理平台API",
    version="1.0.0"
)


# 应用启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    print("[App] 应用启动中...")
    # 启动定时重启任务
    from app.services.scheduler_service import scheduler_service
    scheduler_service.start()
    print("[App] 定时任务已启动")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    print("[App] 应用关闭中...")
    # 停止定时任务
    from app.services.scheduler_service import scheduler_service
    scheduler_service.stop()
    print("[App] 定时任务已停止")


# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(admin.router, prefix="/api/admin", tags=["管理员"])
app.include_router(user.router, prefix="/api/user", tags=["用户"])


# WebSocket连接管理
class ConnectionManager:
    """WebSocket连接管理器"""
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        """广播消息给所有连接"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        # 移除断开的连接
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


@app.get("/api")
async def root():
    """API根路径"""
    return {"message": "Twitch Drops Bot Web API", "version": "1.0.0"}


@app.get("/api/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket端点，实时推送状态更新"""
    await manager.connect(websocket)
    
    try:
        from app.services.config_service import config_service
        from app.services.bot_monitor import bot_monitor
        
        while True:
            # 等待客户端消息（保持连接）
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # 可以处理客户端请求
            except asyncio.TimeoutError:
                # 超时，发送状态更新
                users = config_service.get_users()
                status_updates = {}
                
                for user_data in users:
                    username = user_data.get("Login")
                    status_info = bot_monitor.get_user_status(username)
                    status_updates[username] = {
                        "status": status_info.get("status"),
                        "campaign": status_info.get("campaign"),
                        "broadcaster": status_info.get("broadcaster"),
                        "progress": status_info.get("progress")
                    }
                
                await websocket.send_json({
                    "type": "status_update",
                    "data": status_updates
                })
    except WebSocketDisconnect:
        manager.disconnect(websocket)


# 静态文件服务（前端）
# 前端构建后的文件应该放在 /app/static 目录
static_dir = Path("/app/static")

if static_dir.exists():
    # 挂载静态文件
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")

    # SPA路由回退：所有非API路由都返回index.html
    @app.get("/{full_path:path}")
    async def serve_spa(request: Request, full_path: str):
        """
        服务前端单页应用
        所有非API路由都返回index.html，让前端路由处理
        """
        # API路由已经在上面处理，不会到这里
        # WebSocket路由也已经处理
        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        else:
            return {"error": "Frontend not built", "message": "Please run 'npm run build' in web-frontend"}
else:
    # 开发模式提示
    @app.get("/")
    async def dev_mode_info():
        return {
            "message": "Frontend not found",
            "info": "In production, frontend should be built and placed in /app/static",
            "dev": "Use 'npm run dev' in web-frontend for development"
        }
