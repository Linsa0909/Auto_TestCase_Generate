#!/bin/bash
# ==========================================
#  Test Case Intelligence - 镜像构建 & 导出
#  参照 poc 项目打包流程
# ==========================================
set -e
cd "$(dirname "$0")"

IMAGE_NAME="test-case-intel"
IMAGE_TAG="${1:-latest}"
FULL_IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"
TAR_FILE="test-case-intel_x86_${IMAGE_TAG}.tar"

echo "=========================================="
echo "  第一阶段：构建镜像"
echo "=========================================="
echo ">>> docker build -t ${FULL_IMAGE} ."
# Auto-detect proxy for WSL
_PROXY_ARGS=""
_HOST_IP=$(ip route show default 2>/dev/null | awk '{print $3}' | head -1)
if [ -n "$_HOST_IP" ]; then
    _PROXY_ARGS="--build-arg HTTP_PROXY=http://${_HOST_IP}:7890 --build-arg HTTPS_PROXY=http://${_HOST_IP}:7890 --build-arg http_proxy=http://${_HOST_IP}:7890 --build-arg https_proxy=http://${_HOST_IP}:7890"
    echo ">>> 使用代理: ${_HOST_IP}:7890"
fi
docker build ${_PROXY_ARGS} -t "${FULL_IMAGE}" .
echo ""
echo ">>> 构建完成: ${FULL_IMAGE}"
echo ""

# 验货
echo "=========================================="
echo "  验货：检查镜像内容"
echo "=========================================="
docker run --rm "${FULL_IMAGE}" ls -la /app
echo ""

# 导出
echo "=========================================="
echo "  导出为离线压缩包"
echo "=========================================="
docker save -o "${TAR_FILE}" "${FULL_IMAGE}"
ls -lh "${TAR_FILE}"
echo ""

echo "=========================================="
echo "  构建完成！"
echo "=========================================="
echo ""
echo "  发给同事的文件："
echo "    - ${TAR_FILE}"
echo ""
echo "  同事部署命令："
echo "    # 1. 加载镜像"
echo "    docker load -i ${TAR_FILE}"
echo ""
echo "    # 2. 查看镜像是否加载成功"
echo "    docker images | grep ${IMAGE_NAME}"
echo ""
echo "    # 3. 创建数据目录"
echo "    mkdir -p data"
echo ""
echo "    # 4. 启动"
echo "    docker run -d \\"
echo "      --name ${IMAGE_NAME} \\"
echo "      --restart unless-stopped \\"
echo "      -p 8000:8000 \\"
echo "      -v \$(pwd)/data:/app/data \\"
echo "      ${FULL_IMAGE}"
echo ""
echo "    # 5. 查看日志"
echo "    docker logs -f ${IMAGE_NAME}"
echo ""
echo "    # 6. 停止 / 删除"
echo "    docker stop ${IMAGE_NAME} && docker rm ${IMAGE_NAME}"
echo ""
