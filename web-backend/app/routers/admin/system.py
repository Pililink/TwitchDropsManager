"""系统管理路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.routers.auth import get_current_admin
from app.models.admin import Admin
from app.utils.password import verify_password, get_password_hash

router = APIRouter()


class AdminResponse(BaseModel):
    """管理员响应模型"""
    id: int
    username: str
    is_active: bool
    created_at: datetime
    updated_at: datetime | None


class AdminListResponse(BaseModel):
    """管理员列表响应"""
    admins: List[AdminResponse]


class CreateAdminRequest(BaseModel):
    """创建管理员请求"""
    username: str
    password: str


class UpdateAdminRequest(BaseModel):
    """更新管理员请求"""
    is_active: bool | None = None


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str


@router.get("/admins", response_model=AdminListResponse)
async def get_admins(
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """获取管理员列表"""
    admins = db.query(Admin).all()

    return AdminListResponse(
        admins=[
            AdminResponse(
                id=admin.id,
                username=admin.username,
                is_active=admin.is_active,
                created_at=admin.created_at,
                updated_at=admin.updated_at
            )
            for admin in admins
        ]
    )


@router.post("/admins")
async def create_admin(
    request: CreateAdminRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """创建新管理员"""
    # 检查用户名是否已存在
    existing_admin = db.query(Admin).filter(Admin.username == request.username).first()
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 创建新管理员
    new_admin = Admin(
        username=request.username,
        password_hash=get_password_hash(request.password)
    )
    db.add(new_admin)
    db.commit()
    db.refresh(new_admin)

    return {
        "message": "管理员创建成功",
        "admin": AdminResponse(
            id=new_admin.id,
            username=new_admin.username,
            is_active=new_admin.is_active,
            created_at=new_admin.created_at,
            updated_at=new_admin.updated_at
        )
    }


@router.patch("/admins/{admin_id}")
async def update_admin(
    admin_id: int,
    request: UpdateAdminRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """更新管理员信息"""
    # 不允许禁用自己
    if admin_id == current_admin.id and request.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能禁用自己的账户"
        )

    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="管理员不存在"
        )

    if request.is_active is not None:
        admin.is_active = request.is_active

    db.commit()
    db.refresh(admin)

    return {
        "message": "管理员信息更新成功",
        "admin": AdminResponse(
            id=admin.id,
            username=admin.username,
            is_active=admin.is_active,
            created_at=admin.created_at,
            updated_at=admin.updated_at
        )
    }


@router.delete("/admins/{admin_id}")
async def delete_admin(
    admin_id: int,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """删除管理员"""
    # 不允许删除自己
    if admin_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己的账户"
        )

    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="管理员不存在"
        )

    db.delete(admin)
    db.commit()

    return {"message": "管理员删除成功"}


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """修改当前管理员密码"""
    # 验证旧密码
    if not verify_password(request.old_password, current_admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码不正确"
        )

    # 更新密码
    current_admin.password_hash = get_password_hash(request.new_password)
    db.commit()

    return {"message": "密码修改成功"}


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
