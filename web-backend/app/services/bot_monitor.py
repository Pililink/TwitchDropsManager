"""Bot状态监控服务"""
import re
import os
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from app.config import settings


class BotStatusMonitor:
    """Bot状态监控 - 支持增量读取"""

    def __init__(self):
        self.logs_dir = Path(settings.logs_directory)
        self._status_cache: Dict[str, Dict] = {}
        # 记录每个用户日志文件的读取位置 {username: (file_pos, file_size, inode)}
        self._file_positions: Dict[str, Tuple[int, int, int]] = {}
        # 记录每个用户的完整消息历史（用于状态判断）
        self._message_history: Dict[str, List[str]] = {}
        print("[BotMonitor] 初始化完成，启用增量读取模式")
    
    def _parse_log_line(self, line: str) -> Optional[Dict]:
        """解析单行日志"""
        # 日志格式: YYYY-MM-DD HH:mm:ss.fff +TZ [LEVEL] [username] : message
        # 注意：时区前有空格，例如 "2025-11-04 11:05:56.241 +08:00"
        pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}) ([+\-]\d{2}:\d{2}) \[(\w+)\] \[(\w+)\] : (.+)'
        match = re.match(pattern, line)
        
        if match:
            timestamp_str, timezone_str, level, username, message = match.groups()
            # 组合时间戳和时区
            full_timestamp = f"{timestamp_str}{timezone_str}"
            try:
                timestamp = datetime.strptime(full_timestamp, "%Y-%m-%d %H:%M:%S.%f%z")
            except:
                # 如果解析失败，尝试不带时区
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S.%f")
                except:
                    timestamp = None
            
            return {
                "timestamp": timestamp,
                "level": level,
                "username": username,
                "message": message
            }
        return None
    
    def _determine_status(self, messages: List[str]) -> str:
        """根据日志消息确定状态"""
        # 查找最新的状态相关消息
        for msg in reversed(messages[-50:]):  # 查看最近50条消息
            if "[ERR]" in msg or "Error" in msg:
                return "Error"
            
            if "No campaign found" in msg or "No broadcaster or campaign left" in msg:
                if "Waiting" in msg:
                    return "Idle"
            
            if "Current drop campaign" in msg or "watching" in msg.lower():
                return "Watching"
            
            if "minutes watched" in msg.lower():
                return "Watching"
            
            if "Checking" in msg and "..." in msg:
                return "Seeking"
        
        # 默认状态
        if "Waiting" in " ".join(messages[-10:]):
            return "Idle"
        return "Unknown"
    
    def _extract_campaign_info(self, messages: List[str]) -> Optional[Dict]:
        """提取Campaign信息"""
        # 增加搜索范围到最近500条消息，因为bot持续观看时可能很久才输出一次campaign信息
        search_range = messages[-500:] if len(messages) > 500 else messages

        # 查找 "Current drop campaign: {campaign} ({game}), watching ..."
        pattern2 = r'Current drop campaign: (.+?) \((.+?)\)'
        for msg in reversed(search_range):
            match = re.search(pattern2, msg)
            if match:
                campaign = match.group(1)
                game = match.group(2)
                return {
                    "game": game,
                    "campaign": campaign
                }

        # 查找 "Checking {Game} ({Campaign})..."
        pattern = r'Checking (.+?) \((.+?)\)\.\.\.'
        for msg in reversed(search_range):
            match = re.search(pattern, msg)
            if match:
                game = match.group(1)
                campaign = match.group(2)
                return {
                    "game": game,
                    "campaign": campaign
                }

        return None
    
    def _extract_broadcaster_info(self, messages: List[str]) -> Optional[str]:
        """提取Broadcaster信息"""
        # 增加搜索范围到最近500条消息
        search_range = messages[-500:] if len(messages) > 500 else messages

        # 查找 "watching {broadcaster} | {id}"
        pattern = r'watching (\w+)(?:\s+\|\s+\w+)?'
        for msg in reversed(search_range):
            match = re.search(pattern, msg, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_progress_info(self, messages: List[str]) -> Optional[Dict]:
        """提取进度信息"""
        # 查找 "X/Y minutes watched"（只需要查最近的几条）
        search_range = messages[-100:] if len(messages) > 100 else messages
        pattern = r'(\d+)/(\d+)\s+minutes?\s+watched'
        for msg in reversed(search_range):
            match = re.search(pattern, msg, re.IGNORECASE)
            if match:
                current = int(match.group(1))
                required = int(match.group(2))
                return {
                    "current": current,
                    "required": required,
                    "percentage": (current / required * 100) if required > 0 else 0
                }
        return None
    
    def _read_log_incremental(self, username: str, log_file: Path) -> List[str]:
        """增量读取日志文件，返回新增的行"""
        try:
            stat = os.stat(log_file)
            current_size = stat.st_size
            current_inode = stat.st_ino

            # 获取上次读取的位置
            last_pos, last_size, last_inode = self._file_positions.get(username, (0, 0, 0))

            # 判断是否需要全量读取
            should_full_read = (
                username not in self._file_positions or  # 首次读取
                current_inode != last_inode or  # 文件被重写
                current_size < last_size  # 文件被截断
            )

            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                if should_full_read:
                    # 全量读取（首次或文件变化）
                    print(f"[BotMonitor] {username}: 全量读取日志文件")
                    lines = f.readlines()
                    # 记录新位置
                    self._file_positions[username] = (current_size, current_size, current_inode)
                    return lines
                elif current_size > last_pos:
                    # 增量读取（只读新增内容）
                    f.seek(last_pos)
                    new_lines = f.readlines()
                    print(f"[BotMonitor] {username}: 增量读取 {len(new_lines)} 行新日志")
                    # 更新位置
                    self._file_positions[username] = (current_size, current_size, current_inode)
                    return new_lines
                else:
                    # 文件没有变化
                    return []

        except Exception as e:
            print(f"[BotMonitor] 读取日志文件失败 {log_file}: {e}")
            return []

    def get_user_status(self, username: str) -> Dict:
        """获取用户状态（支持增量更新）"""
        log_file = self.logs_dir / f"{username}.txt"

        if not log_file.exists():
            return {
                "status": "Unknown",
                "last_update": None,
                "campaign": None,
                "broadcaster": None,
                "progress": None,
                "recent_logs": []
            }

        try:
            # 增量读取新日志
            new_lines = self._read_log_incremental(username, log_file)

            # 初始化消息历史（如果不存在）
            if username not in self._message_history:
                self._message_history[username] = []

            # 解析新日志
            parsed_logs = []
            new_messages = []
            last_timestamp = None

            for line in new_lines:
                parsed = self._parse_log_line(line.strip())
                if parsed:
                    parsed_logs.append(parsed)
                    new_messages.append(parsed["message"])
                    last_timestamp = parsed.get("timestamp")

            # 更新消息历史（保留最近1000条）
            if new_messages:
                self._message_history[username].extend(new_messages)
                self._message_history[username] = self._message_history[username][-1000:]

            # 使用完整历史来确定状态
            messages = self._message_history[username]

            # 确定状态
            status = self._determine_status(messages)

            # 提取信息
            campaign_info = self._extract_campaign_info(messages)
            broadcaster = self._extract_broadcaster_info(messages)
            progress = self._extract_progress_info(messages)

            # 获取最后更新时间
            if not last_timestamp and parsed_logs:
                last_timestamp = parsed_logs[-1].get("timestamp")

            # 更新缓存
            result = {
                "status": status,
                "last_update": last_timestamp.isoformat() if last_timestamp else None,
                "campaign": campaign_info,
                "broadcaster": broadcaster,
                "progress": progress,
                "recent_logs": messages[-20:] if messages else []  # 最近20条消息
            }

            self._status_cache[username] = result
            return result

        except Exception as e:
            print(f"[BotMonitor] 获取用户状态失败 {username}: {e}")
            import traceback
            traceback.print_exc()
            # 如果有缓存，返回缓存
            if username in self._status_cache:
                return self._status_cache[username]
            return {
                "status": "Error",
                "last_update": None,
                "campaign": None,
                "broadcaster": None,
                "progress": None,
                "recent_logs": []
            }
    
    def get_all_users_status(self, usernames: List[str]) -> Dict[str, Dict]:
        """获取所有用户状态"""
        result = {}
        for username in usernames:
            result[username] = self.get_user_status(username)
        return result


bot_monitor = BotStatusMonitor()

