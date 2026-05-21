"""
Skill 3: Prompt Engineer
Dynamically constructs enhanced AI prompts based on content quality assessment.
- Layers content by reliability
- Injects test-type-specific guidance
- Adjusts instructions based on OCR quality
"""

from .skill_logger import get_skill_logger


def build_enhanced_prompt(
    semantic_parts: list[dict],
    description: str,
    requirement_name: str,
    test_type: str = "全面覆盖",
) -> str:
    """
    Build an enhanced user prompt with content reliability markers.

    Args:
        semantic_parts: List of {
            "text": str,
            "type": "html"|"docx_text"|"docx_table"|"ocr"|"text",
            "reliable": bool,
            "label": str (source description),
            "score": int (quality score),
        }
        description: User-provided text description
        requirement_name: Requirement name
        test_type: 全面覆盖 / 仅冒烟 / 边界异常 / 功能测试

    Returns:
        Full user prompt string for the AI
    """
    logger = get_skill_logger("prompt-engineer")

    sections = []

    # --- Header ---
    sections.append(f"【需求名称】：{requirement_name}")

    # --- Test type guidance ---
    type_guidance = _get_type_guidance(test_type)
    sections.append(f"【生成要求】：{type_guidance}")

    # --- User description (highest reliability) ---
    if description.strip():
        sections.append("")
        sections.append("=" * 40)
        sections.append("=== [高可信 - 人工编写] 需求描述 ===")
        sections.append("=" * 40)
        sections.append(description.strip())

    # --- Semantic content, layered by reliability ---
    reliable_parts = [p for p in semantic_parts if p.get("reliable", True)]
    uncertain_parts = [p for p in semantic_parts if not p.get("reliable", True)]

    if reliable_parts:
        sections.append("")
        sections.append("=" * 40)
        sections.append("=== [高可信 - 文档/原型提取] 页面交互元素与业务内容 ===")
        sections.append("=" * 40)
        for p in reliable_parts:
            ptype = p.get("type", "text")
            label = p.get("label", "")
            sections.append(f"\n--- {label} ({ptype}) ---")
            sections.append(p["text"])

    if uncertain_parts:
        sections.append("")
        sections.append("=" * 40)
        sections.append("=== [中等可信 - OCR识别] 以下内容来自图片识别，可能存在识别错误，请以高可信内容为准 ===")
        sections.append("=" * 40)
        for p in uncertain_parts:
            label = p.get("label", "")
            sections.append(f"\n--- {label} (ocr, 置信度有限) ---")
            sections.append(p["text"])
        sections.append("\n[!] 请优先基于高可信内容生成用例。OCR 内容仅作为补充参考，如与高可信内容矛盾，以高可信内容为准。")

    # --- Instruction footer ---
    sections.append("")
    sections.append("请立即根据以上信息生成纯JSON格式的测试用例数组。")

    prompt = "\n".join(sections)

    # Log only key stats for debugging
    logger.debug(
        f"Prompt: {len(prompt)}chars | reliable={len(reliable_parts)} uncertain={len(uncertain_parts)} | {test_type}"
    )

    return prompt


def _get_type_guidance(test_type: str) -> str:
    """Get test-type-specific guidance for prompt."""
    guidance_map = {
        "全面覆盖": (
            "请生成包含冒烟测试、功能测试、边界值测试、异常测试的全覆盖用例集。"
            "冒烟测试验证核心流程是否通畅；功能测试覆盖每个交互元素；"
            "边界测试覆盖输入极值/空值/特殊字符；异常测试覆盖错误处理和非法操作。"
        ),
        "仅冒烟": (
            "请仅生成冒烟测试用例，验证核心功能是否可用。"
            "重点覆盖：页面加载、核心操作流程、关键数据展示。"
            "不需要边界值测试和异常测试。"
        ),
        "功能测试": (
            "请重点生成功能测试用例，覆盖每个功能点的完整流程。"
            "包括 UI 元素交互、数据输入/提交/返回、配置保存加载等。"
        ),
        "边界异常": (
            "请重点生成边界值测试和异常测试用例。"
            "边界测试：字段最小/最大值、空值、特殊字符、默认值。"
            "异常测试：必填校验、非法输入、网络异常、权限限制。"
        ),
    }
    return guidance_map.get(test_type, guidance_map["全面覆盖"])
