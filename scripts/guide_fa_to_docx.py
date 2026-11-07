"""Convert long Persian guide Markdown to Word with proper mixed RTL/LTR runs."""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
MD_PATH = ROOT / "paper" / "manuscript" / "guide_explain_fa.md"
OUT_PATH = ROOT / "paper" / "manuscript" / "Guide_Explain_Full_FA.docx"
FONT_FA = "Tahoma"
FONT_EN = "Times New Roman"

# Latin / code-ish tokens (kept LTR)
LATIN_RE = re.compile(
    r"(?:`[^`]+`|\*\*[^*]+\*\*|⟦[^⟧]+⟧|"
    r"[A-Za-z][A-Za-z0-9_./@+\-:%]*|"
    r"\d+(?:\.\d+)?%?|"
    r"[()\[\]{}|=<>]+)"
)


def _rPr(run):
    return run._element.get_or_add_rPr()


def set_run_font(run, *, persian: bool, size: int = 12, bold: bool = False, italic: bool = False):
    font = FONT_FA if persian else FONT_EN
    run.font.name = font
    rPr = _rPr(run)
    rFonts = rPr.find(qn("w:rFonts"))
    if rFonts is None:
        rFonts = OxmlElement("w:rFonts")
        rPr.insert(0, rFonts)
    rFonts.set(qn("w:ascii"), font)
    rFonts.set(qn("w:hAnsi"), font)
    rFonts.set(qn("w:eastAsia"), FONT_FA)
    rFonts.set(qn("w:cs"), FONT_FA)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    # RTL flag on run
    rtl = rPr.find(qn("w:rtl"))
    if rtl is None:
        rtl = OxmlElement("w:rtl")
        rPr.append(rtl)
    rtl.set(qn("w:val"), "1" if persian else "0")
    if not persian:
        run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)


def set_para_rtl(paragraph, *, justify: bool = True):
    pPr = paragraph._p.get_or_add_pPr()
    # bidi
    bidi = pPr.find(qn("w:bidi"))
    if bidi is None:
        bidi = OxmlElement("w:bidi")
        pPr.append(bidi)
    bidi.set(qn("w:val"), "1")
    # text direction
    text_dir = pPr.find(qn("w:textDirection"))
    if text_dir is None:
        text_dir = OxmlElement("w:textDirection")
        pPr.append(text_dir)
    text_dir.set(qn("w:val"), "rl")
    paragraph.paragraph_format.alignment = (
        WD_ALIGN_PARAGRAPH.JUSTIFY if justify else WD_ALIGN_PARAGRAPH.RIGHT
    )
    paragraph.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    paragraph.paragraph_format.space_after = Pt(8)
    paragraph.paragraph_format.space_before = Pt(0)


def add_mixed_runs(paragraph, text: str, *, size: int = 12, force_bold: bool = False):
    """Split Persian vs Latin and emit separate runs with correct direction."""
    text = text.replace("⟦", "").replace("⟧", "")
    pos = 0
    for m in LATIN_RE.finditer(text):
        if m.start() > pos:
            fa = text[pos : m.start()]
            if fa:
                run = paragraph.add_run(fa)
                set_run_font(run, persian=True, size=size, bold=force_bold)
        token = m.group(0)
        bold = force_bold
        italic = False
        if token.startswith("**") and token.endswith("**"):
            token = token[2:-2]
            bold = True
            is_fa = bool(re.search(r"[\u0600-\u06FF]", token))
        elif token.startswith("`") and token.endswith("`"):
            token = token[1:-1]
            is_fa = False
        else:
            is_fa = bool(re.search(r"[\u0600-\u06FF]", token)) and not re.search(
                r"[A-Za-z]", token
            )
        # wrap English with thin spaces + RLM after to stabilize bidi
        if not is_fa and re.search(r"[A-Za-z]", token):
            display = f"\u200e{token}\u200f"
        else:
            display = token
        run = paragraph.add_run(display)
        set_run_font(run, persian=is_fa, size=size, bold=bold, italic=italic)
        pos = m.end()
    if pos < len(text):
        fa = text[pos:]
        if fa:
            run = paragraph.add_run(fa)
            set_run_font(run, persian=True, size=size, bold=force_bold)


def add_para(doc, text: str, *, size=12, bold=False, center=False):
    p = doc.add_paragraph()
    if center:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    else:
        set_para_rtl(p)
    add_mixed_runs(p, text, size=size, force_bold=bold)
    return p


def add_heading(doc, text: str, level: int = 1):
    p = doc.add_heading("", level=min(level, 2))
    # clear default runs
    for child in list(p._p):
        if child.tag.endswith("r"):
            p._p.remove(child)
    set_para_rtl(p, justify=False)
    add_mixed_runs(p, text, size=16 if level == 1 else 14, force_bold=True)
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(8)
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
            set_para_rtl(p, justify=False)
            add_mixed_runs(p, row[j] if j < len(row) else "", size=10, force_bold=(i == 0))


def convert() -> Path:
    lines = MD_PATH.read_text(encoding="utf-8").splitlines()
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = Inches(0.85)
    sec.bottom_margin = Inches(0.85)
    sec.left_margin = Inches(0.85)
    sec.right_margin = Inches(0.85)

    # section bidi
    sectPr = sec._sectPr
    bidi = OxmlElement("w:bidi")
    bidi.set(qn("w:val"), "1")
    sectPr.append(bidi)

    i = 0
    in_code = False
    code_buf: list[str] = []
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("```"):
            if in_code:
                for cl in code_buf:
                    p = doc.add_paragraph()
                    p.paragraph_format.left_indent = Inches(0.2)
                    p.paragraph_format.space_after = Pt(0)
                    run = p.add_run(cl if cl else " ")
                    set_run_font(run, persian=False, size=9)
                code_buf = []
                in_code = False
                sp = doc.add_paragraph()
                sp.paragraph_format.space_after = Pt(8)
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code_buf.append(line)
            i += 1
            continue
        if not line.strip() or set(line.strip()) <= {"-", "—", "–"}:
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
            sp.paragraph_format.space_after = Pt(10)
            i = ni
            continue
        if re.match(r"^[-*]\s+", line.strip()):
            item = re.sub(r"^[-*]\s+", "", line.strip())
            p = doc.add_paragraph(style="List Bullet")
            for child in list(p._p):
                if child.tag.endswith("r"):
                    p._p.remove(child)
            set_para_rtl(p)
            add_mixed_runs(p, item, size=12)
            i += 1
            continue
        if re.match(r"^\d+\.\s+", line.strip()):
            item = re.sub(r"^\d+\.\s+", "", line.strip())
            p = doc.add_paragraph(style="List Number")
            for child in list(p._p):
                if child.tag.endswith("r"):
                    p._p.remove(child)
            set_para_rtl(p)
            add_mixed_runs(p, item, size=12)
            i += 1
            continue
        if line.strip().startswith(">"):
            add_para(doc, line.strip().lstrip("> ").strip(), size=12)
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
