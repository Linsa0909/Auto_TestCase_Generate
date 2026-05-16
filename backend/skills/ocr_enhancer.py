"""
Skill 2: OCR Quality Enhancer
Enhances OCR accuracy through preprocessing and preserves confidence scores.
Outputs structured OCR text with confidence markers for prompt construction.
"""

import io
import logging
from PIL import Image, ImageEnhance, ImageFilter

from .skill_logger import get_skill_logger

logger = logging.getLogger(__name__)


def preprocess_for_ocr(img: Image.Image, aggressive: bool = False) -> Image.Image:
    """Image preprocessing pipeline for OCR enhancement."""
    # Convert to grayscale
    if img.mode != "L":
        img = img.convert("L")

    # Denoise
    img = img.filter(ImageFilter.MedianFilter(3))

    # Contrast enhancement
    factor = 2.5 if aggressive else 1.8
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(factor)

    # Sharpen
    img = img.filter(ImageFilter.SHARPEN)

    # Binarize for text-heavy images (adaptive threshold simulation)
    if aggressive:
        # Simple binarization for stubborn images
        img = img.point(lambda x: 0 if x < 140 else 255)

    return img


def format_ocr_result(raw_result: list, image_label: str = "") -> dict:
    """
    Parse raw RapidOCR result into structured output with confidence levels.

    Args:
        raw_result: List of [[box], text, confidence] from RapidOCR
        image_label: Optional label for the image (filename)

    Returns:
        {
            "text": formatted OCR text with confidence markers,
            "lines": [{text, confidence, y_pos}, ...],
            "high_conf_lines": count,
            "low_conf_lines": count,
            "quality": "good"|"fair"|"poor",
            "needs_review": True/False
        }
    """
    lines = []
    for item in raw_result:
        box = item[0]
        text = item[1].strip() if item[1] else ""
        confidence = item[2]

        if confidence < 0.5 or not text:
            continue

        y_pos = box[0][1]
        lines.append({
            "text": text,
            "confidence": confidence,
            "y_pos": y_pos,
        })

    if not lines:
        return {
            "text": "(OCR未识别到有效文字)",
            "lines": [],
            "high_conf_lines": 0,
            "low_conf_lines": 0,
            "quality": "poor",
            "needs_review": True,
        }

    # Sort by Y position (top to bottom)
    lines.sort(key=lambda x: x["y_pos"])

    # Classify confidence levels
    high_conf = [l for l in lines if l["confidence"] >= 0.8]
    mid_conf = [l for l in lines if 0.6 <= l["confidence"] < 0.8]
    low_conf = [l for l in lines if l["confidence"] < 0.6]

    # Determine quality
    total = len(lines)
    high_ratio = len(high_conf) / total if total > 0 else 0
    if high_ratio >= 0.7:
        quality = "good"
        needs_review = False
    elif high_ratio >= 0.4:
        quality = "fair"
        needs_review = len(low_conf) > total * 0.3
    else:
        quality = "poor"
        needs_review = True

    # Build formatted output
    output_lines = ["--- OCR 图片识别结果 ---"]
    for idx, line in enumerate(lines, 1):
        if line["confidence"] >= 0.8:
            tag = "[高置信]"
        elif line["confidence"] >= 0.6:
            tag = "[中置信]"
        else:
            tag = "[低置信]"
        output_lines.append(f"{tag}[第{idx}行] {line['text']}")

    output_lines.append(
        f"--- 共 {total} 行 (高:{len(high_conf)} 中:{len(mid_conf)} 低:{len(low_conf)}) ---"
    )
    if needs_review:
        output_lines.append("[!] 此OCR结果质量较低，建议以文字描述为准")

    result = {
        "text": "\n".join(output_lines),
        "lines": lines,
        "high_conf_lines": len(high_conf),
        "low_conf_lines": len(low_conf),
        "quality": quality,
        "needs_review": needs_review,
        "total_lines": total,
    }

    # Log
    skill_logger = get_skill_logger("ocr-enhancer")
    skill_logger.info(
        f"[{image_label or 'image'}] quality={quality} total={total} "
        f"high={len(high_conf)} mid={len(mid_conf)} low={len(low_conf)} "
        f"review={needs_review}"
    )

    return result


async def ocr_with_quality(image_bytes: bytes, image_label: str = "") -> dict:
    """
    Run OCR with quality enhancement and retry logic.

    Returns the formatted result from format_ocr_result.
    """
    from ocr_extractor import _get_ocr
    import asyncio

    # First attempt: standard preprocessing
    img = Image.open(io.BytesIO(image_bytes))
    img = preprocess_for_ocr(img, aggressive=False)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    # Save temp file for RapidOCR
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp.write(png_bytes)
        tmp_path = tmp.name

    try:
        ocr = _get_ocr()
        loop = asyncio.get_event_loop()
        raw_result, elapse = await loop.run_in_executor(None, lambda: ocr(tmp_path))
    finally:
        os.unlink(tmp_path)

    result = format_ocr_result(raw_result or [], image_label)

    # Retry with aggressive preprocessing if quality is poor
    if result["quality"] == "poor" and raw_result:
        skill_logger = get_skill_logger("ocr-enhancer")
        skill_logger.info(f"[{image_label or 'image'}] 质量差，尝试激进预处理重试...")

        img2 = Image.open(io.BytesIO(image_bytes))
        img2 = preprocess_for_ocr(img2, aggressive=True)
        buf2 = io.BytesIO()
        img2.save(buf2, format="PNG")

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp2:
            tmp2.write(buf2.getvalue())
            tmp_path2 = tmp2.name

        try:
            raw_result2, _ = await loop.run_in_executor(None, lambda: ocr(tmp_path2))
        finally:
            os.unlink(tmp_path2)

        if raw_result2:
            result2 = format_ocr_result(raw_result2, f"{image_label}_retry")
            # Use the better result
            if result2["high_conf_lines"] > result["high_conf_lines"]:
                skill_logger.info(f"[{image_label or 'image'}] 重试改善了结果")
                result = result2

    return result
