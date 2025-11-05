"""认证路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
import logging

from app.database import get_db
from app.models.admin import Admin, Session as SessionModel
from app.utils.jwt import create_access_token, verify_token
from app.utils.password import verify_password, get_password_hash
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/admin/login")


class AdminLoginRequest(BaseModel):
    """管理员登录请求"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str
    token_type: str = "bearer"


async def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """获取当前管理员"""
    print(f"[Auth] get_current_admin: 验证管理员token，token={token[:30]}...")
    logger.info(f"[Auth] get_current_admin: 验证管理员token，token={token[:30]}...")
    payload = verify_token(token)
    if payload is None:
        print(f"[Auth] ❌ Token验证失败：无效的JWT token")
        logger.error(f"[Auth] ❌ Token验证失败：无效的JWT token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    user_type = payload.get("type")
    print(f"[Auth] Token payload: user_id={user_id}, type={user_type}")
    logger.info(f"[Auth] Token payload: user_id={user_id}, type={user_type}")

    if user_type != "admin":
        logger.warning(f"[Auth] ❌ 权限不足：期望type=admin，实际type={user_type}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )

    # 验证会话
    session = db.query(SessionModel).filter(
        SessionModel.token == token,
        SessionModel.user_id == user_id,
        SessionModel.user_type == "admin",
        SessionModel.expires_at > datetime.utcnow()
    ).first()

    if not session:
        logger.error(f"[Auth] ❌ 会话不存在或已过期: user_id={user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="会话已过期"
        )

    admin = db.query(Admin).filter(Admin.id == user_id).first()
    if not admin or not admin.is_active:
        logger.error(f"[Auth] ❌ 管理员账户不存在或已禁用: user_id={user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理员账户已被禁用"
        )

    logger.info(f"[Auth] ✅ 管理员验证成功: username={admin.username}")
    return admin


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """获取当前普通用户（Twitch登录）"""
    logger.info(f"[Auth] get_current_user: 验证用户token，token={token[:30]}...")
    payload = verify_token(token)
    if payload is None:
        logger.error(f"[Auth] ❌ Token验证失败：无效的JWT token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username = payload.get("sub")
    user_type = payload.get("type")
    logger.info(f"[Auth] Token payload: username={username}, type={user_type}")

    if user_type != "user":
        logger.warning(f"[Auth] ❌ 权限不足：期望type=user，实际type={user_type}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="权限不足"
        )

    # 验证会话
    session = db.query(SessionModel).filter(
        SessionModel.token == token,
        SessionModel.user_id == username,
        SessionModel.user_type == "user",
        SessionModel.expires_at > datetime.utcnow()
    ).first()

    if not session:
        logger.error(f"[Auth] ❌ 会话不存在或已过期: username={username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="会话已过期"
        )

    # 验证用户仍在config.json中
    from app.services.config_service import config_service
    user = config_service.get_user_by_login(username)
    if not user:
        logger.error(f"[Auth] ❌ 用户不在config.json中: username={username}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户已被移除"
        )

    logger.info(f"[Auth] ✅ 用户验证成功: username={username}")
    return {"username": username, "user_data": user}


@router.post("/admin/login", response_model=TokenResponse)
async def admin_login(
    login_data: AdminLoginRequest,
    db: Session = Depends(get_db)
):
    """管理员登录"""
    # 检查是否是默认管理员
    if login_data.username == settings.admin_username:
        # 验证密码
        if settings.admin_password_hash:
            if not verify_password(login_data.password, settings.admin_password_hash):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户名或密码错误"
                )
        else:
            # 首次使用，创建管理员账户
            if login_data.password != settings.admin_password:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="用户名或密码错误"
                )
            
            # 创建管理员记录
            admin = db.query(Admin).filter(Admin.username == login_data.username).first()
            if not admin:
                admin = Admin(
                    username=login_data.username,
                    password_hash=get_password_hash(login_data.password)
                )
                db.add(admin)
                db.commit()
                db.refresh(admin)
        
        admin = db.query(Admin).filter(Admin.username == login_data.username).first()
    else:
        admin = db.query(Admin).filter(Admin.username == login_data.username).first()
        if not admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        if not verify_password(login_data.password, admin.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
    
    # 创建访问令牌
    access_token = create_access_token(
        data={"sub": str(admin.id), "type": "admin"},
        expires_delta=timedelta(hours=settings.jwt_expiration_hours)
    )
    
    # 保存会话
    expires_at = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
    session = SessionModel(
        user_id=admin.id,
        user_type="admin",
        token=access_token,
        expires_at=expires_at
    )
    db.add(session)
    db.commit()
    
    return TokenResponse(access_token=access_token)


@router.post("/logout")
async def logout(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """登出"""
    # 删除会话
    db.query(SessionModel).filter(SessionModel.token == token).delete()
    db.commit()
    
    return {"message": "已成功登出"}


@router.get("/me")
async def get_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """获取当前用户信息（支持管理员和普通用户）"""
    print(f"[Auth] /api/auth/me: 验证token，token={token[:30]}...")

    payload = verify_token(token)
    if payload is None:
        print(f"[Auth] ❌ Token验证失败：无效的JWT token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    user_type = payload.get("type")
    print(f"[Auth] Token payload: user_id={user_id}, type={user_type}")

    # 验证会话
    session = db.query(SessionModel).filter(
        SessionModel.token == token,
        SessionModel.user_id == user_id,
        SessionModel.user_type == user_type,
        SessionModel.expires_at > datetime.utcnow()
    ).first()

    if not session:
        print(f"[Auth] ❌ 会话不存在或已过期: user_id={user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="会话已过期"
        )

    if user_type == "admin":
        # 管理员
        admin = db.query(Admin).filter(Admin.id == user_id).first()
        if not admin or not admin.is_active:
            print(f"[Auth] ❌ 管理员账户不存在或已禁用: user_id={user_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="管理员账户已被禁用"
            )
        print(f"[Auth] ✅ 管理员信息获取成功: username={admin.username}")
        return {
            "id": admin.id,
            "username": admin.username,
            "type": "admin"
        }
    elif user_type == "user":
        # 普通用户
        from app.services.config_service import config_service
        user = config_service.get_user_by_login(user_id)
        if not user:
            print(f"[Auth] ❌ 用户不在config.json中: username={user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户已被移除"
            )
        print(f"[Auth] ✅ 用户信息获取成功: username={user_id}")
        return {
            "id": user.get("Id"),
            "username": user.get("Login"),
            "type": "user"
        }
    else:
        print(f"[Auth] ❌ 未知的用户类型: {user_type}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="未知的用户类型"
        )


@router.post("/user/twitch/initiate")
async def initiate_user_twitch_login():
    """用户通过Twitch登录Web界面（不是添加到bot）"""
    from app.utils.twitch_auth import twitch_auth

    try:
        device_data = await twitch_auth.get_device_code()
        return {
            "device_code": device_data.get("device_code"),
            "user_code": device_data.get("user_code"),
            "verification_uri": device_data.get("verification_uri"),
            "expires_in": device_data.get("expires_in"),
            "interval": device_data.get("interval", 5)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动Twitch认证失败: {str(e)}"
        )


@router.post("/user/twitch/login")
async def user_twitch_login(device_code: str, db: Session = Depends(get_db)):
    """用户通过Twitch OAuth登录"""
    logger.info(f"[Auth] 用户Twitch登录: device_code={device_code[:20]}...")
    from app.utils.twitch_auth import twitch_auth
    from app.services.config_service import config_service

    try:
        # 轮询获取access token
        logger.info(f"[Auth] 步骤1: 轮询获取access token")
        result = await twitch_auth.poll_authorization(device_code)
        if not result:
            logger.error(f"[Auth] ❌ 轮询失败：认证未完成或已过期")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="认证未完成或已过期"
            )

        access_token = result.get("access_token")
        if not access_token:
            logger.error(f"[Auth] ❌ 无法获取access_token from result")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无法获取访问令牌"
            )
        logger.info(f"[Auth] ✅ Access token获取成功")

        # 验证token并获取用户信息
        logger.info(f"[Auth] 步骤2: 验证token并获取用户信息")
        validate_data = await twitch_auth.validate_token(access_token)
        if not validate_data:
            logger.error(f"[Auth] ❌ Token验证失败")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的访问令牌"
            )

        username = validate_data.get("login")
        user_id = validate_data.get("user_id")
        logger.info(f"[Auth] ✅ 用户信息: username={username}, user_id={user_id}")

        # 检查用户是否存在于config.json
        logger.info(f"[Auth] 步骤3: 检查用户是否在config.json中")
        user = config_service.get_user_by_login(username)
        if not user:
            logger.error(f"[Auth] ❌ 用户{username}不在config.json中")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户未被添加到bot系统，请联系管理员"
            )
        logger.info(f"[Auth] ✅ 用户{username}存在于config.json")

        # 创建JWT token
        logger.info(f"[Auth] 步骤4: 创建JWT token")
        jwt_token = create_access_token(
            data={"sub": username, "type": "user", "twitch_id": user_id},
            expires_delta=timedelta(hours=settings.jwt_expiration_hours)
        )
        logger.info(f"[Auth] ✅ JWT token创建成功")

        # 保存会话（使用username作为user_id）
        logger.info(f"[Auth] 步骤5: 保存会话到数据库")
        expires_at = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
        session = SessionModel(
            user_id=username,  # 使用Twitch username
            user_type="user",
            token=jwt_token,
            expires_at=expires_at
        )
        db.add(session)
        db.commit()
        logger.info(f"[Auth] ✅ 会话保存成功，过期时间: {expires_at}")

        logger.info(f"[Auth] ✅ 用户{username}登录成功！")
        return TokenResponse(access_token=jwt_token)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )

