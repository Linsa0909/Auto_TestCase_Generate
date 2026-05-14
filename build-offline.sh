#!/bin/bash
# ==========================================
#  Test Case Intelligence - 离线部署包构建
#  目标: 解压即用，无需安装任何依赖
# ==========================================
set -e
cd "$(dirname "$0")"

PACKAGE_NAME="test-case-intel-offline"
PYTHON_VERSION="3.12.13"
PYTHON_RELEASE="20260510"
PYTHON_BUILD="cpython-${PYTHON_VERSION}+${PYTHON_RELEASE}-x86_64-unknown-linux-gnu-install_only.tar.gz"
# Proxy — auto-detect Windows host IP from WSL
if [ -z "$https_proxy" ]; then
    _host_ip=$(ip route show default 2>/dev/null | awk '{print $3}' | head -1)
    [ -n "$_host_ip" ] && export https_proxy="http://${_host_ip}:7890" http_proxy="http://${_host_ip}:7890"
fi

PYTHON_URL_DIRECT="https://github.com/indygreg/python-build-standalone/releases/download/${PYTHON_RELEASE}/${PYTHON_BUILD}"
PYTHON_URL_MIRRORS=(
    "https://ghproxy.com/${PYTHON_URL_DIRECT}"
    "https://mirror.ghproxy.com/${PYTHON_URL_DIRECT}"
    "${PYTHON_URL_DIRECT}"
)
BUILD_DIR="build/offline-package"
CACHE_DIR="build/cache"
PACKAGE_DIR="${BUILD_DIR}/${PACKAGE_NAME}"

echo "=========================================="
echo "  构建离线部署包"
echo "=========================================="

# --- Step 1: Prepare directories ---
echo "[1/7] 准备构建目录..."
rm -rf "${BUILD_DIR}"
mkdir -p "${PACKAGE_DIR}" "${CACHE_DIR}"

# --- Step 2: Download portable Python (cached) ---
echo "[2/7] 下载嵌入式 Python ${PYTHON_VERSION}..."
_download_python() {
    local url="$1"
    echo "  下载: ${url}"
    curl -L --connect-timeout 10 --max-time 300 -o "${CACHE_DIR}/${PYTHON_BUILD}" "${url}"
    # Verify the download is a valid gzip
    if gzip -t "${CACHE_DIR}/${PYTHON_BUILD}" 2>/dev/null; then
        return 0
    fi
    echo "  [WARN] 下载文件损坏，清理缓存重试..."
    rm -f "${CACHE_DIR}/${PYTHON_BUILD}"
    return 1
}

if [ -f "${CACHE_DIR}/${PYTHON_BUILD}" ]; then
    if ! gzip -t "${CACHE_DIR}/${PYTHON_BUILD}" 2>/dev/null; then
        echo "  缓存文件损坏，重新下载..."
        rm -f "${CACHE_DIR}/${PYTHON_BUILD}"
    fi
fi

if [ ! -f "${CACHE_DIR}/${PYTHON_BUILD}" ]; then
    # Try each mirror in order
    _ok=0
    for _url in "${PYTHON_URL_MIRRORS[@]}"; do
        if _download_python "${_url}"; then
            _ok=1
            break
        fi
    done
    if [ "$_ok" -eq 0 ]; then
        echo "  [ERROR] 所有源下载失败，请检查网络后重试"
        exit 1
    fi
fi

echo "  解压 Python..."
tar xzf "${CACHE_DIR}/${PYTHON_BUILD}" -C "${PACKAGE_DIR}"
PYTHON_DIR="${PACKAGE_DIR}/python"
PYTHON_BIN="${PYTHON_DIR}/bin/python3"

# --- Step 3: Install Python dependencies ---
echo "[3/7] 安装 Python 依赖..."
"${PYTHON_BIN}" -m pip install --no-cache-dir --break-system-packages \
    -r backend/requirements.txt

# --- Step 4: Install Playwright Chromium ---
echo "[4/7] 安装 Playwright Chromium..."
export PLAYWRIGHT_BROWSERS_PATH="${PACKAGE_DIR}/playwright-browsers"
mkdir -p "${PLAYWRIGHT_BROWSERS_PATH}"
"${PYTHON_BIN}" -m playwright install chromium

# --- Step 5: Copy backend code ---
echo "[5/7] 复制后端代码..."
mkdir -p "${PACKAGE_DIR}/backend"
cp -r backend/*.py "${PACKAGE_DIR}/backend/"
# Exclude __pycache__
rm -rf "${PACKAGE_DIR}/backend/__pycache__"

# --- Step 6: Copy built frontend ---
echo "[6/7] 复制前端构建产物..."
if [ -d "backend/static" ]; then
    cp -r backend/static "${PACKAGE_DIR}/backend/static"
else
    echo "  [WARN] 前端未构建，请先执行: cd frontend && npm run build"
    mkdir -p "${PACKAGE_DIR}/backend/static"
fi

# --- Step 7: Create start script ---
echo "[7/7] 生成启动脚本..."
cat > "${PACKAGE_DIR}/start.sh" << 'STARTSCRIPT'
#!/bin/bash
cd "$(dirname "$0")"

export PLAYWRIGHT_BROWSERS_PATH="$(pwd)/playwright-browsers"

mkdir -p data/output

echo "=========================================="
echo "  Test Case Intelligence"
echo "  前端: http://localhost:8000"
echo "  API:  http://localhost:8000/docs"
echo "=========================================="

./python/bin/python3 -m uvicorn main:app \
    --host 0.0.0.0 --port 8000 \
    --app-dir backend

echo "服务已停止"
STARTSCRIPT
chmod +x "${PACKAGE_DIR}/start.sh"

# --- Package ---
echo ""
echo ">>> 打包为 tar.gz..."
ARCHIVE_NAME="${PACKAGE_NAME}-$(date +%Y%m%d).tar.gz"
cd "${BUILD_DIR}"
tar czf "../${ARCHIVE_NAME}" "${PACKAGE_NAME}"
cd ../..

echo ""
echo "=========================================="
echo "  构建完成: build/${ARCHIVE_NAME}"
echo "  $(du -h build/${ARCHIVE_NAME} | cut -f1)"
echo "=========================================="
echo ""
echo "  # 发送给同事，同事在任意 Linux x86_64 机器上:"
echo "  tar xzf ${ARCHIVE_NAME}"
echo "  cd ${PACKAGE_NAME}"
echo "  ./start.sh"
echo ""
echo "  # 修改端口: 编辑 start.sh 中 --port 参数"
echo ""
