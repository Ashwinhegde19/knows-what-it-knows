"""Build report/submission.docx from report/submission.md with paper-style tables.

    python report/build_docx.py        (needs pandoc and python-docx)

Tables get a small font, rules only above and below the header and at the bottom, no vertical lines, and
column widths taken from the dashes in the markdown separator row.
"""
import re
import subprocess
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

HERE = Path(__file__).parent
MD, OUT = HERE / "submission.md", HERE / "submission.docx"
PAGE_WIDTH = 6.5     # inches of text width on a page with 1-inch margins
TABLE_PT, BODY_PT = 8, 11
FONT = "Arial"                # the Apart template's base font is Arial 11 pt; its headings are 14 pt and the title 20 pt

subprocess.run(["pandoc", str(MD), "-o", str(OUT), f"--resource-path={HERE}"], check=True)

# relative column widths, one list per table, in document order
widths = [[len(c) for c in line.strip().strip("|").split("|")]
          for line in MD.read_text().split("\n") if re.fullmatch(r"\|[-|]+\|", line.strip())]


def set_borders(element, tag, **sides):
    """sides: top/bottom/left/right/insideH/insideV = size in eighths of a point, 0 for none."""
    pr = element.tblPr if tag == "tblBorders" else element.get_or_add_tcPr()
    old = pr.find(qn(f"w:{tag}"))
    if old is not None:
        pr.remove(old)
    borders = OxmlElement(f"w:{tag}")
    for side, size in sides.items():
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"), "single" if size else "nil")
        el.set(qn("w:sz"), str(size))
        el.set(qn("w:color"), "000000")
        borders.append(el)
    pr.append(borders)


def stack_interval(cell):
    """Put a trailing [low, high] interval (or [95% CI] in a header) on its own line, so columns stay narrow."""
    par = cell.paragraphs[0]
    m = re.fullmatch(r"(.*?)[\s\u00a0](\[[^\]]*\])", par.text.strip())
    if not m:
        return
    for run in par.runs:
        run._r.getparent().remove(run._r)
    par.add_run(m.group(1)).add_break()
    par.add_run(m.group(2))


def set_grid(table, inches):
    """LibreOffice and Google Docs read column widths from the table grid, not from the cells."""
    grid = table._tbl.tblGrid
    for col, width in zip(grid.findall(qn("w:gridCol")), inches):
        col.set(qn("w:w"), str(int(width * 1440)))
    width = table._tbl.tblPr.find(qn("w:tblW"))
    width.set(qn("w:type"), "dxa")
    width.set(qn("w:w"), str(int(sum(inches) * 1440)))
    margins = OxmlElement("w:tblCellMar")          # tight side padding so short headers do not wrap
    for side in ("left", "right"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:w"), "50")
        el.set(qn("w:type"), "dxa")
        margins.append(el)
    table._tbl.tblPr.append(margins)
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    table._tbl.tblPr.append(layout)


doc = Document(str(OUT))
for section in doc.sections:
    section.left_margin = section.right_margin = section.top_margin = section.bottom_margin = Inches(1)
from docx.shared import RGBColor  # noqa: E402
for style in doc.styles:
    if style.type != 1:                      # paragraph styles only
        continue
    style.font.name = FONT
    rpr = style.element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.append(fonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        fonts.set(qn(attr), FONT)
    for theme in ("w:asciiTheme", "w:hAnsiTheme", "w:cstheme", "w:eastAsiaTheme"):
        fonts.attrib.pop(qn(theme), None)
    size = {"Title": 20, "Heading 1": 20, "Heading 2": 14, "Heading 3": 13}.get(style.name)
    if size:
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor(0, 0, 0)
    elif style.name in ("Normal", "Body Text", "First Paragraph", "Compact", "Image Caption", "Table Caption"):
        style.font.size = Pt(BODY_PT)

for par in doc.paragraphs:                       # a table caption stays on the same page as its table
    if re.match(r"Table \w+\.", par.text):
        par.paragraph_format.keep_with_next = True

for table, rel in zip(doc.tables, widths):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_borders(table._tbl, "tblBorders", top=12, bottom=12, left=0, right=0, insideH=0, insideV=0)
    total = sum(rel)
    set_grid(table, [PAGE_WIDTH * w / total for w in rel])
    for r, row in enumerate(table.rows):
        new_group = r > 1 and row.cells[0].text.strip() != ""
        for c, cell in enumerate(row.cells):
            cell.width = Inches(PAGE_WIDTH * rel[c] / total)
            if r == 0:
                set_borders(cell._tc, "tcBorders", bottom=8)
            elif new_group:
                set_borders(cell._tc, "tcBorders", top=2)      # hairline between models
            stack_interval(cell)
            for par in cell.paragraphs:
                par.alignment = WD_ALIGN_PARAGRAPH.LEFT if c == 0 else WD_ALIGN_PARAGRAPH.CENTER
                par.paragraph_format.keep_with_next = r < len(table.rows) - 1    # keep a table on one page
                par.paragraph_format.space_before = par.paragraph_format.space_after = Pt(1.5)
                for run in par.runs:
                    run.font.size = Pt(TABLE_PT)
                    run.bold = r == 0
doc.save(str(OUT))
print("wrote", OUT)
