"""用户配置路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List

from app.services.config_service import config_service
from app.routers.auth import get_current_user

router = APIRouter()


class UserConfigResponse(BaseModel):
    """用户配置响应"""
    Enabled: bool
    FavouriteGames: List[str]


class UpdateUserConfigRequest(BaseModel):
    """更新用户配置请求"""
    FavouriteGames: List[str]


@router.get("/config")
async def get_user_config(current_user: dict = Depends(get_current_user)):
    """获取用户配置"""
    user_data = current_user["user_data"]

    return UserConfigResponse(
        Enabled=user_data.get("Enabled", True),
        FavouriteGames=user_data.get("FavouriteGames", [])
    )


@router.put("/config")
async def update_user_config(
    request: UpdateUserConfigRequest,
    current_user: dict = Depends(get_current_user)
):
    """更新用户配置"""
    user_data = current_user["user_data"]
    user_id = user_data.get("Id")

    if config_service.update_user_favourite_games(user_id, request.FavouriteGames):
        return {"message": "配置已更新"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新配置失败"
        )

