"""
RapidOCR Text Extractor
Extracts text from images using RapidOCR (ONNX-based, PaddleOCR-compatible).
"""

import asyncio
import logging
import tempfile
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# OCR log directory (project root /log)
LOG_DIR = Path(__file__).resolve().parent.parent / "log"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Lazy singleton
_ocr_instance = None


def _get_ocr():
    global _ocr_instance
    if _ocr_instance is None:
        from rapidocr_onnxruntime import RapidOCR
        logger.info("Initializing RapidOCR (lang=ch)...")
        _ocr_instance = RapidOCR()
        logger.info("RapidOCR initialized.")
    return _ocr_instance


async def extract_text(image_bytes: bytes) -> str:
    """
    Extract text from image bytes using RapidOCR.
    Returns formatted semantic text string.
    """
    # Write bytes to a temp file
    suffix = ".png"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    try:
        ocr = _get_ocr()
        # Run synchronous OCR in thread pool
        loop = asyncio.get_event_loop()
        result, elapse = await loop.run_in_executor(
            None, lambda: ocr(tmp_path)
        )
    finally:
        os.unlink(tmp_path)

    if not result:
        return "(OCR未识别到文字内容)"

    # Parse results: each entry is [box_coords, text, confidence]
    lines = []
    for item in result:
        box = item[0]       # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        text = item[1]      # recognized text
        confidence = item[2] # confidence score

        # Filter low confidence
        if confidence < 0.5:
            continue

        # Use Y coordinate (top of bounding box) for top-to-bottom ordering
        y_pos = box[0][1]
        lines.append((y_pos, text.strip()))

    # Sort by Y coordinate (top to bottom)
    lines.sort(key=lambda x: x[0])

    if not lines:
        return "(OCR未识别到有效文字内容)"

    # Format output
    output_lines = ["--- OCR 图片识别结果 ---"]
    for idx, (_, text) in enumerate(lines, 1):
        if text:
            output_lines.append(f"[第{idx}行] {text}")

    output_lines.append(f"--- 共识别 {len(lines)} 行文字 ---")

    result_text = "\n".join(output_lines)

    # Save OCR result to log file
    _save_ocr_log(result_text, lines)

    return result_text


def _save_ocr_log(formatted_text: str, lines: list):
    """Save OCR result to log directory with naming: 测试用例_ocr识别文字_时间戳.log"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Extract first few characters of recognized text as identifier
        first_text = ""
        for _, text in lines:
            clean = text.strip()
            if clean:
                first_text = clean[:10]
                break
        # Clean filename-unsafe characters
        safe_text = "".join(c for c in first_text if c.isalnum() or c in ('_', '-', '\u4e00', '\u9fff')).strip()
        if not safe_text:
            safe_text = "unknown"
        filename = f"测试用例_ocr识别文字_{safe_text}_{timestamp}.log"
        log_path = LOG_DIR / filename
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(formatted_text)
        logger.info(f"OCR log saved: {log_path}")
    except Exception as e:
        logger.warning(f"Failed to save OCR log: {e}")
