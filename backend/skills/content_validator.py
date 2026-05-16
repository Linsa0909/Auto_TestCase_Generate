"""
Skill 1: Content Validator
Validates extracted content quality before feeding to AI.
Produces a quality report that helps prompt construction.
"""
import re
from .skill_logger import get_skill_logger


def validate_extraction(semantic_text: str, source_label: str = "") -> dict:
    """
    Analyze extracted text and return a quality assessment.

    Returns:
        {
            "score": 0-100 quality score,
            "warnings": [list of issues],
            "line_count": int,
            "type": "html"|"docx_text"|"docx_table"|"ocr"|"text",
            "sample": first 3 lines for logging,
            "reliable": True/False,
            "suggestion": str
        }
    """
    logger = get_skill_logger("content-validator")
    lines = [l.strip() for l in semantic_text.split("\n") if l.strip()]
    total = len(lines)

    # Detect type
    if "--- 原型页面交互元素清单 ---" in semantic_text:
        source_type = "html"
    elif "--- OCR 图片识别结果 ---" in semantic_text:
        source_type = "ocr"
    elif "[表格" in semantic_text and " | " in semantic_text:
        source_type = "docx_table"
    elif "--- Word 文档文字内容 ---" in semantic_text:
        source_type = "docx_text"
    else:
        source_type = source_label or "text"

    warnings = []
    score = 100
    reliable = True

    if total == 0:
        warnings.append("内容为空")
        score = 0
        reliable = False
    elif source_type == "ocr":
        # OCR-specific checks
        garbled = 0
        for line in lines:
            if not line.startswith("[第") and not line.startswith("---"):
                # Check for garbled characters (high ratio of uncommon chars)
                if _garbled_ratio(line) > 0.3:
                    garbled += 1
        if garbled > 0:
            score -= min(40, garbled * 10)
            warnings.append(f"检测到 {garbled} 行可能存在乱码")
            if garbled > len(lines) * 0.5:
                reliable = False

        # Check if OCR produced meaningful content
        meaningful = [l for l in lines if not l.startswith("[第") and not l.startswith("---") and len(l) > 2]
        if len(meaningful) < 3:
            score = max(0, score - 30)
            warnings.append("OCR 识别到的有效文字较少（<3行）")
        if "未识别" in semantic_text:
            reliable = False
            score = 0

    elif source_type == "html":
        # HTML extraction checks
        elements = [l for l in lines if l.startswith("[")]
        types_found = set()
        for el in elements:
            m = re.match(r'\[(\S+)\]', el)
            if m:
                types_found.add(m.group(1))
        if "表单输入" not in types_found and "操作按钮" not in types_found:
            warnings.append("HTML 提取中未发现输入框或按钮，可能遗漏交互元素")
            score -= 15

    # Sample for log
    sample = "\n".join(lines[:3]) if lines else "(empty)"

    result = {
        "score": score,
        "warnings": warnings,
        "line_count": total,
        "type": source_type,
        "sample": sample,
        "reliable": reliable,
        "suggestion": "; ".join(warnings) if warnings else "内容质量良好",
    }

    logger.info(
        f"[{source_type}] score={score} lines={total} reliable={reliable} "
        f"warnings={len(warnings)} | {result['suggestion'][:100]}"
    )

    return result


def _garbled_ratio(text: str) -> float:
    """Estimate ratio of garbled/uncommon characters in text."""
    if not text:
        return 0
    # Characters that are likely garbled OCR artifacts
    garbled_chars = sum(1 for c in text if not (
        '\u4e00' <= c <= '\u9fff' or  # CJK
        '\u3000' <= c <= '\u303f' or  # CJK punctuation
        '\uff00' <= c <= '\uffef' or  # Fullwidth
        c.isascii() or
        c in '，。、；：？！""''【】《》（）—…'
    ))
    return garbled_chars / len(text)
