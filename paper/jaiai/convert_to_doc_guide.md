# Convert Milestone Manuscript to JAIAI DOC Template

The journal requires submission in the official **JAIAI Template (English)** DOC file (not Markdown).

## Steps

1. Download the JAIAI English template from the submissions page:  
   https://www.journalaiai.com/index.php/aiai/about/submissions
2. Open `paper/manuscript/main.md` as the content source.
3. Paste section-by-section into the DOC template (Title → Abstract → … → References).
4. Insert figures from `paper/manuscript/figures/*.png` with captions Figure 1–3.
5. Rebuild tables using Word table tools (copy from Markdown tables in `main.md`).
6. Replace `[To be filled]` author/affiliation fields.
7. Keep the AI writing disclosure sentence exactly as required by JAIAI.
8. Export PDF preview for coauthor review; upload DOC to OJS for submission.

## Files to attach alongside

- Cover letter: `paper/manuscript/cover_letter.md` (paste into DOC/PDF)
- Suggested reviewers: `paper/manuscript/suggested_reviewers.md` (fill real emails)
- Optional zip of replication package (`src/`, `policies/`, `data/sample/`, `annotations/`)
