import streamlit as st
import pandas as pd
import json
import os
import time
import re
import fitz  
from modulos.conexion_api import analizar_expediente
from modulos.base_datos import (
    inicializar_db, guardar_expedientes, obtener_historial, autenticar_usuario,
    actualizar_password, registrar_usuario, obtener_usuarios_empresa, eliminar_usuario
)

st.set_page_config(page_title="Lex IA 360 - Centro de Mando", page_icon="⚖️", layout="wide")
inicializar_db()

# --- ESTADO DE SESIÓN ---
if 'auth' not in st.session_state: st.session_state['auth'] = False
if 'user' not in st.session_state: st.session_state['user'] = None
if 'data' not in st.session_state: st.session_state['data'] = []
if 'analisis_completado' not in st.session_state: st.session_state['analisis_completado'] = False
if 'uploader_key' not in st.session_state: st.session_state['uploader_key'] = 0
if 'all_raw_responses' not in st.session_state: st.session_state['all_raw_responses'] = {}

# --- MOTORES DE EXTRACCIÓN FÍSICA ---
def extraer_texto_fisico_local(ruta_archivo):
    texto = ""
    ext = os.path.splitext(ruta_archivo)[1].lower()
    try:
        if ext == '.pdf':
            doc = fitz.open(ruta_archivo)
            for page in doc: texto += page.get_text("text") + " "
        elif ext == '.docx':
            import docx
            doc = docx.Document(ruta_archivo)
            for p in doc.paragraphs: texto += p.text + " "
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells: texto += cell.text + " "
    except: pass
    return texto.replace('\n', ' ')

def _aplanar_json(obj, resultado=None, prefijo=''):
    if resultado is None: resultado = {}
    if isinstance(obj, dict):
        for k, v in obj.items(): _aplanar_json(v, resultado, prefijo + k.lower() + '_')
    elif isinstance(obj, list):
        for i, item in enumerate(obj): _aplanar_json(item, resultado, prefijo + str(i) + '_')
    else: resultado[prefijo[:-1]] = obj
    return resultado

def _mapear_datos(parsed_flat, data):
    for k_flat, v in parsed_flat.items():
        val = str(v).strip()
        if val.lower() in ["", "null", "none", "n/a", "no detectado", "desconocido", "0", "0.0"]: continue
        k = k_flat.lower()
        
        if any(x in k for x in ['expediente', 'causa', 'nue']): data['numero_expediente'] = val
        elif any(x in k for x in ['juzgado', 'tribunal', 'notario', 'sala', 'dicabi']): data['juzgado'] = val
        elif any(x in k for x in ['materia', 'rama']): data['materia'] = val
        elif any(x in k for x in ['proceso', 'juicio', 'tipo']): data['tipo_proceso'] = val
        elif 'monto' in k or 'litigio' in k or 'cuantia' in k or 'liquido' in k:
            try: data['monto_litigio'] = float(re.sub(r'[^\d.]', '', val))
            except: pass
        
        elif ('demandante' in k or 'actor' in k or 'ejecutante' in k or 'requirente' in k) and 'identificacion' not in k and 'dpi' not in k and 'nit' not in k and 'tipo' not in k:
            if data['demandante'] in ["No detectado", "Desconocido"]: data['demandante'] = val
        elif ('demandado' in k or 'ejecutado' in k or 'procesado' in k or 'apelado' in k) and 'identificacion' not in k and 'dpi' not in k and 'nit' not in k and 'tipo' not in k:
            if data['demandado'] in ["No detectado", "Desconocido"]: data['demandado'] = val
            
        elif ('identificacion' in k or 'dpi' in k) and ('demandante' in k or 'actor' in k or 'requirente' in k): data['documento_identificacion_demandante'] = val
        elif ('identificacion' in k or 'dpi' in k) and ('demandado' in k or 'ejecutado' in k): data['documento_identificacion_demandado'] = val
        elif 'nit' in k and ('demandante' in k or 'actor' in k): data['nit_demandante'] = val
        elif 'nit' in k and ('demandado' in k or 'ejecutado' in k): data['nit_demandado'] = val
            
        elif 'resolucion' in k or 'sentencia' in k: data['fecha_resolucion'] = val
        elif 'audiencia' in k: data['fecha_audiencia'] = val
        elif 'plazo' in k or 'termino' in k: data['plazo_procesal'] = val
    return data

