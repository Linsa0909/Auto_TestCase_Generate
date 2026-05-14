#!/bin/bash
# ==========================================
#  Test Case Intelligence - 一键部署运行
#  同事拿到镜像后执行此脚本
# ==========================================
set -e

IMAGE_NAME="${1:-test-case-intel:latest}"
CONTAINER_NAME="test-case-intel"
DATA_DIR="./data"

echo "=========================================="
echo "  Test Case Intelligence 部署"
echo "=========================================="
echo ""

# 确保数据目录存在
mkdir -p "${DATA_DIR}/output"

# 停止并删除旧容器（如果存在）
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
echo "  查看日志: docker logs -f ${CONTAINER_NAME}"
echo "  停止服务: docker stop ${CONTAINER_NAME}"
echo "  重启服务: docker restart ${CONTAINER_NAME}"
