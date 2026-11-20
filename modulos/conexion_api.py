import streamlit as st
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional
import fitz # PyMuPDF
from PIL import Image
import io
import os
import time
import json
import re

# 1. Conexión con Google AI Studio
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

# 2. Esquema Estructurado Pydantic
class SujetoLegal(BaseModel):
    nombre_completo: str = Field(description="Nombre y apellidos del otorgante o compareciente")
    rol_en_acto: str = Field(description="Vendedor, Comprador, Mandante, Mandatario, Arrendador, Cónyuge, etc.")
    identificacion_dpi: Optional[str] = Field(default="No detectado", description="DPI de 13 dígitos si consta")
    nit: Optional[str] = Field(default="No detectado", description="Número de Identificación Tributaria")

class InstrumentoLegalSchema(BaseModel):
    categoria_documental: str = Field(description="'PROTOCOLO_NOTARIAL' o 'EXPEDIENTE_JUDICIAL'")
    numero_instrumento_o_caso: str = Field(description="Número de escritura pública o número de expediente/causa judicial")
    folio_protocolo: str = Field(default="N/A", description="Número de folio con sufijo A (Anverso) o R (Reverso) si es protocolo")
    fecha_documento: str = Field(description="Fecha exacta del documento o resolución")
    notario_o_juzgado: str = Field(description="Nombre del Notario autorizante o Juzgado/Tribunal competente")
    tipo_acto_o_juicio: str = Field(description="Tipo de contrato (Mandato, Compraventa, Capitulaciones, etc.) o juicio (Ejecutivo, Ordinario, etc.)")
    materia_derecho: str = Field(default="Civil", description="Notarial, Civil, Laboral, Familia, Penal, Mercantil")
    otorgantes_o_partes: List[SujetoLegal]
    monto_cuantia_o_precio: float = Field(default=0.00, description="Monto del contrato, cuantía en litigio o precio pactado")
    timbre_notarial_estimado: float = Field(default=0.00, description="Impuesto timbre notarial según arancel de Guatemala")
    timbre_fiscal_o_iva: float = Field(default=0.00, description="Impuesto fiscal aplicable (3% timbre o 12% IVA)")
    registro_destino: str = Field(default="Archivo General de Protocolos", description="RGP, AGP Registro de Poderes, RENAP, etc.")
    plazo_o_termino: str = Field(default="N/A", description="Plazo contractual o término procesal otorgado")
    semaforo_alerta: str = Field(default="🟢 TRÁMITE", description="🔴 URGENTE, 🟡 EN TÉRMINO o 🟢 TRÁMITE")
    resumen_ejecutivo: str = Field(description="Resumen conciso y sustancial de las cláusulas o resolución")
    alertas_forenses: str = Field(default="Ninguna", description="Anomalías, fojas faltantes o requisitos legales pendientes")

