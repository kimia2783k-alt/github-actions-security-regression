from __future__ import annotations

import re
import zipfile
from importlib.machinery import SourceFileLoader
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MS = ROOT / "paper" / "manuscript"
fa = (MS / "main_fa.md").read_text(encoding="utf-8")
docx = MS / "Security_Regressions_GHA_AI_Agents_Manuscript_FA.docx"
out: list[str] = []
out.append(f"docx_exists={docx.exists()} size={docx.stat().st_size}")

for bad in (
    "تهدیدهای اعتبار",
    "محدودیت‌ها",
    "کاپای کوهن",
    "فایل‌های گم",
    "هم‌ترازی محمول",
    "وضعیت:",
    "نسخهٔ تحویل",
    "تولیدشده از",
):
    out.append(f"md_has[{bad}]={bad in fa}")

m = re.search(r"## چکیده\n\n(.+?)\n\n## ", fa, re.S)
abs_txt = m.group(1) if m else ""
out.append(f"abstract_chars={len(abs_txt)}")
out.append(f"abstract_para_count={abs_txt.count(chr(10)) + 1}")

mod = SourceFileLoader("main_fa_to_docx", str(ROOT / "scripts" / "main_fa_to_docx.py")).load_module()
sample = "کنترل‌های امنیتی (CI/CD) را ویرایش می‌کنند. به دقت ۱٫۰۰ رسید (نشانه صحت)."
parts = [mm.group(0) for mm in mod.LATIN_RE.finditer(sample)]
out.append("latin_tokens=" + repr(parts))
out.append(f"font={mod.FONT_FA}")

with zipfile.ZipFile(docx) as z:
    xml = z.read("word/document.xml").decode("utf-8")
out.append(f"docx_bidi={'w:bidi' in xml}")
out.append(f"docx_has_draft_footer={'تولیدشده' in xml}")
out.append(f"docx_has_status_meta={'وضعیت' in xml}")
out.append(f"docx_nazanin={'B Nazanin' in xml}")
out.append(f"docx_has_limits={'تهدیدهای اعتبار' in xml}")
out.append(f"docx_has_abstract={'چکیده' in xml}")

qa_path = MS / "tables" / "field" / "qa_secretariat_fa.txt"
qa_path.write_text("\n".join(out) + "\n", encoding="utf-8")
print(qa_path)
for line in out:
    print(line)