def rescatar_datos_por_regex(texto_real, data):
    dpis_encontrados = re.findall(r'\b\d{4}[-\s]?\d{5}[-\s]?\d{4}\b', texto_real)
    dpis_unicos = list(dict.fromkeys(dpis_encontrados)) 
    
    if data['documento_identificacion_demandante'] == "No detectado" and len(dpis_unicos) > 0: data['documento_identificacion_demandante'] = dpis_unicos[0]
    if data['documento_identificacion_demandado'] == "No detectado" and len(dpis_unicos) > 1: data['documento_identificacion_demandado'] = dpis_unicos[1]

    if data['numero_expediente'] == "No detectado":
        exp_match = re.search(r'\b\d{4,5}[-\s]?\d{4}[-\s]?\d{4,5}\b', texto_real)
        if exp_match: data['numero_expediente'] = exp_match.group(0)

    if data['nit_demandante'] == "No detectado" or data['nit_demandado'] == "No detectado":
        nits = re.findall(r'\b[1-9]\d{2,7}[-\s]?[0-9Kk]\b', texto_real)
        nits_unicos = list(dict.fromkeys(nits))
        if data['nit_demandante'] == "No detectado" and len(nits_unicos) > 0: data['nit_demandante'] = nits_unicos[0]
        if data['nit_demandado'] == "No detectado" and len(nits_unicos) > 1: data['nit_demandado'] = nits_unicos[1]
    return data

def _calcular_semaforo(p, f):
    p, f = str(p).lower(), str(f).lower()
    if p in ['n/a', 'no detectado'] and f in ['n/a', 'no detectado']: return '🟢 TRÁMITE'
    if any(x in p for x in ['24', '48', '3 dia', '3 día', '2 dia', '2 día', 'inmediato', 'urgente']): return '🔴 URGENTE'
    return '🟡 EN TÉRMINO'

def formato_sujeto(nombre, identificacion):
    nom = str(nombre).strip()
    _id = str(identificacion).strip()
    if nom in ["No detectado", "Desconocido"]: return "Desconocido"
    if _id == "No detectado": return nom
    return f"{nom} (ID: {_id})"

def formato_plazos(res, plazo):
    res, plazo = str(res).strip(), str(plazo).strip()
    if res in ["N/A", "No detectado"] and plazo in ["N/A", "No detectado"]: return "Sin plazos activos"
    if res in ["N/A", "No detectado"]: return f"Plazo: {plazo}"
    if plazo in ["N/A", "No detectado"]: return f"Resolución: {res}"
    return f"Resolución: {res} | Plazo: {plazo}"

