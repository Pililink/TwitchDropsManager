"""定时任务服务 - 管理Bot容器的定时重启"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional


class SchedulerService:
    """定时任务服务"""

    def __init__(self):
        # 每天凌晨4点重启（可配置）
        self.restart_hour = 4
        self.restart_minute = 0
        self._next_restart_time: Optional[datetime] = None
        self._restart_task: Optional[asyncio.Task] = None
        print(f"[Scheduler] 初始化定时任务服务，重启时间：每天 {self.restart_hour:02d}:{self.restart_minute:02d}")

    def calculate_next_restart_time(self) -> datetime:
        """计算下一次重启时间"""
        now = datetime.now()
        # 今天的重启时间
        today_restart = now.replace(
            hour=self.restart_hour,
            minute=self.restart_minute,
            second=0,
            microsecond=0
        )

        if now < today_restart:
            # 如果还没到今天的重启时间，就是今天
            next_restart = today_restart
        else:
            # 否则是明天
            next_restart = today_restart + timedelta(days=1)

        self._next_restart_time = next_restart
        print(f"[Scheduler] 下一次重启时间: {next_restart.strftime('%Y-%m-%d %H:%M:%S')}")
        return next_restart

    def get_next_restart_time(self) -> Optional[datetime]:
        """获取下一次重启时间"""
        if self._next_restart_time is None:
            return self.calculate_next_restart_time()
        return self._next_restart_time

    async def _wait_and_restart(self):
        """等待并执行重启"""
        while True:
            try:
                next_restart = self.calculate_next_restart_time()
                now = datetime.now()
                wait_seconds = (next_restart - now).total_seconds()

                print(f"[Scheduler] 距离下次重启还有 {wait_seconds:.0f} 秒")

                # 等待到重启时间
                await asyncio.sleep(wait_seconds)

                # 执行重启
                print(f"[Scheduler] ⏰ 定时重启时间到，开始重启Bot容器...")
                from app.services.docker_service import docker_service
                result = await docker_service.restart_drop_container()

                if result.get("status") == "success":
                    print(f"[Scheduler] ✅ 定时重启成功")
                else:
                    print(f"[Scheduler] ❌ 定时重启失败: {result.get('message')}")

            except Exception as e:
                print(f"[Scheduler] ❌ 定时重启异常: {str(e)}")
                import traceback
                traceback.print_exc()
                # 发生错误后等待1小时再试
                await asyncio.sleep(3600)

    def start(self):
        """启动定时任务"""
        if self._restart_task is None:
            print("[Scheduler] 启动定时重启任务...")
            self._restart_task = asyncio.create_task(self._wait_and_restart())
        else:
            print("[Scheduler] 定时任务已在运行中")

    def stop(self):
        """停止定时任务"""
        if self._restart_task:
            print("[Scheduler] 停止定时重启任务...")
            self._restart_task.cancel()
            self._restart_task = None


scheduler_service = SchedulerService()
