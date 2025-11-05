"""用户仪表盘路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional

from app.services.bot_monitor import bot_monitor
from app.routers.auth import get_current_user

router = APIRouter()


class DashboardResponse(BaseModel):
    """仪表盘响应"""
    username: str
    status: str
    last_update: Optional[str]
    campaign: Optional[dict]
    broadcaster: Optional[str]
    progress: Optional[dict]
    enabled: bool
    favourite_games: list


@router.get("/dashboard")
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    """
    获取用户仪表盘数据
    需要用户通过Twitch OAuth登录
    """
    username = current_user["username"]
    user_data = current_user["user_data"]
    status_info = bot_monitor.get_user_status(username)

    print(f"[Dashboard] 用户{username}的状态信息:")
    print(f"  status: {status_info.get('status')}")
    print(f"  campaign: {status_info.get('campaign')}")
    print(f"  broadcaster: {status_info.get('broadcaster')}")
    print(f"  progress: {status_info.get('progress')}")

    response = DashboardResponse(
        username=username,
        status=status_info.get("status", "Unknown"),
        last_update=status_info.get("last_update"),
        campaign=status_info.get("campaign"),
        broadcaster=status_info.get("broadcaster"),
        progress=status_info.get("progress"),
        enabled=user_data.get("Enabled", True),
        favourite_games=user_data.get("FavouriteGames", [])
    )

    print(f"[Dashboard] 返回的响应: campaign={response.campaign}")
    return response

