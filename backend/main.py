import json
import os
import shutil
import zipfile
import tempfile
import logging
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

# --- Configuration ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
OUTPUT_DIR = BASE_DIR / "output"
CONFIG_FILE = BASE_DIR / "config.json"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

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
    masked.setdefault("model", "GLM-5.1")
    masked.setdefault("api_base", "http://172.16.3.6:8589")
    return masked


class ConfigModel(BaseModel):
    api_key: str
    api_base: str = ""
    model: str = "GLM-5.1"


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

    model = config.get("model", "GLM-5.1")
    base_url = config.get("api_base", "http://172.16.3.6:8589")

    # Process uploaded files: extract HTML from ZIP or use directly
    semantic_parts = []
    temp_dir = tempfile.mkdtemp(prefix="tci_")

    try:
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

                # Find entry HTML
                html_path = None
                for root, dirs, fnames in os.walk(extract_dir):
                    for name in fnames:
                        if name in ("index.html", "start.html", "debug.html"):
                            html_path = os.path.join(root, name)
                            break
                    if html_path:
                        break

                if not html_path:
                    # Try any HTML file
                    for root, dirs, fnames in os.walk(extract_dir):
                        for name in fnames:
                            if name.endswith(".html"):
                                html_path = os.path.join(root, name)
                                break
                        if html_path:
                            break

                if not html_path:
                    raise HTTPException(400, f"ZIP 中未找到 HTML 文件: {upload.filename}")

            # Extract semantic text via Playwright (HTML files)
            if html_path and html_path.lower().endswith(".html"):
                logger.info(f"Extracting semantics from: {html_path}")
                semantic = await extract_semantic(html_path)
                if semantic:
                    semantic_parts.append(semantic)

            # Extract text from images via PaddleOCR
            elif file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                logger.info(f"Extracting text via OCR from: {file_path}")
                from ocr_extractor import extract_text
                ocr_text = await extract_text(content)
                if ocr_text:
                    semantic_parts.append(ocr_text)

        # Combine all semantic extractions
        full_semantic = "\n\n".join(semantic_parts) if semantic_parts else "(无原型文件，仅基于需求描述生成)"

        # Build enhanced description with test type guidance
        type_guidance = {
            "全面覆盖": "请生成包含冒烟、功能、边界、异常的全覆盖测试用例。",
            "仅冒烟": "请仅生成冒烟测试用例，验证核心功能是否可用。",
            "边界异常": "请重点生成边界值测试和异常测试用例。",
        }
        guidance = type_guidance.get(test_type, "")

        # When no text description provided, tell AI to rely on prototype/OCR
        if not description.strip():
            enhanced_desc = f"{guidance}\n\n（未提供需求描述文本，请严格基于上面的【页面交互元素清单】中提取的UI元素和页面信息来生成测试用例。分析每个控件、按钮、列表、输入框的功能，推导其交互逻辑并生成对应用例。）"
        else:
            enhanced_desc = f"{guidance}\n\n{description}" if guidance else description

        # Generate test cases via GLM
        ai = AIGenerator(api_key=api_key, base_url=base_url, model=model)
        test_cases = await ai.generate(
            semantic_text=full_semantic,
            description=enhanced_desc,
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
                tc["requirement_id"] = requirement_id
            if requirement_name:
                tc["requirement_name"] = requirement_name.strip()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(500, str(e))
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


# --- Static Files (serves Vite build output, must be last) ---
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
