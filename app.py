import streamlit as st
import pandas as pd
import json
import os
import time
import re
import uuid
import fitz  
from modulos.conexion_api import analizar_expediente
from modulos.base_datos import (
    inicializar_db, guardar_expedientes, obtener_historial, autenticar_usuario,
    actualizar_password, registrar_usuario, obtener_usuarios_empresa, eliminar_usuario
)
from modulos.generador_avisos import (
    generar_aviso_dicabi, generar_aviso_agp_testimonio, 
    generar_aviso_trimestral_agp, generar_resumen_juridico_ejecutivo
)
from modulos.catalogo_plantillas import CATALOGO_PLANTILLAS
from modulos.formateador_legal import (
    generar_documento_protocolo_espanol, generar_documento_memorial_judicial
)

# --- 1. CONFIGURACIÓN DEL SISTEMA ---
st.set_page_config(
    page_title="Lex IA 360 — Suite Jurídica y Notarial Forense", 
    page_icon="⚖️", 
    layout="wide"
)
inicializar_db()

# --- 2. ESTADO DE SESIÓN ---
if 'auth' not in st.session_state: st.session_state['auth'] = False
if 'user' not in st.session_state: st.session_state['user'] = None
if 'data' not in st.session_state: st.session_state['data'] = []
if 'analisis_completado' not in st.session_state: st.session_state['analisis_completado'] = False
if 'uploader_key' not in st.session_state: st.session_state['uploader_key'] = 0
if 'all_raw_responses' not in st.session_state: st.session_state['all_raw_responses'] = {}

