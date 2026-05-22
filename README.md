# Test Case Intelligence

AI 驱动的测试用例自动生成工具。上传需求描述或原型文件（HTML/Axure ZIP/Docx/图片），调用大模型自动生成测试用例，支持导出 Excel、推送 DevOps 平台。

## 功能

- **智能生成** — 上传需求文档 + UI 原型，AI 生成冒烟/功能/边界/异常全覆盖测试用例
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
| AI | OpenAI 兼容 API（DeepSeek / GLM / Qwen / Ollama） |
| 解析 | Playwright（HTML 原型语义提取）、RapidOCR（图片文字提取） |
| 存储 | JSON 文件，无需数据库 |

## 镜像构建源说明

Dockerfile 全部使用国内源，**无需代理**：

| 组件 | 源 |
|------|-----|
| npm | `registry.npmmirror.com`（淘宝） |
| apt | `mirrors.ustc.edu.cn`（中科大） |
| pip | `pypi.tuna.tsinghua.edu.cn`（清华） |
| Chromium | apt 系统安装（中科大源），不走 Playwright CDN |

---

## 部署流程

### 方式一：Docker 构建 → 部署（推荐，最通用）

**适用场景：** 任意有 Docker 的机器（Linux / WSL / macOS）

#### 1. 构建镜像

```bash
cd Test_case_auto

# 构建镜像（全部国内源，无需代理）
./build-image.sh

# 镜像名: test-case-intel:latest
```

如果要导出 tar 发给同事：

```bash
./build-image.sh export
# → 生成 test-case-intel_x86_latest.tar
```

#### 2. 部署运行

```bash
# 方式 A：自动部署脚本（推荐）
./deploy-run.sh test-case-intel:latest

# 方式 B：手动 docker run
mkdir -p data/output
docker run -d \
    --name test-case-intel \
    --restart unless-stopped \
    -p 8000:8000 \
    -v $(pwd)/data:/app/data \
    -e TZ=Asia/Shanghai \
    test-case-intel:latest
```

#### 3. 验证

```bash
# 检查容器状态
docker ps | grep test-case-intel

# 查看日志
docker logs -f test-case-intel

# 访问
curl http://localhost:8000/api/plans
# 浏览器打开 http://localhost:8000
```

#### 4. 配置 API Key

打开 `http://localhost:8000`，点击右上角**齿轮图标** → 填入 API Key：

| 配置项 | 说明 | 示例 |
|--------|------|------|
| API Key | 大模型 API 密钥 | `sk-xxxx` |
| Base URL | API 地址（可选） | `https://api.deepseek.com` |
| Model | 模型名称（可选） | `deepseek-chat` |

点击保存即可开始生成用例。

---

### 方式二：Docker Compose

**适用场景：** 本地开发 / 快速启动

```bash
cd Test_case_auto
docker-compose up -d

# 访问 http://localhost:8000
# 停止: docker-compose down
```

---

### 方式三：K8s Venus 部署

**适用场景：** Venus K8s 集群，NodePort 30105 暴露

#### 1. 构建镜像（同方式一）

```bash
cd Test_case_auto
./build-image.sh
```

#### 2. 推送镜像到 Venus 镜像仓库

```bash
# 打标签（替换为你的 Venus 仓库地址）
docker tag test-case-intel:latest <your-registry>/test-case-intel:latest

# 推送
docker push <your-registry>/test-case-intel:latest

# 同时更新 k8s-deploy.yaml 中的 image 字段为 <your-registry>/test-case-intel:latest
```

#### 3. 部署到 K8s

```bash
# 一键部署
bash k8s-deploy.sh

# 或手动 apply
kubectl apply -f k8s-deploy.yaml
```

#### 4. 验证

```bash
# 查看 Pod 状态
kubectl get pod -n test-case-intel

# 查看日志
kubectl logs -f -l app=test-case-intel -n test-case-intel

# 查看 Service
kubectl get svc -n test-case-intel
# 应该看到 NodePort 30105
```

#### 5. 访问

```
http://<任意节点IP>:30105
```

