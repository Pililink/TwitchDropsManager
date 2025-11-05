"""用户日志路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
from app.config import settings
from app.routers.auth import get_current_user

router = APIRouter()


class LogEntry(BaseModel):
    """日志条目"""
    timestamp: Optional[str]
    level: str
    message: str


class LogsResponse(BaseModel):
    """日志响应"""
    logs: List[LogEntry]
    total: int
    page: int
    page_size: int


@router.get("/logs")
async def get_user_logs(
    page: int = 1,
    page_size: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """获取用户日志"""
    from app.services.bot_monitor import bot_monitor

    username = current_user["username"]
    log_file = Path(settings.logs_directory) / f"{username}.txt"

    if not log_file.exists():
        return LogsResponse(logs=[], total=0, page=page, page_size=page_size)

    try:
        # 读取日志文件
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        # 解析日志
        parsed_logs = []
        for line in lines:
            parsed = bot_monitor._parse_log_line(line.strip())
            if parsed:
                parsed_logs.append(LogEntry(
                    timestamp=parsed["timestamp"].isoformat() if parsed["timestamp"] else None,
                    level=parsed["level"],
                    message=parsed["message"]
                ))

        # 分页
        total = len(parsed_logs)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_logs = parsed_logs[start:end]

        return LogsResponse(
            logs=paginated_logs,
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"读取日志失败: {str(e)}"
        )

