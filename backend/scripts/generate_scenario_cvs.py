"""Generar los cinco documentos de entrada; no abre SQLite ni crea candidatos."""
import json
from pathlib import Path
from xml.sax.saxutils import escape
import reportlab
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / 'docs/demo_escenarios'


def generate():
    fonts = Path(reportlab.__file__).parent / 'fonts'
    pdfmetrics.registerFont(TTFont('CVSans', str(fonts / 'Vera.ttf')))
    pdfmetrics.registerFont(TTFont('CVSansBold', str(fonts / 'VeraBd.ttf')))
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='NameCV', fontName='CVSansBold', fontSize=24, leading=29, textColor=colors.HexColor('#16384b'), spaceAfter=10))
    styles.add(ParagraphStyle(name='RoleCV', fontName='CVSans', fontSize=13, leading=18, textColor=colors.HexColor('#26717a'), spaceAfter=14))
    styles.add(ParagraphStyle(name='SectionCV', fontName='CVSansBold', fontSize=11, leading=14, textColor=colors.HexColor('#26717a'), spaceBefore=15, spaceAfter=7))
    styles.add(ParagraphStyle(name='BodyCV', fontName='CVSans', fontSize=10.5, leading=16, spaceAfter=5, alignment=TA_LEFT))
    styles.add(ParagraphStyle(name='NoticeCV', fontName='CVSansBold', fontSize=8, leading=12, textColor=colors.HexColor('#666666'), spaceAfter=18))
    output = DIRECTORY / 'cvs'
    output.mkdir(parents=True, exist_ok=True)
    for item in json.loads((DIRECTORY / 'perfiles_ficticios.json').read_text()):
        p = item['profile']; pref = p['preferences']; experience = p['work_experience'][0]; education = p['education'][0]
        story = []
        def line(text, style='BodyCV'):
            story.append(Paragraph(escape(text), styles[style]))
        def section(title, text):
            line(title, 'SectionCV'); line(text)
        line('WORKINT / CV FICTICIO / DEMOSTRACIÓN ACADÉMICA', 'NoticeCV')
        line(p['name'], 'NameCV')
        line(p['target_role'], 'RoleCV')
        line(f"{p['location']}, Colombia | {p['email']}")
        section('RESUMEN PROFESIONAL', f"Profesional con 3 años de experiencia ficticia. {p['professional_summary']}")
        section('HABILIDADES', ' · '.join(p['skills']))
        line('EXPERIENCIA LABORAL', 'SectionCV')
        line(f"{experience['role']} | {experience['company']} (empresa ficticia)")
        line('Julio de 2023 - junio de 2026 | 3 años')
        line(experience['description'])
        section('EDUCACIÓN', f"{education['degree']} | {education['institution']} | 2018 - 2022")
        line('CARGO OBJETIVO Y PREFERENCIAS', 'SectionCV')
        line('Cargo objetivo: '+p['target_role'])
        modes = {'hibrido':'Híbrido', 'remoto':'Remoto', 'presencial':'Presencial'}
        line(f"Ciudad preferida: {p['location']}. Modalidad: {modes[pref['work_modes'][0]]}.")
        money = lambda x: f'{x:,}'.replace(',', '.')
        line(f"Aspiración salarial mensual: {money(pref['salary_min_cop'])} - {money(pref['salary_max_cop'])} COP.")
        line('Tipo de contrato: indefinido. Disponibilidad: inmediata. Idioma: español.')
        story.append(Spacer(1,16))
        line('Todos los datos personales, educativos y laborales son ficticios. Documento de entrada para una simulación local; no representa una candidatura real.', 'NoticeCV')
        def footer(canvas, doc):
            canvas.setFont('CVSans',8);canvas.setFillColor(colors.HexColor('#666666'))
            canvas.drawString(46,27,'WORKINT | Escenarios controlados | 13 de octubre de 2026')
            canvas.drawRightString(A4[0]-46,27,str(doc.page))
        SimpleDocTemplate(str(output/item['pdf']),pagesize=A4,rightMargin=46,leftMargin=46,topMargin=38,bottomMargin=43,title=f"CV ficticio - {p['name']}",author='WORKINT - demostración académica').build(story,onFirstPage=footer,onLaterPages=footer)
        print(output/item['pdf'])


if __name__ == '__main__':
    generate()
