import io
import re
from typing import Dict, List, Optional

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Cm, Inches, Pt, RGBColor

from modulos.notario_gt import (
    calcular_timbre_notarial_guatemala,
    dpi_a_letras,
    entero_a_letras,
    fecha_a_letras,
    hoy_gt,
    limpiar_texto_xml,
    monto_a_letras,
    normalizar_dpi,
    trimestre_actual_info,
    validar_nit_m11,
)


_COLOR_PRIMARIO = RGBColor(0x1B, 0x36, 0x5D)
_COLOR_TEXTO = RGBColor(0x11, 0x18, 0x27)
_COLOR_SUAVE = RGBColor(0x4B, 0x55, 0x63)


def _crear_documento_gt(alto_pulgadas: float = 11.0) -> docx.Document:
    """Crea documento Carta (11\") u Oficio (13\") con márgenes institucionales de Guatemala y Arial 11 pt."""
    doc = docx.Document()
    normal = doc.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(11)
    normal.font.color.rgb = _COLOR_TEXTO

    for s in doc.sections:
        s.page_width = Inches(8.5)
        s.page_height = Inches(alto_pulgadas)
        s.top_margin = Cm(2.5)
        s.bottom_margin = Cm(2.5)
        s.left_margin = Cm(3.0)
        s.right_margin = Cm(2.5)
    return doc


def _set_cell_shading(cell, fill_hex: str) -> None:
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def _set_cell_margins(cell, top=90, bottom=90, left=130, right=130) -> None:
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for name, val in (("top", top), ("bottom", bottom), ("left", left), ("right", right)):
        node = OxmlElement(f"w:{name}")
        node.set(qn("w:w"), str(val))
        node.set(qn("w:type"), "dxa")
        tcMar.append(node)
    tcPr.append(tcMar)


def _estilar_tabla(table, header_bg: str = "1B365D") -> None:
    table.autofit = False
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        '<w:top w:val="single" w:sz="6" w:space="0" w:color="CBD5E1"/>'
        '<w:bottom w:val="single" w:sz="8" w:space="0" w:color="1B365D"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>'
        '<w:left w:val="none"/><w:right w:val="none"/><w:insideV w:val="none"/>'
        "</w:tblBorders>"
    )
    tblPr.append(borders)
    for row_idx, row in enumerate(table.rows):
        for cell in row.cells:
            _set_cell_margins(cell)
            if row_idx == 0:
                _set_cell_shading(cell, header_bg)
                for p in cell.paragraphs:
                    for r in p.runs:
                        r.bold = True
                        r.font.name = "Arial"
                        r.font.size = Pt(10)
                        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            else:
                if row_idx % 2 == 1:
                    _set_cell_shading(cell, "F8FAFC")
                for p in cell.paragraphs:
                    p.paragraph_format.space_before = Pt(1)
                    p.paragraph_format.space_after = Pt(1)
                    for r in p.runs:
                        r.font.name = "Arial"
                        r.font.size = Pt(10)
                        r.font.color.rgb = _COLOR_TEXTO


def _agregar_bloque_firma_notario(
    doc: docx.Document,
    datos: Dict,
    nota_timbre: str = "",
    incluir_linea_fecha: bool = True,
) -> None:
    sede = limpiar_texto_xml(datos.get("sede_notarial") or "la ciudad de Guatemala").strip()
    fecha_emision = fecha_a_letras(datos.get("fecha_emision"))
    notario = limpiar_texto_xml(datos.get("notario") or "").strip() or "________________________________________"
    colegiado = limpiar_texto_xml(datos.get("colegiado") or "").strip()
    clave = limpiar_texto_xml(datos.get("clave_notario") or "").strip()

    if incluir_linea_fecha:
        p_fecha = doc.add_paragraph()
        p_fecha.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p_fecha.paragraph_format.space_before = Pt(14)
        p_fecha.paragraph_format.space_after = Pt(28)
        r_f = p_fecha.add_run(f"En {sede}, el {fecha_emision}.")
        r_f.font.name = "Arial"
        r_f.font.size = Pt(11)
    else:
        p_sp = doc.add_paragraph()
        p_sp.paragraph_format.space_before = Pt(22)

    p_firma = doc.add_paragraph()
    p_firma.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_firma.paragraph_format.line_spacing = 1.25
    linea_col = f"Colegiado Activo No. {colegiado}" if colegiado else "Colegiado Activo No. ____________"
    linea_clave = f" — Clave de Notario: {clave}" if clave else ""
    r_sig = p_firma.add_run(
        "____________________________________________________\n"
        f"{notario}\n"
        "ABOGADO Y NOTARIO\n"
        f"{linea_col}{linea_clave}\n"
        "(Firma y Sello del Notario)"
    )
    r_sig.bold = True
    r_sig.font.name = "Arial"
    r_sig.font.size = Pt(10.5)

    if nota_timbre:
        p_nota = doc.add_paragraph()
        p_nota.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_nota.paragraph_format.space_before = Pt(8)
        rn = p_nota.add_run(limpiar_texto_xml(nota_timbre))
        rn.italic = True
        rn.font.name = "Arial"
        rn.font.size = Pt(9)
        rn.font.color.rgb = _COLOR_SUAVE


