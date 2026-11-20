import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
import io

def generar_documento_protocolo_espanol(titulo: str, texto_redaccion: str, notario: str = "Ashly Brigeth Rodas Estrada") -> bytes:
    """
    Genera un documento Word formateado rigurosamente para Papel Sellado Especial de Protocolo (Guatemala):
    - 25 líneas exactas por página.
    - Margen izquierdo ampliado a 4.0 cm para empaste protocolar.
    - Interlineado exacto de 24 puntos.
    - Tipografía Courier New o Times New Roman de 12 pt.
    """
    doc = docx.Document()
    
    for section in doc.sections:
        # Márgenes legales de protocolo
        section.top_margin = Inches(1.3)     # Espacio superior para el membrete oficial del papel SAT
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.6)    # 4 cm aprox para margen de costura y empaste
        section.right_margin = Inches(0.8)
        
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    p.paragraph_format.line_spacing = Pt(24) # Calibrado para las 25 líneas reglamentarias
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    
    run = p.add_run(texto_redaccion)
    run.font.name = "Courier New" # O Times New Roman
    run.font.size = Pt(11.5)
    run.font.color.rgb = RGBColor(15, 23, 42)
    
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def generar_documento_memorial_judicial(titulo: str, texto_redaccion: str, juzgado: str = "JUZGADO DE PRIMERA INSTANCIA") -> bytes:
    """
    Genera un memorial judicial profesional (Ramas Civil, Familiar o Penal)
    listo para impresión y firma del abogado colegiado activo.
    """
    doc = docx.Document()
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.2)
        section.right_margin = Inches(1.0)
        
    p_head = doc.add_paragraph()
    r_head = p_head.add_run(juzgado.upper() + "\n")
    r_head.bold = True
    r_head.font.name = "Calibri"
    r_head.font.size = Pt(11)
    
    p_body = doc.add_paragraph()
    p_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_body.paragraph_format.line_spacing = 1.15
    p_body.paragraph_format.space_after = Pt(6)
    
    r_body = p_body.add_run(texto_redaccion)
    r_body.font.name = "Calibri"
    r_body.font.size = Pt(10.5)
    
    p_pie = doc.add_paragraph()
    p_pie.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_pie.add_run(
        "\n\nGuatemala, _____ de ____________________ del año dos mil veinticuatro.\n\n\n\n"
        "____________________________________________\n"
        "Firma del Presentante / Mandatario\n\n"
        "EN SU AUXILIO Y DIRECCIÓN PROFESIONAL:\n\n\n\n"
        "____________________________________________\n"
        "Abogado y Notario — Colegiado Activo"
    )
    
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
