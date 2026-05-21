#!/bin/bash
# ==========================================
#  Test Case Intelligence - 镜像构建 & 导出
#  使用国内源，无需代理
# ==========================================
set -e
cd "$(dirname "$0")"

IMAGE_NAME="test-case-intel"
IMAGE_TAG="${1:-latest}"
FULL_IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"
TAR_FILE="test-case-intel_x86_${IMAGE_TAG}.tar"

echo "=========================================="
echo "  构建镜像: ${FULL_IMAGE}"
echo "  使用国内源 (npm=淘宝, pip=清华, apt=中科大)"
echo "=========================================="

docker build -t "${FULL_IMAGE}" .

echo ""
echo ">>> 构建完成: ${FULL_IMAGE}"
echo ""

# 验货
echo "=========================================="
echo "  验货：检查镜像内容"
echo "=========================================="
docker run --rm "${FULL_IMAGE}" ls -la /app
docker run --rm "${FULL_IMAGE}" ls -la /app/static
echo ""

# 导出（可选）
if [ "${1}" = "export" ] || [ "${2}" = "export" ]; then
    echo "=========================================="
    echo "  导出为离线压缩包"
    echo "=========================================="
    docker save -o "${TAR_FILE}" "${FULL_IMAGE}"
    ls -lh "${TAR_FILE}"
    echo ""
    echo "  发给同事的文件: ${TAR_FILE}"
    echo ""
    echo "  同事部署:"
    echo "    docker load -i ${TAR_FILE}"
    echo "    ./deploy-run.sh ${FULL_IMAGE}"
fi

echo "=========================================="
echo "  构建完成！"
echo "=========================================="
