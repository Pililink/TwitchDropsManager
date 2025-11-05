#!/bin/bash
# 使用Docker构建前端并复制到后端静态目录

set -e

echo "=========================================="
echo "使用Docker构建前端..."
echo "=========================================="

# 进入前端目录
cd "$(dirname "$0")/web-frontend"

# 构建Docker镜像
echo "构建前端Docker镜像..."
docker build --target builder -t twitch-web-frontend-builder .

# 创建临时容器并复制dist目录
echo "从Docker容器复制构建文件..."
CONTAINER_ID=$(docker create twitch-web-frontend-builder)
docker cp "${CONTAINER_ID}:/app/dist" ../dist-temp
docker rm "${CONTAINER_ID}"

# 返回项目根目录
cd ..

# 确保目标目录存在
mkdir -p web-backend/static

# 清空旧文件
rm -rf web-backend/static/*

# 移动新文件
if [ -d "dist-temp" ]; then
  mv dist-temp/* web-backend/static/
  rmdir dist-temp
fi

echo "=========================================="
echo "前端构建完成！"
echo "=========================================="
echo "构建文件已复制到: web-backend/static/"
echo ""
echo "下一步："
echo "  docker compose up -d"
echo "  访问: http://localhost:8000"
echo "=========================================="
