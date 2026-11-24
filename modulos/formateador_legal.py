import io
import re
from typing import Optional

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.shared import Cm, Inches, Pt, RGBColor

from modulos.notario_gt import dpi_a_letras, fecha_a_letras, limpiar_texto_xml, normalizar_dpi


def _activar_margenes_espejo(doc: docx.Document) -> None:
    """Activa <w:mirrorMargins/> para impresión en anverso y reverso del Papel Sellado de Protocolo."""
    settings = doc.settings.element
    mirror = OxmlElement("w:mirrorMargins")
    settings.append(mirror)


def _limpiar_texto_protocolo(texto_redaccion: str) -> list:
    """
    Prepara texto para Papel Sellado Especial para Protocolos (Art. 13 Código de Notariado):
    - Elimina asteriscos/almohadillas Markdown y caracteres de control XML.
    - Expande DPIs numéricos sin letras a formato letras + dígitos.
    - Suprime renglones en blanco y separa párrafos reales para evitar saltos suaves estirados.
    """
    limpio = limpiar_texto_xml(texto_redaccion).replace("**", "").replace("__", "").strip()
    limpio = re.sub(r"^#{1,6}\s+", "", limpio, flags=re.MULTILINE)

    def _reemplazar_dpi_literal(match):
        prefijo = match.group(1)
        cui_raw = match.group(2)
        cui = normalizar_dpi(cui_raw)
        if len(cui) == 13:
            return f"{prefijo} {dpi_a_letras(cui, incluir_digitos=True)}"
        return match.group(0)

    limpio = re.sub(
        r"(DPI\s*(?:número|no\.?|#|:)?)\s*(\d{4}[\s\-]?\d{5}[\s\-]?\d{4})(?!\s*\))",
        _reemplazar_dpi_literal,
        limpio,
        flags=re.IGNORECASE,
    )

    lineas = [ln.strip() for ln in limpio.splitlines() if ln.strip()]
    return lineas or [""]


def generar_documento_protocolo_espanol(titulo: str, texto_redaccion: str) -> bytes:
    """
    Genera documento en formato Papel Español / Papel Sellado Especial para Protocolos SAT
    (Art. 9 y 13 Código de Notariado Dto. 314; Decreto 37-92):
    - Hoja Oficio Guatemala: 8.5" x 13.0" (21.59 cm x 33.02 cm)
    - Caja útil exacta >= 600.0 pt para 25 líneas exactas por cara a 24 pt:
      * Margen superior: 2.15" (encabezado escudo/registro SAT)
      * Margen inferior: 2.50" -> área útil = 8.35" = 601.2 pt (25 líneas exactas x 24 pt)
      * Margen interior (costura/empaste): 4.0 cm | Exterior: 2.0 cm con mirrorMargins activado
    - Tipografía: Courier New 11 pt, justificado, cero renglones en blanco.
    """
    doc = docx.Document()
    _activar_margenes_espejo(doc)

    normal_style = doc.styles["Normal"]
    normal_style.font.name = "Courier New"
    normal_style.font.size = Pt(11)

    for section in doc.sections:
        section.page_width = Inches(8.5)
        section.page_height = Inches(13.0)
        section.top_margin = Inches(2.15)
        section.bottom_margin = Inches(2.50)
        section.left_margin = Cm(4.0)
        section.right_margin = Cm(2.0)
        section.header_distance = Inches(0.5)
        section.footer_distance = Inches(0.5)

    parrafos = _limpiar_texto_protocolo(texto_redaccion)

    for bloque in parrafos:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        p.paragraph_format.line_spacing = Pt(24)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.widow_control = False

        run = p.add_run(bloque)
        run.font.name = "Courier New"
        run.font.size = Pt(11)
        run.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()


