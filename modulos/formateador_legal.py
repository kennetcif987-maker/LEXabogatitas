import io
import re
from typing import Optional

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.shared import Cm, Inches, Pt, RGBColor

from modulos.notario_gt import dpi_a_letras, fecha_a_letras, normalizar_dpi


def _limpiar_texto_protocolo(texto_redaccion: str) -> str:
    """
    Prepara texto para Papel Sellado Especial para Protocolos (Art. 13 Código de Notariado):
    - Elimina asteriscos/almohadillas Markdown.
    - Expande marcadores [DPI: XXXXXXXXXXXXX] o DPI numéricos sin letras a formato letras + dígitos.
    - Suprime renglones en blanco para evitar espacios vacíos entre líneas del protocolo.
    """
    limpio = str(texto_redaccion or "").replace("**", "").replace("__", "").strip()
    limpio = re.sub(r"^#{1,6}\s+", "", limpio, flags=re.MULTILINE)

    def _reemplazar_dpi_literal(match):
        prefijo = match.group(1)
        cui_raw = match.group(2)
        cui = normalizar_dpi(cui_raw)
        if len(cui) == 13:
            return f"{prefijo} {dpi_a_letras(cui, incluir_digitos=True)}"
        return match.group(0)

    # Si aparece "DPI número 2456789010101" sin letras, lo expande automáticamente
    limpio = re.sub(
        r"(DPI\s*(?:número|no\.?|#|:)?)\s*(\d{4}[\s\-]?\d{5}[\s\-]?\d{4})(?!\s*\))",
        _reemplazar_dpi_literal,
        limpio,
        flags=re.IGNORECASE,
    )

    lineas = [ln.strip() for ln in limpio.splitlines() if ln.strip()]
    return " ".join(lineas) if len(lineas) <= 1 else "\n".join(lineas)


def generar_documento_protocolo_espanol(titulo: str, texto_redaccion: str) -> bytes:
    """
    Genera documento en formato Papel Español / Papel Sellado Especial para Protocolos SAT
    (Decreto 37-92 y Código de Notariado Decreto 314):
    - Hoja Oficio Guatemala: 8.5" x 13.0" (21.59 cm x 33.02 cm)
    - Caja de texto exacta para 25 líneas por cara a 24 pt de interlineado exacto (600 pt = 8.333"):
      * Margen superior: 2.15" (encabezado escudo/registro SAT)
      * Margen inferior: 2.52"
      * Margen izquierdo: 4.0 cm (costura / empaste reglamentario)
      * Margen derecho: 2.0 cm
    - Tipografía: Courier New 11 pt, alineación justificada, cero líneas en blanco.
    """
    doc = docx.Document()

    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Courier New"
    normal_style.font.size = Pt(11)

    for section in doc.sections:
        section.page_width = Inches(8.5)
        section.page_height = Inches(13.0)
        section.top_margin = Inches(2.15)
        section.bottom_margin = Inches(2.52)
        section.left_margin = Cm(4.0)
        section.right_margin = Cm(2.0)
        section.header_distance = Inches(0.5)
        section.footer_distance = Inches(0.5)

    cuerpo = _limpiar_texto_protocolo(texto_redaccion)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    p.paragraph_format.line_spacing = Pt(24)
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.widow_control = False

    run = p.add_run(cuerpo)
    run.font.name = "Courier New"
    run.font.size = Pt(11)
    run.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def generar_documento_memorial_judicial(
    titulo: str,
    texto_redaccion: str,
    juzgado_destino: str = "SEÑOR JUEZ DE PRIMERA INSTANCIA DEL RAMO CIVIL DEL DEPARTAMENTO DE GUATEMALA",
    notario_abogado: str = "",
    colegiado: str = "",
    fecha_doc: Optional[object] = None,
) -> bytes:
    """
    Genera memorial judicial conforme al Art. 61 del Código Procesal Civil y Mercantil (CPCyM)
    y prácticas del Organismo Judicial de Guatemala:
    - Hoja tamaño Oficio (8.5" x 13.0")
    - Márgenes: Superior 1.2", Inferior 1.0", Izquierdo 3.8 cm (costura expediente), Derecho 2.5 cm
    - Tipografía Times New Roman 12 pt, interlineado 1.5, justificado
    - Fecha dinámica actual en letras y recordatorio de Timbre Forense Q. 1.00 por hoja (Dto. 82-96)
    """
    doc = docx.Document()

    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Times New Roman"
    normal_style.font.size = Pt(12)

    for section in doc.sections:
        section.page_width = Inches(8.5)
        section.page_height = Inches(13.0)
        section.top_margin = Inches(1.2)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Cm(3.8)
        section.right_margin = Cm(2.5)

    p_enc = doc.add_paragraph()
    p_enc.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_enc.paragraph_format.line_spacing = 1.15
    p_enc.paragraph_format.space_after = Pt(12)
    r_juz = p_enc.add_run(f"{str(juzgado_destino or '').upper()}\n")
    r_juz.bold = True
    r_juz.font.name = "Times New Roman"
    r_juz.font.size = Pt(12)
    if titulo:
        r_ref = p_enc.add_run(f"REFERENCIA: {titulo.upper()}")
        r_ref.bold = True
        r_ref.font.name = "Times New Roman"
        r_ref.font.size = Pt(11)

    cuerpo = str(texto_redaccion or "").replace("**", "").strip()
    bloques = [b.strip() for b in cuerpo.split("\n\n") if b.strip()]
    if not bloques:
        bloques = [cuerpo]

    for bloque in bloques:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(8)
        r = p.add_run(bloque)
        r.font.name = "Times New Roman"
        r.font.size = Pt(12)

    fecha_letras = fecha_a_letras(fecha_doc)
    abogado_txt = notario_abogado.strip() if notario_abogado and notario_abogado.strip() else "____________________________________"
    col_txt = f"Colegiado Activo No. {colegiado.strip()}" if colegiado and str(colegiado).strip() else "Colegiado Activo No. ________"

    p_pie = doc.add_paragraph()
    p_pie.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_pie.paragraph_format.line_spacing = 1.35
    p_pie.paragraph_format.space_before = Pt(14)
    r_pie = p_pie.add_run(
        f"En la ciudad de Guatemala, el {fecha_letras}.\n\n\n"
        f"A RUEGO DEL PRESENTADO QUIEN DE MOMENTO NO PUEDE FIRMAR Y EN SU AUXILIO, DIRECCIÓN Y PROCURACIÓN:\n\n\n"
        f"f) {abogado_txt}\n"
        f"Abogado y Notario — {col_txt}\n"
        f"[Adherir e inutilizar Timbre Forense de Q. 1.00 por cada hoja — Art. 3 num. I Decreto 82-96]"
    )
    r_pie.font.name = "Times New Roman"
    r_pie.font.size = Pt(11)

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
