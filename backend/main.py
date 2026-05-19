import json
import os
import uuid
import shutil
import zipfile
import tempfile
import logging
import asyncio
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from semantic_extractor import extract_semantic
from ai_generator import AIGenerator
from excel_writer import ExcelWriter
from devops_client import DevOpsClient, push_plan_to_devops, push_cases_to_devops

# --- Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
OUTPUT_DIR = BASE_DIR / "output"
DATA_DIR = BASE_DIR / "data"
CONFIG_FILE = DATA_DIR / "config.json"
PLANS_FILE = DATA_DIR / "plans.json"
DEVOPS_CONFIG_FILE = DATA_DIR / "devops_config.json"
OUTPUT_DIR = DATA_DIR / "output"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# --- App Init ---
app = FastAPI(title="Test Case Intelligence", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Services ---
excel_writer = ExcelWriter()


# --- Helper: Load config ---
def load_config() -> dict:
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# --- Config Routes ---
@app.get("/api/config")
async def get_config():
    config = load_config()
    masked = config.copy()
    key = masked.get("api_key", "")
    if key:
        masked["api_key"] = key[:6] + "*" * (len(key) - 6) if len(key) > 6 else "***"
    masked["configured"] = bool(config.get("api_key"))
    masked.setdefault("api_base", "")
    masked.setdefault("model", "deepseek-chat")
    masked.setdefault("api_base", "https://api.deepseek.com")
    return masked


class ConfigModel(BaseModel):
    api_key: str
    api_base: str = ""
    model: str = "deepseek-chat"


@app.put("/api/config")
async def save_config(body: ConfigModel):
    config = {
        "api_key": body.api_key,
        "api_base": body.api_base,
        "model": body.model or "glm-5.1",
    }
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    return {"status": "ok", "message": "配置已保存"}


# --- Helper: split docx extraction into text / table / ocr parts ---
def _split_docx_text(full_text: str) -> list[dict]:
    """Split the combined docx extraction into separate structured parts."""
    parts = []
    # Split by section markers
    sections = full_text.split("=== ")
    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        if sec.startswith("需求文档结构化内容"):
            parts.append({"text": sec, "type": "docx_text", "label": "Word文档-结构化内容"})
        elif sec.startswith("需求文档表格内容"):
            parts.append({"text": sec, "type": "docx_table", "label": "Word文档-表格"})
        elif sec.startswith("文档截图OCR识别结果"):
            parts.append({"text": sec, "type": "ocr", "label": "Word文档-截图OCR"})
        elif "OCR 图片识别结果" in sec:
            parts.append({"text": sec, "type": "ocr", "label": "Word文档-截图OCR"})
        else:
            parts.append({"text": sec, "type": "docx_text", "label": "Word文档-内容"})
    if not parts:
        parts.append({"text": full_text, "type": "docx_text", "label": "Word文档"})
    return parts


# --- Generate Route ---
@app.post("/api/generate")
async def generate_test_cases(
    files: list[UploadFile] = File(default=[]),
    requirement_name: str = Form(""),
    description: str = Form(""),
    requirement_id: str = Form(""),
    group: str = Form(""),
    test_type: str = Form("全面覆盖"),
):
    # Validate input
    if not requirement_name.strip():
        raise HTTPException(400, "请输入需求名称")
    if not description.strip() and not files:
        raise HTTPException(400, "请至少提供需求描述或上传原型文件")

    # Load config
    config = load_config()
    api_key = config.get("api_key", "")
    if not api_key:
        raise HTTPException(400, "请先在设置中配置 API 密钥")

    model = config.get("model", "deepseek-chat")
    base_url = config.get("api_base", "https://api.deepseek.com")

    # Process uploaded files: extract and validate content
    semantic_parts = []  # list of {text, type, reliable, label, score}
    temp_dir = tempfile.mkdtemp(prefix="tci_")

    try:
        from skills.content_validator import validate_extraction

        for upload in files:
            file_path = os.path.join(temp_dir, upload.filename or "upload.html")
            content = await upload.read()
            with open(file_path, "wb") as f:
                f.write(content)

            html_path = file_path

            # Handle ZIP files (Axure exports)
            if file_path.lower().endswith(".zip"):
                extract_dir = os.path.join(temp_dir, "extracted")
                with zipfile.ZipFile(file_path, "r") as zf:
                    zf.extractall(extract_dir)
                html_path = None
                for root, dirs, fnames in os.walk(extract_dir):
                    for name in fnames:
                        if name in ("index.html", "start.html", "debug.html"):
                            html_path = os.path.join(root, name)
                            break
                    if html_path:
                        break
                if not html_path:
                    for root, dirs, fnames in os.walk(extract_dir):
                        for name in fnames:
                            if name.endswith(".html"):
                                html_path = os.path.join(root, name)
                                break
                        if html_path:
                            break
                if not html_path:
                    raise HTTPException(400, f"ZIP 中未找到 HTML 文件: {upload.filename}")

            # Extract + validate HTML
            if html_path and html_path.lower().endswith(".html"):
                logger.info(f"Extracting semantics from: {html_path}")
                semantic = await extract_semantic(html_path)
                if semantic:
                    q = validate_extraction(semantic, "html")
                    semantic_parts.append({
                        "text": semantic, "type": "html",
                        "reliable": q["reliable"], "label": f"HTML原型-{upload.filename or 'page'}",
                        "score": q["score"],
                    })

            # Extract + validate Word documents (split text and OCR sections)
            elif file_path.lower().endswith('.docx'):
                logger.info(f"Extracting from Word document: {file_path}")
                from docx_extractor import extract_docx
                docx_text = await extract_docx(file_path)
                if docx_text:
                    # Split structured docx output into text and OCR parts
                    doc_parts = _split_docx_text(docx_text)
                    for dp in doc_parts:
                        q = validate_extraction(dp["text"], dp.get("type", "docx"))
                        dp["reliable"] = q["reliable"]
                        dp["score"] = q["score"]
                        semantic_parts.append(dp)

            # Extract + validate images via OCR with quality enhancement
            elif file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                logger.info(f"Extracting text via OCR from: {file_path}")
                from skills.ocr_enhancer import ocr_with_quality
                ocr_result = await ocr_with_quality(content, upload.filename or "image")
                if ocr_result["text"] and "未识别" not in ocr_result["text"]:
                    q = validate_extraction(ocr_result["text"], "ocr")
                    semantic_parts.append({
                        "text": ocr_result["text"], "type": "ocr",
                        "reliable": q["reliable"] and not ocr_result["needs_review"],
                        "label": f"OCR-{upload.filename or 'image'}",
                        "score": min(q["score"], 80 if ocr_result["quality"] == "good" else 50),
                    })

        # No files: treat description as primary content
        if not semantic_parts:
            semantic_parts.append({
                "text": "(无原型文件，仅基于需求描述生成)",
                "type": "text", "reliable": True, "label": "纯文本描述", "score": 100,
            })

        # === BUILD ENHANCED PROMPT via skills ===
        from skills.prompt_engineer import build_enhanced_prompt

        enhanced_prompt = build_enhanced_prompt(
            semantic_parts=semantic_parts,
            description=description,
            requirement_name=requirement_name.strip(),
            test_type=test_type,
        )

        # Generate test cases
        ai = AIGenerator(api_key=api_key, base_url=base_url, model=model)
        test_cases = await ai.generate(
            user_prompt=enhanced_prompt,
            requirement_name=requirement_name.strip(),
        )

        # Apply user-specified group, requirement_id, and title prefix
        for tc in test_cases:
            if group:
                if not tc.get("group"):
                    tc["group"] = group
                # Add group prefix to title: 【0321】原始标题
                title = tc.get("title", "")
                if title and not title.startswith("【"):
                    tc["title"] = f"【{group}】{title}"
            if requirement_id:
                rid = requirement_id.strip().lstrip('#')
                if rid and not rid.endswith(','):
                    rid = rid + ','
                tc["requirement_id"] = rid
            if requirement_name:
                tc["requirement_name"] = requirement_name.strip()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generation failed [{type(e).__name__}]: {e}")
        raise HTTPException(500, f"[{type(e).__name__}] {e}")
    finally:
        # Cleanup temp files
        shutil.rmtree(temp_dir, ignore_errors=True)

    if not test_cases:
        raise HTTPException(500, "AI未生成任何测试用例，请重试")

    # Write Excel file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = requirement_name.strip().replace("/", "_").replace("\\", "_")
    filename = f"{safe_name}_测试用例_{timestamp}.xlsx"
    output_subdir = OUTPUT_DIR / safe_name
    output_subdir.mkdir(parents=True, exist_ok=True)
    filepath = output_subdir / filename

    excel_writer.write(test_cases, str(filepath), requirement_name.strip())

    relative_path = f"{safe_name}/{filename}"

    return {
        "status": "ok",
        "filename": filename,
        "requirement_name": requirement_name.strip(),
        "count": len(test_cases),
        "download_url": f"/api/download/{relative_path}",
        "test_cases": test_cases,
    }


# --- History Route ---
@app.get("/api/history")
async def get_history():
    results = []
    if not OUTPUT_DIR.exists():
        return results

    for folder in sorted(OUTPUT_DIR.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
        if not folder.is_dir():
            continue
        for f in sorted(folder.glob("*.xlsx"), key=lambda x: x.stat().st_mtime, reverse=True):
            relative = f.relative_to(OUTPUT_DIR)
            stat = f.stat()
            results.append({
                "requirement_name": folder.name,
                "filename": f.name,
                "download_url": f"/api/download/{relative}",
                "created": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "size_kb": round(stat.st_size / 1024, 1),
            })
    return results


# --- Download Route ---
@app.get("/api/download/{filepath:path}")
async def download_file(filepath: str):
    full_path = OUTPUT_DIR / filepath
    if not full_path.exists():
        raise HTTPException(404, "文件不存在")
    return FileResponse(
        str(full_path),
        filename=full_path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# --- History Cases Route (read Excel back as JSON) ---
@app.get("/api/history-cases/{filepath:path}")
async def get_history_cases(filepath: str):
    full_path = OUTPUT_DIR / filepath
    if not full_path.exists():
        raise HTTPException(404, "文件不存在")
    try:
        cases = excel_writer.read(str(full_path))
        return {"test_cases": cases, "count": len(cases)}
    except Exception as e:
        raise HTTPException(500, f"读取文件失败: {str(e)}")


# --- Export Route (export edited test cases) ---
class ExportModel(BaseModel):
    test_cases: list
    requirement_name: str = "导出"


@app.post("/api/export")
async def export_test_cases(body: ExportModel):
    test_cases = body.test_cases
    if not test_cases:
        raise HTTPException(400, "测试用例列表为空")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = body.requirement_name.strip().replace("/", "_").replace("\\", "_")
    filename = f"{safe_name}_编辑导出_{timestamp}.xlsx"
    output_subdir = OUTPUT_DIR / safe_name
    output_subdir.mkdir(parents=True, exist_ok=True)
    filepath = output_subdir / filename

    excel_writer.write(test_cases, str(filepath), body.requirement_name.strip())

    relative_path = f"{safe_name}/{filename}"
    return {
        "status": "ok",
        "filename": filename,
        "download_url": f"/api/download/{relative_path}",
        "count": len(test_cases),
    }


# --- Export Batch Route (export all test cases from a plan) ---
class ExportBatchModel(BaseModel):
    plan_name: str = "测试计划"
    requirements: list


@app.post("/api/export-batch")
async def export_batch_test_cases(body: ExportBatchModel):
    all_cases = []
    for req in body.requirements:
        cases = req.get("test_cases", [])
        for tc in cases:
            if tc not in all_cases:
                all_cases.append(tc)
    if not all_cases:
        raise HTTPException(400, "没有可导出的测试用例")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = body.plan_name.strip().replace("/", "_").replace("\\", "_")
    filename = f"{safe_name}_批量导出_{timestamp}.xlsx"
    output_subdir = OUTPUT_DIR / safe_name
    output_subdir.mkdir(parents=True, exist_ok=True)
    filepath = output_subdir / filename

    excel_writer.write(all_cases, str(filepath), body.plan_name.strip())

    relative_path = f"{safe_name}/{filename}"
    return {
        "status": "ok",
        "filename": filename,
        "download_url": f"/api/download/{relative_path}",
        "count": len(all_cases),
    }


# --- DevOps Config ---


def load_devops_config() -> dict:
    if DEVOPS_CONFIG_FILE.exists():
        with open(DEVOPS_CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_devops_config(config: dict):
    with open(DEVOPS_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


@app.get("/api/devops-config")
async def get_devops_config():
    config = load_devops_config()
    masked = config.copy()
    password = masked.get("devops_password", "")
    if password:
        masked["devops_password"] = password[:2] + "*" * (len(password) - 2) if len(password) > 2 else "***"
    masked["configured"] = bool(config.get("devops_url") and (config.get("devops_token") or config.get("devops_username")))
    masked.setdefault("devops_url", "")
    masked.setdefault("devops_token", "")
    masked.setdefault("devops_username", "")
    masked.setdefault("devops_password", "")
    masked.setdefault("product_name", "")
    return masked


class DevOpsConfigModel(BaseModel):
    devops_url: str = ""
    devops_token: str = ""
    devops_username: str = ""
    devops_password: str = ""
    product_name: str = ""


@app.put("/api/devops-config")
async def save_devops_config_route(body: DevOpsConfigModel):
    config = {
        "devops_url": body.devops_url,
        "devops_token": body.devops_token,
        "devops_username": body.devops_username,
        "devops_password": body.devops_password,
        "product_name": body.product_name,
    }
    save_devops_config(config)
    return {"status": "ok", "message": "DevOps 配置已保存"}


# --- Push to DevOps ---
_push_progress = {}


@app.post("/api/push-to-devops/{plan_id}")
async def push_to_devops(plan_id: str):
    # Load plan
    plans = load_plans()
    plan = None
    for p in plans:
        if p["id"] == plan_id:
            plan = p
            break
    if not plan:
        raise HTTPException(404, "测试计划不存在")

    requirements = plan.get("requirements", [])
    if not requirements:
        raise HTTPException(400, "测试计划中没有需求")

    has_cases = any(r.get("testCases") and len(r.get("testCases", [])) > 0 for r in requirements)
    if not has_cases:
        raise HTTPException(400, "没有已生成的测试用例，请先生成用例")

    # Load DevOps config
    devops_config = load_devops_config()
    devops_url = devops_config.get("devops_url", "")
    devops_token = devops_config.get("devops_token", "")
    devops_username = devops_config.get("devops_username", "")
    devops_password = devops_config.get("devops_password", "")
    product_name = devops_config.get("product_name", "") or plan.get("product_name", "")

    if not devops_url:
        raise HTTPException(400, "请先在设置中配置 DevOps 平台地址")
    if not devops_username or not devops_password:
        raise HTTPException(400, "请先在设置中配置 DevOps 用户名和密码")
    if not product_name:
        raise HTTPException(400, "请先在设置中配置产品名称")

    client = DevOpsClient(base_url=devops_url)

    # Initialize progress tracking
    _push_progress[plan_id] = {"step": 0, "total": 10, "message": "登录中...", "done": False, "result": None}

    def progress_callback(step, total, message):
        _push_progress[plan_id] = {"step": step, "total": total, "message": message, "done": False, "result": None}

    try:
        # Step 0: Login (password auto-encrypted with DES)
        token = await client.login(devops_username, devops_password)
        if not token:
            raise ValueError("登录失败，请检查用户名和密码")

        plan_title = f"{plan.get('product_name', '')} - {plan.get('iteration_name', '测试计划')}"

        result = await push_plan_to_devops(
            client=client,
            product_name=product_name,
            plan_title=plan_title,
            requirements=requirements,
            progress_callback=progress_callback,
        )
        _push_progress[plan_id] = {"step": 10, "total": 10, "message": "推送完成", "done": True, "result": result}
        return {"status": "ok", "result": result}
    except Exception as e:
        logger.error(f"Push to DevOps failed: {e}")
        _push_progress[plan_id] = {"step": 0, "total": 10, "message": f"推送失败: {str(e)}", "done": True, "result": None, "error": str(e)}
        raise HTTPException(500, f"推送失败: {str(e)}")


@app.get("/api/push-progress/{plan_id}")
async def get_push_progress(plan_id: str):
    progress = _push_progress.get(plan_id, {"step": 0, "total": 8, "message": "等待开始", "done": True})
    return progress


# --- Push Cases to DevOps (from TestCaseView) ---
class PushCasesModel(BaseModel):
    test_cases: list
    requirement_name: str = ""
    description: str = ""
    group: str = ""


@app.post("/api/push-cases-to-devops")
async def push_cases_to_devops_route(body: PushCasesModel):
    if not body.test_cases:
        raise HTTPException(400, "没有可推送的测试用例")
    if not body.requirement_name.strip():
        raise HTTPException(400, "请填写需求名称")

    devops_config = load_devops_config()
    devops_url = devops_config.get("devops_url", "")
    devops_username = devops_config.get("devops_username", "")
    devops_password = devops_config.get("devops_password", "")
    product_name = devops_config.get("product_name", "")

    if not devops_url:
        raise HTTPException(400, "请先在设置中配置 DevOps 平台地址")
    if not devops_username or not devops_password:
        raise HTTPException(400, "请先在设置中配置 DevOps 用户名和密码")
    if not product_name:
        raise HTTPException(400, "请先在设置中配置产品名称")

    client = DevOpsClient(base_url=devops_url)

    try:
        token = await client.login(devops_username, devops_password)
        if not token:
            raise ValueError("登录失败，请检查用户名和密码")

        result = await push_cases_to_devops(
            client=client,
            product_name=product_name,
            requirement_name=body.requirement_name.strip(),
            test_cases=body.test_cases,
            description=body.description,
            group_name=body.group,
        )
        return {"status": "ok", "result": result}
    except Exception as e:
        import traceback
        logger.error(f"Push cases to DevOps failed:\n{traceback.format_exc()}")
        msg = str(e) or type(e).__name__
        raise HTTPException(500, f"推送失败: {msg}")


# --- Plan CRUD ---
def load_plans() -> list:
    if PLANS_FILE.exists():
        with open(PLANS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_plans(plans: list):
    with open(PLANS_FILE, "w", encoding="utf-8") as f:
        json.dump(plans, f, indent=2, ensure_ascii=False)


class PlanCreateModel(BaseModel):
    product_name: str
    iteration_name: str


class PlanUpdateModel(BaseModel):
    product_name: str = ""
    iteration_name: str = ""
    requirements: list = []


@app.get("/api/plans")
async def list_plans():
    plans = load_plans()
    # Return summary for list view
    result = []
    for p in plans:
        reqs = p.get("requirements", [])
        result.append({
            "id": p["id"],
            "product_name": p.get("product_name", ""),
            "iteration_name": p.get("iteration_name", ""),
            "total": len(reqs),
            "completed": len([r for r in reqs if r.get("status") == "done"]),
            "created_at": p.get("created_at", ""),
            "updated_at": p.get("updated_at", ""),
        })
    return result


@app.post("/api/plans")
async def create_plan(body: PlanCreateModel):
    if not body.product_name.strip() or not body.iteration_name.strip():
        raise HTTPException(400, "产品名称和迭代名称不能为空")
    plans = load_plans()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    plan = {
        "id": uuid.uuid4().hex[:8],
        "product_name": body.product_name.strip(),
        "iteration_name": body.iteration_name.strip(),
        "requirements": [],
        "created_at": now,
        "updated_at": now,
    }
    plans.insert(0, plan)
    save_plans(plans)
    return plan


@app.get("/api/plans/{plan_id}")
async def get_plan(plan_id: str):
    plans = load_plans()
    for p in plans:
        if p["id"] == plan_id:
            return p
    raise HTTPException(404, "测试计划不存在")


@app.put("/api/plans/{plan_id}")
async def update_plan(plan_id: str, body: PlanUpdateModel):
    plans = load_plans()
    for p in plans:
        if p["id"] == plan_id:
            if body.product_name:
                p["product_name"] = body.product_name
            if body.iteration_name:
                p["iteration_name"] = body.iteration_name
            if body.requirements is not None:
                p["requirements"] = body.requirements
            p["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_plans(plans)
            return p
    raise HTTPException(404, "测试计划不存在")


@app.delete("/api/plans/{plan_id}")
async def delete_plan(plan_id: str):
    plans = load_plans()
    plans = [p for p in plans if p["id"] != plan_id]
    save_plans(plans)
    return {"status": "ok"}


# --- Static Files (serves Vite build output, must be last) ---
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
