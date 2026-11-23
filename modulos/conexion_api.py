import json
import os
import re
import time
from typing import List, Literal, Optional

import fitz
import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

MODEL_ID = "gemini-3.1-flash-lite"
MODEL_FALLBACKS = (
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-flash-latest",
    "gemini-3-flash-preview",
)


def _obtener_api_key() -> str:
    try:
        if "GEMINI_API_KEY" in st.secrets and str(st.secrets["GEMINI_API_KEY"]).strip():
            return str(st.secrets["GEMINI_API_KEY"]).strip()
    except Exception:
        pass
    return os.environ.get("GEMINI_API_KEY", "").strip()


def _obtener_cliente() -> genai.Client:
    api_key = _obtener_api_key()
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY no configurada. Agréguela en .streamlit/secrets.toml o Secrets de Streamlit Cloud."
        )
    return genai.Client(api_key=api_key)


class OtorganteOParte(BaseModel):
    nombre_completo: str = Field(description="Nombre completo del otorgante, vendedor, comprador, demandante o demandado")
    rol_en_acto: str = Field(description="Ej: Vendedor, Comprador, Mandante, Mandatario, Actor, Demandado, Testador")
    identificacion_dpi: str = Field(
        description="Número de DPI/CUI de 13 dígitos en dígitos (ej: 2456 78901 0101). "
        "Si en la escritura aparece escrito en letras ('dos mil... cero ciento uno'), transcríbelo a sus 13 dígitos exactos."
    )
    nit: str = Field(description="NIT si consta o C/F o No detectado")


class InstrumentoLegalSchema(BaseModel):
    categoria_documental: Literal[
        "PROTOCOLO_NOTARIAL", "EXPEDIENTE_JUDICIAL", "ACTA_O_CONTRATO", "CEDULA_NOTIFICACION"
    ]
    numero_instrumento_o_caso: str = Field(
        description="Número de escritura pública (si venía en letras convertir a dígitos, ej. 'ciento veinticinco' -> '125') o número de expediente judicial"
    )
    folio_protocolo: str = Field(
        description="Número de folio y cara (ej: 145 Anverso, o N/A si es memorial judicial)"
    )
    fecha_documento: str = Field(description="Fecha del instrumento o resolución en formato DD/MM/AAAA")
    notario_o_juzgado: str = Field(description="Nombre del Notario autorizante o Juzgado/Tribunal competente")
    tipo_acto_o_juicio: str = Field(
        description="Ej: Compraventa de Bien Inmueble, Mandato General, Juicio Ejecutivo, Pensión Alimenticia"
    )
    materia_derecho: Literal[
        "Notarial", "Civil", "Familia", "Penal", "Laboral", "Mercantil", "Administrativo", "Constitucional"
    ]
    otorgantes_o_partes: List[OtorganteOParte]
    datos_registrales_e_inmueble: str = Field(
        description="Si aplica: Finca, Folio, Libro, Departamento, Matrícula Fiscal y Dirección del inmueble; de lo contrario N/A"
    )
    monto_cuantia_o_precio: float = Field(description="Precio, cuantía o pensión en Quetzales (solo número)")
    timbre_notarial_estimado: float = Field(
        description="Impuesto de timbre notarial estimado (2 por millar mínimo Q1 máx Q300 o Q10 valor indeterminado)"
    )
    timbre_fiscal_o_iva: float = Field(
        description="Impuesto fiscal (3% segunda venta, 12% IVA primera venta, Q10 mandato general) o Q0 si no aplica"
    )
    registro_destino: str = Field(
        description="Ej: Archivo General de Protocolos, Registro de la Propiedad, DICABI, RENAP, Juzgado"
    )
    plazo_o_termino: str = Field(
        description="Ej: 15 días hábiles aviso DICABI, 25 días hábiles Testimonio Especial AGP, 5 días audiencia"
    )
    semaforo_alerta: str = Field(description="'🔴 URGENTE', '🟡 PRECAUCIÓN', o '🟢 TRÁMITE'")
    alertas_forenses: str = Field(
        description="Anomalías detectadas (ej: diferencia entre monto en letras y cifras, DPI incompleto, timbre faltante, plazo por vencer) o 'ninguna'"
    )
    resumen_ejecutivo: str = Field(
        description="Resumen jurídico estructurado y directo de las obligaciones, partes, bienes y pasos siguientes"
    )


_PROMPT_GUATEMALA = """
Eres un Abogado, Notario Público y Auditor Jurídico Experto en Legislación de Guatemala
(Código de Notariado Decreto 314, Código Civil, CPCyM, Ley del Timbre Forense y Notarial Dto. 82-96,
Ley del Timbre Fiscal Dto. 37-92).

REGLAS CRÍTICAS DE EXTRACCIÓN FORENSE:
1. CUI / DPI EN LETRAS (Art. 13 y 29 Dto. 314): En escrituras públicas y actas guatemaltecas, los DPI de 13 dígitos
   suelen estar redactados en palabras en 3 bloques (4-5-4 dígitos), por ejemplo:
   "dos mil cuatrocientos cincuenta y seis, espacio, setenta y ocho mil novecientos uno, espacio, cero ciento uno" -> "2456789010101".
   Tradúcelo SIEMPRE con precisión matemática a sus 13 dígitos en `identificacion_dpi` (poniendo el cero inicial de cada bloque cuando diga "cero ...").
2. NÚMEROS Y MONTOS EN LETRAS: Convierte el número de escritura pública (ej. "NÚMERO CUARENTA Y OCHO") a su valor numérico ("48") y la cuantía pactada en letras a número exacto en `monto_cuantia_o_precio`. Si notas discordancia entre letras y números, repórtala en `alertas_forenses`.
3. DATOS REGISTRALES: Extrae Finca, Folio, Libro, Departamento y Dirección si se trata de inmueble.
4. VALIDACIÓN DE TIMBRES Y PLAZOS EN GUATEMALA:
   - Aviso a DICABI/Catastro Municipal (compraventas de inmuebles): 15 días hábiles (Art. 38 CDN).
   - Testimonio Especial al Archivo General de Protocolos: 25 días hábiles (Art. 37 lit. a CDN); Timbre Notarial 2‰ (mín Q1.00, máx Q300.00; o Q10.00 valor indeterminado) + Timbre Fiscal Q0.50 por hoja.
   - Aviso de Matrimonio Civil a RENAP: 15 días hábiles (Art. 102 Código Civil).
   - Memoriales Judiciales: Timbre Forense Q1.00 por hoja (Dto. 82-96).
5. Clasifica con precisión `categoria_documental` y emite `semaforo_alerta`.
"""


