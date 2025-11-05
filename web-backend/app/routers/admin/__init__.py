# 管理员路由模块
from fastapi import APIRouter
from app.routers.admin import users, system

router = APIRouter()

router.include_router(users.router)
router.include_router(system.router)
