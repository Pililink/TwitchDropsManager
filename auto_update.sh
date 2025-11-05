#!/bin/bash
# 自动更新脚本 - 更新 TwitchDropsBot 和 Web 管理平台
# 功能：更新所有服务到最新版本并重新构建

set -e  # 遇到错误立即退出

cd /root/twitch

echo "=========================================="
echo "开始更新系统..."
echo "=========================================="

# 1. 停止所有服务
echo ""
echo "停止所有服务..."
docker compose down

# 2. 更新 TwitchDropsBot
echo ""
echo "更新 TwitchDropsBot..."
if [ -d "./TwitchDropsBot" ]; then
    cd ./TwitchDropsBot
    echo "拉取最新代码..."
    git pull
    cd ..
else
    echo "TwitchDropsBot 目录不存在，正在克隆仓库..."
    git clone https://github.com/Alorf/TwitchDropsBot.git TwitchDropsBot
fi

# 3. 构建前端（如果存在前端目录）
echo ""
echo "检查前端目录..."
if [ -d "./web-frontend" ]; then
    echo "构建前端..."
    
    # 尝试使用 Docker 构建（推荐方式）
    if docker build --target builder -t twitch-web-frontend-builder ./web-frontend 2>/dev/null; then
        echo "使用 Docker 构建前端..."
        CONTAINER_ID=$(docker create twitch-web-frontend-builder)
        docker cp "${CONTAINER_ID}:/app/dist" ./dist-temp
        docker rm "${CONTAINER_ID}"
        
        mkdir -p ./web-backend/static
        rm -rf ./web-backend/static/*
        
        if [ -d "./dist-temp" ]; then
            mv ./dist-temp/* ./web-backend/static/
            rmdir ./dist-temp 2>/dev/null || rm -rf ./dist-temp
        fi
        echo "前端构建完成，文件已复制到 web-backend/static/"
    # 如果 Docker 构建失败，尝试使用本地 npm
    elif command -v npm &> /dev/null; then
        echo "Docker 构建失败，使用本地 npm 构建..."
        cd ./web-frontend
        npm install
        npm run build
        cd ..
        
        mkdir -p ./web-backend/static
        rm -rf ./web-backend/static/*
        if [ -d "./web-frontend/dist" ]; then
            cp -r ./web-frontend/dist/* ./web-backend/static/
            echo "前端构建完成，文件已复制到 web-backend/static/"
        fi
    else
        echo "警告: 无法构建前端（Docker 和 npm 都不可用），跳过前端构建"
    fi
else
    echo "前端目录不存在，跳过前端构建"
fi

# 4. 确保必要的目录和文件存在
echo ""
echo "检查必要的目录和文件..."

# 创建 logs 目录
if [ ! -d "./logs" ]; then
    mkdir -p ./logs
    echo "创建 logs 目录"
fi

# 确保 web-backend/static 目录存在
if [ ! -d "./web-backend/static" ]; then
    mkdir -p ./web-backend/static
    echo "创建 web-backend/static 目录"
fi

# 确保 web-backend/logs 目录存在（后端可能需要）
if [ ! -d "./web-backend/logs" ]; then
    mkdir -p ./web-backend/logs
    echo "创建 web-backend/logs 目录"
fi

# 5. 设置文件权限
echo ""
echo "设置文件权限..."

if [ -f "./config.json" ]; then
    chmod 666 ./config.json
    echo "config.json 权限已更新"
fi

chmod -R 777 ./logs
echo "logs 目录权限已更新"

# 6. 清理旧的 Docker 镜像（可选）
echo ""
echo "清理未使用的 Docker 镜像..."
docker image prune -f

# 7. 构建所有服务
echo ""
echo "构建所有服务..."
docker compose build

# 8. 启动所有服务
echo ""
echo "启动所有服务..."
docker compose up -d

# 9. 显示服务状态
echo ""
echo "=========================================="
echo "更新完成！"
echo "=========================================="
echo ""
echo "服务状态："
docker compose ps
echo ""
echo "访问 Web 界面: http://localhost:8000"
echo ""
echo "查看日志："
echo "  docker compose logs -f"
echo "  docker compose logs -f web    # 仅查看 Web 服务日志"
echo "  docker compose logs -f drop   # 仅查看 Bot 服务日志"
echo "=========================================="
