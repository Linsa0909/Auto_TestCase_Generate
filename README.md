# Test Case Intelligence

AI 驱动的测试用例自动生成工具。上传需求描述或原型文件（HTML/Axure ZIP），调用大模型自动生成符合业务规范的测试用例，支持导出 Excel、推送 DevOps 平台。

## 功能

- **智能生成** — 上传需求文档 + UI 原型，AI 自动生成冒烟/功能/边界/异常全覆盖测试用例
- **测试计划管理** — 按产品 → 迭代两级组织测试计划，支持粘贴批量导入需求
- **批量生成** — 一键生成全部需求的用例，支持取消中断
- **DevOps 推送** — 一键推送测试计划、需求、用例到 DevOps 平台
- **Excel 导出** — 单需求导出、批量导出，格式对齐 DevOps 导入模板
- **在线编辑** — 生成的用例可直接编辑标题、步骤、预期结果

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Vue 3 + Tailwind CSS v4 + Vite |
| 后端 | FastAPI (Python) |
| AI | OpenAI 兼容 API（GLM / DeepSeek / Qwen / Ollama） |
| 解析 | Playwright（HTML 原型语义提取）、PaddleOCR（图片文字提取） |
| 存储 | JSON 文件，无需数据库 |

## 快速开始

### 方式一：Docker（推荐）

```bash
# 克隆并启动
git clone git@github.com:Linsa0909/Auto_TestCase_Generate.git
cd Auto_TestCase_Generate
docker-compose up -d

# 访问 http://localhost:8000
```

### 方式二：离线部署包（完全离线环境）

```bash
# 1. 在有网络的机器上构建（仅需一次）
./build-offline.sh
# → 生成 build/test-case-intel-offline-YYYYMMDD.tar.gz

# 2. 将 tar.gz 发送到目标机器，解压即用
tar xzf test-case-intel-offline-YYYYMMDD.tar.gz
cd test-case-intel-offline
./start.sh
# → http://localhost:8000
```

目标机器仅需 Linux x86_64（Ubuntu 20.04+ / Debian 11+），无需安装 Python、Node.js、Docker 或网络。

### 方式三：源码启动

```bash
# Linux / macOS
./start.sh

# Windows
start.bat
```

需要：Python 3.10+、Node.js 18+、Playwright Chromium。

## 配置

启动后打开页面，点击右上角齿轮图标进入设置：

- **AI 配置** — API Key、Base URL、模型名称（支持 OpenAI / DeepSeek / GLM 等）
- **DevOps 配置** — 平台地址、用户名、密码、产品名称（用于推送）

## Docker 镜像打包

```bash
# 构建镜像并导出 tar（发给同事）
./build-image.sh export

# 或推送到 GitHub Container Registry
./build-image.sh push
```

同事拿到后仅需 Docker：

```bash
docker load < test-case-intel-latest.tar
docker run -d -p 8000:8000 -v ./data:/app/data --name test-case-intel test-case-intel:latest
```

或使用自动部署脚本：

```bash
./deploy-run.sh test-case-intel:latest
```

## 目录结构

```
Test_Case_Auto/
├── frontend/           # Vue 3 前端
│   └── src/views/      # 页面组件
├── backend/            # FastAPI 后端
│   ├── main.py         # API 路由
│   ├── ai_generator.py # AI 生成器
│   ├── devops_client.py# DevOps API 客户端
│   ├── excel_writer.py # Excel 导出
│   └── data/           # 持久化数据 (plans.json, config.json)
├── Dockerfile          # Docker 镜像构建
├── docker-compose.yml
├── build-offline.sh    # 离线部署包构建
├── build-image.sh      # Docker 镜像打包
├── deploy-run.sh       # Docker 一键部署
├── start.sh            # 源码启动 (Linux/Mac)
└── start.bat           # 源码启动 (Windows)
```
