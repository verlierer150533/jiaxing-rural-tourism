# -*- coding: utf-8 -*-
"""检查学校模板 docx 的段落、表格与样式。"""
import sys

from docx import Document


def dump(path, limit=80):
    doc = Document(path)
    print("=" * 70)
    print("文件:", path)
    print("段落数:", len(doc.paragraphs), " 表格数:", len(doc.tables))
    section = doc.sections[0]
    print("纸张: {0} x {1} mm 页边距: 上{2} 下{3} 左{4} 右{5} mm".format(
        round(section.page_width.mm, 1), round(section.page_height.mm, 1),
        round(section.top_margin.mm, 1), round(section.bottom_margin.mm, 1),
        round(section.left_margin.mm, 1), round(section.right_margin.mm, 1)))

    for index, para in enumerate(doc.paragraphs[:limit]):
        text = para.text.strip()
        if not text:
            continue
        size = font = None
        for run in para.runs:
            if run.font.size and size is None:
                size = run.font.size.pt
            if run.font.name and font is None:
                font = run.font.name
        print("[P{0:03d}] style={1:<10} size={2} font={3} align={4} | {5}".format(
            index, para.style.name, size, font, para.alignment, text[:50]))

    for t_index, table in enumerate(doc.tables):
        print("-" * 70)
        print("表格 {0}: {1} 行 x {2} 列".format(t_index, len(table.rows), len(table.columns)))
        for r_index, row in enumerate(table.rows[:12]):
            cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
            print("  行{0}: {1}".format(r_index, " | ".join(cells)))


if __name__ == "__main__":
    for path in sys.argv[1:]:
        dump(path)
