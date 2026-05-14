"""
Word Document Extractor
Extracts text and embedded images from .docx files.
Text: extracted from paragraphs and tables.
Images: extracted from document XML, then OCR'd via RapidOCR.
"""

import logging
import tempfile
import os
import io
from pathlib import Path
from zipfile import ZipFile

from docx import Document
from PIL import Image

logger = logging.getLogger(__name__)


async def extract_docx(file_path: str) -> str:
    """
    Extract all content from a .docx file:
    - Text from paragraphs and tables
    - OCR text from embedded images
    Returns combined semantic text.
    """
    parts = []

    # --- 1. Extract text ---
    try:
        doc = Document(file_path)

        # Paragraphs
        para_lines = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                para_lines.append(text)
        if para_lines:
            parts.append("--- Word 文档文字内容 ---")
            parts.append("\n".join(para_lines))

        # Tables
        for ti, table in enumerate(doc.tables):
            table_lines = [f"[表格 {ti + 1}]"]
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                table_lines.append(" | ".join(cells))
            parts.append("\n".join(table_lines))

        logger.info(f"Extracted {len(para_lines)} paragraphs, {len(doc.tables)} tables from {file_path}")

    except Exception as e:
        logger.error(f"Failed to extract text from docx: {e}")
        parts.append("(Word 文档文字提取失败)")

    # --- 2. Extract embedded images and OCR ---
    try:
        from ocr_extractor import extract_text as ocr_text

        image_count = 0
        with ZipFile(file_path, "r") as zf:
            # Images are stored in word/media/ within the docx zip
            for name in zf.namelist():
                if name.startswith("word/media/") and any(
                    name.lower().endswith(ext) for ext in ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')
                ):
                    image_bytes = zf.read(name)
                    try:
                        # Convert to PNG bytes for OCR
                        img = Image.open(io.BytesIO(image_bytes))
                        if img.mode not in ("RGB", "L"):
                            img = img.convert("RGB")
                        buf = io.BytesIO()
                        img.save(buf, format="PNG")
                        png_bytes = buf.getvalue()

                        result = await ocr_text(png_bytes)
                        if result and "未识别" not in result:
                            image_count += 1
                            parts.append(result)
                    except Exception as e:
                        logger.warning(f"OCR failed for docx image {name}: {e}")

        if image_count > 0:
            logger.info(f"OCR'd {image_count} images from {file_path}")

    except Exception as e:
        logger.error(f"Failed to extract images from docx: {e}")

    if not parts:
        return "(Word 文档未提取到有效内容)"

    return "\n\n".join(parts)
