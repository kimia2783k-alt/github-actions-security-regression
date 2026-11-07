"""Convert paper/manuscript/main_fa.md to a print-ready RTL Persian academic Word file."""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
MD_PATH = ROOT / "paper" / "manuscript" / "main_fa.md"
OUT_PATH = ROOT / "paper" / "manuscript" / "Security_Regressions_GHA_AI_Agents_Manuscript_FA.docx"
FIG_DIR = ROOT / "paper" / "manuscript" / "figures"
FONT_EN = "Times New Roman"

FIGURES = [
    ("شکل ۱. مقایسهٔ اف‌یک تشخیص‌گرها در پایلوت میدانی.", "method_f1.png"),
    ("شکل ۲. شمار برخورد قواعد پسرفت در میدان.", "rule_counts.png"),
    ("شکل ۳. نرخ پسرفت بر حسب برچسب عامل (N=330).", "agent_rates.png"),
]

# Only alphabetic Latin / markdown wrappers — never bare () or pure digits (breaks RTL).
LATIN_RE = re.compile(
    r"(?:`[^`]+`|\*\*[^*]+\*\*|"
    r"[A-Za-z][A-Za-z0-9_./@+\-:%]*)"
)

SKIP_META_PREFIXES = (
    "**نوع اثر:**",
    "**وضعیت:**",
    "**تاریخ:**",
    "**Manuscript type:**",
    "**Status:**",
    "**Date:**",
    "**Target venue:**",
)


def pick_fa_font() -> str:
    try:
        from matplotlib import font_manager

        available = {f.name for f in font_manager.fontManager.ttflist}
        for name in ("B Nazanin", "BNazanin", "IRANSans", "Tahoma"):
            if name in available:
                return name
    except Exception:
        pass
    return "Tahoma"


FONT_FA = pick_fa_font()


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
    rtl = rPr.find(qn("w:rtl"))
    if rtl is None:
        rtl = OxmlElement("w:rtl")
        rPr.append(rtl)
    rtl.set(qn("w:val"), "1" if persian else "0")
    if not persian:
        run.font.color.rgb = RGBColor(0x1A, 0x1A, 0x1A)


def set_para_rtl(paragraph, *, justify: bool = True, first_line: bool = False):
    pPr = paragraph._p.get_or_add_pPr()
    bidi = pPr.find(qn("w:bidi"))
    if bidi is None:
        bidi = OxmlElement("w:bidi")
        pPr.append(bidi)
    bidi.set(qn("w:val"), "1")
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
    if first_line:
        paragraph.paragraph_format.first_line_indent = Cm(0.75)


def add_mixed_runs(paragraph, text: str, *, size: int = 12, force_bold: bool = False):
    text = text.replace("⟦", "").replace("⟧", "")
    # Strip markdown italic markers for print prose
    text = re.sub(r"(?<!\*)\*(?!\*)([^*]+)\*(?!\*)", r"\1", text)
    pos = 0
    for m in LATIN_RE.finditer(text):
        if m.start() > pos:
            fa = text[pos : m.start()]
            if fa:
                run = paragraph.add_run(fa)
                set_run_font(run, persian=True, size=size, bold=force_bold)
        token = m.group(0)
        bold = force_bold
        if token.startswith("**") and token.endswith("**"):
            token = token[2:-2]
            bold = True
            is_fa = bool(re.search(r"[\u0600-\u06FF]", token)) and not re.search(r"[A-Za-z]", token)
        elif token.startswith("`") and token.endswith("`"):
            token = token[1:-1]
            is_fa = False
        else:
            is_fa = bool(re.search(r"[\u0600-\u06FF]", token)) and not re.search(r"[A-Za-z]", token)
        if not is_fa and re.search(r"[A-Za-z]", token):
            display = f"\u200e{token}\u200f"
            run = paragraph.add_run(display)
            set_run_font(run, persian=False, size=size, bold=bold)
        else:
            run = paragraph.add_run(token)
            set_run_font(run, persian=True, size=size, bold=bold)
        pos = m.end()
    if pos < len(text):
        fa = text[pos:]
        if fa:
            run = paragraph.add_run(fa)
            set_run_font(run, persian=True, size=size, bold=force_bold)


