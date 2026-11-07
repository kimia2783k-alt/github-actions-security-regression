"""Convert Persian supervisor briefing Markdown to Word (RTL-friendly)."""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
MD_PATH = ROOT / "paper" / "manuscript" / "supervisor_briefing_fa.md"
OUT_PATH = ROOT / "paper" / "manuscript" / "Supervisor_Briefing_FA.docx"
FONT = "Tahoma"


def set_run_font(run, size: int = 12, bold: bool = False, italic: bool = False):
    run.font.name = FONT
    run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    run._element.rPr.rFonts.set(qn("w:cs"), FONT)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic


def set_rtl(paragraph):
    pPr = paragraph._p.get_or_add_pPr()
    bidi = OxmlElement("w:bidi")
    bidi.set(qn("w:val"), "1")
    pPr.append(bidi)
    paragraph.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.RIGHT


def add_runs(paragraph, text: str, size: int = 12, force_bold: bool = False):
    pattern = re.compile(r"(\*\*[^*]+\*\*|`[^`]+`)")
    for part in pattern.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            run = paragraph.add_run(part[2:-2])
            set_run_font(run, size=size, bold=True)
        elif part.startswith("`") and part.endswith("`"):
            run = paragraph.add_run(part[1:-1])
            set_run_font(run, size=size - 1)
        else:
            run = paragraph.add_run(part)
            set_run_font(run, size=size, bold=force_bold)


def add_para(doc, text: str, *, size=12, bold=False, center=False):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    p.paragraph_format.space_after = Pt(6)
    if center:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    else:
        set_rtl(p)
    add_runs(p, text, size=size, force_bold=bold)
    return p


def add_heading(doc, text: str, level: int = 1):
    p = doc.add_heading(text, level=min(level, 2))
    set_rtl(p)
    for run in p.runs:
        set_run_font(run, size=14 if level == 1 else 13, bold=True)
    return p


def parse_table(lines: list[str], start: int) -> tuple[list[list[str]], int]:
    rows = []
    i = start
    while i < len(lines) and lines[i].strip().startswith("|"):
        raw = lines[i].strip()
        if re.match(r"^\|?\s*:?-+:?\s*\|", raw):
            i += 1
            continue
        cells = [c.strip() for c in raw.strip("|").split("|")]
        rows.append(cells)
        i += 1
    return rows, i


def add_table(doc, rows: list[list[str]]):
    if not rows:
        return
    cols = max(len(r) for r in rows)
    table = doc.add_table(rows=len(rows), cols=cols)
    table.style = "Table Grid"
    for i, row in enumerate(rows):
        for j in range(cols):
            cell = table.cell(i, j)
            cell.text = ""
            p = cell.paragraphs[0]
            set_rtl(p)
            run = p.add_run(row[j] if j < len(row) else "")
            set_run_font(run, size=10, bold=(i == 0))


def convert() -> Path:
    text = MD_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.9)
    section.bottom_margin = Inches(0.9)
    section.left_margin = Inches(0.9)
    section.right_margin = Inches(0.9)

    i = 0
    in_code = False
    code_buf: list[str] = []
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("```"):
            if in_code:
                for cl in code_buf:
                    p = doc.add_paragraph()
                    set_rtl(p)
                    run = p.add_run(cl if cl else " ")
                    set_run_font(run, size=9)
                code_buf = []
                in_code = False
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue
        if not line.strip() or line.strip() == "---":
            i += 1
            continue
        if line.startswith("# "):
            add_heading(doc, line[2:].strip(), 1)
            i += 1
            continue
        if line.startswith("## "):
            add_heading(doc, line[3:].strip(), 1)
            i += 1
            continue
        if line.startswith("### "):
            add_heading(doc, line[4:].strip(), 2)
            i += 1
            continue
        if line.strip().startswith("|"):
            rows, ni = parse_table(lines, i)
            add_table(doc, rows)
            sp = doc.add_paragraph()
            sp.paragraph_format.space_after = Pt(8)
            i = ni
            continue
        if re.match(r"^[-*]\s+", line.strip()):
            item = re.sub(r"^[-*]\s+", "", line.strip())
            p = doc.add_paragraph(style="List Bullet")
            set_rtl(p)
            for child in list(p._p):
                if child.tag.endswith("r"):
                    p._p.remove(child)
            add_runs(p, item)
            i += 1
            continue
        if re.match(r"^\d+\.\s+", line.strip()):
            item = re.sub(r"^\d+\.\s+", "", line.strip())
            p = doc.add_paragraph(style="List Number")
            set_rtl(p)
            for child in list(p._p):
                if child.tag.endswith("r"):
                    p._p.remove(child)
            add_runs(p, item)
            i += 1
            continue
        if line.strip().startswith(">"):
            add_para(doc, line.strip().lstrip("> ").strip(), size=12, bold=False)
            i += 1
            continue
        add_para(doc, line.strip())
        i += 1

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUT_PATH))
    print(f"Wrote {OUT_PATH}")
    return OUT_PATH


if __name__ == "__main__":
    convert()
