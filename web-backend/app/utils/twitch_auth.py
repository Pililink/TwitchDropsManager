"""Twitch OAuth认证工具"""
import httpx
import asyncio
import logging
from typing import Optional, Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)


class TwitchAuth:
    """Twitch OAuth设备流认证"""

    def __init__(self):
        self.client_id = settings.twitch_client_id
        self.device_code_url = "https://id.twitch.tv/oauth2/device"
        self.token_url = "https://id.twitch.tv/oauth2/token"
        self.validate_url = "https://id.twitch.tv/oauth2/validate"
        self.mobile_url = "https://m.twitch.tv"
        logger.info(f"[TwitchAuth] 初始化完成，client_id={self.client_id[:20]}...")

    async def get_device_code(self) -> Dict[str, Any]:
        """获取设备码（等效于C#的AuthSystem.GetCodeAsync）"""
        print(f"[TwitchAuth] 开始获取设备码，client_id={self.client_id[:20]}...")
        logger.info(f"[TwitchAuth] 开始获取设备码，client_id={self.client_id[:20]}...")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.device_code_url,
                data={
                    "client_id": self.client_id,
                    "scopes": ""
                }
            )
            response.raise_for_status()
            result = response.json()
            print(f"[TwitchAuth] 设备码获取成功: user_code={result.get('user_code')}, device_code={result.get('device_code')[:20]}...")
            logger.info(f"[TwitchAuth] 设备码获取成功: user_code={result.get('user_code')}, device_code={result.get('device_code')[:20]}...")
            return result
    
    async def poll_authorization(
        self,
        device_code: str,
        interval: int = 5,
        timeout: int = 900
    ) -> Optional[Dict[str, Any]]:
        """轮询授权状态（等效于C#的AuthSystem.CodeConfirmationAsync）"""
        logger.info(f"[TwitchAuth] 开始轮询授权状态，device_code={device_code[:20]}..., interval={interval}s")
        async with httpx.AsyncClient(timeout=timeout) as client:
            start_time = asyncio.get_event_loop().time()
            poll_count = 0

            while True:
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > timeout:
                    logger.warning(f"[TwitchAuth] 轮询超时 ({timeout}s)，已轮询{poll_count}次")
                    return None

                try:
                    poll_count += 1
                    response = await client.post(
                        self.token_url,
                        data={
                            "client_id": self.client_id,
                            "device_code": device_code,
                            "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                        }
                    )

                    if response.status_code == 200:
                        result = response.json()
                        logger.info(f"[TwitchAuth] ✅ 授权成功！已轮询{poll_count}次，耗时{elapsed:.1f}s")
                        return result
                    elif response.status_code == 400:
                        data = response.json()
                        error = data.get("error")
                        if error == "authorization_pending":
                            logger.debug(f"[TwitchAuth] 等待授权中... (第{poll_count}次轮询)")
                            await asyncio.sleep(interval)
                            continue
                        elif error == "slow_down":
                            logger.warning(f"[TwitchAuth] 收到slow_down，增加轮询间隔")
                            interval += 5
                            await asyncio.sleep(interval)
                            continue
                        else:
                            logger.error(f"[TwitchAuth] ❌ 授权失败: error={error}, message={data.get('message')}")
                            return None
                    else:
                        logger.error(f"[TwitchAuth] ❌ 意外的响应状态码: {response.status_code}, body={response.text[:200]}")
                        return None
                except Exception as e:
                    logger.error(f"[TwitchAuth] ❌ 轮询异常: {str(e)}")
                    return None
    
    async def validate_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """验证访问令牌"""
        logger.info(f"[TwitchAuth] 验证访问令牌，token={access_token[:20]}...")
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.validate_url,
                headers={"Authorization": f"OAuth {access_token}"}
            )
            if response.status_code == 200:
                result = response.json()
                logger.info(f"[TwitchAuth] ✅ Token验证成功: user={result.get('login')}, user_id={result.get('user_id')}")
                return result
            else:
                logger.error(f"[TwitchAuth] ❌ Token验证失败: status={response.status_code}, body={response.text[:200]}")
            return None
    
    async def get_unique_id(self, access_token: str) -> Optional[str]:
        """获取Unique ID（等效于C#的ClientSecretUserAsync中的UniqueId获取）"""
        logger.info(f"[TwitchAuth] 获取Unique ID")
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.mobile_url,
                headers={
                    "Accept": "*/*",
                    "Authorization": f"OAuth {access_token}"
                }
            )
            if response.status_code == 200:
                cookies = response.headers.get("Set-Cookie", "")
                for cookie in cookies.split(","):
                    if "unique_id=" in cookie:
                        unique_id = cookie.split("unique_id=")[1].split(";")[0]
                        logger.info(f"[TwitchAuth] ✅ Unique ID获取成功: {unique_id[:20]}...")
                        return unique_id
                logger.warning(f"[TwitchAuth] ⚠️  Cookie中未找到unique_id")
            else:
                logger.error(f"[TwitchAuth] ❌ 获取Unique ID失败: status={response.status_code}")
            return None

    async def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """获取用户完整信息"""
        logger.info(f"[TwitchAuth] 获取用户完整信息")
        # 验证token并获取用户信息
        validate_data = await self.validate_token(access_token)
        if not validate_data:
            logger.error(f"[TwitchAuth] ❌ Token验证失败，无法获取用户信息")
            return None

        # 获取Unique ID
        unique_id = await self.get_unique_id(access_token)
        if not unique_id:
            logger.error(f"[TwitchAuth] ❌ Unique ID获取失败")
            return None

        result = {
            "login": validate_data.get("login"),
            "user_id": validate_data.get("user_id"),
            "client_secret": access_token,
            "unique_id": unique_id
        }
        logger.info(f"[TwitchAuth] ✅ 用户完整信息获取成功: {result.get('login')}")
        return result


twitch_auth = TwitchAuth()

