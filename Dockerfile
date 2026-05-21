# ==========================================
#  Test Case Intelligence - Dockerfile
#  前端构建 + 后端运行，全部使用国内源
# ==========================================

# --- Stage 1: 前端构建 ---
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend

RUN npm config set registry https://registry.npmmirror.com

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# --- Stage 2: 后端运行 ---
FROM python:3.12-slim
WORKDIR /app

# apt 使用中科大源（Debian Trixie）
RUN sed -i 's|deb.debian.org|mirrors.ustc.edu.cn|g' /etc/apt/sources.list.d/debian.sources \
    && sed -i 's|security.debian.org|mirrors.ustc.edu.cn|g' /etc/apt/sources.list.d/debian.sources

# 系统依赖 (Playwright Chromium)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libatk1.0-0t64 libatk-bridge2.0-0t64 \
    libcups2t64 libdrm2 libdbus-1-3 libxkbcommon0 \
    libatspi2.0-0t64 libxcomposite1 libxdamage1 libxfixes3 \
    libxrandr2 libgbm1 libpango-1.0-0 libcairo2 libasound2t64 \
    && rm -rf /var/lib/apt/lists/*

# pip 使用清华源；Playwright Chromium 从官方 CDN 下载（国内镜像滞后严重）
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple \
    -r requirements.txt \
    && python -m playwright install chromium

COPY backend/ ./
COPY --from=frontend-builder /app/backend/static ./static

RUN mkdir -p data/output

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
