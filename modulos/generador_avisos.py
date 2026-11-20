import io
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

def generar_aviso_dicabi(datos: dict) -> bytes:
    """
    Genera el Aviso Notarial de Traspaso para DICABI y Catastro Municipal
    conforme al Art. 38 del Código de Notariado y Ley del IUSI.
    """
    doc = docx.Document()
    for s in doc.sections:
        s.top_margin = Inches(1)
        s.bottom_margin = Inches(1)
        s.left_margin = Inches(1)
        s.right_margin = Inches(1)

    p_head = doc.add_paragraph()
    r = p_head.add_run("SEÑOR DIRECTOR DE LA DIRECCIÓN DE CATASTRO Y AVALÚO DE BIENES INMUEBLES (DICABI)\nMINISTERIO DE FINANZAS PÚBLICAS, CIUDAD DE GUATEMALA.")
    r.bold = True
    r.font.name = "Calibri"
    r.font.size = Pt(11)
    p_head.alignment = WD_ALIGN_PARAGRAPH.LEFT

    p_body = doc.add_paragraph()
    notario = datos.get('notario', 'Ashly Brigeth Rodas Estrada')
    p_body.add_run(
        f"\nYo, {notario}, Notaria en ejercicio, con oficina profesional ubicada en la ciudad de Guatemala, "
        f"en cumplimiento de lo preceptuado en el artículo treinta y ocho (38) del Código de Notariado y legislación tributaria vigente, "
        f"a usted atentamente expongo que autoricé el siguiente instrumento público traslativo de dominio:\n"
    )
    
    items = [
        f"1. NÚMERO DE ESCRITURA PÚBLICA: {datos.get('numero_instrumento', '___')}",
        f"2. FECHA DE AUTORIZACIÓN: {datos.get('fecha', '___')}",
        f"3. NATURALEZA DEL ACTO O CONTRATO: {datos.get('tipo_contrato', 'Compraventa de Bien Inmueble')}",
        f"4. ENAJENANTE (VENDEDOR): {datos.get('vendedor', '___')} (NIT: {datos.get('nit_vendedor', 'No consignado')})",
        f"5. ADQUIRENTE (COMPRADOR): {datos.get('comprador', '___')} (NIT: {datos.get('nit_comprador', 'No consignado')})",
        f"6. PRECIO O CUANTÍA PACTADA: Q. {float(datos.get('monto', 0.0)):,.2f}",
        f"7. IDENTIFICACIÓN REGISTRAL: Finca número {datos.get('finca', '____')}, Folio {datos.get('folio', '____')}, del Libro {datos.get('libro', '____')} de Guatemala.",
        f"8. MATRÍCULA FISCAL: {datos.get('matricula_fiscal', 'En trámite de asignación')}."
    ]
    for it in items:
        p_it = doc.add_paragraph()
        r_it = p_it.add_run(it)
        r_it.font.name = "Calibri"
        r_it.font.size = Pt(10.5)

    p_close = doc.add_paragraph()
    p_close.add_run(
        "\nPara los efectos legales de actualización de matrícula y avalúo fiscal, remito el presente aviso dentro del término legal de quince días.\n\n"
        "Guatemala, _____ de ____________________ del año 2024.\n\n\n\n"
        "____________________________________________\n"
        f"Licda. {notario}\nAbogada y Notaria - Colegiada Activa"
    )
    p_close.alignment = WD_ALIGN_PARAGRAPH.CENTER

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def generar_aviso_agp_testimonio(datos: dict) -> bytes:
    """
    Genera el Aviso de Entrega de Testimonio Especial al Archivo General de Protocolos (AGP)
    (Art. 37 literal 'a' del Código de Notariado).
    """
    doc = docx.Document()
    for s in doc.sections:
        s.top_margin = Inches(1)
        s.bottom_margin = Inches(1)
        s.left_margin = Inches(1)
        s.right_margin = Inches(1)

    p_head = doc.add_paragraph()
    r = p_head.add_run("SEÑOR DIRECTOR DEL ARCHIVO GENERAL DE PROTOCOLOS\nORGANISMO JUDICIAL DE GUATEMALA.")
    r.bold = True
    r.font.name = "Calibri"
    r.font.size = Pt(11)

    p_body = doc.add_paragraph()
    notario = datos.get('notario', 'Ashly Brigeth Rodas Estrada')
    p_body.add_run(
        f"\nAtentamente comparezco a remitir a usted el TESTIMONIO ESPECIAL del instrumento público autorizado en mi protocolo notarial, "
        f"en cumplimiento estricto del artículo treinta y siete (37) literal a) del Código de Notariado, conforme al siguiente detalle:\n"
    )

    items = [
        f"• INSTRUMENTO PÚBLICO NÚMERO: {datos.get('numero_instrumento', '___')}",
        f"• FECHA DE AUTORIZACIÓN: {datos.get('fecha', '___')}",
        f"• OBJETO O CONTRATO: {datos.get('tipo_contrato', '___')}",
        f"• COMPARECIENTES / OTORGANTES: {datos.get('otorgantes', '___')}",
        f"• FOLIOS DE PROTOCOLO: Del folio {datos.get('folio_inicial', '___')} al folio {datos.get('folio_final', '___')}",
        f"• LIQUIDACIÓN DE TIMBRE NOTARIAL: Adherido en timbres notariales la cantidad de Q. {float(datos.get('timbre_notarial', 10.0)):,.2f} (conforme arancel Dto. 82-96).",
        f"• TIMBRE FISCAL POR RAZÓN: Adherido timbre fiscal de Q.0.50 en la razón final del testimonio."
    ]
    for it in items:
        p_it = doc.add_paragraph()
        r_it = p_it.add_run(it)
        r_it.font.name = "Calibri"
        r_it.font.size = Pt(10.5)

    p_close = doc.add_paragraph()
    p_close.add_run(
        "\nSe acompaña el testimonio extendido en hojas de papel bond legalmente confrontadas y selladas.\n\n"
        "Guatemala, _____ de ____________________ del año 2024.\n\n\n\n"
        "____________________________________________\n"
        f"Licda. {notario}\nAbogada y Notaria - Colegiada Activa"
    )
    p_close.alignment = WD_ALIGN_PARAGRAPH.CENTER

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def generar_aviso_trimestral_agp(datos: dict) -> bytes:
    """
    Genera el Aviso Notarial Trimestral obligatorio (Art. 37 literal 'c' Código de Notariado).
    """
    doc = docx.Document()
    for s in doc.sections:
        s.top_margin = Inches(1)
        s.bottom_margin = Inches(1)
        s.left_margin = Inches(1)
        s.right_margin = Inches(1)

    p_head = doc.add_paragraph()
    r = p_head.add_run("SEÑOR DIRECTOR DEL ARCHIVO GENERAL DE PROTOCOLOS\nORGANISMO JUDICIAL DE GUATEMALA.")
    r.bold = True
    r.font.name = "Calibri"
    r.font.size = Pt(11)

    trimestre = datos.get('trimestre', 'Primer Trimestre')
    ano = datos.get('ano', '2024')
    notario = datos.get('notario', 'Ashly Brigeth Rodas Estrada')

    p_body = doc.add_paragraph()
    p_body.add_run(
        f"\nEn cumplimiento del artículo 37 literal c) del Código de Notariado, me dirijo a usted con el objeto de presentar "
        f"el AVISO TRIMESTRAL correspondiente al {trimestre.upper()} DEL AÑO {ano}, informándole sobre los instrumentos autorizados "
        f"en mi protocolo notarial:\n"
    )

    items = [
        f"1. PRIMER INSTRUMENTO AUTORIZADO EN EL TRIMESTRE: Número {datos.get('primer_num', '1')}, de fecha {datos.get('primera_fecha', '10 de enero de 2024')}.",
        f"2. ÚLTIMO INSTRUMENTO AUTORIZADO EN EL TRIMESTRE: Número {datos.get('ultimo_num', '8')}, de fecha {datos.get('ultima_fecha', '03 de mayo de 2024')}.",
        f"3. NÚMERO TOTAL DE INSTRUMENTOS AUTORIZADOS: {datos.get('total_autorizados', '8')}.",
        f"4. NÚMERO DE INSTRUMENTOS CANCELADOS: {datos.get('total_cancelados', '0')}.",
        f"5. TESTIMONIOS ESPECIALES: Todos remitidos oportunamente con sus timbres notariales de ley."
    ]
    for it in items:
        p_it = doc.add_paragraph()
        r_it = p_it.add_run(it)
        r_it.font.name = "Calibri"
        r_it.font.size = Pt(10.5)

    p_close = doc.add_paragraph()
    p_close.add_run(
        "\nAtentamente,\n\n\n\n"
        "____________________________________________\n"
        f"Licda. {notario}\nAbogada y Notaria - Colegiada Activa"
    )
    p_close.alignment = WD_ALIGN_PARAGRAPH.CENTER

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def generar_resumen_juridico_ejecutivo(datos: dict) -> bytes:
    """
    Genera un dictamen y ficha ejecutiva del caso o escritura en Word (.docx)
    para entregar directamente al cliente o socio del bufete.
    """
    doc = docx.Document()
    for s in doc.sections:
        s.top_margin = Inches(0.9)
        s.bottom_margin = Inches(0.9)
        s.left_margin = Inches(0.9)
        s.right_margin = Inches(0.9)

    p_head = doc.add_paragraph()
    r = p_head.add_run("FICHA EJECUTIVA Y DICTAMEN DE AUDITORÍA LEGAL")
    r.bold = True
    r.font.name = "Calibri"
    r.font.size = Pt(15)
    r.font.color.rgb = RGBColor(74, 14, 78)
    p_head.alignment = WD_ALIGN_PARAGRAPH.CENTER

    p_sub = doc.add_paragraph()
    r_sub = p_sub.add_run(f"Expediente / Instrumento: {datos.get('numero_expediente', 'N/A')} | Categoría: {datos.get('categoria_documental', 'LEGAL')}")
    r_sub.font.name = "Calibri"
    r_sub.font.size = Pt(10)
    r_sub.font.color.rgb = RGBColor(100, 116, 139)
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph("―" * 50)

    p_sec1 = doc.add_heading("1. Resumen Ejecutivo del Negocio / Asunto", level=2)
    texto_res = str(datos.get('resumen_forense') or 'No disponible')
    p_res = doc.add_paragraph()
    r_res = p_res.add_run(texto_res)
    r_res.font.name = "Calibri"
    r_res.font.size = Pt(10)

    doc.add_heading("2. Sujetos Procesales e Identificación", level=2)
    p_suj = doc.add_paragraph(
        f"• Sujeto 1 / Parte Promoviente: {datos.get('demandante', 'N/A')} (DPI: {datos.get('dpi_demandante', 'No registrado')})\n"
        f"• Sujeto 2 / Contraparte / Adquirente: {datos.get('demandado', 'N/A')} (DPI: {datos.get('dpi_demandado', 'No registrado')})"
    )

    doc.add_heading("3. Régimen Fiscal y Registral", level=2)
    p_fisc = doc.add_paragraph(
        f"• Cuantía / Precio: Q. {float(datos.get('monto_litigio', 0.0)):,.2f}\n"
        f"• Timbre Notarial Obligatorio: Q. {float(datos.get('timbre_notarial', 0.0)):,.2f}\n"
        f"• Timbre Fiscal / IVA: Q. {float(datos.get('timbre_fiscal', 0.0)):,.2f}\n"
        f"• Registro de Destino: {datos.get('registro_destino', 'Archivo General de Protocolos')}\n"
        f"• Folio en Protocolo: {datos.get('folio_protocolo', 'N/A')}"
    )

    doc.add_heading("4. Alertas y Recomendación Notarial", level=2)
    alerta = datos.get('anomalia', 'Ninguna')
    p_ale = doc.add_paragraph(f"Auditoría preventiva: {alerta}\nSemáforo procesal: {datos.get('semaforo', '🟢 TRÁMITE')}")

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
