"""Convert paper/manuscript/main.md to a JAIAI-oriented English Word manuscript."""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
MD_PATH = ROOT / "paper" / "manuscript" / "main.md"
OUT_PATH = ROOT / "paper" / "manuscript" / "Security_Regressions_GHA_AI_Agents_Manuscript.docx"
FIG_DIR = ROOT / "paper" / "manuscript" / "figures"

FIGURES = [
    ("Figure 1. Detector F1 comparison on the field pilot (policy-v3 gold; pin-semantics-v0.5).", "method_f1.png"),
    ("Figure 2. Security regression rule hit counts (field detector findings).", "rule_counts.png"),
    ("Figure 3. Audited regression rate by agent label (field pilot N=330).", "agent_rates.png"),
]


def set_run_font(run, name: str = "Times New Roman", size: int = 12, bold=False, italic=False):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic


def set_paragraph_format(p, *, first_line: bool = False, space_after: float = 6, align=None):
    fmt = p.paragraph_format
    fmt.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    fmt.space_after = Pt(space_after)
    fmt.space_before = Pt(0)
    if first_line:
        fmt.first_line_indent = Inches(0.3)
    if align is not None:
        p.alignment = align


def add_styled_paragraph(doc, text: str, *, style_size=12, first_line=True, bold_all=False, center=False):
    p = doc.add_paragraph()
    set_paragraph_format(
        p,
        first_line=first_line and not center,
        align=WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.JUSTIFY,
    )
    add_inline_runs(p, text, size=style_size, force_bold=bold_all)
    return p