def _extraer_texto_documento(ruta_archivo: str) -> Optional[str]:
    """Extrae texto nativo de PDF digital, Word (.docx) o TXT evitando tokens de visión."""
    ext = os.path.splitext(ruta_archivo)[1].lower()
    if ext == ".txt":
        try:
            with open(ruta_archivo, "r", encoding="utf-8", errors="ignore") as f:
                txt = f.read().strip()
            return txt[:120000] if txt else None
        except Exception:
            return None

    if ext == ".docx":
        try:
            import docx as _docx

            d = _docx.Document(ruta_archivo)
            partes = [p.text.strip() for p in d.paragraphs if p.text and p.text.strip()]
            for t in d.tables:
                for row in t.rows:
                    vals = [c.text.strip() for c in row.cells if c.text and c.text.strip()]
                    if vals:
                        partes.append(" | ".join(vals))
            txt = "\n".join(partes).strip()
            return txt[:120000] if txt else None
        except Exception:
            return None

    if ext != ".pdf":
        return None

    doc = fitz.open(ruta_archivo)
    try:
        bloques = []
        for idx, page in enumerate(doc):
            txt = (page.get_text("text") or "").strip()
            if txt:
                bloques.append(f"--- PÁGINA {idx + 1} ---\n{txt}")
        completo = "\n\n".join(bloques).strip()
        if len(completo) >= 250 and len(re.findall(r"[A-Za-zÁÉÍÓÚáéíóúÑñ0-9]", completo)) >= 120:
            return completo[:120000]
        return None
    finally:
        doc.close()


def _preparar_partes_multimodales(ruta_archivo: str, max_paginas: int = 10) -> List[types.Part]:
    """Convierte PDF escaneado o imagen a Partes para Gemini Vision (150 DPI para conservar legibilidad de sellos/folios)."""
    ext = os.path.splitext(ruta_archivo)[1].lower()
    partes: List[types.Part] = []

    if ext == ".pdf":
        doc = fitz.open(ruta_archivo)
        try:
            total_paginas = min(len(doc), max_paginas)
            for idx in range(total_paginas):
                pix = doc.load_page(idx).get_pixmap(dpi=150)
                partes.append(types.Part.from_bytes(data=pix.tobytes("png"), mime_type="image/png"))
        finally:
            doc.close()
        return partes

    mime_map = {
        ".png": "image/png",
        ".webp": "image/webp",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }
    mime_type = mime_map.get(ext, "image/jpeg")
    with open(ruta_archivo, "rb") as f:
        partes.append(types.Part.from_bytes(data=f.read(), mime_type=mime_type))
    return partes


def analizar_expediente(ruta_archivo: str) -> str:
    """
    Analiza un documento legal/notarial de Guatemala mediante extracción híbrida:
    1) Texto digital nativo en PDF (más rápido, completo y económico).
    2) Gemini Vision a 150 DPI para escaneos y fotografías.
    """
    if not os.path.exists(ruta_archivo):
        return json.dumps({"error": "Archivo no encontrado en ruta temporal"})

    ext = os.path.splitext(ruta_archivo)[1].lower()
    try:
        cliente = _obtener_cliente()
        contenidos: List[object] = []

        texto_doc = _extraer_texto_documento(ruta_archivo)
        if texto_doc:
            contenidos.append(f"{_PROMPT_GUATEMALA}\n\nTEXTO ÍNTEGRO DEL DOCUMENTO:\n{texto_doc}")
        else:
            partes_img = _preparar_partes_multimodales(ruta_archivo, max_paginas=10)
            if not partes_img:
                return json.dumps({"error": "No se pudieron renderizar páginas válidas del archivo."})
            contenidos = [_PROMPT_GUATEMALA] + partes_img

        ultimo_error = "Sin respuesta de Gemini"
        for modelo in MODEL_FALLBACKS:
            for _ in range(2):
                try:
                    response = cliente.models.generate_content(
                        model=modelo,
                        contents=contenidos,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=InstrumentoLegalSchema,
                            temperature=0.05,
                        ),
                    )
                    if response.text and response.text.strip():
                        return response.text
                except Exception as e_mod:
                    ultimo_error = str(e_mod)
                    if any(code in ultimo_error for code in ("429", "503", "UNAVAILABLE")):
                        time.sleep(2)
                        continue
                    break
        return json.dumps({"error": f"Fallo en procesamiento Gemini: {ultimo_error}"})
    except Exception as e:
        return json.dumps({"error": f"Fallo en procesamiento Gemini: {str(e)}"})