def _numero_a_letras_si_entero(valor: object, fallback: str = "___") -> str:
    txt = limpiar_texto_xml(valor).strip()
    if not txt or txt in ("___", "____", "No detectado", "N/A"):
        return fallback
    sin_comas = txt.replace(",", "").strip()
    if re.match(r"^\d{1,9}$", sin_comas):
        return f"{entero_a_letras(int(sin_comas))} ({txt})"
    return txt


def _limpiar_sufijo_rol(nombre: object) -> str:
    """Quita sufijos automáticos tipo ' (Vendedor)' o ' (Parte 1)' para documentos oficiales."""
    txt = limpiar_texto_xml(nombre).strip()
    return re.sub(r"\s*\((?:Vendedor|Comprador|Compradora|Mandante|Mandatario|Mandataria|Actor|Demandado|Parte \d+)\)\s*$", "", txt, flags=re.IGNORECASE)


def _formatear_identificacion_parte(nombre: str, dpi_raw: str, nit_raw: str) -> str:
    nom = _limpiar_sufijo_rol(nombre) or "No consignado"
    cui = normalizar_dpi(dpi_raw)
    if len(cui) == 13:
        dpi_txt = f"identificado con Documento Personal de Identificación —DPI— con Código Único de Identificación —CUI— número {dpi_a_letras(cui, incluir_digitos=True)}"
    elif str(dpi_raw or "").strip() and str(dpi_raw).strip() not in ("No detectado", "N/A", "No consignado"):
        dpi_txt = f"DPI/CUI: {limpiar_texto_xml(dpi_raw)}"
    else:
        dpi_txt = "DPI/CUI: No consignado"

    nit_ok, nit_norm = validar_nit_m11(nit_raw)
    if nit_norm:
        nit_lbl = nit_norm if nit_ok else f"{nit_norm} (verificar dígito SAT)"
        return f"{nom}, {dpi_txt}, NIT {nit_lbl}."
    return f"{nom}, {dpi_txt}."