# 3. Compresión y optimización visual
def _preparar_partes_multimodales(ruta_archivo, max_paginas=6, max_dim=1600):
    ext = os.path.splitext(ruta_archivo)[1].lower()
    partes = []

    if ext == '.pdf':
        doc = fitz.open(ruta_archivo)
        total_pags = len(doc)
        indices = range(min(max_paginas, total_pags))
        
        for p_no in indices:
            page = doc[p_no]
            pix = page.get_pixmap(dpi=150)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            partes.append(types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg"))
        doc.close()
            
    elif ext in ['.png', '.jpg', '.jpeg']:
        img = Image.open(ruta_archivo)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=80)
        partes.append(types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg"))

    elif ext in ['.docx', '.txt']:
        texto = ""
        if ext == '.docx':
            try:
                import docx
                d = docx.Document(ruta_archivo)
                texto = "\n".join([p.text for p in d.paragraphs if p.text.strip()])
            except: pass
        else:
            with open(ruta_archivo, 'r', encoding='utf-8', errors='ignore') as f:
                texto = f.read()
        partes.append(types.Part.from_text(text=f"CONTENIDO TEXTUAL DEL EXPEDIENTE:\n{texto[:200000]}"))
    return partes

# 4. Función de análisis principal con Gemini 3.1 Flash
def analizar_expediente(ruta_archivo):
    """
    Analiza expedientes judiciales y escrituras matrices de protocolo notarial
    conforme a la legislación de Guatemala, devolviendo un JSON estructurado de alta precisión.
    """
    prompt = """
    ACTÚA COMO UN AUDITOR FORENSE Y NOTARIO SENIOR DE GUATEMALA (CÓDIGO DE NOTARIADO, DTO. 314 Y CÓDIGO PROCESAL CIVIL Y MERCANTIL).
    
    Analiza este documento escaneado (escritura pública de protocolo, índice notarial o resolución judicial).
    
    INSTRUCCIONES CRÍTICAS:
    1. Si es PROTOCOLO NOTARIAL:
       - Identifica el Número de Instrumento (escritura/acta).
       - Identifica el Número de Folio con sufijo 'A' (Anverso) o 'R' (Reverso) (ej: '1 A', '5 R', '16 R').
       - Extrae a todos los comparecientes (nombres exactos), su rol (Vendedor, Comprador, Mandante, Mandatario, Cónyuge, etc.) y su DPI (13 dígitos) o NIT.
       - Determina el negocio jurídico exacto (Mandato, Compraventa, Promesa, Capitulaciones, Arrendamiento, Construcción de Obra, Protocolización de Matrimonio, Toma de Razón, etc.).
       - Calcula el precio/cuantía e impuestos aplicables en Guatemala (IVA 12%, Timbres Fiscales 3%, Timbre Notarial 2 por millar máx Q300, Timbre Notarial fijo Q10 para mandatos).
       - Indica el registro de destino (Registro de la Propiedad, Archivo General de Protocolos Poderes, RENAP).
       
    2. Si es EXPEDIENTE JUDICIAL:
       - Identifica Número de Expediente/Causa (NUE) y Juzgado/Tribunal.
       - Extrae Actor/Demandante y Demandado con sus documentos de identificación.
       - Extrae la cuantía en litigio, fecha de resolución/audiencia y el plazo procesal.
       - Asigna el Semáforo: '🔴 URGENTE' si el plazo vence en 24h, 48h o 3 días; '🟡 EN TÉRMINO' para plazos ordinarios; '🟢 TRÁMITE' para diligencias sin apercibimiento.
    
    Responde ÚNICAMENTE conforme al esquema estructurado obligatorio.
    """

    try:
        partes = _preparar_partes_multimodales(ruta_archivo)
        if not partes:
            return '{"error": "No se pudo extraer contenido visual ni textual del archivo."}'
            
        partes.append(types.Part.from_text(text=prompt))

        # Modelos prioritarios de Gemini Flash disponibles
        modelos_a_probar = [
            'gemini-3.1-flash-lite',
            'gemini-3.1-flash-lite-preview',
            'gemini-3.5-flash-lite',
            'gemini-2.5-flash-lite',
            'gemini-2.5-flash',
        ]
        
        for modelo in modelos_a_probar:
            for intento in range(2):
                try:
                    response = client.models.generate_content(
                        model=modelo,
                        contents=partes,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=InstrumentoLegalSchema,
                            temperature=0.0
                        )
                    )
                    if response.text and response.text.strip():
                        return response.text.strip()
                except Exception as e_gen:
                    err_msg = str(e_gen)
                    if "429" in err_msg or "503" in err_msg or "UNAVAILABLE" in err_msg:
                        time.sleep(2)
                        continue
                    break # probar siguiente modelo si el error no es de saturación

        return '{"error": "La API de Gemini está experimentando alta demanda en este momento. Reintente en un momento."}'

    except Exception as e:
        return f'{{"error": "Fallo de procesamiento: {str(e)}"}}'