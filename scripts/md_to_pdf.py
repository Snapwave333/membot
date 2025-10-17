import sys
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors
import re
from html import escape

def md_to_flowables(md_text):
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=22, leading=26, spaceAfter=12, alignment=TA_LEFT)
    h1_style = ParagraphStyle('Heading1', parent=styles['Heading1'], fontSize=18, leading=22, spaceAfter=8)
    h2_style = ParagraphStyle('Heading2', parent=styles['Heading2'], fontSize=16, leading=20, spaceAfter=6)
    h3_style = ParagraphStyle('Heading3', parent=styles['Heading3'], fontSize=14, leading=18, spaceAfter=4)
    normal_style = ParagraphStyle('Normal', parent=styles['BodyText'], fontSize=11, leading=15, spaceAfter=6)
    bullet_style = ParagraphStyle('Bullet', parent=styles['BodyText'], leftIndent=14, bulletIndent=0, fontSize=11, leading=15, spaceAfter=2)

    flow = []
    bullets = []

    def flush_bullets():
        nonlocal bullets
        if bullets:
            flow.append(ListFlowable([Paragraph(escape(b), bullet_style) for b in bullets], bulletType='bullet', start='bullet', leftIndent=20))
            bullets = []

    lines = md_text.splitlines()
    for line in lines:
        s = line.strip('\n')
        if not s.strip():
            flush_bullets()
            flow.append(Spacer(1, 8))
            continue
        if s.startswith('# '):
            flush_bullets()
            flow.append(Paragraph(escape(s[2:].strip()), title_style))
            continue
        if s.startswith('## '):
            flush_bullets()
            flow.append(Paragraph(escape(s[3:].strip()), h1_style))
            continue
        if s.startswith('### '):
            flush_bullets()
            flow.append(Paragraph(escape(s[4:].strip()), h2_style))
            continue
        if s.startswith('- '):
            bullets.append(s[2:].strip())
            continue
        # blockquote
        if s.startswith('> '):
            flush_bullets()
            flow.append(Paragraph(escape(s[2:].strip()), normal_style))
            continue
        # drop inline links formatting to just text + url
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", s)
        flow.append(Paragraph(escape(s), normal_style))
    flush_bullets()
    return flow

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: md_to_pdf.py <input.md> <output.pdf>')
        sys.exit(1)
    infile = sys.argv[1]
    outfile = sys.argv[2]
    with open(infile, 'r', encoding='utf-8') as f:
        md = f.read()
    doc = SimpleDocTemplate(outfile, pagesize=letter, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54)
    flow = md_to_flowables(md)
    doc.build(flow)
