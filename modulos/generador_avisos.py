import datetime
import io
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
    monto_a_letras,
    normalizar_dpi,
    trimestre_actual_info,
    validar_nit_m11,
)


_COLOR_PRIMARIO = RGBColor(0x1B, 0x36, 0x5D)
_COLOR_TEXTO = RGBColor(0x11, 0x18, 0x27)
_COLOR_SUAVE = RGBColor(0x4B, 0x55, 0x63)


def _crear_documento_carta_gt() -> docx.Document:
    """Documento tamaño Carta (8.5\" x 11\") con márgenes institucionales de Guatemala y Arial 11 pt."""
    doc = docx.Document()
    normal = doc.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(11)
    normal.font.color.rgb = _COLOR_TEXTO

    for s in doc.sections:
        s.page_width = Inches(8.5)
        s.page_height = Inches(11.0)
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


def _agregar_bloque_firma_notario(doc: docx.Document, datos: Dict, nota_timbre: str = "") -> None:
    fecha_emision = fecha_a_letras(datos.get("fecha_emision"))
    notario = str(datos.get("notario") or "").strip() or "________________________________________"
    colegiado = str(datos.get("colegiado") or "").strip()
    clave = str(datos.get("clave_notario") or "").strip()

    p_fecha = doc.add_paragraph()
    p_fecha.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_fecha.paragraph_format.space_before = Pt(14)
    p_fecha.paragraph_format.space_after = Pt(28)
    r_f = p_fecha.add_run(f"En la ciudad de Guatemala, el {fecha_emision}.")
    r_f.font.name = "Arial"
    r_f.font.size = Pt(11)

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
        rn = p_nota.add_run(nota_timbre)
        rn.italic = True
        rn.font.name = "Arial"
        rn.font.size = Pt(9)
        rn.font.color.rgb = _COLOR_SUAVE


def _numero_a_letras_si_entero(valor: object, fallback: str = "___") -> str:
    txt = str(valor or "").strip()
    if not txt or txt in ("___", "____", "No detectado", "N/A"):
        return fallback
    digitos = "".join(ch for ch in txt if ch.isdigit())
    if digitos and len(digitos) <= 9 and txt.replace(".", "").replace(",", "").strip().isdigit():
        return f"{entero_a_letras(int(digitos))} ({txt})"
    return txt