#### K8s 资源说明 (`k8s-deploy.yaml`)

| 资源 | 说明 |
|------|------|
| Namespace | `test-case-intel` |
| PVC | 10Gi，存储 plans.json / config.json / Excel 输出 |
| Deployment | 1 副本，512Mi~2Gi 内存，健康检查 `/api/plans` |
| Service | **NodePort 30105** → 容器 8000 |

#### K8s 常用命令

```bash
# 重启
kubectl rollout restart deployment/test-case-intel -n test-case-intel

# 查看最近日志
kubectl logs --tail=100 -l app=test-case-intel -n test-case-intel

# 进入容器调试
kubectl exec -it deployment/test-case-intel -n test-case-intel -- bash

# 卸载
kubectl delete -f k8s-deploy.yaml
```

---

### 方式四：源码启动（开发调试）

```bash
# Linux / macOS
./start.sh

# Windows
start.bat

# 前端: http://localhost:5173 (Vite dev server)
# 后端: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

需要：Python 3.10+、Node.js 18+、Playwright Chromium。

---

## 配置说明

首次使用必须配置 **AI API Key**，否则无法生成用例。

| 配置项 | 必填 | 默认值 | 说明 |
|--------|------|--------|------|
| API Key | **是** | - | 大模型 API 密钥 |
| Base URL | 否 | `https://api.deepseek.com` | API 地址 |
| Model | 否 | `deepseek-chat` | 模型名称 |

支持所有 OpenAI 兼容 API，例如：
- DeepSeek: `https://api.deepseek.com`，模型 `deepseek-chat`
- 智谱 GLM: `https://open.bigmodel.cn/api/paas/v4`，模型 `glm-4`
- 阿里 Qwen: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- Ollama 本地: `http://localhost:11434/v1`

---

## 目录结构

```
Test_case_auto/
├── frontend/              # Vue 3 前端 (Vite + Tailwind CSS v4)
│   └── src/views/         # 页面组件
├── backend/               # FastAPI 后端
│   ├── main.py            # API 路由
│   ├── main_tb.py         # 测试计划管理
│   ├── ai_generator.py    # AI 生成器
│   ├── devops_client.py   # DevOps API 客户端
│   ├── excel_writer.py    # Excel 读写
│   ├── semantic_extractor.py  # HTML 原型语义提取 (Playwright)
│   ├── docx_extractor.py  # Word 文档解析
│   ├── ocr_extractor.py   # 图片 OCR 提取
│   ├── skills/            # AI 技能模块（提示词工程、内容验证）
│   └── data/              # 运行时数据（plans.json / config.json / output/）
├── Dockerfile             # Docker 镜像构建（国内源，零代理）
├── docker-compose.yml     # Docker Compose 配置
├── k8s-deploy.yaml        # K8s 部署清单（NodePort 30105）
├── k8s-deploy.sh          # K8s 一键部署脚本
├── build-image.sh         # Docker 镜像构建 + 导出
├── deploy-run.sh          # Docker 一键部署脚本
├── start.sh               # 源码启动 (Linux/Mac)
├── start.bat              # 源码启动 (Windows)
└── .env.example           # 环境变量参考（一般不需要）
```

---

## 常见问题

### Q: 部署后无法生成用例，提示"请先配置 API 密钥"？

A: 首次使用需通过页面右上角齿轮图标配置 API Key。配置保存在 `data/config.json`，挂载卷后重启不会丢失。

### Q: 配置了 API Key 但生成用例时报网络错误？

A: 检查部署环境是否能访问 AI API 地址（如 `api.deepseek.com`）。K8s Venus 集群可能有出口网络限制，需要确认节点是否有外网访问权限。

### Q: 镜像构建失败，Chromium 下载超时？

A: Dockerfile 已通过 apt（中科大源）安装 Chromium，不再从 Playwright CDN 下载。如果 apt 也慢，可换其他 Debian 镜像源。

### Q: DevOps 推送报错 `No module named 'Crypto'`？

A: 已修复，`requirements.txt` 包含 `pycryptodome`。
