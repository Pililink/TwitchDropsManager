"""管理员用户管理路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.database import get_db
from app.routers.auth import get_current_admin
from app.models.admin import Admin
from app.services.config_service import config_service
from app.services.bot_monitor import bot_monitor

router = APIRouter()


class UserResponse(BaseModel):
    """用户响应模型"""
    Login: str
    Id: str
    Enabled: bool
    FavouriteGames: List[str]
    status: dict = {}


class UserListResponse(BaseModel):
    """用户列表响应"""
    users: List[UserResponse]


class UpdateUserEnabledRequest(BaseModel):
    """更新用户启用状态请求"""
    enabled: bool


@router.get("/stats")
async def get_system_stats(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取系统统计信息"""
    users_data = config_service.get_users()

    # 统计信息
    total_users = len(users_data)
    enabled_users = sum(1 for u in users_data if u.get("Enabled", True))
    disabled_users = total_users - enabled_users

    # 获取状态统计
    status_counts = {
        "Idle": 0,
        "Seeking": 0,
        "Watching": 0,
        "Error": 0,
        "Unknown": 0
    }

    total_progress = 0
    total_required = 0
    active_campaigns = set()
    active_games = set()

    for user in users_data:
        if not user.get("Enabled", True):
            continue

        username = user.get("Login")
        status_info = bot_monitor.get_user_status(username)

        # 状态统计
        status = status_info.get("status", "Unknown")
        if status in status_counts:
            status_counts[status] += 1
        else:
            status_counts["Unknown"] += 1

        # 进度统计
        progress = status_info.get("progress")
        if progress:
            total_progress += progress.get("current", 0)
            total_required += progress.get("required", 0)

        # Campaign和游戏统计
        campaign_info = status_info.get("campaign")
        if campaign_info:
            if campaign_info.get("campaign"):
                active_campaigns.add(campaign_info.get("campaign"))
            if campaign_info.get("game"):
                active_games.add(campaign_info.get("game"))

    return {
        "total_users": total_users,
        "enabled_users": enabled_users,
        "disabled_users": disabled_users,
        "status_counts": status_counts,
        "total_progress": total_progress,
        "total_required": total_required,
        "progress_percentage": (total_progress / total_required * 100) if total_required > 0 else 0,
        "active_campaigns_count": len(active_campaigns),
        "active_games_count": len(active_games),
        "active_campaigns": list(active_campaigns),
        "active_games": list(active_games)
    }


@router.get("/users", response_model=UserListResponse)
async def get_users(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取用户列表"""
    users_data = config_service.get_users()

    # 获取每个用户的状态
    result = []
    for user in users_data:
        username = user.get("Login")
        status_info = bot_monitor.get_user_status(username)

        result.append(UserResponse(
            Login=user.get("Login"),
            Id=user.get("Id"),
            Enabled=user.get("Enabled", True),
            FavouriteGames=user.get("FavouriteGames", []),
            status=status_info
        ))

    return UserListResponse(users=result)


@router.get("/users/{user_id}/detail")
async def get_user_detail(
    user_id: str,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取用户详细信息"""
    user = config_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    username = user.get("Login")
    status_info = bot_monitor.get_user_status(username)

    return {
        "user": {
            "Login": user.get("Login"),
            "Id": user.get("Id"),
            "Enabled": user.get("Enabled", True),
            "FavouriteGames": user.get("FavouriteGames", [])
        },
        "status": status_info.get("status"),
        "last_update": status_info.get("last_update"),
        "campaign": status_info.get("campaign"),
        "broadcaster": status_info.get("broadcaster"),
        "progress": status_info.get("progress"),
        "recent_logs": status_info.get("recent_logs", [])
    }


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """删除用户"""
    user = config_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    if config_service.delete_user(user_id):
        return {"message": "用户已删除"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除用户失败"
        )


@router.patch("/users/{user_id}/enable")
async def update_user_enabled(
    user_id: str,
    request: UpdateUserEnabledRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """启用/禁用用户"""
    user = config_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    if config_service.update_user_enabled(user_id, request.enabled):
        return {"message": f"用户已{'启用' if request.enabled else '禁用'}"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新用户状态失败"
        )


@router.post("/users/add/initiate")
async def initiate_add_user_via_bot(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    启动添加用户流程：调用C# bot的--add-account命令
    Bot会处理完整的OAuth流程并自动添加到config.json
    """
    from app.services.docker_service import docker_service

    try:
        # 调用docker_service执行add_account命令，并直接返回结果
        result = await docker_service.execute_add_account()
        print(f"[API] docker_service返回结果: {result}")
        return result
    except Exception as e:
        print(f"[API] 调用添加用户命令异常: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"调用添加用户命令失败: {str(e)}"
        )


@router.get("/users/check/{username}")
async def check_user_added(
    username: str,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    检查用户是否已被C# bot添加到config.json
    """
    user = config_service.get_user_by_login(username)
    if user:
        return {
            "added": True,
            "user": {
                "Login": user.get("Login"),
                "Id": user.get("Id"),
                "Enabled": user.get("Enabled", True)
            }
        }
    else:
        return {"added": False}


@router.post("/bot/restart")
async def restart_bot_container(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    重启drop容器（C# bot）
    """
    from app.services.docker_service import docker_service

    try:
        result = await docker_service.restart_drop_container()
        print(f"[API] 重启容器结果: {result}")
        return result
    except Exception as e:
        print(f"[API] 重启容器异常: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重启容器失败: {str(e)}"
        )


@router.get("/bot/next-restart")
async def get_next_restart_time(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    获取下一次定时重启时间
    """
    from app.services.scheduler_service import scheduler_service

    next_restart = scheduler_service.get_next_restart_time()
    if next_restart:
        return {
            "next_restart_time": next_restart.isoformat(),
            "formatted_time": next_restart.strftime("%Y-%m-%d %H:%M:%S")
        }
    else:
        return {
            "next_restart_time": None,
            "formatted_time": "未设置"
        }
