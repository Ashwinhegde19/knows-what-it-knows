"""Fill Apart's report template with the text of report/submission.md.

    python report/fill_template.py

Reads  report/apart_template.docx   (Apart's official template, copied from their Google Doc)
       report/submission.md         (the report text, tables and figures)
Writes report/Apart_submission.docx (upload to Google Drive, open with Google Docs, download as PDF)

The template's own title block, fonts, headings, numbered and bulleted lists are kept; only the guidance text is
replaced. Tables are drawn paper-style (horizontal rules only, 95% intervals stacked under the value).
Needs python-docx.
"""
import copy
import re
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from docx.text.paragraph import Paragraph

HERE = Path(__file__).parent
TEMPLATE, MD, OUT = HERE / "apart_template.docx", HERE / "submission.md", HERE / "Apart_submission.docx"
FONT = "Old Standard TT"      # the template's font
TABLE_PT = 8
PAGE_WIDTH = 6.5              # inches between 1-inch margins
AUTHOR, AFFILIATION = "Ashwin K M", "Independent"

doc = Document(str(TEMPLATE))
body = doc.element.body
sect = body.find(qn("w:sectPr"))
kids = list(body)

# ---- prototypes from the template (copied before the guidance text is removed) ----
PROTO = {
    "h2": copy.deepcopy(kids[4]),      # "1. Introduction"
    "h3": copy.deepcopy(kids[49]),     # "Limitations"
    "p": copy.deepcopy(kids[5]),       # plain paragraph
    "num": copy.deepcopy(kids[14]),    # numbered list (contributions)
    "bullet": copy.deepcopy(kids[61]),  # bulleted list
    "ref": copy.deepcopy(kids[71]),    # numbered list (references, its own counter)
}

# ---- title block: title, author, abstract ----
md = MD.read_text()
title = re.match(r"# (.+)", md).group(1)
abstract = re.search(r"## Abstract\n\n(.*?)\n\n## ", md, re.S).group(1)
abstract = " ".join(abstract.split())

title_table = kids[1]
w_t = qn("w:t")
for t in title_table.iter(w_t):
    if t.text == "PROJECT TITLE":
        t.text = title
        for sz in t.getparent().iter(qn("w:sz")):
            sz.set(qn("w:val"), "32")          # 16 pt: the full title is long (template: 20 pt)
        for sz in t.getparent().iter(qn("w:szCs")):
            sz.set(qn("w:val"), "32")
# the innermost table that holds "Author name 1" (iter() lists outer tables before the ones nested inside them)
author_grid = [t for t in title_table.iter(qn("w:tbl"))
               if any((x.text or "").startswith("Author name 1") for x in t.iter(w_t))][-1]
assert author_grid is not title_table
for line_text, bold in ((AUTHOR, True), (AFFILIATION, False)):
    para_el = copy.deepcopy(PROTO["p"])
    for child in list(para_el):
        if child.tag != qn("w:pPr"):
            para_el.remove(child)
    run_ = OxmlElement("w:r")
    rpr_ = OxmlElement("w:rPr")
    fonts_ = OxmlElement("w:rFonts")
    for a in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fonts_.set(qn(a), FONT)
    rpr_.append(fonts_)
    if bold:
        rpr_.append(OxmlElement("w:b"))
    run_.append(rpr_)
    t_ = OxmlElement("w:t")
    t_.text = line_text
    run_.append(t_)
    para_el.append(run_)
    ppr_ = para_el.find(qn("w:pPr"))
    jc_ = OxmlElement("w:jc")
    jc_.set(qn("w:val"), "center")
    ppr_.insert(0, jc_)
    author_grid.addprevious(para_el)
author_grid.getparent().remove(author_grid)
for p in title_table.iter(qn("w:p")):
    texts = [t for t in p.iter(w_t)]
    joined = "".join(t.text or "" for t in texts)
    if joined.startswith("Summarize your project"):
        runs = p.findall(qn("w:r"))
        first_t = runs[0].find(w_t)
        first_t.text = abstract
        for extra in runs[1:]:
            p.remove(extra)
        for tag in ("w:i", "w:iCs"):
            for el in runs[0].iter(qn(tag)):
                el.getparent().remove(el)

# ---- remove the info box and every guidance paragraph ----
for el in kids[3:]:
    if el is not sect:
        body.remove(el)