def _formatear_identificacion_parte(nombre: str, dpi_raw: str, nit_raw: str) -> str:
    nom = str(nombre or "").strip() or "No consignado"
    cui = normalizar_dpi(dpi_raw)
    if len(cui) == 13:
        dpi_txt = f"identificado con Documento Personal de Identificación —DPI— con Código Único de Identificación —CUI— número {dpi_a_letras(cui, incluir_digitos=True)}"
    elif str(dpi_raw or "").strip() and str(dpi_raw).strip() not in ("No detectado", "N/A", "No consignado"):
        dpi_txt = f"DPI/CUI: {dpi_raw}"
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
    Artículo 38 del Código de Notariado (Dto. 314). Plazo legal: 15 días hábiles.
    Incluye DPI de otorgantes en letras y cifras, montos y finca/folio en letras y fecha dinámica.
    """
    doc = _crear_documento_carta_gt()

    p_tit = doc.add_paragraph()
    p_tit.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tit.paragraph_format.space_after = Pt(12)
    r_tit = p_tit.add_run(
        "AVISO NOTARIAL DE ENAJENACIÓN DE BIEN INMUEBLE\n"
        "(Artículo 38 del Código de Notariado, Decreto 314)"
    )
    r_tit.bold = True
    r_tit.font.size = Pt(12)
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
    tipo_cto = str(datos.get("tipo_contrato") or "Compraventa de Bien Inmueble")
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
    depto_reg = str(datos.get("departamento_registro") or "Guatemala").strip()
    direccion = str(datos.get("direccion_inmueble") or "Según descripción registral del instrumento").strip()
    matricula = str(datos.get("matricula_fiscal") or "En trámite de inscripción / actualización").strip()

    p_intro = doc.add_paragraph()
    p_intro.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_intro.paragraph_format.line_spacing = 1.25
    p_intro.paragraph_format.space_after = Pt(10)
    p_intro.add_run(
        "En cumplimiento estricto de lo preceptuado por el Artículo treinta y ocho (38) del Código de Notariado "
        "(Decreto 314 del Congreso de la República), dentro del plazo legal de quince (15) días hábiles, "
        "por este medio doy AVISO circunstanciado de la autorización del siguiente instrumento público traslativo de dominio:"
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
        ("8. Ubicación / Dirección Inmueble", direccion),
        ("9. Matrícula Fiscal", matricula),
    ]

    tabla = doc.add_table(rows=1 + len(filas), cols=2)
    tabla.rows[0].cells[0].text = "REQUISITO LEGAL (ART. 38 CDN)"
    tabla.rows[0].cells[1].text = "INFORMACIÓN DECLARADA"
    for idx, (k, v) in enumerate(filas, start=1):
        tabla.rows[idx].cells[0].text = k
        tabla.rows[idx].cells[1].text = v
        tabla.rows[idx].cells[0].width = Inches(2.2)
        tabla.rows[idx].cells[1].width = Inches(4.2)
    _estilar_tabla(tabla)

    p_cierre = doc.add_paragraph()
    p_cierre.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_cierre.paragraph_format.space_before = Pt(10)
    p_cierre.add_run(
        "Solicito atentamente se sirvan efectuar la anotación, traspaso y actualización de la matrícula fiscal "
        "y registro catastral correspondiente. Acompaño copia simple legalizada / datos de verificación cuando proceda."
    )

    _agregar_bloque_firma_notario(doc, datos)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def generar_aviso_agp_testimonio(datos: Dict) -> bytes:
    """
    Genera carátula/razón de Remisión de Testimonio Especial al Archivo General de Protocolos
    conforme al Art. 37 literal a) del Código de Notariado (plazo: 25 días hábiles),
    liquidando Timbre Notarial (Dto. 82-96 Art. 3 num. II) y Timbre Fiscal de Q. 0.50 por hoja (Dto. 37-92).
    """
    doc = _crear_documento_carta_gt()

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
    timbre_fiscal_razon = round(hojas * 0.50, 2)

    monto_val = float(datos.get("monto", 0.0) or 0.0)
    if datos.get("timbre_notarial") not in (None, "", 0, 0.0):
        timbre_not_val = float(datos.get("timbre_notarial", 10.0))
        regla_timbre = "Según monto ingresado / liquidación notarial."
    else:
        calc = calcular_timbre_notarial_guatemala(
            monto_val,
            "VALOR_DETERMINADO" if monto_val > 0 else "INDETERMINADO",
        )
        timbre_not_val = float(calc["timbre_notarial"])
        regla_timbre = str(calc["regla"])

    otorgantes_str = str(datos.get("otorgantes") or "").strip() or "No consignados"
    # Enriquecer otorgantes si se pasaron dpi_vendedor/dpi_comprador aparte
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
        ("Acto o Contrato", str(datos.get("tipo_contrato") or "___")),
        ("Otorgantes / Comparecientes", otorgantes_str),
        ("Folios de Protocolo", f"Del folio {fol_ini} al folio {fol_fin}"),
        ("Hojas del Testimonio Especial", f"{entero_a_letras(hojas)} ({hojas}) hoja(s)"),
        (
            "Timbre Notarial (Dto. 82-96)",
            f"{monto_a_letras(timbre_not_val, 'GTQ', incluir_cifra=True, mayusculas=True)}. ({regla_timbre})",
        ),
        (
            "Timbre Fiscal Razón (Dto. 37-92 Art. 5 num. 6)",
            f"{monto_a_letras(timbre_fiscal_razon, 'GTQ', incluir_cifra=True)} (Q. 0.50 por cada hoja adherido e inutilizado).",
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
        tabla.rows[idx].cells[0].text = k
        tabla.rows[idx].cells[1].text = v
        tabla.rows[idx].cells[0].width = Inches(2.2)
        tabla.rows[idx].cells[1].width = Inches(4.2)
    _estilar_tabla(tabla)

    _agregar_bloque_firma_notario(
        doc,
        datos,
        nota_timbre="Adherir Timbre Notarial en la primera hoja y Timbre Fiscal de Q. 0.50 por hoja en la razón final.",
    )
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def generar_aviso_trimestral_agp(datos: Dict) -> bytes:
    """
    Genera Aviso Trimestral Obligatorio al Archivo General de Protocolos
    conforme al Art. 37 literal c) del Código de Notariado (25 días hábiles post-trimestre).
    """
    doc = _crear_documento_carta_gt()

    trim_def, anio_def = trimestre_actual_info()
    trimestre = str(datos.get("trimestre") or trim_def)
    anio = str(datos.get("ano") or anio_def)

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

    primer_num = _numero_a_letras_si_entero(datos.get("primer_num", "1"))
    ultimo_num = _numero_a_letras_si_entero(datos.get("ultimo_num", "0"))
    total_aut = _numero_a_letras_si_entero(datos.get("total_autorizados", "0"))
    cancelados = str(datos.get("cancelados") or "Ninguno").strip()
    fecha_ult = fecha_a_letras(datos.get("fecha_ultimo"))
    colegiado = str(datos.get("colegiado") or "____").strip()
    clave = str(datos.get("clave_notario") or "____").strip()
    notario = str(datos.get("notario") or "Notario Autorizante").strip()

    p_body = doc.add_paragraph()
    p_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_body.paragraph_format.line_spacing = 1.35
    p_body.paragraph_format.space_after = Pt(10)
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
        tabla.rows[idx].cells[0].text = k
        tabla.rows[idx].cells[1].text = v
        tabla.rows[idx].cells[0].width = Inches(2.4)
        tabla.rows[idx].cells[1].width = Inches(4.0)
    _estilar_tabla(tabla)

    _agregar_bloque_firma_notario(doc, datos)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def generar_aviso_matrimonio_renap(datos: Dict) -> bytes:
    """
    Genera Aviso Circunstanciado de Matrimonio Civil para el Registro Nacional de las Personas (RENAP)
    conforme al Art. 102 del Código Civil (Dto. Ley 106) y Ley del RENAP (Dto. 90-2005).
    Plazo legal: 15 días hábiles siguientes a la celebración.
    """
    doc = _crear_documento_carta_gt()

    p_tit = doc.add_paragraph()
    p_tit.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tit.paragraph_format.space_after = Pt(12)
    rt = p_tit.add_run(
        "AVISO CIRCUNSTANCIADO DE MATRIMONIO CIVIL\n"
        "REGISTRO NACIONAL DE LAS PERSONAS (RENAP) — REPÚBLICA DE GUATEMALA\n"
        "(Artículo 102 del Código Civil, Decreto Ley 106)"
    )
    rt.bold = True
    rt.font.size = Pt(11.5)
    rt.font.color.rgb = _COLOR_PRIMARIO

    p_dest = doc.add_paragraph()
    p_dest.paragraph_format.space_after = Pt(10)
    rd = p_dest.add_run(
        "SEÑOR REGISTRADOR CIVIL DE LAS PERSONAS\n"
        "REGISTRO NACIONAL DE LAS PERSONAS (RENAP)\n"
        f"MUNICIPIO Y DEPARTAMENTO DE {str(datos.get('municipio_celebracion') or 'GUATEMALA').upper()}."
    )
    rd.bold = True

    fecha_mat = fecha_a_letras(datos.get("fecha_matrimonio"))
    hora_mat = str(datos.get("hora_matrimonio") or "diez horas con cero minutos").strip()
    lugar_mat = str(datos.get("lugar_celebracion") or "la ciudad de Guatemala").strip()
    regimen = str(datos.get("regimen_economico") or "Comunidad de Gananciales (subsidiario legal, Art. 124 Código Civil)").strip()

    dpi_el = dpi_a_letras(datos.get("dpi_contrayente_1", ""), incluir_digitos=True)
    dpi_ella = dpi_a_letras(datos.get("dpi_contrayente_2", ""), incluir_digitos=True)

    p_body = doc.add_paragraph()
    p_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_body.paragraph_format.line_spacing = 1.25
    p_body.paragraph_format.space_after = Pt(10)
    p_body.add_run(
        f"En cumplimiento del Artículo ciento dos (102) del Código Civil y dentro del término legal de quince (15) días hábiles, "
        f"aviso a usted que el día {fecha_mat}, siendo las {hora_mat}, en {lugar_mat}, autoricé mediante Acta Notarial "
        f"el MATRIMONIO CIVIL de las siguientes personas:"
    )

    filas = [
        ("Contrayente 1 (Varón)", str(datos.get("nombre_contrayente_1") or "___")),
        ("Edad / Estado Civil Anterior / Origen", str(datos.get("generales_1") or "Mayor de edad, soltero, guatemalteco")),
        ("CUI / DPI Contrayente 1 (En Letras)", dpi_el),
        ("Padres de Contrayente 1", str(datos.get("padres_1") or "No consignados")),
        ("Contrayente 2 (Mujer)", str(datos.get("nombre_contrayente_2") or "___")),
        ("Edad / Estado Civil Anterior / Origen", str(datos.get("generales_2") or "Mayor de edad, soltera, guatemalteca")),
        ("CUI / DPI Contrayente 2 (En Letras)", dpi_ella),
        ("Padres de Contrayente 2", str(datos.get("padres_2") or "No consignados")),
        ("Régimen Económico Adoptado", regimen),
        ("Protocolización del Acta (Art. 101 CC)", str(datos.get("escritura_protocolizacion") or "Protocolizada conforme Art. 101 Código Civil")),
    ]

    tabla = doc.add_table(rows=1 + len(filas), cols=2)
    tabla.rows[0].cells[0].text = "DATO REGISTRAL CIVIL"
    tabla.rows[0].cells[1].text = "INFORMACIÓN CIRCUNSTANCIADA"
    for idx, (k, v) in enumerate(filas, start=1):
        tabla.rows[idx].cells[0].text = k
        tabla.rows[idx].cells[1].text = v
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
) -> bytes:
    """
    Genera el ÍNDICE OFICIAL DEL PROTOCOLO en Word (.docx) conforme a los Artículos 15 y 92
    del Código de Notariado (Dto. 314), con las 5 columnas reglamentarias, orden numérico,
    razón de cierre y nota de Timbre Fiscal de Q. 0.50 por hoja (Dto. 37-92 Art. 5 num. 6).
    """
    doc = _crear_documento_carta_gt()
    anio_val = int(anio or datetime.date.today().year)
    anio_txt = entero_a_letras(anio_val)

    p_tit = doc.add_paragraph()
    p_tit.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tit.paragraph_format.space_after = Pt(10)
    rt = p_tit.add_run(
        f"ÍNDICE DEL PROTOCOLO CORRESPONDIENTE AL AÑO {anio_txt.upper()} ({anio_val})\n"
        f"DEL NOTARIO {str(notario or '__________________________').upper()}\n"
        "(Artículo 15 y Artículo 92 del Código de Notariado, Decreto 314)"
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
    anchos = [Inches(0.7), Inches(1.2), Inches(2.2), Inches(1.6), Inches(0.7)]
    for i, tit in enumerate(encabezados):
        tabla.rows[0].cells[i].text = tit
        tabla.rows[0].cells[i].width = anchos[i]

    if not ordenados:
        tabla.rows[1].cells[0].text = "---"
        tabla.rows[1].cells[1].text = "---"
        tabla.rows[1].cells[2].text = "Sin instrumentos registrados en este período"
        tabla.rows[1].cells[3].text = "---"
        tabla.rows[1].cells[4].text = "---"
    else:
        for idx, r in enumerate(ordenados, start=1):
            num_inst = str(r.get("numero_expediente") or "---")
            fecha_inst = str(r.get("fecha_resolucion") or "N/A")
            otorg1 = str(r.get("demandante") or "---")
            otorg2 = str(r.get("demandado") or "")
            otorg_txt = f"{otorg1} / {otorg2}" if otorg2 and otorg2 not in ("Desconocido", "N/A") else otorg1
            objeto = str(r.get("tipo_proceso") or r.get("materia") or "Instrumento Público")
            folio = str(r.get("folio_protocolo") or "---")

            valores = [num_inst, f"Guatemala, {fecha_inst}", otorg_txt, objeto, folio]
            for c_i, val in enumerate(valores):
                tabla.rows[idx].cells[c_i].text = val
                tabla.rows[idx].cells[c_i].width = anchos[c_i]

    _estilar_tabla(tabla)

    total_reg = len(ordenados)
    p_cierre = doc.add_paragraph()
    p_cierre.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p_cierre.paragraph_format.space_before = Pt(14)
    p_cierre.add_run(
        f"En la ciudad de Guatemala, el {fecha_a_letras()}, extiendo, sello y firmo el presente "
        f"ÍNDICE DEL PROTOCOLO a mi cargo correspondiente al año {anio_txt}, el cual contiene "
        f"{entero_a_letras(total_reg)} ({total_reg}) instrumentos públicos debidamente autorizados."
    )

    _agregar_bloque_firma_notario(
        doc,
        {
            "notario": notario,
            "colegiado": colegiado,
            "clave_notario": clave_notario,
        },
        nota_timbre="De conformidad con el Art. 5 num. 6 del Decreto 37-92, adherir Timbre Fiscal de Q. 0.50 en cada hoja del Índice.",
    )
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def generar_resumen_juridico_ejecutivo(reg: Dict) -> bytes:
    """Genera Dictamen / Hoja de Control Forense del expediente o escritura desde Bóveda."""
    doc = _crear_documento_carta_gt()

    p_tit = doc.add_paragraph()
    p_tit.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_tit.paragraph_format.space_after = Pt(12)
    rt = p_tit.add_run(
        "DICTAMEN Y HOJA DE CONTROL LEGAL / NOTARIAL — LEX IA 360\n"
        f"DOCUMENTO REF.: {str(reg.get('numero_expediente') or 'S/N').upper()}"
    )
    rt.bold = True
    rt.font.size = Pt(12)
    rt.font.color.rgb = _COLOR_PRIMARIO

    monto_val = float(reg.get("monto_litigio", 0.0) or 0.0)
    tn_val = float(reg.get("timbre_notarial", 0.0) or 0.0)
    tf_val = float(reg.get("timbre_fiscal", 0.0) or 0.0)

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
        ("Categoría Documental", str(reg.get("categoria_documental") or "N/A")),
        ("Órgano / Notario / Registro", str(reg.get("juzgado") or "N/A")),
        ("Materia / Tipo de Acto", f"{reg.get('materia', '')} — {reg.get('tipo_proceso', '')}"),
        ("Folio de Protocolo", str(reg.get("folio_protocolo") or "N/A")),
        ("Compareciente / Actor 1", p1),
        ("Compareciente / Demandado 2", p2),
        ("Cuantía / Monto Declarado", monto_a_letras(monto_val, "GTQ", incluir_cifra=True)),
        ("Timbre Notarial / Fiscal", f"Notarial: Q. {tn_val:,.2f} | Fiscal: Q. {tf_val:,.2f}"),
        ("Registro Destino y Plazo", f"{reg.get('registro_destino', 'N/A')} — Plazo: {reg.get('plazo_procesal', 'N/A')}"),
        ("Semáforo de Control", f"{reg.get('semaforo', '')} | Alerta: {reg.get('anomalia', 'Ninguna')}"),
    ]

    tabla = doc.add_table(rows=1 + len(filas), cols=2)
    tabla.rows[0].cells[0].text = "CAMPO AUDITADO"
    tabla.rows[0].cells[1].text = "DETERMINACIÓN LEGAL"
    for idx, (k, v) in enumerate(filas, start=1):
        tabla.rows[idx].cells[0].text = k
        tabla.rows[idx].cells[1].text = v
        tabla.rows[idx].cells[0].width = Inches(2.2)
        tabla.rows[idx].cells[1].width = Inches(4.2)
    _estilar_tabla(tabla)

    p_res = doc.add_paragraph()
    p_res.paragraph_format.space_before = Pt(12)
    r_h = p_res.add_run("RESUMEN JURÍDICO FORENSE:\n")
    r_h.bold = True
    r_h.font.color.rgb = _COLOR_PRIMARIO
    p_res.add_run(str(reg.get("resumen_forense") or "Sin observaciones adicionales registradas."))

    p_pie = doc.add_paragraph()
    p_pie.paragraph_format.space_before = Pt(14)
    r_pie = p_pie.add_run(f"Emitido el {fecha_a_letras()} — Sistema Lex IA 360 Guatemala.")
    r_pie.italic = True
    r_pie.font.size = Pt(9.5)
    r_pie.font.color.rgb = _COLOR_SUAVE

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
