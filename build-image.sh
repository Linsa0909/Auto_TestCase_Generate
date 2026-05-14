#!/bin/bash
# ==========================================
#  Test Case Intelligence - 镜像构建脚本
# ==========================================
set -e
cd "$(dirname "$0")"

IMAGE_NAME="${IMAGE_NAME:-test-case-intel}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
FULL_IMAGE="${IMAGE_NAME}:${IMAGE_TAG}"

echo ">>> 构建 Docker 镜像: ${FULL_IMAGE}"
docker build -t "${FULL_IMAGE}" .

echo ""
echo ">>> 构建完成: ${FULL_IMAGE}"
echo ""

# --- Option: export as tar ---
if [ "$1" = "export" ] || [ "$1" = "tar" ]; then
    TAR_FILE="test-case-intel-${IMAGE_TAG}.tar"
    echo ">>> 导出镜像为: ${TAR_FILE}"
    docker save -o "${TAR_FILE}" "${FULL_IMAGE}"
    ls -lh "${TAR_FILE}"
    echo ""
    echo ">>> 将 ${TAR_FILE} 发送给同事，同事执行："
    echo "    docker load < ${TAR_FILE}"
    echo "    docker run -d -p 8000:8000 -v ./data:/app/data --name test-case-intel ${FULL_IMAGE}"
fi

# --- Option: push to GitHub Container Registry ---
if [ "$1" = "push" ]; then
    GHCR_IMAGE="ghcr.io/linsa0909/test-case-intel:${IMAGE_TAG}"
    echo ">>> 推送到 GitHub Container Registry: ${GHCR_IMAGE}"
    docker tag "${FULL_IMAGE}" "${GHCR_IMAGE}"
    docker push "${GHCR_IMAGE}"
    echo ""
    echo ">>> 同事拉取并运行："
    echo "    docker run -d -p 8000:8000 -v ./data:/app/data --name test-case-intel ${GHCR_IMAGE}"
fi