# --- 3. PROCESAMIENTO FORENSE DE RESPUESTAS GEMINI ---
def procesar_respuesta_gemini(raw_response, file_name):
    data = {
        "archivo_origen": file_name,
        "categoria_documental": "EXPEDIENTE_JUDICIAL",
        "numero_expediente": "No detectado",
        "folio_protocolo": "N/A",
        "juzgado": "No detectado",
        "materia": "Civil",
        "tipo_proceso": "No detectado",
        "demandante": "Desconocido",
        "dpi_demandante": "No detectado",
        "nit_demandante": "No detectado",
        "demandado": "Desconocido",
        "dpi_demandado": "No detectado",
        "nit_demandado": "No detectado",
        "monto_litigio": 0.0,
        "timbre_notarial": 0.0,
        "timbre_fiscal": 0.0,
        "registro_destino": "Archivo General de Protocolos",
        "fecha_resolucion": "N/A",
        "fecha_audiencia": "N/A",
        "plazo_procesal": "N/A",
        "semaforo": "🟢 TRÁMITE",
        "anomalia": "ninguna",
        "resumen_forense": ""
    }

    if not raw_response or '"error"' in str(raw_response).lower():
        data["anomalia"] = "Error en análisis o documento ilegible"
        return data

    try:
        match = re.search(r'\{.*\}', str(raw_response), re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
            data["categoria_documental"] = parsed.get("categoria_documental", "EXPEDIENTE_JUDICIAL")
            data["numero_expediente"] = str(parsed.get("numero_instrumento_o_caso", "No detectado"))
            data["folio_protocolo"] = str(parsed.get("folio_protocolo", "N/A"))
            data["fecha_resolucion"] = str(parsed.get("fecha_documento", "N/A"))
            data["juzgado"] = str(parsed.get("notario_o_juzgado", "No detectado"))
            data["tipo_proceso"] = str(parsed.get("tipo_acto_o_juicio", "No detectado"))
            data["materia"] = str(parsed.get("materia_derecho", "Notarial" if "PROTOCOLO" in data["categoria_documental"] else "Civil"))
            data["monto_litigio"] = float(parsed.get("monto_cuantia_o_precio", 0.0))
            data["timbre_notarial"] = float(parsed.get("timbre_notarial_estimado", 0.0))
            data["timbre_fiscal"] = float(parsed.get("timbre_fiscal_o_iva", 0.0))
            data["registro_destino"] = str(parsed.get("registro_destino", "Archivo General de Protocolos"))
            data["plazo_procesal"] = str(parsed.get("plazo_o_termino", "N/A"))
            data["semaforo"] = str(parsed.get("semaforo_alerta", "🟢 TRÁMITE"))
            data["resumen_forense"] = str(parsed.get("resumen_ejecutivo", ""))
            data["anomalia"] = str(parsed.get("alertas_forenses", "ninguna"))

            otorgantes = parsed.get("otorgantes_o_partes", [])
            if isinstance(otorgantes, list) and len(otorgantes) > 0:
                p1 = otorgantes[0]
                data["demandante"] = f"{p1.get('nombre_completo', 'Desconocido')} ({p1.get('rol_en_acto', 'Parte 1')})"
                data["dpi_demandante"] = str(p1.get("identificacion_dpi", "No detectado"))
                data["nit_demandante"] = str(p1.get("nit", "No detectado"))

                if len(otorgantes) > 1:
                    p2_list = [f"{p.get('nombre_completo', '')} ({p.get('rol_en_acto', '')})" for p in otorgantes[1:]]
                    data["demandado"] = " | ".join(p2_list)
                    data["dpi_demandado"] = str(otorgantes[1].get("identificacion_dpi", "No detectado"))
                    data["nit_demandado"] = str(otorgantes[1].get("nit", "No detectado"))
                else:
                    data["demandado"] = "Unilateral / Acto notarial sin contraparte"
    except Exception as e:
        data["anomalia"] = f"Parseo parcial: {str(e)}"

    return data

# --- 4. INTERFACES DE USUARIO ---
def login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.write("\n\n\n")
        st.markdown("<h1 style='text-align:center;color:#4A0E4E;'>⚖️ Lex IA 360</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;color:#64748B;'>Centro de Inteligencia Notarial y Forense Judicial</p>", unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("👤 Usuario Corporativo")
            p = st.text_input("🔑 Contraseña", type="password")
            if st.form_submit_button("Ingresar al Despacho", use_container_width=True, type="primary"):
                res = autenticar_usuario(u.strip(), p)
                if res:
                    st.session_state.update({'auth': True, 'user': res})
                    st.rerun()
                else: 
                    st.error("🚨 Credenciales inválidas. Verifique con administración.")

def main():
    user = st.session_state['user']
    bufete, abogado_activo, es_admin = user['empresa'], user['usuario'], user['rol'] == 'Administrador'

    with st.sidebar:
        st.markdown(f"### 🏛️ {bufete}")
        st.caption(f"Profesional Activo: **{abogado_activo}**\n\nNivel: `{user['rol']}`")
        st.write("---")
        
        with st.expander("🔐 Seguridad y Clave"):
            with st.form("form_clave"):
                np = st.text_input("Nueva Contraseña", type="password")
                cp = st.text_input("Confirmar", type="password")
                if st.form_submit_button("Actualizar", use_container_width=True):
                    if np and np == cp:
                        actualizar_password(abogado_activo, np)
                        st.success("¡Clave actualizada!")
                    else: st.error("Las claves no coinciden.")
                    
        st.write("---")
        if st.button("🗑️ Limpiar Mesa de Trabajo", use_container_width=True):
            st.session_state['uploader_key'] += 1
            st.session_state.update({'data': [], 'analisis_completado': False, 'all_raw_responses': {}})
            st.rerun()
            
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.update({'auth': False, 'user': None})
            st.rerun()

    st.title(f"Centro de Operaciones Notariales y Forenses — {bufete}")
    tabs_nombres = [
        "📑 Extracción y Auditoría", 
        "🏛️ Generador de Plantillas y Minutas",
        "📝 Generador de Avisos Notariales", 
        "📜 Índice Oficial de Protocolo", 
        "🗄️ Bóveda Histórica"
    ]
    if es_admin: tabs_nombres.append("⚙️ Administración")
    tabs = st.tabs(tabs_nombres)

    # =========================================================================
    # PESTAÑA 1: EXTRACCIÓN Y AUDITORÍA MULTIMODAL
    # =========================================================================
    with tabs[0]:
        st.markdown(
            "Cargue expedientes judiciales, cédulas de notificación o escrituras matrices del protocolo notarial "
            "*(soporta PDFs escaneados, fojas de protocolo, y documentos Word)*."
        )
        
        uploaded_files = st.file_uploader(
            "Arrastre documentos escaneados aquí:",
            accept_multiple_files=True,
            type=['pdf','png','jpg','jpeg','docx','txt'],
            key=f"uploader_{st.session_state['uploader_key']}"
        )

        if uploaded_files and not st.session_state['analisis_completado']:
            if st.button("🚀 Iniciar Auditoría Forense con Gemini 3.1 Flash", type="primary", use_container_width=True):
                res_temp, all_raw = [], {}
                bar, status = st.progress(0), st.empty()

                for i, file in enumerate(uploaded_files):
                    status.text(f"Auditando documento {i+1} de {len(uploaded_files)}: {file.name}...")
                    temp_path = f"temp_{uuid.uuid4().hex}_{file.name}"
                    try:
                        with open(temp_path, "wb") as tmp:
                            tmp.write(file.getbuffer())

                        raw_response = analizar_expediente(temp_path)
                        all_raw[file.name] = raw_response

                        data = procesar_respuesta_gemini(raw_response, file.name)
                        res_temp.append(data)
                    finally:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                    bar.progress((i + 1) / len(uploaded_files))

                    if i < len(uploaded_files) - 1:
                        time.sleep(1.5)

                status.empty()

                # Detección de duplicados
                if res_temp:
                    df_chk = pd.DataFrame(res_temp)
                    dups = df_chk.duplicated(subset=['numero_expediente', 'folio_protocolo'], keep=False)
                    for idx, is_dup in enumerate(dups):
                        if is_dup and df_chk.iloc[idx]['numero_expediente'] not in ['No detectado', 'N/A']:
                            if res_temp[idx]['anomalia'] == 'ninguna':
                                res_temp[idx]['anomalia'] = '⚠️ POSIBLE DUPLICADO'
                            else:
                                res_temp[idx]['anomalia'] += ' | ⚠️ POSIBLE DUPLICADO'

                guardadas, omitidas = guardar_expedientes(res_temp, bufete, abogado_activo)
                st.success(f"✅ Auditoría completada: {guardadas} registros indexados ({omitidas} omitidos por preexistencia).")

                st.session_state.update({'data': res_temp, 'analisis_completado': True, 'all_raw_responses': all_raw})
                st.rerun()

        # RESULTADOS DEL LOTE
        if st.session_state['analisis_completado'] and st.session_state['data']:
            df_raw = pd.DataFrame(st.session_state['data'])
            
            st.write("---")
            st.header("📊 Resumen Ejecutivo del Lote Analizado")
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Total Documentos", len(df_raw))
            k2.metric("Cuantía / Valor Económico", f"Q {df_raw['monto_litigio'].sum():,.2f}")
            k3.metric("Timbres Notariales Est.", f"Q {df_raw['timbre_notarial'].sum():,.2f}")
            k4.metric("Plazos Urgentes 🔴", len(df_raw[df_raw['semaforo'].str.contains('🔴', na=False)]))

            st.write("---")
            st.subheader("📋 Matriz Consolidada de Instrumentos y Resoluciones")
            
            cols_mostrar = [
                'semaforo', 'categoria_documental', 'numero_expediente', 'folio_protocolo',
                'fecha_resolucion', 'juzgado', 'tipo_proceso', 'demandante', 'demandado',
                'monto_litigio', 'timbre_notarial', 'registro_destino', 'anomalia'
            ]
            df_view = df_raw[cols_mostrar].copy()
            df_view.columns = [
                'Semáforo', 'Categoría', 'No. Instrumento / Caso', 'Folio (A/R)',
                'Fecha', 'Notario / Juzgado', 'Acto o Juicio', 'Otorgante 1 / Actor',
                'Otorgante 2 / Demandado', 'Cuantía (Q)', 'Timbre Notarial (Q)', 'Destino Registral', 'Alertas'
            ]
            st.dataframe(df_view, use_container_width=True, hide_index=True)

            c_down1, c_down2 = st.columns(2)
            with c_down1:
                csv_lote = df_view.to_csv(index=False, sep=';').encode('utf-8-sig')
                st.download_button("📥 Descargar Tabla en Excel/CSV", csv_lote, "auditoria_lote.csv", "text/csv", type="primary")

            with c_down2:
                if st.button("🔄 Analizar Nuevo Lote de Expedientes", use_container_width=True):
                    st.session_state['uploader_key'] += 1
                    st.session_state.update({'data': [], 'analisis_completado': False})
                    st.rerun()

            # VISOR VISUAL Y COTEJO
            if uploaded_files:
                st.write("---")
                st.subheader("👁️ Auditoría Visual y Cotejo de Fojas Originales")
                nombres = [f.name for f in uploaded_files]
                sel_doc = st.selectbox("Seleccione documento para cotejar:", nombres)
                if sel_doc:
                    for f in uploaded_files:
                        if f.name == sel_doc:
                            with st.container(height=600, border=True):
                                if f.name.lower().endswith(('png', 'jpg', 'jpeg')):
                                    st.image(f, caption=f.name, use_container_width=True)
                                elif f.name.lower().endswith('pdf'):
                                    try:
                                        doc = fitz.open(stream=f.getvalue(), filetype="pdf")
                                        for p_no in range(min(6, len(doc))):
                                            pix = doc.load_page(p_no).get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                                            st.image(pix.tobytes("png"), caption=f"Página {p_no+1}", use_container_width=True)
                                    except Exception as e:
                                        st.warning("No se pudo previsualizar el PDF.")
                            break

            with st.expander("🛠️ Depuración de IA (Ver JSON Estructurado)"):
                all_raw = st.session_state.get('all_raw_responses', {})
                if all_raw:
                    sel_raw = st.selectbox("Documento:", list(all_raw.keys()))
                    st.code(all_raw.get(sel_raw, "Sin datos"), language="json")

    # =========================================================================
    # PESTAÑA 2: GENERADOR DE PLANTILLAS Y MINUTAS (FORMATO PROTOCOLO 25 LÍNEAS)
    # =========================================================================
    with tabs[1]:
        st.header("🏛️ Generador de Minutas y Memoriales (Formato Oficial Guatemala)")
        st.markdown(
            "Seleccione la rama del derecho y la plantilla requerida. El sistema configurará automáticamente "
            "los márgenes y el interlineado exacto de **25 líneas por cara en Papel Español de Protocolo** "
            "o formato de **Memorial Judicial** listo para presentar."
        )

        # --- SUITE DE PLANTILLAS LEGALES (5 POR RAMA) ---
        ramas_disponibles = {
            "📜 Notarial (Protocolo)": "NOTARIAL",
            "⚖️ Civil y Mercantil": "CIVIL",
            "👨‍👩‍👧‍👦 Derecho de Familia": "FAMILIA",
            "🛡️ Derecho Penal": "PENAL"
        }

        rama_sel = st.radio(
            "📁 Seleccione la Rama Jurídica:",
            list(ramas_disponibles.keys()),
            horizontal=True
        )
        clave_cat = ramas_disponibles[rama_sel]
        lista_5_plantillas = CATALOGO_PLANTILLAS[clave_cat]

        st.markdown(f"### 📋 Los 5 Instrumentos / Memoriales Más Comunes en `{rama_sel}`")
        st.caption("Seleccione cualquiera de los 5 formatos para completar datos mínimos y generar en Word (.docx) con las 25 líneas oficiales o formato judicial:")

        # Desplegamos las 5 plantillas en pestañas visuales directas
        nombres_pills = [f"#{i+1} {p['nombre'].split('(')[0].strip()[:35]}..." for i, p in enumerate(lista_5_plantillas)]
        tabs_plantillas = st.tabs(nombres_pills)

        for i, (tab_pl, pl) in enumerate(zip(tabs_plantillas, lista_5_plantillas)):
            with tab_pl:
                st.markdown(f"#### 📄 {i+1}. {pl['nombre']}")
                st.info(f"**🏛️ Soporte de Ley:** `{pl['soporte']}`  \n**🎯 Objeto Legal:** {pl['descripcion']}")
                
                with st.form(f"form_generar_{pl['id']}"):
                    st.markdown("**✏️ Datos Mínimos del Caso:**")
                    col1, col2 = st.columns(2)
                    valores = {}
                    
                    for j, campo in enumerate(pl["campos"]):
                        target_col = col1 if j % 2 == 0 else col2
                        nombre_etiqueta = campo.replace("_", " ").title()
                        with target_col:
                            valores[campo] = st.text_input(f"{nombre_etiqueta}:", key=f"inp_{pl['id']}_{campo}")

                    btn_generar = st.form_submit_button(f"🚀 Generar {pl['nombre'][:25]}... en Word", type="primary", use_container_width=True)

                if btn_generar:
                    texto_completo = pl["redaccion"]
                    for k_c, v_c in valores.items():
                        reemplazo = v_c.strip() if v_c.strip() else f"[{k_c.upper()}]"
                        texto_completo = texto_completo.replace(f"{{{k_c}}}", reemplazo)

                    if clave_cat == "NOTARIAL" and "Protocolo" in pl["soporte"]:
                        doc_bytes = generar_documento_protocolo_espanol(pl["nombre"], texto_completo)
                        nombre_doc = f"Protocolo_25Lineas_{pl['id']}.docx"
                    else:
                        juz_nombre = valores.get("juzgado", valores.get("juzgado_familia", valores.get("juzgado_penal", "JUZGADO DE PRIMERA INSTANCIA")))
                        doc_bytes = generar_documento_memorial_judicial(pl["nombre"], texto_completo, juz_nombre)
                        nombre_doc = f"Memorial_{pl['id']}.docx"

                    st.success(f"✅ ¡Minuta generada con éxito con las formalidades y tipografía oficial!")
                    st.download_button(
                        label=f"📥 Descargar '{pl['nombre']}' (.docx)",
                        data=doc_bytes,
                        file_name=nombre_doc,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        type="primary",
                        use_container_width=True,
                        key=f"btn_dl_{pl['id']}"
                    )

                    with st.expander("👁️ Ver Redacción Previa"):
                        st.text(texto_completo)

    # =========================================================================
    # PESTAÑA 3: GENERADOR AUTOMÁTICO DE AVISOS NOTARIALES Y DICTÁMENES (.DOCX)
    # =========================================================================
    with tabs[2]:
        st.header("📝 Generador de Avisos Notariales y Dictámenes Oficiales en Word (.docx)")
        st.markdown(
            "Seleccione un documento analizado o complete información mínima para emitir los avisos "
            "obligatorios de ley listos para firmar y presentar."
        )

        registros = st.session_state.get('data', [])
        if not registros:
            hist_db = obtener_historial(bufete)
            if not hist_db.empty:
                registros = hist_db.to_dict('records')

        if registros:
            nombres_opc = [f"{r.get('numero_expediente', 'S/N')} - {r.get('tipo_proceso', 'Acto')} ({r.get('archivo_origen', '')})" for r in registros]
            sel_idx = st.selectbox("Seleccione instrumento para generar aviso:", range(len(nombres_opc)), format_func=lambda i: nombres_opc[i])
            reg_sel = registros[sel_idx]
            
            st.write("---")
            c_av1, c_av2 = st.columns(2)

            with c_av1:
                st.subheader("🏛️ Avisos Obligatorios al Archivo de Protocolos y DICABI")
                
                # AVISO DICABI TRASPASO
                with st.expander("📍 Aviso Notarial de Traspaso (DICABI / IUSI Municipal)", expanded=True):
                    st.caption("Obligatorio dentro de los 15 días hábiles siguientes a la compraventa.")
                    finca = st.text_input("No. de Finca:", "1234", key=f"finca_{sel_idx}")
                    folio = st.text_input("Folio:", "25", key=f"folio_{sel_idx}")
                    libro = st.text_input("Libro:", "89 de Guatemala", key=f"libro_{sel_idx}")
                    
                    datos_dicabi = {
                        "notario": reg_sel.get('juzgado', 'Ashly Brigeth Rodas Estrada'),
                        "numero_instrumento": reg_sel.get('numero_expediente', '1'),
                        "fecha": reg_sel.get('fecha_resolucion', '2024'),
                        "tipo_contrato": reg_sel.get('tipo_proceso', 'Compraventa de Bien Inmueble'),
                        "vendedor": reg_sel.get('demandante', 'Vendedor'),
                        "nit_vendedor": reg_sel.get('nit_demandante', 'C/F'),
                        "comprador": reg_sel.get('demandado', 'Comprador'),
                        "nit_comprador": reg_sel.get('nit_demandado', 'C/F'),
                        "monto": reg_sel.get('monto_litigio', 0.0),
                        "finca": finca, "folio": folio, "libro": libro
                    }
                    doc_bytes_dicabi = generar_aviso_dicabi(datos_dicabi)
                    st.download_button(
                        "📄 Descargar Aviso DICABI en Word (.docx)",
                        doc_bytes_dicabi,
                        f"Aviso_DICABI_Escritura_{reg_sel.get('numero_expediente', '1')}.docx",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        type="primary",
                        use_container_width=True
                    )

                # AVISO AGP TESTIMONIO ESPECIAL
                with st.expander("📜 Aviso de Testimonio Especial (Archivo General de Protocolos)"):
                    st.caption("Plazo de 25 días hábiles conforme al Art. 37 del Código de Notariado.")
                    fol_ini = st.text_input("Folio Inicial:", reg_sel.get('folio_protocolo', '1 A'), key=f"fini_{sel_idx}")
                    fol_fin = st.text_input("Folio Final:", "2 R", key=f"ffin_{sel_idx}")
                    
                    datos_agp = {
                        "notario": reg_sel.get('juzgado', 'Ashly Brigeth Rodas Estrada'),
                        "numero_instrumento": reg_sel.get('numero_expediente', '1'),
                        "fecha": reg_sel.get('fecha_resolucion', '2024'),
                        "tipo_contrato": reg_sel.get('tipo_proceso', 'Mandato / Compraventa'),
                        "otorgantes": f"{reg_sel.get('demandante', '')} y {reg_sel.get('demandado', '')}",
                        "folio_inicial": fol_ini,
                        "folio_final": fol_fin,
                        "timbre_notarial": reg_sel.get('timbre_notarial', 10.0)
                    }
                    doc_bytes_agp = generar_aviso_agp_testimonio(datos_agp)
                    st.download_button(
                        "📄 Descargar Entrega Testimonio Especial (.docx)",
                        doc_bytes_agp,
                        f"Entrega_Testimonio_Especial_{reg_sel.get('numero_expediente', '1')}.docx",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )

            with c_av2:
                st.subheader("📊 Ficha Ejecutiva y Avisos Trimestrales")
                
                # FICHA EJECUTIVA / DICTAMEN
                with st.expander("📑 Dictamen y Resumen Ejecutivo para el Cliente / Bufete", expanded=True):
                    st.caption("Informe formal con resumen, partes, gravámenes y liquidación de timbres.")
                    st.write(f"**Resumen Registrado:** {reg_sel.get('resumen_forense', 'Acto notarial formal.')}")
                    doc_bytes_ficha = generar_resumen_juridico_ejecutivo(reg_sel)
                    st.download_button(
                        "📥 Descargar Ficha Ejecutiva en Word (.docx)",
                        doc_bytes_ficha,
                        f"Dictamen_Ejecutivo_{reg_sel.get('numero_expediente', 'caso')}.docx",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        type="primary",
                        use_container_width=True
                    )

                # AVISO TRIMESTRAL
                with st.expander("🗓️ Aviso Notarial Trimestral (AGP)"):
                    st.caption("Aviso por trimestre vencido (Enero-Marzo, Abril-Junio, etc.).")
                    trimestre = st.selectbox("Trimestre:", ["Primer Trimestre", "Segundo Trimestre", "Tercer Trimestre", "Cuarto Trimestre"])
                    ano_t = st.text_input("Año Fiscal:", "2024")
                    
                    datos_trim = {
                        "trimestre": trimestre, "ano": ano_t,
                        "notario": reg_sel.get('juzgado', 'Ashly Brigeth Rodas Estrada'),
                        "primer_num": "1", "primera_fecha": "10 de enero de 2024",
                        "ultimo_num": "18", "ultima_fecha": "12 de agosto de 2024",
                        "total_autorizados": "18", "total_cancelados": "0"
                    }
                    doc_bytes_trim = generar_aviso_trimestral_agp(datos_trim)
                    st.download_button(
                        "📄 Descargar Aviso Trimestral (.docx)",
                        doc_bytes_trim,
                        f"Aviso_{trimestre.replace(' ', '_')}_{ano_t}.docx",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
        else:
            st.info("Primero cargue o procese documentos en la pestaña de 'Extracción y Auditoría' para habilitar los generadores.")

    # =========================================================================
    # PESTAÑA 4: ÍNDICE OFICIAL DE PROTOCOLO (ART. 92 CÓDIGO DE NOTARIADO)
    # =========================================================================
    with tabs[3]:
        st.header("📜 Generador Oficial del Índice de Protocolo Notarial")
        st.markdown(
            "Cumple con el **Artículo 92 del Código de Notariado de Guatemala**. "
            "Genera la nómina exacta para encuadernación de fin de año con folios (Anverso/Reverso)."
        )

        historial = obtener_historial(bufete)
        if not historial.empty:
            notariales = historial[historial['categoria_documental'] == 'PROTOCOLO_NOTARIAL'].copy()
            if notariales.empty:
                notariales = historial[historial['folio_protocolo'] != 'N/A'].copy()

            if not notariales.empty:
                notariales = notariales.sort_values(by=['numero_expediente'], ascending=True)
                
                tabla_indice = pd.DataFrame()
                tabla_indice['No. Instrumento'] = notariales['numero_expediente']
                tabla_indice['Fecha de Otorgamiento'] = notariales['fecha_resolucion']
                tabla_indice['Otorgantes / Comparecientes'] = notariales['demandante'] + " y " + notariales['demandado']
                tabla_indice['Objeto / Contrato'] = notariales['tipo_proceso']
                tabla_indice['Folio (A/R)'] = notariales['folio_protocolo']

                st.dataframe(tabla_indice, use_container_width=True, hide_index=True)

                csv_indice = tabla_indice.to_csv(index=False, sep=';').encode('utf-8-sig')
                st.download_button(
                    "📥 Descargar Índice Notarial Oficial (Excel / Impresión)",
                    csv_indice,
                    "indice_protocolo_oficial.csv",
                    "text/csv",
                    type="primary"
                )
            else:
                st.info("Aún no ha procesado escrituras de protocolo notarial en esta sesión.")
        else:
            st.info("Bóveda sin registros notariales.")

    # =========================================================================
    # PESTAÑA 5: BÓVEDA HISTÓRICA
    # =========================================================================
    with tabs[4]:
        st.header("🗄️ Bóveda Centralizada del Despacho")
        hist = obtener_historial(bufete)
        if not hist.empty:
            st.dataframe(hist, use_container_width=True, hide_index=True)
            st.download_button(
                "📥 Exportar Toda la Bóveda a Excel",
                hist.to_csv(index=False, sep=';').encode('utf-8-sig'),
                "boveda_completa_despacho.csv",
                "text/csv"
            )
        else:
            st.info("No hay registros almacenados todavía.")

    # =========================================================================
    # PESTAÑA 6: ADMINISTRACIÓN
    # =========================================================================
    # =========================================================================
    # PESTAÑA 6: ADMINISTRACIÓN SAAS Y GESTIÓN DE USUARIOS
    # =========================================================================
    if es_admin:
        with tabs[5]:
            st.header("⚙️ Gobernanza, Control de Accesos y Soporte del Bufete")
            st.markdown("Gestione los abogados, secretarias y procuradores que tienen acceso al sistema.")
            
            col_admin_a, col_admin_b = st.columns([1, 1.3])

            with col_admin_a:
                st.subheader("➕ Registrar Nuevo Abogado o Colaborador")
                with st.form("form_crear_usuario"):
                    nuevo_id = st.text_input("ID o Correo de Usuario:")
                    nuevo_pass = st.text_input("Contraseña Temporal:", type="password")
                    nuevo_rol = st.selectbox("Nivel de Acceso / Rol:", ["Abogado Asociado", "Secretaria / Procurador", "Administrador"])
                    
                    if st.form_submit_button("Crear Credencial de Acceso", type="primary", use_container_width=True):
                        if nuevo_id and nuevo_pass:
                            if registrar_usuario(nuevo_id.strip(), nuevo_pass.strip(), bufete, nuevo_rol):
                                st.success(f"✅ Usuario '{nuevo_id}' creado exitosamente.")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ Error: Ese usuario ya se encuentra registrado en el sistema.")
                        else:
                            st.warning("⚠️ Complete todos los campos.")

            with col_admin_b:
                st.subheader("📋 Nómina de Usuarios Activos")
                df_usuarios = obtener_usuarios_empresa(bufete)
                if not df_usuarios.empty:
                    st.dataframe(df_usuarios, use_container_width=True, hide_index=True)
                    
                    st.write("---")
                    st.subheader("🔑 Soporte Técnico: Restablecer Contraseña Olvidada")
                    with st.form("form_reset_pass"):
                        lista_u = df_usuarios['usuario'].tolist()
                        u_reset = st.selectbox("Seleccione el usuario que olvidó o perdió su clave:", lista_u)
                        p_nueva = st.text_input("Nueva Contraseña Temporal:", type="password")
                        
                        if st.form_submit_button("Forzar Cambio de Contraseña", type="primary", use_container_width=True):
                            if p_nueva:
                                actualizar_password(u_reset, p_nueva)
                                st.success(f"✅ La contraseña de '{u_reset}' fue restablecida con éxito. Ya puede iniciar sesión con la nueva clave.")
                            else:
                                st.warning("Escriba la nueva contraseña temporal.")

                    st.write("---")
                    st.subheader("🚫 Revocar Acceso / Eliminar Usuario")
                    with st.form("form_eliminar_u"):
                        u_eliminar = st.selectbox("Seleccione usuario a dar de baja:", lista_u)
                        if u_eliminar == "admin":
                            st.caption("🔒 El usuario Maestro 'admin' está protegido y no puede ser eliminado.")
                        
                        if st.form_submit_button("Eliminar Acceso Permanentemente", use_container_width=True):
                            if u_eliminar == "admin":
                                st.error("❌ Acción denegada: Imposible eliminar al Administrador Maestro del sistema.")
                            else:
                                eliminar_usuario(u_eliminar)
                                st.warning(f"⚠️ Acceso de '{u_eliminar}' revocado de forma permanente.")
                                time.sleep(1)
                                st.rerun()
                else:
                    st.info("No hay colaboradores registrados en este bufete.")

if __name__ == "__main__":
    if not st.session_state['auth']: login()
    else: main()