def add_inline_runs(paragraph, text: str, size: int = 12, force_bold: bool = False):
    # Split on **bold**, *italic*, `code`, and leave [n] citations as plain text
    pattern = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)")
    parts = pattern.split(text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            run = paragraph.add_run(part[2:-2])
            set_run_font(run, size=size, bold=True)
        elif part.startswith("*") and part.endswith("*") and not part.startswith("**"):
            run = paragraph.add_run(part[1:-1])
            set_run_font(run, size=size, italic=True)
        elif part.startswith("`") and part.endswith("`"):
            run = paragraph.add_run(part[1:-1])
            set_run_font(run, name="Consolas", size=size - 1)
        else:
            run = paragraph.add_run(part)
            set_run_font(run, size=size, bold=force_bold)


def add_heading_custom(doc, text: str, level: int):
    # Use built-in heading styles then reformat font
    p = doc.add_heading(text, level=min(level, 3))
    for run in p.runs:
        set_run_font(run, size=14 if level == 1 else 13 if level == 2 else 12, bold=True)
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    return p


def add_code_block(doc, code: str):
    for line in code.splitlines() or [""]:
        p = doc.add_paragraph()
        set_paragraph_format(p, first_line=False, space_after=0)
        p.paragraph_format.left_indent = Inches(0.25)
        run = p.add_run(line if line else " ")
        set_run_font(run, name="Consolas", size=9)
        run.font.color.rgb = RGBColor(0x20, 0x20, 0x20)
    # spacer
    sp = doc.add_paragraph()
    set_paragraph_format(sp, first_line=False, space_after=6)


def add_table(doc, rows: list[list[str]]):
    if not rows:
        return
    cols = max(len(r) for r in rows)
    table = doc.add_table(rows=len(rows), cols=cols)
    table.style = "Table Grid"
    for i, row in enumerate(rows):
        for j in range(cols):
            cell = table.rows[i].cells[j]
            cell.text = ""
            p = cell.paragraphs[0]
            val = row[j] if j < len(row) else ""
            run = p.add_run(val)
            set_run_font(run, size=9, bold=(i == 0))
            p.paragraph_format.space_after = Pt(2)
    cap = doc.add_paragraph()
    set_paragraph_format(cap, first_line=False, space_after=10)
    # caption already in markdown as bold line before table often — keep spacing only


def add_list_item(doc, text: str, ordered: bool = False, number: int | None = None):
    style = "List Number" if ordered else "List Bullet"
    p = doc.add_paragraph(style=style)
    # Remove any auto-inserted empty run text, then add formatted content
    for child in list(p._p):
        if child.tag.endswith("r"):
            p._p.remove(child)
    body = text if not ordered else text  # numbering comes from Word list style
    add_inline_runs(p, body, size=12)
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    p.paragraph_format.space_after = Pt(3)


def insert_figures(doc):
    add_heading_custom(doc, "Figures", 1)
    note = doc.add_paragraph()
    set_paragraph_format(note, first_line=False)
    add_inline_runs(
        note,
        "The following figures are generated from the reproducible evaluation pipeline "
        "(paper/manuscript/figures/).",
        size=11,
    )
    for caption, fname in FIGURES:
        path = FIG_DIR / fname
        if not path.exists():
            p = doc.add_paragraph()
            add_inline_runs(p, f"[Missing figure file: {fname}]", size=11, force_bold=False)
            continue
        doc.add_picture(str(path), width=Inches(5.8))
        last = doc.paragraphs[-1]
        last.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap = doc.add_paragraph()
        set_paragraph_format(cap, first_line=False, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=12)
        run = cap.add_run(caption)
        set_run_font(run, size=10, italic=True)


def parse_md_table(lines: list[str], start: int) -> tuple[list[list[str]], int]:
    rows = []
    i = start
    while i < len(lines) and lines[i].strip().startswith("|"):
        line = lines[i].strip()
        if re.match(r"^\|?\s*:?-{3,}", line.replace("|", " ").strip()) or set(
            line.replace("|", "").replace(":", "").replace("-", "").replace(" ", "")
        ) == set():
            # separator row
            i += 1
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        rows.append(cells)
        i += 1
    return rows, i


def convert():
    text = MD_PATH.read_text(encoding="utf-8")
    lines = text.splitlines()

    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)

    # Default style
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")

    i = 0
    title_done = False
    in_code = False
    code_lines: list[str] = []
    list_counter = 0
    figures_inserted = False

    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()

        # code fence
        if line.strip().startswith("```"):
            if not in_code:
                in_code = True
                code_lines = []
            else:
                in_code = False
                add_code_block(doc, "\n".join(code_lines))
                code_lines = []
            i += 1
            continue
        if in_code:
            code_lines.append(raw)
            i += 1
            continue

        if not line.strip() or line.strip() == "---":
            i += 1
            continue

        # Title
        if line.startswith("# ") and not title_done:
            title = line[2:].strip()
            p = doc.add_paragraph()
            set_paragraph_format(p, first_line=False, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=12)
            run = p.add_run(title)
            set_run_font(run, size=16, bold=True)
            title_done = True
            i += 1
            continue

        # Metadata lines after title (**Authors:** etc.)
        if line.startswith("**") and ":**" in line and not line.startswith("##"):
            p = doc.add_paragraph()
            set_paragraph_format(p, first_line=False, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=2)
            add_inline_runs(p, line.replace("  ", ""), size=11)
            i += 1
            continue

        # Headings
        if line.startswith("### "):
            add_heading_custom(doc, line[4:].strip(), 3)
            list_counter = 0
            i += 1
            continue
        if line.startswith("## "):
            heading = line[3:].strip()
            # Editorial checklist is not part of the submission Word manuscript
            if heading.lower().startswith("appendix a"):
                i += 1
                while i < len(lines):
                    nxt = lines[i]
                    if nxt.startswith("## ") and not nxt[3:].strip().lower().startswith("appendix"):
                        break
                    i += 1
                continue
            # Insert figures before Acknowledgments / References for journal flow
            if (not figures_inserted) and heading.lower().startswith("acknowledgment"):
                insert_figures(doc)
                figures_inserted = True
            add_heading_custom(doc, heading, 1)
            list_counter = 0
            i += 1
            continue

        # Table
        if line.strip().startswith("|"):
            rows, ni = parse_md_table(lines, i)
            add_table(doc, rows)
            # small spacer
            sp = doc.add_paragraph()
            set_paragraph_format(sp, first_line=False, space_after=8)
            i = ni
            continue

        # Ordered list
        m_ord = re.match(r"^(\d+)\.\s+(.*)$", line.strip())
        if m_ord:
            list_counter = int(m_ord.group(1))
            add_list_item(doc, m_ord.group(2), ordered=True, number=list_counter)
            i += 1
            continue

        # Unordered list
        if re.match(r"^[-*]\s+", line.strip()):
            item = re.sub(r"^[-*]\s+", "", line.strip())
            add_list_item(doc, item, ordered=False)
            i += 1
            continue

        # Italic-only end marker
        if line.strip().startswith("*End of milestone"):
            p = doc.add_paragraph()
            set_paragraph_format(p, first_line=False, align=WD_ALIGN_PARAGRAPH.CENTER)
            run = p.add_run(line.strip().strip("*"))
            set_run_font(run, size=10, italic=True)
            i += 1
            continue

        # Normal paragraph (may continue? treat each non-empty as paragraph)
        add_styled_paragraph(doc, line.strip(), first_line=True)
        i += 1

    if not figures_inserted:
        insert_figures(doc)

    # Footer note
    note = doc.add_paragraph()
    set_paragraph_format(note, first_line=False, space_after=0)
    run = note.add_run(
        "Generated from paper/manuscript/main.md (pin-semantics-v0.5). "
        "Paste into the official JAIAI English DOC template before submission; fill remaining author metadata there."
    )
    set_run_font(run, size=9, italic=True)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(OUT_PATH))
    print(f"Wrote {OUT_PATH}")
    return OUT_PATH


if __name__ == "__main__":
    convert()