# --- PLATAFORMA ---
def login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.write("\n\n\n")
        st.markdown("<h1 style='text-align:center;color:#1a365d;'>⚖️ Lex IA 360</h1>", unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("👤 Usuario Corporativo")
            p = st.text_input("🔑 Contraseña", type="password")
            if st.form_submit_button("Ingresar", width="stretch"):
                res = autenticar_usuario(u.strip(), p)
                if res:
                    st.session_state.update({'auth': True, 'user': res})
                    st.rerun()
                else: 
                    st.warning("Credenciales inválidas. Verifique con administración.")

def main():
    user = st.session_state['user']
    bufete, abogado_activo, es_admin = user['empresa'], user['usuario'], user['rol'] == 'Administrador'

    with st.sidebar:
        st.markdown(f"### 🏛️ {bufete}")
        st.caption(f"Sesión: **{abogado_activo}**")
        if st.button("🗑️ Limpiar Mesa", width="stretch"):
            st.session_state['uploader_key'] += 1
            st.session_state.update({'data': [], 'analisis_completado': False, 'all_raw_responses': {}})
            st.rerun()
        if st.button("🚪 Salir", width="stretch"):
            st.session_state.update({'auth': False, 'user': None})
            st.rerun()

    st.title(f"Centro de Operaciones — {bufete}")
    tabs = st.tabs(["📑 Extracción Forense", "🗄️ Bóveda Legal", "⚙️ Admin"] if es_admin else ["📑 Extracción", "🗄️ Bóveda"])

    with tabs[0]:
        uploaded_files = st.file_uploader("Arrastre expedientes", accept_multiple_files=True, type=['pdf','png','jpg','docx', 'doc'])

        if uploaded_files and not st.session_state['analisis_completado']:
            if st.button("🚀 Iniciar Extracción Segura", type="primary", width="stretch"):
                res_temp, all_raw, errores_detectados = [], {}, False
                bar, status = st.progress(0), st.empty()

                for i, file in enumerate(uploaded_files):
                    status.text(f"Auditando: {file.name}...")
                    temp_path = f"temp_{file.name}"
                    
                    with open(temp_path, "wb") as tmp: tmp.write(file.getbuffer())

                    texto_real_documento = extraer_texto_fisico_local(temp_path)
                    raw_response = analizar_expediente(temp_path)
                    all_raw[file.name] = raw_response

                    data = {
                        "archivo_origen": file.name, "numero_expediente": "No detectado", "juzgado": "No detectado",
                        "materia": "No detectada", "tipo_proceso": "No detectado", 
                        "demandante": "Desconocido", "documento_identificacion_demandante": "No detectado", "nit_demandante": "No detectado",
                        "demandado": "Desconocido", "documento_identificacion_demandado": "No detectado", "nit_demandado": "No detectado",
                        "monto_litigio": 0.0, "fecha_resolucion": "N/A", "fecha_audiencia": "N/A", "plazo_procesal": "N/A",
                        "semaforo": "🟢 TRÁMITE", "anomalia": "ninguna"
                    }

                    if '"error"' in str(raw_response).lower():
                        st.info(f"⚠️ Nota sobre '{file.name}': Se omitieron algunos datos por legibilidad del archivo original.")
                        errores_detectados = True
                    else:
                        try:
                            match = re.search(r'\{.*\}', str(raw_response), re.DOTALL)
                            if match:
                                json_str = re.sub(r',\s*([}\]])', r'\1', match.group(0))
                                parsed = json.loads(json_str)
                                parsed_flat = _aplanar_json(parsed)
                                data = _mapear_datos(parsed_flat, data)
                        except: pass
                        
                        data = rescatar_datos_por_regex(texto_real_documento, data)

                    if data['documento_identificacion_demandante'] == data['documento_identificacion_demandado'] and data['documento_identificacion_demandante'] != "No detectado":
                        data['documento_identificacion_demandado'] = "No detectado"
                    if data['nit_demandante'] == data['nit_demandado'] and data['nit_demandante'] != "No detectado":
                        data['nit_demandado'] = "No detectado"

                    data['semaforo'] = _calcular_semaforo(data['plazo_procesal'], data['fecha_audiencia'])
                    res_temp.append(data)
                    
                    if os.path.exists(temp_path): os.remove(temp_path)
                    bar.progress((i + 1) / len(uploaded_files))
                    
                    if i < len(uploaded_files) - 1:
                        status.text("Procesando expediente seguro...")
                        time.sleep(4)

                status.empty()

                # --- CORRECCIÓN FORENSE: DETECCIÓN DE DUPLICADOS PURA ---
                if res_temp:
                    df_check = pd.DataFrame(res_temp)
                    # Elimina espacios, guiones, tabs, y convierte a minúsculas para comparar la esencia alfanumérica
                    df_check['exp_limpio'] = df_check['numero_expediente'].astype(str).apply(lambda x: re.sub(r'[^a-z0-9]', '', x.lower()))
                    
                    dups = df_check.duplicated(subset=['exp_limpio'], keep=False)
                    for idx, is_dup in enumerate(dups):
                        if is_dup and df_check.iloc[idx]['exp_limpio'] not in ["nodetectado", "na", ""]:
                            res_temp[idx]['anomalia'] = '⚠️ POSIBLE CASO DUPLICADO'

                guardadas, omit = guardar_expedientes(res_temp, bufete, abogado_activo)
                
                mensaje_final = f"✅ {guardadas} indexados con éxito."
                if errores_detectados: mensaje_final += " (Algunos documentos requirieron extracción básica)."
                st.success(mensaje_final)
                
                st.session_state.update({'data': res_temp, 'analisis_completado': True, 'all_raw_responses': all_raw})
                st.rerun()

        if st.session_state['analisis_completado'] and st.session_state['data']:
            df_raw = pd.DataFrame(st.session_state['data'])
            
            st.write("---")
            st.header("📊 Resumen Ejecutivo del Lote")
            c1, c2, c3 = st.columns(3)
            c1.metric("Expedientes", len(df_raw))
            c2.metric("Monto en Riesgo", f"Q {df_raw['monto_litigio'].sum():,.2f}")
            c3.metric("Plazos Críticos", len(df_raw[df_raw['semaforo'].str.contains('🔴')]))

            st.write("---")
            st.write("### 🚨 Auditoría de Litispendencia (Duplicados)")
            duplicados = df_raw[df_raw['anomalia'].str.contains('DUPLICADO', na=False)]
            
            if not duplicados.empty:
                st.error(f"⚠️ Se detectaron {len(duplicados)} expedientes duplicados en este lote.")
                st.dataframe(duplicados[['archivo_origen', 'numero_expediente', 'juzgado', 'anomalia']], width="stretch", hide_index=True)
            else:
                st.success("✅ Lote Limpio: No se detectaron expedientes repetidos por Número de Caso.")
            st.write("---")

            df_base = pd.DataFrame()
            df_base['Semáforo'] = df_raw['semaforo']
            df_base['Documento'] = df_raw['archivo_origen']
            df_base['NUE / Juzgado'] = df_raw['numero_expediente'] + " - " + df_raw['juzgado']
            df_base['Proceso'] = df_raw['materia'] + " | " + df_raw['tipo_proceso']
            df_base['Actor (Demandante)'] = df_raw.apply(lambda row: formato_sujeto(row['demandante'], row['documento_identificacion_demandante']), axis=1)
            df_base['Demandado'] = df_raw.apply(lambda row: formato_sujeto(row['demandado'], row['documento_identificacion_demandado']), axis=1)
            df_base['Fechas y Plazos'] = df_raw.apply(lambda row: formato_plazos(row['fecha_resolucion'], row['plazo_procesal']), axis=1)
            df_base['Alertas y Anomalías'] = df_raw['anomalia'].replace('ninguna', 'OK')

            df_web = df_base.copy()
            df_web.insert(6, 'Monto en Litigio', df_raw['monto_litigio'].apply(lambda x: f"Q {float(x):,.2f}"))
            
            st.write("### 📋 Tabla Consolidada")
            st.dataframe(df_web, width="stretch", hide_index=True)

            df_excel = df_base.copy()
            df_excel.insert(6, 'Monto en Litigio', df_raw['monto_litigio']) 
            
            csv_lote = df_excel.to_csv(index=False, sep=';').encode('utf-8-sig')
            st.download_button("📥 Descargar Reporte Ejecutivo (Excel/CSV)", csv_lote, "reporte_lote.csv", "text/csv", type="primary")

            if uploaded_files:
                st.write("---")
                st.write("### 👁️ Auditoría Visual (Cotejo de Foja Original)")
                nombres = [f.name for f in uploaded_files]
                seleccion_doc = st.selectbox("Seleccione un documento para cotejar:", nombres)
                
                if seleccion_doc:
                    for f in uploaded_files:
                        if f.name == seleccion_doc:
                            with st.container(height=600, border=True):
                                if f.name.lower().endswith(('png', 'jpg', 'jpeg')):
                                    st.image(f, caption=f.name, width="stretch")
                                elif f.name.lower().endswith('pdf'):
                                    try:
                                        doc = fitz.open(stream=f.getvalue(), filetype="pdf")
                                        for page_num in range(len(doc)):
                                            pix = doc.load_page(page_num).get_pixmap(matrix=fitz.Matrix(2, 2))
                                            st.image(pix.tobytes("png"), width="stretch")
                                    except Exception as e:
                                        st.warning("⚠️ No fue posible renderizar el documento PDF en el visor web.")
                                elif f.name.lower().endswith('.docx'):
                                    try:
                                        import docx
                                        doc_word = docx.Document(f)
                                        st.markdown(f"#### 📄 Vista de Lectura: {f.name}")
                                        
                                        texto_visor = ""
                                        for p in doc_word.paragraphs:
                                            if p.text.strip(): texto_visor += p.text.strip() + "\n\n"
                                        
                                        for table in doc_word.tables:
                                            texto_visor += "--- *Tabla Extraída* ---\n"
                                            for row in table.rows:
                                                fila = " | ".join([cell.text.strip().replace("\n", " ") for cell in row.cells if cell.text.strip()])
                                                if fila: texto_visor += f"{fila}\n"
                                            texto_visor += "------------------------\n\n"
                                        
                                        st.text(texto_visor)
                                    except Exception as e:
                                        st.info("⚠️ La previsualización de este Word no se pudo cargar.")
                            break

            with st.expander("🛠️ Depuración de IA (Ver JSON Crudo)"):
                all_raw = st.session_state.get('all_raw_responses', {})
                if all_raw:
                    archivo_debug = st.selectbox("Inspeccionar:", list(all_raw.keys()))
                    st.code(all_raw.get(archivo_debug, "Sin datos"), language='json')

    with tabs[1]:
        st.header("🗄️ Bóveda Corporativa")
        historial_df = obtener_historial(bufete)
        if not historial_df.empty:
            if not es_admin:
                col_abogado = next((c for c in historial_df.columns if c.lower() in ['usuario', 'abogado', 'creado_por']), None)
                if col_abogado: historial_df = historial_df[historial_df[col_abogado] == abogado_activo]

            if not historial_df.empty:
                columnas_requeridas = {
                    'semaforo': '🟢 TRÁMITE', 'archivo_origen': 'Desconocido', 
                    'numero_expediente': 'No detectado', 'juzgado': 'No detectado',
                    'materia': 'No detectada', 'tipo_proceso': 'No detectado',
                    'demandante': 'Desconocido', 'documento_identificacion_demandante': 'No detectado',
                    'demandado': 'Desconocido', 'documento_identificacion_demandado': 'No detectado',
                    'fecha_resolucion': 'N/A', 'plazo_procesal': 'N/A', 'anomalia': 'ninguna'
                }
                for col, default in columnas_requeridas.items():
                    if col not in historial_df.columns:
                        historial_df[col] = default
                
                if 'monto_litigio' not in historial_df.columns:
                    historial_df['monto_litigio'] = historial_df.get('monto', 0.0)

                df_base_hist = pd.DataFrame()
                df_base_hist['Semáforo'] = historial_df['semaforo']
                df_base_hist['Documento'] = historial_df['archivo_origen']
                df_base_hist['NUE / Juzgado'] = historial_df['numero_expediente'] + " - " + historial_df['juzgado']
                df_base_hist['Proceso'] = historial_df['materia'] + " | " + historial_df['tipo_proceso']
                df_base_hist['Actor (Demandante)'] = historial_df.apply(lambda row: formato_sujeto(row['demandante'], row['documento_identificacion_demandante']), axis=1)
                df_base_hist['Demandado'] = historial_df.apply(lambda row: formato_sujeto(row['demandado'], row['documento_identificacion_demandado']), axis=1)
                df_base_hist['Fechas y Plazos'] = historial_df.apply(lambda row: formato_plazos(row['fecha_resolucion'], row['plazo_procesal']), axis=1)
                df_base_hist['Alertas y Anomalías'] = historial_df['anomalia'].replace('ninguna', 'OK')

                df_web_hist = df_base_hist.copy()
                df_web_hist.insert(6, 'Monto en Litigio', pd.to_numeric(historial_df['monto_litigio'], errors='coerce').fillna(0.0).apply(lambda x: f"Q {x:,.2f}"))
                st.dataframe(df_web_hist, width="stretch", hide_index=True)

                df_excel_hist = df_base_hist.copy()
                df_excel_hist.insert(6, 'Monto en Litigio', pd.to_numeric(historial_df['monto_litigio'], errors='coerce').fillna(0.0))
                st.download_button("📥 Exportar Bóveda", df_excel_hist.to_csv(index=False, sep=';').encode('utf-8-sig'), "boveda_limpia.csv", "text/csv")
            else: st.info("Portafolio vacío.")
        else: st.info("Base de datos sin registros.")

    if es_admin:
        with tabs[2]:
            st.header("⚙️ Gestión")
            st.info("Panel de gestión de usuarios activo.") 

if __name__ == "__main__":
    if not st.session_state['auth']: login()
    else: main()