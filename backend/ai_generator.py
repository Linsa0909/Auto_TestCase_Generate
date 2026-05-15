"""
AI Test Case Generator
Uses OpenAI-compatible API (via proxy) to call GLM-5.1 for test case generation.
"""

import json
import re
import logging
import httpx

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位资深的软件测试工程师（SDET），专注于根据需求文档和UI原型生成全面、专业的测试用例。

## 任务
根据提供的【页面交互元素清单】和【需求描述】，生成完整的测试用例集。

## 测试覆盖要求

### 1. 冒烟测试 (Smoke) - 高优先级
验证核心功能是否可用：
- 页面/模块基本加载和展示
- 核心操作流程是否通畅
- 关键数据展示是否正确

### 2. 功能性测试 (Functional) - 高/中优先级
验证每个功能点的完整流程：
- UI元素的渲染和交互（按钮、输入框、下拉列表、Tab切换）
- 数据输入、提交和返回流程
- 配置保存和加载
- 展开/折叠、筛选等交互
- 表格数据展示

### 3. 边界值测试 (Boundary) - 中/低优先级
验证输入和数据的边界：
- 字段最小值、最大值、零值
- 空值、特殊字符
- 数据类型边界（int溢出、float精度、string长度）
- 默认值验证

### 4. 异常测试 (Exception) - 中/低优先级
验证错误处理：
- 必填字段未填写
- 非法输入校验
- 网络异常、超时
- 按钮禁用状态

## 输出格式

严格输出纯JSON数组，不要包含任何Markdown标记、解释性文字或总结。
每个对象必须包含以下字段：

[
  {
    "title": "用例标题（清晰明确）",
    "type": "冒烟|功能|边界|异常",
    "level": "高|中|低",
    "pre_condition": "前置条件",
    "steps": "1. 步骤一\\n2. 步骤二\\n3. 步骤三",
    "expected": "1. 步骤一的预期结果\\n2. 步骤二的预期结果\\n3. 步骤三的预期结果"
  }
]

## 关键要求（必须遵守）
1. 只输出JSON数组，不输出其他任何内容
2. 用例标题格式："功能模块-具体测试点"
3. 根据原型UI元素确保每个交互元素都有对应测试
4. 总数建议30-60条
5. 步骤描述要详细、可执行，每个步骤用数字编号独立一行
6. **预期结果必须与步骤一一对应，步骤有几条，预期结果就必须有几条，编号必须对齐**
7. 预期结果要明确、可验证，禁止出现空预期"""


class AIGenerator:
    """Test case generator using OpenAI-compatible API (proxy -> GLM)."""

    def __init__(self, api_key: str, base_url: str, model: str = "GLM-5.1"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def generate(self, semantic_text: str, description: str,
                       requirement_name: str = "") -> list:
        """
        Generate test cases via OpenAI-compatible chat completions API.
        """
        user_prompt = f"""【页面交互元素清单】：
{semantic_text}

【需求描述】：
{description}
"""
        if requirement_name:
            user_prompt = f"【需求名称】：{requirement_name}\n\n" + user_prompt

        user_prompt += "\n请立即生成纯JSON格式的测试用例数组。"

        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 4096,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        logger.info(f"Calling {url} model={self.model}")

        async with httpx.AsyncClient(timeout=300.0) as client:
            resp = await client.post(url, json=payload, headers=headers)

        if resp.status_code != 200:
            logger.error(f"API error {resp.status_code}: {resp.text[:500]}")
            raise Exception(f"API调用失败 (HTTP {resp.status_code}): {resp.text[:300]}")

        data = resp.json()
        try:
            raw_content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            raise Exception(f"API返回格式异常: {json.dumps(data, ensure_ascii=False)[:300]}")

        logger.info(f"Response length: {len(raw_content)} chars")
        return self._parse_response(raw_content)

    def _parse_response(self, text: str) -> list:
        """Parse AI response into structured test cases."""
        # Clean markdown wrappers
        cleaned = text.replace("```json", "").replace("```", "").strip()

        # Try to find JSON array
        bracket_start = cleaned.find('[')
        bracket_end = cleaned.rfind(']')
        if bracket_start != -1 and bracket_end != -1:
            cleaned = cleaned[bracket_start:bracket_end + 1]

        try:
            data = json.loads(cleaned, strict=False)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}\nRaw: {text[:500]}")
            raise Exception(f"AI返回内容无法解析为JSON: {str(e)}")

        if not isinstance(data, list) or len(data) == 0:
            raise Exception("AI返回的测试用例列表为空")

        validated = []
        for item in data:
            if not isinstance(item, dict):
                continue

            tc_type = item.get("type", "功能")
            tc_level = item.get("level", "中")

            priority_map = {"冒烟": "L0", "功能": "L1", "边界": "L2", "异常": "L2"}
            priority = priority_map.get(tc_type, "L1")
            level_priority = {"高": "L0", "中": "L1", "低": "L2"}
            if tc_level in level_priority:
                priority = level_priority[tc_level]

            raw_steps = item.get("steps", "")
            raw_expected = item.get("expected", "")

            # Split steps into individual lines, stripping "1. " prefixes
            if raw_steps:
                step_lines = [s.strip() for seg in re.split(r'\n', raw_steps) for s in re.split(r'\d+\.\s*', seg) if s.strip()]
            else:
                step_lines = ["执行测试操作"]

            # Split expected into individual lines the same way
            if raw_expected:
                expected_lines = [s.strip() for seg in re.split(r'\n', raw_expected) for s in re.split(r'\d+\.\s*', seg) if s.strip()]
            else:
                expected_lines = []

            # Pair step[i] with expected[i] one-to-one
            steps = []
            last_exp = ""
            for i, step in enumerate(step_lines):
                exp = expected_lines[i] if i < len(expected_lines) else ""
                if not exp.strip():
                    exp = last_exp if last_exp else "验证通过"
                else:
                    last_exp = exp
                steps.append({"step": step, "expected": exp})

            validated.append({
                "group": item.get("group", ""),
                "title": item.get("title", ""),
                "type": "手动测试用例",
                "priority": priority,
                "precondition": item.get("pre_condition", ""),
                "steps": steps,
                "requirement_id": "",
                "requirement_name": "",
                "raw_type": tc_type,
                "raw_level": tc_level,
            })

        return validated
