#!/bin/bash
# ==========================================
#  Test Case Intelligence - Docker 一键部署
# ==========================================
set -e

IMAGE_NAME="${1:-test-case-intel:latest}"
CONTAINER_NAME="test-case-intel"
DATA_DIR="./data"

echo "=========================================="
echo "  Test Case Intelligence 部署"
echo "=========================================="

# 数据目录
mkdir -p "${DATA_DIR}/output"

# 停止旧容器
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo ">>> 停止旧容器..."
    docker stop "${CONTAINER_NAME}" 2>/dev/null || true
    docker rm "${CONTAINER_NAME}" 2>/dev/null || true
fi

echo ">>> 启动容器: ${IMAGE_NAME}"
docker run -d \
    --name "${CONTAINER_NAME}" \
    --restart unless-stopped \
    -p 8000:8000 \
    -v "$(pwd)/${DATA_DIR}:/app/data" \
    -e TZ=Asia/Shanghai \
    "${IMAGE_NAME}"

echo ""
echo "=========================================="
echo "  部署完成"
echo "  前端页面: http://localhost:8000"
echo "  API 文档: http://localhost:8000/docs"
echo "=========================================="
echo ""
echo "  docker logs -f ${CONTAINER_NAME}    # 查看日志"
echo "  docker stop ${CONTAINER_NAME}       # 停止"
echo "  docker restart ${CONTAINER_NAME}    # 重启"