# ---- helpers ----
def place(el):
    sect.addprevious(el)
    return el


def clean(el):
    """Drop bookmarks and paragraph ids copied from the template, so none are duplicated."""
    for tag in ("w:bookmarkStart", "w:bookmarkEnd"):
        for b in el.findall(qn(tag)):
            el.remove(b)
    for attr in list(el.attrib):
        if attr.endswith("paraId") or attr.endswith("textId"):
            del el.attrib[attr]
    return el


def set_spacing(el, after=None, before=None):
    ppr = el.get_or_add_pPr()
    sp = ppr.find(qn("w:spacing"))
    if sp is None:
        sp = OxmlElement("w:spacing")
        ppr.append(sp)
    sp.set(qn("w:line"), "240")          # single spacing (the template's default is 1.15)
    sp.set(qn("w:lineRule"), "auto")
    if after is not None:
        sp.set(qn("w:after"), str(after))
    if before is not None:
        sp.set(qn("w:before"), str(before))


def make_runs(par, text, size=None):
    """Add runs for **bold**, *italic* and `code` text."""
    for tok in re.split(r"(\*\*.+?\*\*|\*[^*\s][^*]*?\*|`[^`]+`)", text):
        if not tok:
            continue
        bold = tok.startswith("**")
        ital = not bold and tok.startswith("*")
        code = tok.startswith("`")
        s = tok[2:-2] if bold else tok[1:-1] if (ital or code) else tok
        r = par.add_run(s)
        r.bold, r.italic = bold or None, ital or None
        r.font.name = "Courier New" if code else FONT
        rpr = r._r.get_or_add_rPr()
        fonts = rpr.find(qn("w:rFonts"))
        for a in ("w:cs", "w:eastAsia"):
            fonts.set(qn(a), r.font.name)
        if code:
            r.font.size = Pt(10)
        elif size:
            r.font.size = Pt(size)


def para(kind, text, after=None, keep_next=False, align=None):
    el = clean(copy.deepcopy(PROTO[kind]))
    for child in list(el):
        if child.tag != qn("w:pPr"):
            el.remove(child)
    place(el)
    p = Paragraph(el, doc._body)
    make_runs(p, text)
    set_spacing(el, after=after if after is not None else 120)
    if keep_next:
        p.paragraph_format.keep_with_next = True
    if align:
        p.alignment = align
    return p


def heading(kind, text, page_break=False):
    el = clean(copy.deepcopy(PROTO[kind]))
    runs = el.findall(qn("w:r"))
    for extra in runs[1:]:
        el.remove(extra)
    runs[0].find(w_t).text = text
    place(el)
    hp = Paragraph(el, doc._body)
    hp.paragraph_format.keep_with_next = True
    hp.paragraph_format.page_break_before = page_break


def picture(alt, path, width):
    el = clean(copy.deepcopy(PROTO["p"]))
    for child in list(el):
        if child.tag != qn("w:pPr"):
            el.remove(child)
    place(el)
    p = Paragraph(el, doc._body)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str((HERE / path).resolve()), width=Inches(width))
    set_spacing(el, after=40)
    para("p", alt, after=120)


def cell_border(tc, **sides):
    pr = tc.get_or_add_tcPr()
    old = pr.find(qn("w:tcBorders"))
    if old is not None:
        pr.remove(old)
    b = OxmlElement("w:tcBorders")
    for side, size in sides.items():
        e = OxmlElement(f"w:{side}")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), str(size))
        e.set(qn("w:color"), "000000")
        b.append(e)
    pr.append(b)