def add_para(doc, text: str, *, size=12, bold=False, center=False, first_line=False):
    p = doc.add_paragraph()
    if center:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
        p.paragraph_format.space_after = Pt(6)
    else:
        set_para_rtl(p, first_line=first_line)
    add_mixed_runs(p, text, size=size, force_bold=bold)
    return p


def add_heading(doc, text: str, level: int = 1):
    p = doc.add_heading("", level=min(level, 2))
    for child in list(p._p):
        if child.tag.endswith("r"):
            p._p.remove(child)
    set_para_rtl(p, justify=False)
    add_mixed_runs(p, text, size=14 if level == 1 else 12, force_bold=True)
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(8)
    return p


def insert_figures(doc) -> None:
    add_heading(doc, "شکل‌ها", 1)
    for caption, fname in FIGURES:
        path = FIG_DIR / fname
        if not path.exists():
            add_para(doc, f"[فایل شکل موجود نیست: {fname}]", size=11, first_line=False)
            continue
        doc.add_picture(str(path), width=Inches(5.6))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap = doc.add_paragraph()
        set_para_rtl(cap, justify=False)
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_mixed_runs(cap, caption, size=10)
        cap.paragraph_format.space_after = Pt(12)


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
    # ~2.5 cm print margins
    for side in ("top_margin", "bottom_margin", "left_margin", "right_margin"):
        setattr(sec, side, Cm(2.5))

    sectPr = sec._sectPr
    bidi = OxmlElement("w:bidi")
    bidi.set(qn("w:val"), "1")
    sectPr.append(bidi)

    title_done = False
    in_body = False
    figures_inserted = False
    i = 0
    in_code = False
    code_buf: list[str] = []
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("```"):
            if in_code:
                for cl in code_buf:
                    p = doc.add_paragraph()
                    p.paragraph_format.left_indent = Cm(0.5)
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
        if not line.strip() or line.strip() == "---":
            i += 1
            continue
        # Skip internal draft meta
        if any(line.startswith(p) for p in SKIP_META_PREFIXES):
            i += 1
            continue
        if line.strip().startswith("*پایان") or line.strip().startswith("*End"):
            i += 1
            continue

        if line.startswith("# ") and not title_done:
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
            p.paragraph_format.space_after = Pt(14)
            add_mixed_runs(p, line[2:].strip(), size=16, force_bold=True)
            title_done = True
            i += 1
            continue
        if line.startswith("## "):
            heading = line[3:].strip()
            # چک‌لیست ویرایشی جزء فایل ورد ارسالی نیست
            if heading.startswith("پیوست الف"):
                i += 1
                while i < len(lines):
                    nxt = lines[i]
                    if nxt.startswith("## ") and not nxt[3:].strip().startswith("پیوست"):
                        break
                    i += 1
                continue
            if (not figures_inserted) and heading.startswith("سپاسگزاری"):
                insert_figures(doc)
                figures_inserted = True
            add_heading(doc, heading, 1)
            in_body = heading not in ("چکیده", "کلیدواژه‌ها", "منابع")
            i += 1
            continue
        if line.startswith("### "):
            add_heading(doc, line[4:].strip(), 2)
            in_body = True
            i += 1
            continue
        if line.startswith("**") and ":**" in line and not line.startswith("##"):
            add_para(doc, line.replace("  ", ""), size=11, center=True)
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
        if re.match(r"^\d+\.\s+", line.strip()) or re.match(r"^[۰-۹]+\.\s+", line.strip()):
            item = re.sub(r"^[\d۰-۹]+\.\s+", "", line.strip())
            p = doc.add_paragraph(style="List Number")
            for child in list(p._p):
                if child.tag.endswith("r"):
                    p._p.remove(child)
            set_para_rtl(p)
            add_mixed_runs(p, item, size=12)
            i += 1
            continue

        # Abstract / keywords: no first-line indent; body paragraphs indent
        first = in_body and not line.startswith("**جدول")
        add_para(doc, line.strip(), first_line=first)
        i += 1

    if not figures_inserted:
        insert_figures(doc)

    note = doc.add_paragraph()
    set_para_rtl(note, justify=False)
    add_mixed_runs(
        note,
        "تولیدشده از paper/manuscript/main_fa.md (نسخه pin-semantics-v0.5).",
        size=9,
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUT_PATH))
    print(f"Wrote {OUT_PATH} (font={FONT_FA})")
    return OUT_PATH


if __name__ == "__main__":
    convert()