def generar_documento_acta_notarial(
    titulo: str,
    texto_redaccion: str,
    notario_abogado: str = "",
    colegiado: str = "",
) -> bytes:
    """
    Genera Acta Notarial en papel bond tamaño Oficio conforme a los Artículos 60, 61 y 62
    del Código de Notariado (Dto. 314): sin encabezado judicial ni Timbre Forense,
    con firma del requirente, 'ANTE MÍ:' y nota de Timbre Fiscal Q. 0.50/hoja + Notarial Q. 10.00.
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
        section.left_margin = Cm(3.5)
        section.right_margin = Cm(2.5)

    cuerpo = limpiar_texto_xml(texto_redaccion).replace("**", "").strip()
    bloques = [b.strip() for b in cuerpo.split("\n\n") if b.strip()] or [cuerpo]

    for bloque in bloques:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(8)
        r = p.add_run(bloque)
        r.font.name = "Times New Roman"
        r.font.size = Pt(12)

    notario_txt = limpiar_texto_xml(notario_abogado).strip() or "____________________________________"
    col_txt = f"Colegiado Activo No. {limpiar_texto_xml(colegiado).strip()}" if colegiado and str(colegiado).strip() else "Colegiado Activo No. ________"

    p_pie = doc.add_paragraph()
    p_pie.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_pie.paragraph_format.line_spacing = 1.35
    p_pie.paragraph_format.space_before = Pt(18)
    r_pie = p_pie.add_run(
        "\n\nf) ____________________________________\n"
        "Firma del Requirente\n\n\n"
        "ANTE MÍ:\n\n\n"
        f"f) {notario_txt}\n"
        f"Abogado y Notario — {col_txt}\n"
        "[Art. 62 Código de Notariado: numerar, sellar y firmar todas las hojas. "
        "Adherir Timbre Fiscal de Q. 0.50 por hoja (Art. 5 num. 6 Dto. 37-92) y "
        "Timbre Notarial de Q. 10.00 (Art. 3 num. II lit. c Dto. 82-96)]"
    )
    r_pie.font.name = "Times New Roman"
    r_pie.font.size = Pt(11)

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
    es_exhibicion_personal: bool = False,
    es_denuncia_mp: bool = False,
    firma_a_ruego: bool = False,
) -> bytes:
    """
    Genera memorial judicial conforme al Art. 61 del CPCyM (Dto. Ley 107):
    - Hoja tamaño Oficio (8.5" x 13.0"), margen izquierdo 3.8 cm, Times New Roman 12 pt, 1.5 líneas.
    - Respeta exención de auxilio y Timbre Forense en Exhibición Personal (Art. 85 Dto. 1-86).
    - Evita duplicar encabezado en Denuncias ante el Ministerio Público (Art. 297 CPP).
    - Permite firma directa del solicitante (Art. 61 num. 8 CPCyM) o firma a ruego cuando aplique.
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

    juz_limpio = limpiar_texto_xml(juzgado_destino).strip()
    if not juz_limpio:
        juz_limpio = (
            "SEÑOR FISCAL GENERAL Y JEFE DEL MINISTERIO PÚBLICO"
            if es_denuncia_mp
            else "SEÑOR JUEZ DE PRIMERA INSTANCIA DEL RAMO COMPETENTE"
        )

    p_enc = doc.add_paragraph()
    p_enc.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_enc.paragraph_format.line_spacing = 1.15
    p_enc.paragraph_format.space_after = Pt(12)
    r_juz = p_enc.add_run(f"{juz_limpio.upper()}\n")
    r_juz.bold = True
    r_juz.font.name = "Times New Roman"
    r_juz.font.size = Pt(12)
    if titulo:
        r_ref = p_enc.add_run(f"REFERENCIA: {limpiar_texto_xml(titulo).upper()}")
        r_ref.bold = True
        r_ref.font.name = "Times New Roman"
        r_ref.font.size = Pt(11)

    cuerpo = limpiar_texto_xml(texto_redaccion).replace("**", "").strip()
    bloques = [b.strip() for b in cuerpo.split("\n\n") if b.strip()] or [cuerpo]

    for bloque in bloques:
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(8)
        r = p.add_run(bloque)
        r.font.name = "Times New Roman"
        r.font.size = Pt(12)

    fecha_letras = fecha_a_letras(fecha_doc)
    abogado_txt = limpiar_texto_xml(notario_abogado).strip() or "____________________________________"
    col_txt = f"Colegiado Activo No. {limpiar_texto_xml(colegiado).strip()}" if colegiado and str(colegiado).strip() else "Colegiado Activo No. ________"

    p_pie = doc.add_paragraph()
    p_pie.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_pie.paragraph_format.line_spacing = 1.35
    p_pie.paragraph_format.space_before = Pt(14)

    if es_exhibicion_personal:
        texto_pie = (
            f"En la ciudad de Guatemala, el {fecha_letras}.\n\n\n"
            "f) ____________________________________\n"
            "Firma del Solicitante\n"
            "[Acción Constitucional de Exhibición Personal — Art. 85 Decreto 1-86: "
            "exenta de formalidades, auxilio profesional obligatorio y Timbre Forense]"
        )
    elif es_denuncia_mp:
        texto_pie = (
            f"En la ciudad de Guatemala, el {fecha_letras}.\n\n\n"
            "f) ____________________________________\n"
            "Firma del Denunciante\n\n"
            "(Opcional) En su auxilio profesional:\n"
            f"f) {abogado_txt} — {col_txt}\n"
            "[Denuncia Penal — Art. 297-299 CPP: la denuncia ante el Ministerio Público no requiere Timbre Forense]"
        )
    elif firma_a_ruego:
        texto_pie = (
            f"En la ciudad de Guatemala, el {fecha_letras}.\n\n\n"
            "A RUEGO DEL PRESENTADO QUIEN DE MOMENTO NO PUEDE FIRMAR Y EN SU AUXILIO, DIRECCIÓN Y PROCURACIÓN:\n\n\n"
            f"f) {abogado_txt}\n"
            f"Abogado y Notario — {col_txt}\n"
            "[Adherir e inutilizar Timbre Forense de Q. 1.00 por cada hoja — Art. 3 num. I Decreto 82-96]"
        )
    else:
        texto_pie = (
            f"En la ciudad de Guatemala, el {fecha_letras}.\n\n\n"
            "f) ____________________________________\n"
            "Firma del Solicitante / Presentado\n\n"
            "EN SU AUXILIO, DIRECCIÓN Y PROCURACIÓN:\n\n\n"
            f"f) {abogado_txt}\n"
            f"Abogado y Notario — {col_txt}\n"
            "[Adherir e inutilizar Timbre Forense de Q. 1.00 por cada hoja — Art. 3 num. I Decreto 82-96]"
        )

    r_pie = p_pie.add_run(texto_pie)
    r_pie.font.name = "Times New Roman"
    r_pie.font.size = Pt(11)

    buffer = io.BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
