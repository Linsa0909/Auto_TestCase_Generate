import os
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill


class ExcelWriter:
    """Generate Excel test case files matching the DevOps import template."""

    HEADERS = [
        "用例分组",
        "用例标题",
        "用例类型",
        "重要程度",
        "前置条件",
        "步骤描述",
        "预期结果",
        "需求编号(多个以逗号隔开)",
        "需求名称",
    ]

    COLUMN_WIDTHS = [16, 44, 14, 10, 48, 55, 55, 24, 20]

    def write(self, test_cases: list, filepath: str,
              requirement_name: str = "") -> str:
        """
        Write test cases to an Excel file.

        Args:
            test_cases: List of test case dicts with 'steps' sub-list
            filepath: Output file path
            requirement_name: Default requirement name if not set per case

        Returns:
            The filepath of the generated Excel file
        """
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Sheet0"

        # Styles
        header_font = Font(name="Microsoft YaHei", bold=True, size=11)
        header_fill = PatternFill(
            start_color="F1F5F9", end_color="F1F5F9", fill_type="solid",
        )
        header_alignment = Alignment(horizontal="center", vertical="center")
        cell_alignment = Alignment(vertical="top", wrap_text=True)
        thin_border = Border(
            left=Side(style="thin", color="E2E8F0"),
            right=Side(style="thin", color="E2E8F0"),
            top=Side(style="thin", color="E2E8F0"),
            bottom=Side(style="thin", color="E2E8F0"),
        )

        # Write headers
        for col, header in enumerate(self.HEADERS, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border

        # Write data
        row = 2
        for tc in test_cases:
            steps = tc.get("steps", [{}])
            if not steps:
                steps = [{}]

            for i, step in enumerate(steps):
                r = row + i
                if i == 0:
                    # First step row: fill all columns
                    ws.cell(row=r, column=1, value=tc.get("group", "")).alignment = cell_alignment
                    ws.cell(row=r, column=2, value=tc.get("title", "")).alignment = cell_alignment
                    ws.cell(row=r, column=3, value=tc.get("type", "手动测试用例")).alignment = cell_alignment
                    ws.cell(row=r, column=4, value=tc.get("priority", "L1")).alignment = cell_alignment
                    ws.cell(row=r, column=5, value=tc.get("precondition", "")).alignment = cell_alignment
                    ws.cell(row=r, column=8, value=tc.get("requirement_id", "")).alignment = cell_alignment
                    ws.cell(row=r, column=9, value=tc.get("requirement_name", "") or requirement_name).alignment = cell_alignment
                    # Apply border to all cells in first row
                    for c in range(1, 10):
                        ws.cell(row=r, column=c).border = thin_border

                # Every step row: fill step and expected
                ws.cell(row=r, column=6, value=step.get("step", "")).alignment = cell_alignment
                ws.cell(row=r, column=7, value=step.get("expected", "")).alignment = cell_alignment
                if i > 0:
                    for c in range(1, 10):
                        ws.cell(row=r, column=c).border = thin_border

            row += len(steps)

        # Set column widths
        for i, width in enumerate(self.COLUMN_WIDTHS, 1):
            col_letter = openpyxl.utils.get_column_letter(i)
            ws.column_dimensions[col_letter].width = width

        # Freeze header row
        ws.freeze_panes = "A2"

        # Auto-filter
        ws.auto_filter.ref = f"A1:I{row - 1}"

        # Ensure parent directory exists
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else ".", exist_ok=True)
        wb.save(filepath)
        return filepath
