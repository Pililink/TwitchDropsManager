"""config.json管理服务"""
import json
import fcntl
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from app.config import settings


class ConfigService:
    """配置文件管理服务"""
    
    def __init__(self):
        self.config_path = Path(settings.config_file_path)
        self._cache: Optional[Dict[str, Any]] = None
        self._last_modified: float = 0
    
    def _read_config(self) -> Dict[str, Any]:
        """读取配置文件（带文件锁）"""
        if not self.config_path.exists():
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                # 尝试获取读锁（非阻塞）
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
                    data = json.load(f)
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    return data
                except BlockingIOError:
                    # 如果文件被锁定，返回缓存或默认配置
                    if self._cache:
                        return self._cache
                    return self._get_default_config()
        except (json.JSONDecodeError, IOError) as e:
            # 如果读取失败，返回缓存或默认配置
            if self._cache:
                return self._cache
            return self._get_default_config()
    
    def _write_config(self, data: Dict[str, Any]) -> bool:
        """写入配置文件（带文件锁）"""
        try:
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # 直接写入文件（带重试机制）
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    with open(self.config_path, 'w', encoding='utf-8') as f:
                        # 获取写锁（阻塞，最多等待2秒）
                        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                        json.dump(
                            data,
                            f,
                            indent=2,
                            ensure_ascii=False  # 等效于JavaScriptEncoder.UnsafeRelaxedJsonEscaping
                        )
                        f.flush()
                        os.fsync(f.fileno())
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)

                    self._cache = data
                    self._last_modified = os.path.getmtime(self.config_path)
                    return True
                except (IOError, OSError) as e:
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(0.5)  # 等待500ms后重试
                        continue
                    raise

            return False
        except Exception as e:
            print(f"写入配置文件失败: {e}")
            return False
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置结构"""
        return {
            "Users": [],
            "FavouriteGames": [],
            "AvoidCampaign": [],
            "OnlyFavouriteGames": False,
            "LaunchOnStartup": False,
            "MinimizeInTray": True,
            "ForceTryWithTags": False,
            "OnlyConnectedAccounts": False,
            "LogLevel": 0,
            "WebhookURL": None,
            "waitingSeconds": 300,
            "AttemptToWatch": 3,
            "WatchManagerConfig": {
                "WatchManager": "WatchRequest",
                "headless": True
            }
        }
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置（带缓存）"""
        if self.config_path.exists():
            current_modified = os.path.getmtime(self.config_path)
            if current_modified != self._last_modified or self._cache is None:
                self._cache = self._read_config()
                self._last_modified = current_modified
        else:
            self._cache = self._get_default_config()
        
        return self._cache.copy()
    
    def get_users(self) -> List[Dict[str, Any]]:
        """获取用户列表"""
        config = self.get_config()
        return config.get("Users", [])
    
    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取用户"""
        users = self.get_users()
        for user in users:
            if user.get("Id") == user_id:
                return user
        return None
    
    def get_user_by_login(self, login: str) -> Optional[Dict[str, Any]]:
        """根据Login获取用户"""
        users = self.get_users()
        for user in users:
            if user.get("Login") == login:
                return user
        return None
    
    def add_user(self, user_data: Dict[str, Any]) -> bool:
        """添加用户"""
        config = self.get_config()
        users = config.get("Users", [])
        
        # 检查用户是否已存在
        user_id = user_data.get("Id")
        existing_user = self.get_user_by_id(user_id)
        if existing_user:
            # 更新现有用户
            users = [u for u in users if u.get("Id") != user_id]
        
        # 确保必需字段存在
        required_fields = ["Login", "Id", "ClientSecret", "UniqueId"]
        if not all(field in user_data for field in required_fields):
            return False
        
        # 添加默认值
        if "Enabled" not in user_data:
            user_data["Enabled"] = True
        if "FavouriteGames" not in user_data:
            user_data["FavouriteGames"] = []
        
        users.append(user_data)
        config["Users"] = users
        
        return self._write_config(config)
    
    def delete_user(self, user_id: str) -> bool:
        """删除用户"""
        config = self.get_config()
        users = config.get("Users", [])
        users = [u for u in users if u.get("Id") != user_id]
        config["Users"] = users
        
        return self._write_config(config)
    
    def update_user_enabled(self, user_id: str, enabled: bool) -> bool:
        """更新用户启用状态"""
        config = self.get_config()
        users = config.get("Users", [])
        
        for user in users:
            if user.get("Id") == user_id:
                user["Enabled"] = enabled
                return self._write_config(config)
        
        return False
    
    def update_user_favourite_games(self, user_id: str, favourite_games: List[str]) -> bool:
        """更新用户优先游戏列表"""
        config = self.get_config()
        users = config.get("Users", [])
        
        for user in users:
            if user.get("Id") == user_id:
                user["FavouriteGames"] = favourite_games
                return self._write_config(config)
        
        return False
    
    def update_global_config(self, updates: Dict[str, Any]) -> bool:
        """更新全局配置"""
        config = self.get_config()
        
        # 只允许更新特定字段
        allowed_fields = [
            "FavouriteGames", "AvoidCampaign", "OnlyFavouriteGames",
            "LaunchOnStartup", "MinimizeInTray", "ForceTryWithTags",
            "OnlyConnectedAccounts", "LogLevel", "WebhookURL",
            "waitingSeconds", "AttemptToWatch", "WatchManagerConfig"
        ]
        
        for key, value in updates.items():
            if key in allowed_fields:
                config[key] = value
        
        return self._write_config(config)


config_service = ConfigService()

