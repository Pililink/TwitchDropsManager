# 用户路由模块
from fastapi import APIRouter
from app.routers.user import dashboard, config, logs

router = APIRouter()

router.include_router(dashboard.router)
router.include_router(config.router)
router.include_router(logs.router)