def table(rows, rel):
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    tblpr = t._tbl.tblPr
    for old in tblpr.findall(qn("w:tblBorders")):
        tblpr.remove(old)
    borders = OxmlElement("w:tblBorders")
    for side, size in (("top", 12), ("bottom", 12)):
        e = OxmlElement(f"w:{side}")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), str(size))
        e.set(qn("w:color"), "000000")
        borders.append(e)
    tblpr.append(borders)
    total = sum(rel)
    inches = [PAGE_WIDTH * w / total for w in rel]
    for col, w in zip(t._tbl.tblGrid.findall(qn("w:gridCol")), inches):
        col.set(qn("w:w"), str(int(w * 1440)))
    tw = tblpr.find(qn("w:tblW"))
    tw.set(qn("w:type"), "dxa")
    tw.set(qn("w:w"), str(int(sum(inches) * 1440)))
    mar = OxmlElement("w:tblCellMar")
    for side in ("left", "right"):
        e = OxmlElement(f"w:{side}")
        e.set(qn("w:w"), "50")
        e.set(qn("w:type"), "dxa")
        mar.append(e)
    tblpr.append(mar)
    lay = OxmlElement("w:tblLayout")
    lay.set(qn("w:type"), "fixed")
    tblpr.append(lay)
    for tr in t._tbl.tr_lst:
        trpr = tr.get_or_add_trPr()
        trpr.append(OxmlElement("w:cantSplit"))
    for r, row in enumerate(rows):
        for c, text in enumerate(row):
            cell = t.cell(r, c)
            cell.width = Inches(inches[c])
            if r == 0:
                cell_border(cell._tc, bottom=8)
            elif r > 1 and row[0].strip():
                cell_border(cell._tc, top=2)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if c == 0 else WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = p.paragraph_format.space_after = Pt(1.5)
            p.paragraph_format.line_spacing = 1.0
            p.paragraph_format.keep_with_next = r < len(rows) - 1
            m = re.fullmatch(r"(.*?)[\s ](\[[^\]]*\])", text.strip())
            parts = [m.group(1), m.group(2)] if m else [text.strip()]
            for i, part in enumerate(parts):
                run = p.add_run(part)
                run.font.size = Pt(TABLE_PT)
                run.font.name = FONT
                run.bold = (r == 0) or None
                if i < len(parts) - 1:
                    run.add_break()
    place(t._tbl)       # keep order: add_table already inserts before sectPr; this is a no-op safeguard
    spacer = para("p", "", after=60)
    spacer.paragraph_format.line_spacing = 0.5


# ---- walk the markdown ----
text_lines = md.split("\n")
start = next(i for i, l in enumerate(text_lines) if l.startswith("## 1."))
lines = text_lines[start:]
section = ""
appendix_started = False
i = 0
while i < len(lines):
    line = lines[i]
    if not line.strip():
        i += 1
        continue
    m = re.match(r"(#{2,3}) (.+)", line)
    if m:
        name = m.group(2).strip()
        section = name
        if name.startswith("Appendix "):
            if not appendix_started:
                heading("h2", "Appendix")
                appendix_started = True
            heading("h3", name, page_break=name.startswith("Appendix B"))
        else:
            heading("h2" if m.group(1) == "##" else "h3", name)
        i += 1
        continue
    if line.startswith("!["):
        mm = re.match(r"!\[(.*?)\]\((.*?)\)(?:\{width=([\d.]+)in\})?", line)
        picture(mm.group(1), mm.group(2), float(mm.group(3) or 6.0))
        i += 1
        continue
    if line.startswith("|"):
        block = []
        while i < len(lines) and lines[i].startswith("|"):
            block.append(lines[i])
            i += 1
        rows = [[c.strip() for c in b.strip().strip("|").split("|")] for b in block if not re.fullmatch(r"\|[-|]+\|", b.strip())]
        rel = [len(c) for c in next(b for b in block if re.fullmatch(r"\|[-|]+\|", b.strip())).strip().strip("|").split("|")]
        table(rows, rel)
        continue
    lm = re.match(r"(- |\d+\. )(.*)", line)
    if lm:
        item = [lm.group(2)]
        numbered = lm.group(1) != "- "
        i += 1
        while i < len(lines) and lines[i].startswith("  ") and lines[i].strip():
            item.append(lines[i].strip())
            i += 1
        kind = ("ref" if section == "References" else "num") if numbered else "bullet"
        para(kind, " ".join(item), after=40)
        continue
    block = [line.strip()]
    i += 1
    while i < len(lines) and lines[i].strip() and not re.match(r"(#|!\[|\||- |\d+\. )", lines[i]):
        block.append(lines[i].strip())
        i += 1
    joined = " ".join(block)
    is_caption = joined.startswith("**Table")
    cp = para("p", joined, after=60 if is_caption else 120, keep_next=is_caption)
    if joined.startswith(("**Table B2", "**Table B3")):
        cp.paragraph_format.page_break_before = True

doc.save(str(OUT))
print("wrote", OUT)
