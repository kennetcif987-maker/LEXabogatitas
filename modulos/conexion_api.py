import streamlit as st
from google import genai
from google.genai import types
import time
import os
import shutil
import uuid

try:
    import docx
except ImportError:
    docx = None

API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

def analizar_expediente(ruta_archivo):
    prompt = """
    Analiza este documento legal de Guatemala. Extrae los siguientes datos y responde ÚNICAMENTE con un objeto JSON plano.
    Si un dato no existe, pon "No detectado".

    REGLAS ESTRICTAS DE IDENTIFICACIÓN:
    - Demandante: Quien promueve la acción (Actor, Ejecutante, Requirente, Apelante, o Heredero).
    - Demandado: Contra quien se promueve (Ejecutado, Apelado). Si es un trámite notarial o de DICABI, el Demandado es "No aplica".
    - DPI: Busca secuencias de 13 dígitos.
    - NIT: Busca números con guion (ej. 123456-7 o 1234567-K).
    - Monto: Extrae solo la cantidad numérica del total en litigio, pensión o inventario (ej. 17361.53).

    ESTRUCTURA OBLIGATORIA:
    {
      "numero_expediente": "",
      "juzgado": "",
      "materia": "",
      "tipo_proceso": "",
      "demandante": "",
      "documento_identificacion_demandante": "",
      "nit_demandante": "",
      "demandado": "",
      "documento_identificacion_demandado": "",
      "nit_demandado": "",
      "monto_litigio": 0.00,
      "fecha_resolucion": "",
      "fecha_audiencia": "",
      "plazo_procesal": ""
    }
    """

    ext = os.path.splitext(ruta_archivo)[1].lower()
    archivo_seguro = f"temp_{uuid.uuid4().hex}"

    if ext == '.docx':
        if docx is None: return '{"error": "Falta la librería. Ejecuta: pip install python-docx"}'
        try:
            doc = docx.Document(ruta_archivo)
            textos = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip(): textos.append(cell.text.strip())
            archivo_seguro += ".txt"
            with open(archivo_seguro, "w", encoding="utf-8") as f: f.write("\n".join(textos))
        except Exception as e: return f'{{"error": "Error extrayendo DOCX: {e}"}}'
            
    elif ext == '.doc':
        return '{"error": "El formato .doc (1997-2003) es un binario cerrado. Ábrelo y guárdalo como .docx o PDF."}'
    else:
        archivo_seguro += ext
        shutil.copy(ruta_archivo, archivo_seguro)

    try:
        archivo_ia = client.files.upload(file=archivo_seguro)
        
        estado = str(archivo_ia.state).upper()
        while estado in ['PROCESSING', 'PENDING']:
            time.sleep(2)
            archivo_ia = client.files.get(name=archivo_ia.name)
            estado = str(archivo_ia.state).upper()
            
        if estado == 'FAILED': return '{"error": "Fallo visual en la nube."}'

        for intento in range(3):
            try:
                respuesta = client.models.generate_content(
                    model='gemini-3.1-flash-lite', 
                    contents=[archivo_ia, prompt],
                    config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.0)
                )
                client.files.delete(name=archivo_ia.name)
                return respuesta.text.strip()
            except Exception as e_api:
                if '429' in str(e_api) or 'RESOURCE_EXHAUSTED' in str(e_api):
                    if intento < 2:
                        time.sleep(30) 
                        continue
                raise e_api 
    except Exception as e: return f'{{"error": "Error interno: {str(e)}" }}'
    finally:
        if os.path.exists(archivo_seguro): os.remove(archivo_seguro)
