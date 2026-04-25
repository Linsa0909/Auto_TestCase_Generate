"""
DOM Semantic Extractor
Uses Playwright to extract UI interaction semantics from HTML prototypes.
"""

import os
import logging

logger = logging.getLogger(__name__)

EXTRACT_JS = """
() => {
    const result = [];

    // 1. Page titles / sections
    document.querySelectorAll('h1, h2, h3, [class*="title"], [class*="heading"]').forEach(el => {
        const text = el.innerText?.trim();
        if (text && text.length < 200) {
            result.push({ type: 'heading', text: text });
        }
    });

    // 2. Navigation items / tabs
    document.querySelectorAll('[class*="tab"], [class*="nav-item"], [role="tab"]').forEach(el => {
        const text = el.innerText?.trim();
        if (text && text.length < 100) {
            result.push({ type: 'tab', text: text });
        }
    });

    // 3. Text labels / paragraphs (key visible text)
    document.querySelectorAll('[class*="text"], [class*="label"], [class*="paragraph"]').forEach(el => {
        const text = el.innerText?.trim();
        if (text && text.length > 1 && text.length < 300) {
            const cls = el.className || '';
            if (cls.includes('bold') || cls.includes('weight') || el.style.fontWeight === '700') {
                result.push({ type: 'label', text: text });
            }
        }
    });

    // 4. All select dropdowns
    document.querySelectorAll('select').forEach(el => {
        const options = Array.from(el.options).map(opt => opt.text.trim()).filter(Boolean);
        const name = el.name || el.id || '';
        result.push({ type: 'select', name: name, options: options });
    });

    // 5. All text inputs and textareas
    document.querySelectorAll('input, textarea').forEach(el => {
        if (el.type === 'hidden' || el.style.display === 'none') return;
        const inputType = el.tagName.toLowerCase() === 'textarea' ? 'textarea' : el.type;
        const placeholder = el.placeholder || '';
        const name = el.name || el.id || '';
        const value = el.value || '';
        result.push({ type: 'input', inputType: inputType, name: name, placeholder: placeholder, value: value });
    });

    // 6. Buttons and actions
    document.querySelectorAll('button, [class*="button"], [class*="btn"], input[type="button"], input[type="submit"]').forEach(el => {
        const text = (el.innerText || el.value || '').trim();
        if (text && text.length < 100) {
            result.push({ type: 'button', text: text });
        }
    });

    // 7. Table structures
    document.querySelectorAll('table').forEach(table => {
        const headers = Array.from(table.querySelectorAll('th')).map(th => th.innerText?.trim()).filter(Boolean);
        const rowCount = table.querySelectorAll('tr').length;
        if (headers.length > 0) {
            result.push({ type: 'table', headers: headers, rowCount: rowCount });
        }
    });

    // 8. Data lists / repeater items
    document.querySelectorAll('[class*="list"] > div, [class*="item"]').forEach(el => {
        const text = el.innerText?.trim();
        if (text && text.length > 2 && text.length < 200) {
            result.push({ type: 'list_item', text: text.substring(0, 150) });
        }
    });

    // 9. Links
    document.querySelectorAll('a').forEach(el => {
        const text = el.innerText?.trim();
        if (text && text.length < 100 && !text.startsWith('http')) {
            result.push({ type: 'link', text: text });
        }
    });

    return result;
}
"""


async def extract_semantic(file_path: str) -> str:
    """
    Open an HTML file with Playwright and extract UI interaction semantics.
    Returns a structured text description of the prototype's UI elements.
    """
    from playwright.async_api import async_playwright

    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"File not found: {abs_path}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Block non-essential resources for speed
        await page.route(
            "**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2,ttf,eot}",
            lambda route: route.abort(),
        )

        await page.goto(f"file://{abs_path}", wait_until="domcontentloaded")
        await page.wait_for_timeout(500)  # Allow dynamic content to render

        elements = await page.evaluate(EXTRACT_JS)
        await browser.close()

    # Convert structured data to readable text
    lines = ["--- 原型页面交互元素清单 ---"]

    type_labels = {
        'heading': '页面标题',
        'tab': '导航Tab',
        'label': '文本标签',
        'select': '下拉菜单',
        'input': '表单输入',
        'button': '操作按钮',
        'table': '数据表格',
        'list_item': '列表项',
        'link': '链接',
    }

    for el in elements:
        t = el.get('type', '')
        label = type_labels.get(t, t)

        if t == 'heading':
            lines.append(f"[{label}] {el['text']}")
        elif t == 'tab':
            lines.append(f"[{label}] {el['text']}")
        elif t == 'label':
            lines.append(f"[{label}] {el['text']}")
        elif t == 'select':
            opts = ', '.join(el.get('options', []))
            lines.append(f"[{label}] 名称:{el.get('name', '')} 选项:[{opts}]")
        elif t == 'input':
            lines.append(
                f"[{label}] 类型:{el.get('inputType', '')} "
                f"名称:{el.get('name', '')} "
                f"提示:{el.get('placeholder', '')} "
                f"默认值:{el.get('value', '')}"
            )
        elif t == 'button':
            lines.append(f"[{label}] \"{el['text']}\"")
        elif t == 'table':
            hdrs = ', '.join(el.get('headers', []))
            lines.append(f"[{label}] 列:[{hdrs}] 共{el.get('rowCount', 0)}行")
        elif t == 'list_item':
            lines.append(f"[{label}] {el['text']}")
        elif t == 'link':
            lines.append(f"[{label}] {el['text']}")

    semantic_text = '\n'.join(lines)
    logger.info(f"Extracted {len(elements)} UI elements from {abs_path}")
    return semantic_text
