"""Docker命令调用服务 - 用于调用C# bot命令"""
import asyncio
import subprocess
import re
from typing import Dict, Optional


class DockerService:
    """Docker服务：通过docker compose调用C# bot命令"""

    def __init__(self):
        self.container_name = "drop"
        self._add_account_process = None
        self._add_account_output = []

    async def execute_add_account(self) -> Dict[str, str]:
        """
        调用C# bot的 --add-account 命令并捕获输出
        提取Twitch OAuth的授权链接和代码
        """
        try:
            print("[DockerService] 执行 add_account 命令...")

            # 构建命令（使用docker-compose调用C# bot）
            cmd = [
                "/usr/local/bin/docker-compose",
                "-f", "/root/twitch/compose.yml",
                "exec", "-T", "drop",
                "dotnet", "TwitchDropsBot.Console.dll", "--add-account"
            ]

            print(f"[DockerService] 执行命令: {' '.join(cmd)}")

            # 启动进程并捕获输出
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                stdin=asyncio.subprocess.PIPE
            )

            self._add_account_process = process
            self._add_account_output = []

            # 自动发送 'Y' 确认（bot可能会询问是否继续）
            try:
                process.stdin.write(b'Y\n')
                await process.stdin.drain()
                print("[DockerService] 已自动发送确认 'Y'")
            except Exception as e:
                print(f"[DockerService] 发送确认失败（可能不需要）: {e}")

            # 读取输出直到获取到授权信息（最多等待30秒）
            auth_info = None
            start_time = asyncio.get_event_loop().time()
            timeout = 30

            while True:
                if asyncio.get_event_loop().time() - start_time > timeout:
                    print("[DockerService] 等待超时")
                    break

                try:
                    line = await asyncio.wait_for(
                        process.stdout.readline(),
                        timeout=5.0
                    )
                    if not line:
                        break

                    line_str = line.decode('utf-8', errors='ignore').strip()
                    self._add_account_output.append(line_str)
                    print(f"[DockerService] Bot输出: {line_str}")

                    # 提取授权信息
                    # 查找类似：https://www.twitch.tv/activate?device-code=BGVRDDZK and enter the code: BGVRDDZK
                    if 'twitch.tv/activate' in line_str.lower():
                        url_match = re.search(r'(https://[^\s]+)', line_str)
                        if url_match:
                            url = url_match.group(1)
                            # 尝试从URL提取代码（device-code或user_code参数）
                            code_match = re.search(r'(?:device-code|user_code)=([A-Z0-9\-]+)', url, re.IGNORECASE)
                            code = None
                            if code_match:
                                code = code_match.group(1)

                            # 如果URL中没找到，尝试从消息中提取 "enter the code: XXXX"
                            if not code:
                                code_match = re.search(r'enter the code[:\s]+([A-Z0-9\-]+)', line_str, re.IGNORECASE)
                                if code_match:
                                    code = code_match.group(1)

                            if code:
                                auth_info = {
                                    "verification_uri": url,
                                    "user_code": code
                                }
                                print(f"[DockerService] ✅ 提取到授权信息: {auth_info}")
                                break

                    # 或者查找分开的URL和代码
                    if 'please go to:' in line_str.lower() or 'visit:' in line_str.lower():
                        # 继续读取下一行获取URL
                        continue

                except asyncio.TimeoutError:
                    continue

            if auth_info:
                return {
                    "status": "success",
                    "verification_uri": auth_info["verification_uri"],
                    "user_code": auth_info["user_code"],
                    "message": "请访问链接并输入代码完成授权"
                }
            else:
                # 如果没有提取到授权信息，返回收集到的输出
                output_text = "\n".join(self._add_account_output[-10:])  # 最后10行
                print(f"[DockerService] ⚠️ 未能提取授权信息，Bot输出:\n{output_text}")
                return {
                    "status": "initiated",
                    "message": "命令已执行，请查看Docker日志获取授权信息",
                    "bot_output": output_text
                }

        except Exception as e:
            import traceback
            traceback.print_exc()
            raise Exception(f"调用add_account命令失败: {str(e)}")

    async def check_user_added(self, username: str, max_wait: int = 300) -> Optional[Dict]:
        """
        监控config.json，检查用户是否已被C# bot添加

        参数:
            username: Twitch用户名
            max_wait: 最大等待时间（秒）
        """
        from app.services.config_service import config_service

        wait_time = 0
        while wait_time < max_wait:
            user = config_service.get_user_by_login(username)
            if user:
                return user

            await asyncio.sleep(5)  # 每5秒检查一次
            wait_time += 5

        return None

    async def restart_drop_container(self) -> Dict[str, str]:
        """
        重启drop容器（C# bot）
        """
        try:
            print("[DockerService] 准备重启drop容器...")

            # 构建重启命令
            cmd = [
                "/usr/local/bin/docker-compose",
                "-f", "/root/twitch/compose.yml",
                "restart", "drop"
            ]

            print(f"[DockerService] 执行命令: {' '.join(cmd)}")

            # 执行重启命令
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT
            )

            stdout, _ = await process.communicate()
            output = stdout.decode('utf-8', errors='ignore').strip()

            if process.returncode == 0:
                print(f"[DockerService] ✅ drop容器重启成功")
                return {
                    "status": "success",
                    "message": "drop容器已重启",
                    "output": output
                }
            else:
                print(f"[DockerService] ❌ drop容器重启失败: {output}")
                return {
                    "status": "error",
                    "message": f"重启失败: {output}",
                    "output": output
                }

        except Exception as e:
            print(f"[DockerService] ❌ 重启容器异常: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"重启容器失败: {str(e)}")


docker_service = DockerService()
