"""应用配置管理"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用设置"""
    
    # 管理员账户
    admin_username: str = "admin"
    admin_password: str = "admin"
    admin_password_hash: Optional[str] = None
    
    # JWT配置
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # 服务器配置
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    
    # 数据库
    database_url: str = "sqlite:///./app.db"
    
    # 文件路径
    config_file_path: str = "./config.json"
    logs_directory: str = "./logs"
    
    # CORS
    cors_origins: list[str] = ["http://localhost:8080", "http://localhost:3000"]
    
    # Twitch OAuth (使用Android App的客户端ID)
    twitch_client_id: str = "kimne78kx3ncx6brgo4mv6wki5h1ko"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