def generar_aviso_dicabi(datos: Dict) -> bytes:
    """
    Genera Aviso Notarial de Traspaso a DICABI y Catastro Municipal conforme al
    Artículo 38 del Código de Notariado (Dto. 314) y Artículo 43 de la Ley del IUSI (Dto. 15-98).
    Plazo legal: 15 días hábiles.
    """
    doc = _crear_documento_gt(11.0)

    p_tit = doc.add_paragraph()
    p_tit.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tit.paragraph_format.space_after = Pt(12)
    r_tit = p_tit.add_run(
        "AVISO NOTARIAL DE ENAJENACIÓN DE BIEN INMUEBLE\n"
        "(Artículo 38 del Código de Notariado, Dto. 314 y Artículo 43 Ley del IUSI, Dto. 15-98)"
    )
    r_tit.bold = True
    r_tit.font.size = Pt(11.5)
    r_tit.font.color.rgb = _COLOR_PRIMARIO

    p_dest = doc.add_paragraph()
    p_dest.paragraph_format.space_after = Pt(10)
    r_dest = p_dest.add_run(
        "SEÑOR DIRECTOR DE CATASTRO Y AVALÚO DE BIENES INMUEBLES (DICABI)\n"
        "MINISTERIO DE FINANZAS PÚBLICAS — REPÚBLICA DE GUATEMALA\n"
        "Y DEPARTAMENTO DE CATASTRO MUNICIPAL CORRESPONDIENTE\n"
        "SU DESPACHO."
    )
    r_dest.bold = True

    num_esc = _numero_a_letras_si_entero(datos.get("numero_instrumento"))
    fecha_aut = fecha_a_letras(datos.get("fecha"))
    tipo_cto = limpiar_texto_xml(datos.get("tipo_contrato") or "Compraventa de Bien Inmueble")
    monto_val = float(datos.get("monto", 0.0) or 0.0)
    monto_txt = monto_a_letras(monto_val, "GTQ", incluir_cifra=True, mayusculas=True)

    enajenante_txt = _formatear_identificacion_parte(
        datos.get("vendedor", "___"),
        datos.get("dpi_vendedor", ""),
        datos.get("nit_vendedor", ""),
    )
    adquirente_txt = _formatear_identificacion_parte(
        datos.get("comprador", "___"),
        datos.get("dpi_comprador", ""),
        datos.get("nit_comprador", ""),
    )

    finca_txt = _numero_a_letras_si_entero(datos.get("finca"), "____")
    folio_txt = _numero_a_letras_si_entero(datos.get("folio"), "____")
    libro_txt = _numero_a_letras_si_entero(datos.get("libro"), "____")
    depto_reg = limpiar_texto_xml(datos.get("departamento_registro") or "Guatemala").strip()
    direccion = limpiar_texto_xml(datos.get("direccion_inmueble") or "Según descripción registral del instrumento").strip()
    area_inm = limpiar_texto_xml(datos.get("area_inmueble") or "Según inscripción de dominio en el RGP").strip()
    matricula = limpiar_texto_xml(datos.get("matricula_fiscal") or "En trámite de inscripción / actualización").strip()
    val_mat = limpiar_texto_xml(datos.get("valor_matricula") or "Según constancia catastral / avalúo vigente").strip()

    p_intro = doc.add_paragraph()
    p_intro.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_intro.paragraph_format.line_spacing = 1.25
    p_intro.paragraph_format.space_after = Pt(10)
    p_intro.add_run(
        "En cumplimiento estricto de lo preceptuado por el Artículo treinta y ocho (38) del Código de Notariado "
        "(Decreto 314) y el Artículo cuarenta y tres (43) de la Ley del Impuesto Único Sobre Inmuebles (Decreto 15-98), "
        "dentro del plazo legal de quince (15) días hábiles, por este medio doy AVISO circunstanciado de la autorización "
        "del siguiente instrumento público traslativo de dominio:"
    )

    filas = [
        ("1. Escritura Pública No.", num_esc),
        ("2. Fecha de Autorización", fecha_aut),
        ("3. Naturaleza del Contrato", tipo_cto),
        ("4. Enajenante (Vendedor)", enajenante_txt),
        ("5. Adquirente (Comprador)", adquirente_txt),
        ("6. Precio o Valor Pactado", monto_txt),
        (
            "7. Datos Registrales (RGP)",
            f"Finca número {finca_txt}, Folio {folio_txt}, del Libro {libro_txt} de {depto_reg}.",
        ),
        ("8. Área / Extensión y Dirección", f"Extensión: {area_inm}. Ubicación: {direccion}"),
        ("9. Matrícula y Valor Fiscal", f"Matrícula: {matricula} | Valor en Matrícula: {val_mat}"),
    ]

    tabla = doc.add_table(rows=1 + len(filas), cols=2)
    tabla.rows[0].cells[0].text = "REQUISITO LEGAL (ART. 38 CDN / ART. 43 IUSI)"
    tabla.rows[0].cells[1].text = "INFORMACIÓN DECLARADA"
    for idx, (k, v) in enumerate(filas, start=1):
        tabla.rows[idx].cells[0].text = limpiar_texto_xml(k)
        tabla.rows[idx].cells[1].text = limpiar_texto_xml(v)
        tabla.rows[idx].cells[0].width = Inches(2.2)
        tabla.rows[idx].cells[1].width = Inches(4.2)
    _estilar_tabla(tabla)

    p_cierre = doc.add_paragraph()
    p_cierre.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_cierre.paragraph_format.space_before = Pt(10)
    p_cierre.add_run(
        "Solicito atentamente se sirvan efectuar la anotación, traspaso y actualización de la matrícula fiscal "
        "y registro catastral correspondiente."
    )

    _agregar_bloque_firma_notario(doc, datos)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def generar_aviso_agp_testimonio(datos: Dict) -> bytes:
    """
    Genera carátula/razón de Remisión de Testimonio Especial al Archivo General de Protocolos
    conforme al Art. 37 literal a) del Código de Notariado (plazo: 25 días hábiles),
    liquidando Timbre Notarial (Dto. 82-96 Art. 3 num. II) y Timbre Fiscal de Q. 0.50 en cada hoja (Dto. 37-92 Art. 5 num. 6).
    """
    doc = _crear_documento_gt(11.0)

    p_tit = doc.add_paragraph()
    p_tit.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tit.paragraph_format.space_after = Pt(12)
    rt = p_tit.add_run(
        "REMISIÓN Y RAZÓN DE TESTIMONIO ESPECIAL\n"
        "ARCHIVO GENERAL DE PROTOCOLOS — ORGANISMO JUDICIAL DE GUATEMALA\n"
        "(Artículo 37 literal a del Código de Notariado, Decreto 314)"
    )
    rt.bold = True
    rt.font.size = Pt(11.5)
    rt.font.color.rgb = _COLOR_PRIMARIO

    p_dest = doc.add_paragraph()
    p_dest.paragraph_format.space_after = Pt(10)
    rd = p_dest.add_run(
        "SEÑOR DIRECTOR DEL ARCHIVO GENERAL DE PROTOCOLOS\n"
        "CORTE SUPREMA DE JUSTICIA — ORGANISMO JUDICIAL\n"
        "REPÚBLICA DE GUATEMALA."
    )
    rd.bold = True

    num_esc = _numero_a_letras_si_entero(datos.get("numero_instrumento"))
    fecha_aut = fecha_a_letras(datos.get("fecha"))
    fol_ini = _numero_a_letras_si_entero(datos.get("folio_inicial"), "___")
    fol_fin = _numero_a_letras_si_entero(datos.get("folio_final"), "___")
    hojas = max(1, int(datos.get("hojas_testimonio") or 1))
    hojas_txt = "una (1) hoja" if hojas == 1 else f"{entero_a_letras(hojas)} ({hojas}) hojas"
    timbre_fiscal_total = round(hojas * 0.50, 2)

    monto_val = float(datos.get("monto", 0.0) or 0.0)
    calc = calcular_timbre_notarial_guatemala(
        monto_val,
        "VALOR_DETERMINADO" if monto_val > 0 else "INDETERMINADO",
    )
    timbre_not_val = float(calc["timbre_notarial"])
    regla_timbre = str(calc["regla"])

    sistema_compulsa = limpiar_texto_xml(
        datos.get("sistema_compulsa") or "Reproducción en fotocopias impresas en anverso y reverso, más la presente hoja de razón"
    )
    otorgantes_str = limpiar_texto_xml(datos.get("otorgantes") or "").strip() or "No consignados"
    dpi1 = normalizar_dpi(datos.get("dpi_vendedor", ""))
    dpi2 = normalizar_dpi(datos.get("dpi_comprador", ""))
    extra_dpis = []
    if len(dpi1) == 13:
        extra_dpis.append(f"Otorgante 1 CUI/DPI: {dpi_a_letras(dpi1)}")
    if len(dpi2) == 13:
        extra_dpis.append(f"Otorgante 2 CUI/DPI: {dpi_a_letras(dpi2)}")
    if extra_dpis:
        otorgantes_str = f"{otorgantes_str}\n" + "\n".join(extra_dpis)

    filas = [
        ("Instrumento Público No.", num_esc),
        ("Fecha de Autorización", fecha_aut),
        ("Acto o Contrato", limpiar_texto_xml(datos.get("tipo_contrato") or "___")),
        ("Otorgantes / Comparecientes", otorgantes_str),
        ("Folios de Protocolo", f"Del folio {fol_ini} al folio {fol_fin}"),
        ("Sistema de Compulsación", sistema_compulsa),
        ("Extensión del Testimonio Especial", hojas_txt),
        (
            "Timbre Notarial (Dto. 82-96)",
            f"{monto_a_letras(timbre_not_val, 'GTQ', incluir_cifra=True, mayusculas=True)}. ({regla_timbre})",
        ),
        (
            "Timbre Fiscal (Dto. 37-92 Art. 5 num. 6)",
            f"{monto_a_letras(timbre_fiscal_total, 'GTQ', incluir_cifra=True)} (Q. 0.50 adherido en CADA hoja del testimonio especial).",
        ),
    ]

    p_body = doc.add_paragraph()
    p_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_body.paragraph_format.space_after = Pt(10)
    p_body.add_run(
        "Con fundamento en el Artículo treinta y siete (37) literal a) del Código de Notariado, "
        "y dentro del término de veinticinco (25) días hábiles siguientes al otorgamiento, "
        "ES TESTIMONIO ESPECIAL del instrumento público detallado a continuación, que compulso, numero, sello y firmo:"
    )

    tabla = doc.add_table(rows=1 + len(filas), cols=2)
    tabla.rows[0].cells[0].text = "ELEMENTO DEL TESTIMONIO"
    tabla.rows[0].cells[1].text = "DETALLE LEGAL"
    for idx, (k, v) in enumerate(filas, start=1):
        tabla.rows[idx].cells[0].text = limpiar_texto_xml(k)
        tabla.rows[idx].cells[1].text = limpiar_texto_xml(v)
        tabla.rows[idx].cells[0].width = Inches(2.2)
        tabla.rows[idx].cells[1].width = Inches(4.2)
    _estilar_tabla(tabla)

    _agregar_bloque_firma_notario(
        doc,
        datos,
        nota_timbre="Adherir Timbre Notarial en la primera hoja (Dto. 82-96) y Timbre Fiscal de Q. 0.50 en CADA hoja del testimonio especial (Art. 5 num. 6 Dto. 37-92).",
    )
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def generar_aviso_cancelacion_agp(datos: Dict) -> bytes:
    """
    Genera Aviso de Cancelación de Instrumento Público al Archivo General de Protocolos
    conforme al Artículo 37 literal b) del Código de Notariado (plazo: 25 días hábiles).
    """
    doc = _crear_documento_gt(11.0)

    p_tit = doc.add_paragraph()
    p_tit.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tit.paragraph_format.space_after = Pt(12)
    rt = p_tit.add_run(
        "AVISO DE CANCELACIÓN DE INSTRUMENTO PÚBLICO\n"
        "ARCHIVO GENERAL DE PROTOCOLOS — ORGANISMO JUDICIAL DE GUATEMALA\n"
        "(Artículo 37 literal b del Código de Notariado, Decreto 314)"
    )
    rt.bold = True
    rt.font.size = Pt(11.5)
    rt.font.color.rgb = _COLOR_PRIMARIO

    p_dest = doc.add_paragraph()
    p_dest.paragraph_format.space_after = Pt(10)
    rd = p_dest.add_run(
        "SEÑOR DIRECTOR DEL ARCHIVO GENERAL DE PROTOCOLOS\n"
        "ORGANISMO JUDICIAL DE GUATEMALA\n"
        "SU DESPACHO."
    )
    rd.bold = True

    num_esc = _numero_a_letras_si_entero(datos.get("numero_instrumento"))
    fecha_canc = fecha_a_letras(datos.get("fecha_cancelacion"))
    folios = limpiar_texto_xml(datos.get("folios") or "___")
    motivo = limpiar_texto_xml(datos.get("motivo") or "Por desistimiento o falta de firma de los comparecientes")

    p_body = doc.add_paragraph()
    p_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_body.paragraph_format.line_spacing = 1.35
    p_body.paragraph_format.space_after = Pt(10)
    p_body.add_run(
        f"En cumplimiento del Artículo treinta y siete (37) literal b) del Código de Notariado, "
        f"dentro del plazo de veinticinco (25) días hábiles siguientes a la cancelación, por este medio "
        f"DOY AVISO que procedí a CANCELAR la Escritura Pública número {num_esc}, de fecha {fecha_canc}, "
        f"contenida en el(los) folio(s) {folios} del Registro Notarial a mi cargo, por el motivo siguiente: {motivo}."
    )

    _agregar_bloque_firma_notario(doc, datos)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def generar_aviso_trimestral_agp(datos: Dict) -> bytes:
    """
    Genera Aviso Trimestral Obligatorio al Archivo General de Protocolos (positivo o negativo)
    conforme al Art. 37 literal c) del Código de Notariado (25 días hábiles post-trimestre).
    """
    doc = _crear_documento_gt(11.0)

    trim_def, anio_def = trimestre_actual_info()
    trimestre = limpiar_texto_xml(datos.get("trimestre") or trim_def)
    anio = limpiar_texto_xml(datos.get("ano") or anio_def)

    p_tit = doc.add_paragraph()
    p_tit.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tit.paragraph_format.space_after = Pt(12)
    rt = p_tit.add_run(
        "AVISO TRIMESTRAL DE INSTRUMENTOS PÚBLICOS AUTORIZADOS\n"
        f"{trimestre.upper()} — AÑO {anio}\n"
        "(Artículo 37 literal c del Código de Notariado, Decreto 314)"
    )
    rt.bold = True
    rt.font.size = Pt(11.5)
    rt.font.color.rgb = _COLOR_PRIMARIO

    p_dest = doc.add_paragraph()
    p_dest.paragraph_format.space_after = Pt(10)
    rd = p_dest.add_run(
        "SEÑOR DIRECTOR DEL ARCHIVO GENERAL DE PROTOCOLOS\n"
        "ORGANISMO JUDICIAL DE GUATEMALA\n"
        "SU DESPACHO."
    )
    rd.bold = True

    try:
        total_int = int(re.sub(r"\D", "", str(datos.get("total_autorizados") or "0")) or "0")
    except ValueError:
        total_int = 0

    colegiado = limpiar_texto_xml(datos.get("colegiado") or "____").strip()
    clave = limpiar_texto_xml(datos.get("clave_notario") or "____").strip()
    notario = limpiar_texto_xml(datos.get("notario") or "Notario Autorizante").strip()
    cancelados = limpiar_texto_xml(datos.get("cancelados") or "Ninguno").strip()

    p_body = doc.add_paragraph()
    p_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_body.paragraph_format.line_spacing = 1.35
    p_body.paragraph_format.space_after = Pt(10)

    if total_int == 0:
        p_body.add_run(
            f"Yo, {notario}, Abogado y Notario, Colegiado Activo número {colegiado} y con Clave de Registro Notarial {clave}, "
            f"en cumplimiento del Artículo treinta y siete (37) literal c) del Código de Notariado, dentro del plazo de "
            f"veinticinco (25) días hábiles siguientes al vencimiento del trimestre calendario, por este medio DOY AVISO "
            f"que durante el {trimestre} del año {anio} NO AUTORICÉ NINGÚN INSTRUMENTO PÚBLICO en el Protocolo a mi cargo."
        )
        filas = [
            ("Período Trimestral Reportado", f"{trimestre} de {anio}"),
            ("Estado del Movimiento", "SIN AUTORIZACIÓN DE INSTRUMENTOS PÚBLICOS (AVISO NEGATIVO)"),
            ("Total de Instrumentos Autorizados", "cero (0) instrumentos públicos"),
            ("Instrumentos Cancelados (Art. 37 lit. b)", cancelados),
        ]
    else:
        primer_num = _numero_a_letras_si_entero(datos.get("primer_num", "1"))
        ultimo_num = _numero_a_letras_si_entero(datos.get("ultimo_num", str(total_int)))
        total_aut = _numero_a_letras_si_entero(str(total_int))
        fecha_ult = fecha_a_letras(datos.get("fecha_ultimo"))
        p_body.add_run(
            f"Yo, {notario}, Abogado y Notario, Colegiado Activo número {colegiado} y con Clave de Registro Notarial {clave}, "
            f"en cumplimiento del Artículo treinta y siete (37) literal c) del Código de Notariado, dentro del plazo de "
            f"veinticinco (25) días hábiles siguientes al vencimiento del trimestre calendario, por este medio DOY AVISO "
            f"del movimiento del Protocolo a mi cargo correspondiente al {trimestre} del año {anio}, en la forma siguiente:"
        )
        filas = [
            ("Período Trimestral Reportado", f"{trimestre} de {anio}"),
            ("Primer Instrumento del Período", f"Escritura Pública número {primer_num}"),
            ("Último Instrumento Autorizado", f"Escritura Pública número {ultimo_num}"),
            ("Fecha del Último Instrumento", fecha_ult),
            ("Total de Instrumentos Autorizados", f"{total_aut} instrumento(s) público(s)"),
            ("Instrumentos Cancelados (Art. 37 lit. b)", cancelados),
        ]

    tabla = doc.add_table(rows=1 + len(filas), cols=2)
    tabla.rows[0].cells[0].text = "CONCEPTO DEL PROTOCOLO"
    tabla.rows[0].cells[1].text = "DETALLE DECLARADO"
    for idx, (k, v) in enumerate(filas, start=1):
        tabla.rows[idx].cells[0].text = limpiar_texto_xml(k)
        tabla.rows[idx].cells[1].text = limpiar_texto_xml(v)
        tabla.rows[idx].cells[0].width = Inches(2.4)
        tabla.rows[idx].cells[1].width = Inches(4.0)
    _estilar_tabla(tabla)

    _agregar_bloque_firma_notario(doc, datos)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def generar_aviso_matrimonio_renap(datos: Dict) -> bytes:
    """
    Genera Aviso Circunstanciado de Matrimonio Civil para el RENAP conforme al
    Art. 102 del Código Civil (Dto. Ley 106) y Art. 84 de la Ley del RENAP (Dto. 90-2005).
    """
    doc = _crear_documento_gt(11.0)

    p_tit = doc.add_paragraph()
    p_tit.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tit.paragraph_format.space_after = Pt(12)
    rt = p_tit.add_run(
        "AVISO CIRCUNSTANCIADO DE MATRIMONIO CIVIL\n"
        "REGISTRO NACIONAL DE LAS PERSONAS (RENAP) — REPÚBLICA DE GUATEMALA\n"
        "(Artículo 102 Código Civil, Dto. Ley 106 y Artículo 84 Ley del RENAP, Dto. 90-2005)"
    )
    rt.bold = True
    rt.font.size = Pt(11.5)
    rt.font.color.rgb = _COLOR_PRIMARIO

    muni_cel = limpiar_texto_xml(datos.get("municipio_celebracion") or "Guatemala, Guatemala").strip()
    p_dest = doc.add_paragraph()
    p_dest.paragraph_format.space_after = Pt(10)
    rd = p_dest.add_run(
        "SEÑOR REGISTRADOR CIVIL DE LAS PERSONAS\n"
        "REGISTRO NACIONAL DE LAS PERSONAS (RENAP)\n"
        f"MUNICIPIO Y DEPARTAMENTO DE {muni_cel.upper()}."
    )
    rd.bold = True

    fecha_mat = fecha_a_letras(datos.get("fecha_matrimonio"))
    hora_mat = limpiar_texto_xml(datos.get("hora_matrimonio") or "____________________").strip()
    lugar_mat = limpiar_texto_xml(datos.get("lugar_celebracion") or muni_cel).strip()
    regimen = limpiar_texto_xml(
        datos.get("regimen_economico") or "Comunidad de Gananciales (régimen subsidiario legal, Art. 126 Código Civil)"
    ).strip()

    dpi_el = dpi_a_letras(datos.get("dpi_contrayente_1", ""), incluir_digitos=True)
    dpi_ella = dpi_a_letras(datos.get("dpi_contrayente_2", ""), incluir_digitos=True)

    p_body = doc.add_paragraph()
    p_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_body.paragraph_format.line_spacing = 1.25
    p_body.paragraph_format.space_after = Pt(10)
    p_body.add_run(
        f"En cumplimiento del Artículo ciento dos (102) del Código Civil y Artículo ochenta y cuatro (84) de la "
        f"Ley del RENAP, aviso a usted que el día {fecha_mat}, siendo las {hora_mat}, en {lugar_mat}, autoricé "
        f"mediante Acta Notarial el MATRIMONIO CIVIL de las siguientes personas:"
    )

    filas = [
        ("Contrayente 1 (Varón)", limpiar_texto_xml(datos.get("nombre_contrayente_1") or "___")),
        ("Generales Contrayente 1", limpiar_texto_xml(datos.get("generales_1") or "______________________________")),
        ("CUI / DPI Contrayente 1 (En Letras)", dpi_el),
        ("Padres / Partida Nacimiento 1", limpiar_texto_xml(datos.get("padres_1") or "______________________________")),
        ("Contrayente 2 (Mujer)", limpiar_texto_xml(datos.get("nombre_contrayente_2") or "___")),
        ("Generales Contrayente 2", limpiar_texto_xml(datos.get("generales_2") or "______________________________")),
        ("CUI / DPI Contrayente 2 (En Letras)", dpi_ella),
        ("Padres / Partida Nacimiento 2", limpiar_texto_xml(datos.get("padres_2") or "______________________________")),
        ("Régimen Económico Adoptado", regimen),
        ("Protocolización del Acta (Art. 101 CC)", limpiar_texto_xml(datos.get("escritura_protocolizacion") or "Protocolizada conforme Art. 101 Código Civil")),
    ]

    tabla = doc.add_table(rows=1 + len(filas), cols=2)
    tabla.rows[0].cells[0].text = "DATO REGISTRAL CIVIL"
    tabla.rows[0].cells[1].text = "INFORMACIÓN CIRCUNSTANCIADA"
    for idx, (k, v) in enumerate(filas, start=1):
        tabla.rows[idx].cells[0].text = limpiar_texto_xml(k)
        tabla.rows[idx].cells[1].text = limpiar_texto_xml(v)
        tabla.rows[idx].cells[0].width = Inches(2.2)
        tabla.rows[idx].cells[1].width = Inches(4.2)
    _estilar_tabla(tabla)

    _agregar_bloque_firma_notario(doc, datos)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def generar_indice_protocolo_docx(
    registros: List[Dict],
    anio: Optional[int] = None,
    notario: str = "",
    colegiado: str = "",
    clave_notario: str = "",
    sede_notarial: str = "la ciudad de Guatemala",
    total_cancelados: int = 0,
) -> bytes:
    """
    Genera el ÍNDICE OFICIAL DEL PROTOCOLO en Word (.docx) tamaño Oficio (8.5\" x 13\")
    conforme a los Artículos 15 y 16 del Código de Notariado (Dto. 314), con las 5 columnas
    reglamentarias, orden numérico, razón de cierre única y nota de Timbre Fiscal de Q. 0.50/hoja.
    """
    doc = _crear_documento_gt(13.0)
    anio_val = int(anio or hoy_gt().year)
    anio_txt = entero_a_letras(anio_val)
    sede_limpia = limpiar_texto_xml(sede_notarial or "la ciudad de Guatemala").strip()
    notario_limpio = limpiar_texto_xml(notario or "__________________________").strip()

    p_tit = doc.add_paragraph()
    p_tit.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tit.paragraph_format.space_after = Pt(10)
    rt = p_tit.add_run(
        f"ÍNDICE DEL PROTOCOLO CORRESPONDIENTE AL AÑO {anio_txt.upper()} ({anio_val})\n"
        f"DEL NOTARIO {notario_limpio.upper()}\n"
        "(Artículos 15 y 16 del Código de Notariado, Decreto 314)"
    )
    rt.bold = True
    rt.font.size = Pt(11)
    rt.font.color.rgb = _COLOR_PRIMARIO

    def _clave_orden(reg: Dict):
        raw = str(reg.get("numero_expediente") or "")
        dig = "".join(ch for ch in raw if ch.isdigit())
        return (0, int(dig)) if dig else (1, raw)

    ordenados = sorted(registros, key=_clave_orden)

    tabla = doc.add_table(rows=1 + max(1, len(ordenados)), cols=5)
    encabezados = [
        "No. Orden",
        "Lugar y Fecha",
        "Otorgantes",
        "Objeto del Instrumento",
        "Folio",
    ]
    anchos = [Inches(0.7), Inches(1.3), Inches(2.1), Inches(1.6), Inches(0.7)]
    for i, tit in enumerate(encabezados):
        tabla.rows[0].cells[i].text = tit
        tabla.rows[0].cells[i].width = anchos[i]

    if not ordenados:
        tabla.rows[1].cells[0].text = "---"
        tabla.rows[1].cells[1].text = "---"
        tabla.rows[1].cells[2].text = "Sin instrumentos registrados en este año fiscal"
        tabla.rows[1].cells[3].text = "---"
        tabla.rows[1].cells[4].text = "---"
    else:
        for idx, r in enumerate(ordenados, start=1):
            num_inst = limpiar_texto_xml(r.get("numero_expediente") or "---")
            fecha_inst = limpiar_texto_xml(r.get("fecha_resolucion") or "N/A")
            otorg1 = _limpiar_sufijo_rol(r.get("demandante") or "---")
            otorg2 = _limpiar_sufijo_rol(r.get("demandado") or "")
            otorg_txt = (
                f"{otorg1} / {otorg2}"
                if otorg2 and otorg2 not in ("Desconocido", "N/A", "Unilateral / Acto notarial sin contraparte")
                else otorg1
            )
            objeto = limpiar_texto_xml(r.get("tipo_proceso") or r.get("materia") or "Instrumento Público")
            folio = limpiar_texto_xml(r.get("folio_protocolo") or "---")

            valores = [num_inst, f"{sede_limpia}, {fecha_inst}", otorg_txt, objeto, folio]
            for c_i, val in enumerate(valores):
                tabla.rows[idx].cells[c_i].text = val
                tabla.rows[idx].cells[c_i].width = anchos[c_i]

    _estilar_tabla(tabla)

    total_reg = len(ordenados)
    canc_n = max(0, int(total_cancelados or 0))
    txt_canc = (
        "sin instrumentos cancelados"
        if canc_n == 0
        else f"y {entero_a_letras(canc_n)} ({canc_n}) instrumento(s) cancelado(s)"
    )

    p_cierre = doc.add_paragraph()
    p_cierre.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_cierre.paragraph_format.space_before = Pt(14)
    p_cierre.add_run(
        f"En {sede_limpia}, el {fecha_a_letras()}, extiendo, sello y firmo el presente "
        f"ÍNDICE DEL PROTOCOLO a mi cargo correspondiente al año {anio_txt}, el cual contiene "
        f"{entero_a_letras(total_reg)} ({total_reg}) instrumentos públicos autorizados {txt_canc}, "
        f"de conformidad con los Artículos 15 y 16 del Código de Notariado."
    )

    _agregar_bloque_firma_notario(
        doc,
        {
            "notario": notario_limpio,
            "colegiado": colegiado,
            "clave_notario": clave_notario,
            "sede_notarial": sede_limpia,
        },
        nota_timbre="De conformidad con el Art. 5 num. 6 del Decreto 37-92, adherir Timbre Fiscal de Q. 0.50 en CADA hoja del Índice.",
        incluir_linea_fecha=False,
    )
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def generar_resumen_juridico_ejecutivo(reg: Dict) -> bytes:
    """Genera Dictamen / Hoja de Control Forense del expediente o escritura desde Bóveda."""
    doc = _crear_documento_gt(11.0)

    p_tit = doc.add_paragraph()
    p_tit.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tit.paragraph_format.space_after = Pt(12)
    rt = p_tit.add_run(
        "DICTAMEN Y HOJA DE CONTROL LEGAL / NOTARIAL — LEX IA 360\n"
        f"DOCUMENTO REF.: {limpiar_texto_xml(reg.get('numero_expediente') or 'S/N').upper()}"
    )
    rt.bold = True
    rt.font.size = Pt(12)
    rt.font.color.rgb = _COLOR_PRIMARIO

    monto_val = float(reg.get("monto_litigio") or 0.0)
    tn_val = float(reg.get("timbre_notarial") or 0.0)
    tf_val = float(reg.get("timbre_fiscal") or 0.0)

    p1 = _formatear_identificacion_parte(
        reg.get("demandante", "N/A"),
        reg.get("dpi_demandante", ""),
        reg.get("nit_demandante", ""),
    )
    p2 = _formatear_identificacion_parte(
        reg.get("demandado", "N/A"),
        reg.get("dpi_demandado", ""),
        reg.get("nit_demandado", ""),
    )

    filas = [
        ("Categoría Documental", limpiar_texto_xml(reg.get("categoria_documental") or "N/A")),
        ("Órgano / Notario / Registro", limpiar_texto_xml(reg.get("juzgado") or "N/A")),
        ("Materia / Tipo de Acto", f"{limpiar_texto_xml(reg.get('materia', ''))} — {limpiar_texto_xml(reg.get('tipo_proceso', ''))}"),
        ("Folio de Protocolo", limpiar_texto_xml(reg.get("folio_protocolo") or "N/A")),
        ("Datos Registrales / Inmueble", limpiar_texto_xml(reg.get("datos_registrales") or "N/A")),
        ("Compareciente / Actor 1", p1),
        ("Compareciente / Demandado 2", p2),
        ("Cuantía / Monto Declarado", monto_a_letras(monto_val, "GTQ", incluir_cifra=True)),
        ("Timbre Notarial / Fiscal", f"Notarial: Q. {tn_val:,.2f} | Fiscal: Q. {tf_val:,.2f}"),
        ("Registro Destino y Plazo", f"{limpiar_texto_xml(reg.get('registro_destino', 'N/A'))} — Plazo: {limpiar_texto_xml(reg.get('plazo_procesal', 'N/A'))}"),
        ("Semáforo de Control", f"{limpiar_texto_xml(reg.get('semaforo', ''))} | Alerta: {limpiar_texto_xml(reg.get('anomalia', 'Ninguna'))}"),
    ]

    tabla = doc.add_table(rows=1 + len(filas), cols=2)
    tabla.rows[0].cells[0].text = "CAMPO AUDITADO"
    tabla.rows[0].cells[1].text = "DETERMINACIÓN LEGAL"
    for idx, (k, v) in enumerate(filas, start=1):
        tabla.rows[idx].cells[0].text = limpiar_texto_xml(k)
        tabla.rows[idx].cells[1].text = limpiar_texto_xml(v)
        tabla.rows[idx].cells[0].width = Inches(2.2)
        tabla.rows[idx].cells[1].width = Inches(4.2)
    _estilar_tabla(tabla)

    p_res = doc.add_paragraph()
    p_res.paragraph_format.space_before = Pt(12)
    r_h = p_res.add_run("RESUMEN JURÍDICO FORENSE:\n")
    r_h.bold = True
    r_h.font.color.rgb = _COLOR_PRIMARIO
    p_res.add_run(limpiar_texto_xml(reg.get("resumen_forense") or "Sin observaciones adicionales registradas."))

    p_pie = doc.add_paragraph()
    p_pie.paragraph_format.space_before = Pt(14)
    r_pie = p_pie.add_run(f"Emitido el {fecha_a_letras()} — Sistema Lex IA 360 Guatemala.")
    r_pie.italic = True
    r_pie.font.size = Pt(9.5)
    r_pie.font.color.rgb = _COLOR_SUAVE

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
