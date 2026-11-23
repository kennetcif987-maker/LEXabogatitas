import datetime
import json
import os
import re
import time
import uuid

import fitz
import pandas as pd
import streamlit as st

from modulos.base_datos import (
    actualizar_password,
    autenticar_usuario,
    eliminar_usuario,
    guardar_expedientes,
    inicializar_db_una_vez,
    obtener_empresas_activas,
    obtener_historial,
    obtener_todos_usuarios,
    obtener_usuarios_empresa,
    registrar_nueva_empresa_usuario,
    registrar_usuario,
)
from modulos.catalogo_plantillas import CATALOGO_PLANTILLAS
from modulos.conexion_api import analizar_expediente
from modulos.formateador_legal import (
    generar_documento_memorial_judicial,
    generar_documento_protocolo_espanol,
)
from modulos.generador_avisos import (
    generar_aviso_agp_testimonio,
    generar_aviso_dicabi,
    generar_aviso_matrimonio_renap,
    generar_aviso_trimestral_agp,
    generar_indice_protocolo_docx,
    generar_resumen_juridico_ejecutivo,
)
from modulos.notario_gt import (
    PLAZOS_NOTARIALES_GT,
    calcular_impuestos_testimonio_gt,
    calcular_timbre_notarial_guatemala,
    dataframe_a_csv_seguro,
    dpi_a_letras,
    fecha_a_letras,
    formatear_dpi_espaciado,
    hora_a_letras,
    monto_a_letras,
    normalizar_dpi,
    trimestre_actual_info,
    validar_dpi,
    validar_nit_m11,
)

# --- 1. CONFIGURACIÓN DEL SISTEMA ---
st.set_page_config(
    page_title="Lex IA 360 — Suite Jurídica y Notarial Forense",
    page_icon="⚖️",
    layout="wide",
)
inicializar_db_una_vez()

# --- 2. ESTADO DE SESIÓN ---
if "auth" not in st.session_state:
    st.session_state["auth"] = False
if "user" not in st.session_state:
    st.session_state["user"] = None
if "data" not in st.session_state:
    st.session_state["data"] = []
if "analisis_completado" not in st.session_state:
    st.session_state["analisis_completado"] = False
if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0
if "all_raw_responses" not in st.session_state:
    st.session_state["all_raw_responses"] = {}
if "notario_nombre" not in st.session_state:
    st.session_state["notario_nombre"] = ""
if "notario_colegiado" not in st.session_state:
    st.session_state["notario_colegiado"] = ""
if "notario_clave" not in st.session_state:
    st.session_state["notario_clave"] = ""


def _normalizar_doc_identidad_lex(dpi_raw: str, nit_raw: str, rol_label: str, alertas: list):
    dpi_str = str(dpi_raw or "No detectado").strip()
    if dpi_str and "no detectado" not in dpi_str.lower() and dpi_str.lower() not in ("n/a", "none"):
        cui = normalizar_dpi(dpi_str)
        if cui:
            ok_dpi, msg_dpi = validar_dpi(cui)
            dpi_str = cui
            if not ok_dpi:
                alertas.append(f"DPI {rol_label} ({dpi_str}): {msg_dpi}")
        else:
            digs = re.sub(r"\D", "", dpi_str)
            alertas.append(f"DPI {rol_label} incompleto ({len(digs)} dígitos, debe tener 13)")

    nit_str = str(nit_raw or "No detectado").strip().upper()
    if nit_str and "no detectado" not in nit_str.lower() and nit_str not in ("N/A", "CF", "C/F", "NONE"):
        nit_ok, nit_clean = validar_nit_m11(nit_str)
        if nit_ok:
            nit_str = nit_clean
        else:
            alertas.append(f"NIT {rol_label} no supera Módulo 11 ({nit_str})")
    return dpi_str, nit_str


def _clave_orden_instrumento(valor) -> tuple:
    raw = str(valor or "").strip()
    dig = re.sub(r"\D", "", raw)
    return (0, int(dig), raw) if dig else (1, 0, raw)


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
        "resumen_forense": "",
    }

    if not raw_response or '"error"' in str(raw_response).lower():
        try:
            err_obj = json.loads(str(raw_response))
            data["anomalia"] = err_obj.get("error", "Error en análisis o documento ilegible")
        except Exception:
            data["anomalia"] = "Error en análisis o documento ilegible"
        return data

    try:
        match = re.search(r"\{.*\}", str(raw_response), re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
            data["categoria_documental"] = parsed.get("categoria_documental", "EXPEDIENTE_JUDICIAL")
            data["numero_expediente"] = str(parsed.get("numero_instrumento_o_caso", "No detectado"))
            data["folio_protocolo"] = str(parsed.get("folio_protocolo", "N/A"))
            data["fecha_resolucion"] = str(parsed.get("fecha_documento", "N/A"))
            data["juzgado"] = str(parsed.get("notario_o_juzgado", "No detectado"))
            data["tipo_proceso"] = str(parsed.get("tipo_acto_o_juicio", "No detectado"))
            data["materia"] = str(
                parsed.get(
                    "materia_derecho",
                    "Notarial" if "PROTOCOLO" in data["categoria_documental"] else "Civil",
                )
            )
            monto_val = float(parsed.get("monto_cuantia_o_precio", 0.0) or 0.0)
            data["monto_litigio"] = monto_val

            tn_raw = float(parsed.get("timbre_notarial_estimado", 0.0) or 0.0)
            if tn_raw == 0.0 and "PROTOCOLO" in str(data["categoria_documental"]):
                calc_tn = calcular_timbre_notarial_guatemala(
                    monto_val,
                    "VALOR_DETERMINADO" if monto_val > 0 else "INDETERMINADO",
                )
                tn_raw = float(calc_tn["timbre_notarial"])
            data["timbre_notarial"] = tn_raw

            data["timbre_fiscal"] = float(parsed.get("timbre_fiscal_o_iva", 0.0) or 0.0)
            data["registro_destino"] = str(parsed.get("registro_destino", "Archivo General de Protocolos"))
            data["plazo_procesal"] = str(parsed.get("plazo_o_termino", "N/A"))
            data["semaforo"] = str(parsed.get("semaforo_alerta", "🟢 TRÁMITE"))
            data["resumen_forense"] = str(parsed.get("resumen_ejecutivo", ""))
            data["anomalia"] = str(parsed.get("alertas_forenses", "ninguna"))

            otorgantes = parsed.get("otorgantes_o_partes", [])
            alertas_id = []
            if isinstance(otorgantes, list) and len(otorgantes) > 0:
                p1 = otorgantes[0]
                data["demandante"] = f"{p1.get('nombre_completo', 'Desconocido')} ({p1.get('rol_en_acto', 'Parte 1')})"
                d1, n1 = _normalizar_doc_identidad_lex(
                    p1.get("identificacion_dpi"), p1.get("nit"), "Parte 1", alertas_id
                )
                data["dpi_demandante"] = d1
                data["nit_demandante"] = n1

                if len(otorgantes) > 1:
                    p2_list = [
                        f"{p.get('nombre_completo', '')} ({p.get('rol_en_acto', '')})"
                        for p in otorgantes[1:]
                    ]
                    data["demandado"] = " | ".join(p2_list)
                    d2, n2 = _normalizar_doc_identidad_lex(
                        otorgantes[1].get("identificacion_dpi"),
                        otorgantes[1].get("nit"),
                        "Parte 2",
                        alertas_id,
                    )
                    data["dpi_demandado"] = d2
                    data["nit_demandado"] = n2
                else:
                    data["demandado"] = "Unilateral / Acto notarial sin contraparte"

            if alertas_id:
                base_anom = str(data.get("anomalia") or "").strip()
                extra = " | ".join(f"⚠️ {a}" for a in alertas_id)
                data["anomalia"] = (
                    extra if base_anom.lower() in ("", "ninguna", "none") else f"{base_anom} | {extra}"
                )
    except Exception as e:
        data["anomalia"] = f"Parseo parcial: {str(e)}"

    return data


def _sustituir_campos_plantilla(texto_base: str, valores: dict, notario_def: str) -> str:
    """Rellena campos convirtiendo DPIs y montos ingresados a letras + cifras cuando aplica."""
    texto = texto_base
    hoy_letras = f"la ciudad de Guatemala, el {fecha_a_letras()}"
    hora_actual_letras = hora_a_letras()

    for campo, raw_val in valores.items():
        val = str(raw_val or "").strip()
        if not val:
            if campo == "notario" or campo == "abogado_auxiliante" or campo == "defensor_nombre":
                val = notario_def or f"[{campo.upper()}]"
            elif campo in ("lugar_y_fecha_letras", "ciudad_y_fecha"):
                val = hoy_letras
            elif campo in ("hora_letras", "hora_cierre"):
                val = hora_actual_letras
            else:
                val = f"[{campo.upper()}]"
        else:
            if campo.startswith("dpi"):
                cui = normalizar_dpi(val)
                if len(cui) == 13:
                    val = dpi_a_letras(cui, incluir_digitos=True)
            elif any(k in campo for k in ("monto", "precio", "renta", "deposito", "pension", "total_adeudado")):
                limpio_num = val.replace("Q", "").replace("q", "").replace(",", "").strip()
                if re.match(r"^\d+(\.\d{1,2})?$", limpio_num):
                    val = monto_a_letras(float(limpio_num), "GTQ", incluir_cifra=True)

        texto = texto.replace(f"{{{campo}}}", val)
    return texto


# --- 4. INTERFACES DE USUARIO ---
def login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.write("\n\n\n")
        st.markdown("<h1 style='text-align:center;color:#4A0E4E;'>⚖️ Lex IA 360</h1>", unsafe_allow_html=True)
        st.markdown(
            "<p style='text-align:center;color:#64748B;'>Centro de Inteligencia Notarial y Forense Judicial (Guatemala)</p>",
            unsafe_allow_html=True,
        )
        with st.form("login_form"):
            u = st.text_input("👤 Usuario Corporativo")
            p = st.text_input("🔑 Contraseña", type="password")
            if st.form_submit_button("Ingresar al Despacho", use_container_width=True, type="primary"):
                res = autenticar_usuario(u.strip(), p)
                if res:
                    st.session_state.update({"auth": True, "user": res})
                    st.rerun()
                else:
                    st.error("🚨 Credenciales inválidas. Verifique con administración.")


def main():
    user = st.session_state["user"]
    bufete, abogado_activo, es_admin = user["empresa"], user["usuario"], user["rol"] == "Administrador"

    with st.sidebar:
        st.markdown(f"### 🏛️ {bufete}")
        st.caption(f"Profesional Activo: **{abogado_activo}**\n\nNivel: `{user['rol']}`")
        st.write("---")

        with st.expander("🖋️ Sello y Datos del Notario", expanded=False):
            st.session_state["notario_nombre"] = st.text_input(
                "Nombre del Abogado y Notario:",
                value=st.session_state.get("notario_nombre", ""),
                placeholder="Ej. Lic. Carlos Méndez Pérez",
            )
            st.session_state["notario_colegiado"] = st.text_input(
                "No. Colegiado Activo:",
                value=st.session_state.get("notario_colegiado", ""),
                placeholder="Ej. 24510",
            )
            st.session_state["notario_clave"] = st.text_input(
                "Clave de Notario (AGP):",
                value=st.session_state.get("notario_clave", ""),
                placeholder="Ej. M-1842",
            )

        with st.expander("🔐 Seguridad y Clave"):
            with st.form("form_clave"):
                np = st.text_input("Nueva Contraseña", type="password")
                cp = st.text_input("Confirmar", type="password")
                if st.form_submit_button("Actualizar", use_container_width=True):
                    if np and np == cp:
                        actualizar_password(abogado_activo, np, empresa=bufete)
                        st.success("¡Clave actualizada!")
                    else:
                        st.error("Las claves no coinciden.")

        st.write("---")
        if st.button("🗑️ Limpiar Mesa de Trabajo", use_container_width=True):
            st.session_state["uploader_key"] += 1
            st.session_state.update({"data": [], "analisis_completado": False, "all_raw_responses": {}})
            st.rerun()

        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            st.session_state.update({"auth": False, "user": None})
            st.rerun()

    notario_cfg = st.session_state.get("notario_nombre", "").strip()
    colegiado_cfg = st.session_state.get("notario_colegiado", "").strip()
    clave_cfg = st.session_state.get("notario_clave", "").strip()

    st.title(f"Centro de Operaciones Notariales y Forenses — {bufete}")
    tabs_nombres = [
        "📑 Extracción y Auditoría",
        "🏛️ Generador de Plantillas y Minutas",
        "📝 Avisos Notariales y Calculadoras",
        "📜 Índice Oficial de Protocolo",
        "🗄️ Bóveda Histórica",
    ]
    if es_admin:
        tabs_nombres.append("⚙️ Administración")
    tabs = st.tabs(tabs_nombres)

    # =========================================================================
    # PESTAÑA 1: EXTRACCIÓN Y AUDITORÍA MULTIMODAL
    # =========================================================================
    with tabs[0]:
        st.markdown(
            "Cargue expedientes judiciales, cédulas de notificación o escrituras matrices del protocolo notarial "
            "*(PDFs digitales y escaneados hasta 10 págs., imágenes, Word `.docx` y `.txt` — lee DPIs escritos en letras)*."
        )

        uploaded_files = st.file_uploader(
            "Arrastre documentos escaneados aquí:",
            accept_multiple_files=True,
            type=["pdf", "png", "jpg", "jpeg", "docx", "txt"],
            key=f"uploader_{st.session_state['uploader_key']}",
        )

        if uploaded_files and not st.session_state["analisis_completado"]:
            if st.button("🚀 Iniciar Auditoría Forense con Gemini", type="primary", use_container_width=True):
                res_temp, all_raw = [], {}
                bar, status = st.progress(0), st.empty()

                for i, file in enumerate(uploaded_files):
                    status.text(f"Auditando documento {i+1} de {len(uploaded_files)}: {file.name}...")
                    safe_name = os.path.basename(file.name)
                    temp_path = f"temp_{uuid.uuid4().hex}_{safe_name}"
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

                if res_temp:
                    df_chk = pd.DataFrame(res_temp)
                    dups = df_chk.duplicated(subset=["numero_expediente", "folio_protocolo"], keep=False)
                    for idx, is_dup in enumerate(dups):
                        if is_dup and df_chk.iloc[idx]["numero_expediente"] not in ["No detectado", "N/A"]:
                            if res_temp[idx]["anomalia"] == "ninguna":
                                res_temp[idx]["anomalia"] = "⚠️ POSIBLE DUPLICADO"
                            else:
                                res_temp[idx]["anomalia"] += " | ⚠️ POSIBLE DUPLICADO"

                guardadas, omitidas = guardar_expedientes(res_temp, bufete, abogado_activo)
                st.success(
                    f"✅ Auditoría completada: {guardadas} registros indexados ({omitidas} omitidos por preexistencia)."
                )

                st.session_state.update(
                    {"data": res_temp, "analisis_completado": True, "all_raw_responses": all_raw}
                )
                st.rerun()

        if st.session_state["analisis_completado"] and st.session_state["data"]:
            df_raw = pd.DataFrame(st.session_state["data"])

            st.write("---")
            st.header("📊 Resumen Ejecutivo del Lote Analizado")
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Total Documentos", len(df_raw))
            k2.metric("Cuantía / Valor Económico", f"Q {df_raw['monto_litigio'].sum():,.2f}")
            k3.metric("Timbres Notariales Est.", f"Q {df_raw['timbre_notarial'].sum():,.2f}")
            k4.metric("Plazos Urgentes 🔴", len(df_raw[df_raw["semaforo"].str.contains("🔴", na=False)]))

            st.write("---")
            st.subheader("📋 Matriz Consolidada de Instrumentos y Resoluciones")

            cols_mostrar = [
                "semaforo",
                "categoria_documental",
                "numero_expediente",
                "folio_protocolo",
                "fecha_resolucion",
                "juzgado",
                "tipo_proceso",
                "demandante",
                "dpi_demandante",
                "demandado",
                "dpi_demandado",
                "monto_litigio",
                "timbre_notarial",
                "registro_destino",
                "anomalia",
            ]
            df_view = df_raw[cols_mostrar].copy()
            df_view.columns = [
                "Semáforo",
                "Categoría",
                "No. Instrumento / Caso",
                "Folio (A/R)",
                "Fecha",
                "Notario / Juzgado",
                "Acto o Juicio",
                "Otorgante 1 / Actor",
                "DPI 1",
                "Otorgante 2 / Demandado",
                "DPI 2",
                "Cuantía (Q)",
                "Timbre Notarial (Q)",
                "Destino Registral",
                "Alertas",
            ]
            st.dataframe(df_view, use_container_width=True, hide_index=True)

            c_down1, c_down2 = st.columns(2)
            with c_down1:
                csv_lote = dataframe_a_csv_seguro(df_view)
                st.download_button(
                    "📥 Descargar Tabla en Excel/CSV",
                    csv_lote,
                    "auditoria_lote.csv",
                    "text/csv",
                    type="primary",
                )

            with c_down2:
                if st.button("🔄 Analizar Nuevo Lote de Expedientes", use_container_width=True):
                    st.session_state["uploader_key"] += 1
                    st.session_state.update({"data": [], "analisis_completado": False})
                    st.rerun()

            if uploaded_files:
                st.write("---")
                st.subheader("👁️ Auditoría Visual y Cotejo de Fojas Originales")
                nombres = [f.name for f in uploaded_files]
                sel_doc = st.selectbox("Seleccione documento para cotejar:", nombres)
                if sel_doc:
                    for f in uploaded_files:
                        if f.name == sel_doc:
                            with st.container(height=600, border=True):
                                if f.name.lower().endswith(("png", "jpg", "jpeg")):
                                    st.image(f, caption=f.name, use_container_width=True)
                                elif f.name.lower().endswith("pdf"):
                                    try:
                                        doc = fitz.open(stream=f.getvalue(), filetype="pdf")
                                        for p_no in range(min(6, len(doc))):
                                            pix = doc.load_page(p_no).get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                                            st.image(
                                                pix.tobytes("png"),
                                                caption=f"Página {p_no+1}",
                                                use_container_width=True,
                                            )
                                    except Exception:
                                        st.warning("No se pudo previsualizar el PDF.")
                            break

            with st.expander("🛠️ Depuración de IA (Ver JSON Estructurado)"):
                all_raw = st.session_state.get("all_raw_responses", {})
                if all_raw:
                    sel_raw = st.selectbox("Documento:", list(all_raw.keys()))
                    st.code(all_raw.get(sel_raw, "Sin datos"), language="json")

    # =========================================================================
    # PESTAÑA 2: GENERADOR DE PLANTILLAS Y MINUTAS (FORMATO PROTOCOLO 25 LÍNEAS)
    # =========================================================================
    with tabs[1]:
        st.header("🏛️ Generador de Minutas y Memoriales (Formato Oficial Guatemala)")
        st.markdown(
            "Seleccione la rama del derecho y la plantilla. El sistema calibra **Hoja Oficio 8.5\" x 13\" con 25 líneas exactas** "
            "para Papel Sellado Especial de Protocolo (4 cm costura / 2 cm derecho, sin renglones en blanco) o formato de "
            "**Memorial Judicial** (Art. 61 CPCyM). Si ingresa DPIs o montos en números, el sistema los escribe automáticamente **en letras y cifras**."
        )

        ramas_disponibles = {
            "📜 Notarial (Protocolo)": "NOTARIAL",
            "⚖️ Civil y Mercantil": "CIVIL",
            "👨‍👩‍👧‍👦 Derecho de Familia": "FAMILIA",
            "🛡️ Derecho Penal": "PENAL",
        }

        rama_sel = st.radio(
            "📁 Seleccione la Rama Jurídica:",
            list(ramas_disponibles.keys()),
            horizontal=True,
        )
        clave_cat = ramas_disponibles[rama_sel]
        lista_5_plantillas = CATALOGO_PLANTILLAS[clave_cat]

        st.markdown(f"### 📋 Los 5 Instrumentos / Memoriales Más Comunes en `{rama_sel}`")
        nombres_pills = [
            f"#{i+1} {p['nombre'].split('(')[0].strip()[:35]}..."
            for i, p in enumerate(lista_5_plantillas)
        ]
        tabs_plantillas = st.tabs(nombres_pills)

        for i, (tab_pl, pl) in enumerate(zip(tabs_plantillas, lista_5_plantillas)):
            with tab_pl:
                st.markdown(f"#### 📄 {i+1}. {pl['nombre']}")
                st.info(
                    f"**🏛️ Soporte de Ley:** `{pl['soporte']}`  \n**🎯 Objeto Legal:** {pl['descripcion']}"
                )

                with st.form(f"form_generar_{pl['id']}"):
                    st.markdown("**✏️ Datos del Caso (DPI y montos numéricos se convierten a letras automáticamente):**")
                    col1, col2 = st.columns(2)
                    valores = {}

                    for j, campo in enumerate(pl["campos"]):
                        target_col = col1 if j % 2 == 0 else col2
                        nombre_etiqueta = campo.replace("_", " ").title()
                        placeholder = ""
                        default_v = ""
                        if campo == "notario" and notario_cfg:
                            default_v = notario_cfg
                        elif campo.startswith("dpi"):
                            placeholder = "Ej. 2456 78901 0101 (se convierte a letras)"
                        elif campo in ("lugar_y_fecha_letras", "ciudad_y_fecha"):
                            default_v = f"la ciudad de Guatemala, el {fecha_a_letras()}"
                        elif campo in ("hora_letras", "hora_cierre"):
                            placeholder = "Si queda vacío usa la hora actual en letras"
                        with target_col:
                            valores[campo] = st.text_input(
                                f"{nombre_etiqueta}:",
                                value=default_v,
                                placeholder=placeholder,
                                key=f"inp_{pl['id']}_{campo}",
                            )

                    btn_generar = st.form_submit_button(
                        f"🚀 Generar {pl['nombre'][:25]}... en Word",
                        type="primary",
                        use_container_width=True,
                    )

                if btn_generar:
                    texto_completo = _sustituir_campos_plantilla(
                        pl["redaccion"], valores, notario_cfg
                    )

                    if clave_cat == "NOTARIAL" and "Protocolo" in pl["soporte"]:
                        doc_bytes = generar_documento_protocolo_espanol(pl["nombre"], texto_completo)
                        nombre_doc = f"Protocolo_25Lineas_{pl['id']}.docx"
                    else:
                        juz_nombre = valores.get(
                            "juzgado",
                            valores.get(
                                "juzgado_familia",
                                valores.get("juzgado_penal", "SEÑOR JUEZ DE PRIMERA INSTANCIA"),
                            ),
                        )
                        doc_bytes = generar_documento_memorial_judicial(
                            pl["nombre"],
                            texto_completo,
                            juz_nombre,
                            notario_abogado=notario_cfg,
                            colegiado=colegiado_cfg,
                        )
                        nombre_doc = f"Memorial_{pl['id']}.docx"

                    st.success("✅ ¡Minuta generada conforme al formato legal de Guatemala!")
                    st.download_button(
                        label=f"📥 Descargar '{pl['nombre']}' (.docx)",
                        data=doc_bytes,
                        file_name=nombre_doc,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        type="primary",
                        use_container_width=True,
                        key=f"btn_dl_{pl['id']}",
                    )

                    with st.expander("👁️ Ver Redacción Previa"):
                        st.text(texto_completo)

    # =========================================================================
    # PESTAÑA 3: AVISOS NOTARIALES (CON DPI EN LETRAS), RENAP Y CALCULADORAS
    # =========================================================================
    with tabs[2]:
        st.header("📝 Generador de Avisos Notariales, RENAP y Calculadoras Fiscales GT")
        st.markdown(
            "Emite los avisos obligatorios de ley en Word (`.docx`) con **DPI escrito en letras y dígitos**, "
            "cantidades en letras y cifras, fechas actuales en español y aranceles vigentes."
        )

        registros = st.session_state.get("data", [])
        if not registros:
            hist_db = obtener_historial(bufete)
            if not hist_db.empty:
                registros = hist_db.to_dict("records")

        reg_sel = {}
        sel_idx = 0
        if registros:
            nombres_opc = [
                f"{r.get('numero_expediente', 'S/N')} - {r.get('tipo_proceso', 'Acto')} ({r.get('archivo_origen', '')})"
                for r in registros
            ]
            sel_idx = st.selectbox(
                "Seleccione instrumento analizado (precarga datos automáticamente):",
                range(len(nombres_opc)),
                format_func=lambda i: nombres_opc[i],
            )
            reg_sel = registros[sel_idx]
        else:
            st.info(
                "No hay documentos cargados aún; puede llenar los campos manualmente aquí abajo o procesar primero un PDF/imagen en la Pestaña 1."
            )

        notario_aviso = notario_cfg or str(reg_sel.get("juzgado") or "").strip()
        if not notario_aviso or notario_aviso == "No detectado":
            notario_aviso = st.text_input(
                "Nombre del Notario para los Avisos:",
                key="av_notario_manual",
                placeholder="Configúrelo también en la barra lateral izquierda",
            )

        st.write("---")
        c_av1, c_av2 = st.columns(2)

        with c_av1:
            st.subheader("🏛️ Avisos Obligatorios (AGP y DICABI)")

            with st.expander("📍 Aviso Notarial de Traspaso DICABI / Catastro (Art. 38 CDN)", expanded=True):
                st.caption(f"Plazo: {PLAZOS_NOTARIALES_GT['DICABI']}")
                num_esc_d = st.text_input("No. Escritura Pública:", str(reg_sel.get("numero_expediente", "1")), key=f"d_num_{sel_idx}")
                fecha_d = st.text_input("Fecha Escritura (DD/MM/AAAA):", str(reg_sel.get("fecha_resolucion") or datetime.date.today().strftime("%d/%m/%Y")), key=f"d_fec_{sel_idx}")
                vend_nom = st.text_input("Vendedor (Enajenante):", str(reg_sel.get("demandante", "")), key=f"d_vnd_{sel_idx}")
                dpi_v = st.text_input("DPI Vendedor (13 dígitos):", formatear_dpi_espaciado(reg_sel.get("dpi_demandante", "")), key=f"d_dpiv_{sel_idx}")
                nit_v = st.text_input("NIT Vendedor:", str(reg_sel.get("nit_demandante", "CF")), key=f"d_nitv_{sel_idx}")
                comp_nom = st.text_input("Comprador (Adquirente):", str(reg_sel.get("demandado", "")), key=f"d_cmp_{sel_idx}")
                dpi_c = st.text_input("DPI Comprador (13 dígitos):", formatear_dpi_espaciado(reg_sel.get("dpi_demandado", "")), key=f"d_dpic_{sel_idx}")
                nit_c = st.text_input("NIT Comprador:", str(reg_sel.get("nit_demandado", "CF")), key=f"d_nitc_{sel_idx}")
                monto_d = st.number_input("Precio Pactado (Q):", min_value=0.0, value=float(reg_sel.get("monto_litigio", 0.0) or 0.0), step=100.0, key=f"d_mnt_{sel_idx}")
                col_f1, col_f2, col_f3 = st.columns(3)
                finca = col_f1.text_input("Finca:", "1234", key=f"finca_{sel_idx}")
                folio = col_f2.text_input("Folio:", "25", key=f"folio_{sel_idx}")
                libro = col_f3.text_input("Libro:", "89", key=f"libro_{sel_idx}")
                depto_reg = st.text_input("Departamento Registro:", "Guatemala", key=f"d_dep_{sel_idx}")
                dir_inm = st.text_input("Dirección del Inmueble:", "", placeholder="Ej. 5a calle 12-40 zona 10, Guatemala", key=f"d_dir_{sel_idx}")
                mat_fisc = st.text_input("Matrícula Fiscal (si consta):", "En trámite", key=f"d_mat_{sel_idx}")

                datos_dicabi = {
                    "notario": notario_aviso,
                    "colegiado": colegiado_cfg,
                    "clave_notario": clave_cfg,
                    "numero_instrumento": num_esc_d,
                    "fecha": fecha_d,
                    "tipo_contrato": reg_sel.get("tipo_proceso", "Compraventa de Bien Inmueble"),
                    "vendedor": vend_nom,
                    "dpi_vendedor": dpi_v,
                    "nit_vendedor": nit_v,
                    "comprador": comp_nom,
                    "dpi_comprador": dpi_c,
                    "nit_comprador": nit_c,
                    "monto": monto_d,
                    "finca": finca,
                    "folio": folio,
                    "libro": libro,
                    "departamento_registro": depto_reg,
                    "direccion_inmueble": dir_inm,
                    "matricula_fiscal": mat_fisc,
                }
                doc_bytes_dicabi = generar_aviso_dicabi(datos_dicabi)
                st.download_button(
                    "📄 Descargar Aviso DICABI con DPI en Letras (.docx)",
                    doc_bytes_dicabi,
                    f"Aviso_DICABI_Escritura_{num_esc_d or '1'}.docx",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    type="primary",
                    use_container_width=True,
                )

            with st.expander("📜 Razón Testimonio Especial AGP (Art. 37 lit. a CDN)"):
                st.caption(f"Plazo: {PLAZOS_NOTARIALES_GT['TESTIMONIO_ESPECIAL']}")
                fol_ini = st.text_input("Folio Inicial:", str(reg_sel.get("folio_protocolo", "1")), key=f"fini_{sel_idx}")
                fol_fin = st.text_input("Folio Final:", "2", key=f"ffin_{sel_idx}")
                hojas_te = st.number_input("Cantidad de hojas del Testimonio (Q.0.50 timbre/hoja):", min_value=1, value=2, step=1, key=f"hojas_te_{sel_idx}")

                datos_agp = {
                    "notario": notario_aviso,
                    "colegiado": colegiado_cfg,
                    "clave_notario": clave_cfg,
                    "numero_instrumento": num_esc_d,
                    "fecha": fecha_d,
                    "tipo_contrato": reg_sel.get("tipo_proceso", "Instrumento Público"),
                    "otorgantes": f"{vend_nom} y {comp_nom}",
                    "dpi_vendedor": dpi_v,
                    "dpi_comprador": dpi_c,
                    "folio_inicial": fol_ini,
                    "folio_final": fol_fin,
                    "hojas_testimonio": hojas_te,
                    "monto": monto_d,
                    "timbre_notarial": reg_sel.get("timbre_notarial", 0.0),
                }
                doc_bytes_agp = generar_aviso_agp_testimonio(datos_agp)
                st.download_button(
                    "📄 Descargar Entrega Testimonio Especial (.docx)",
                    doc_bytes_agp,
                    f"Testimonio_Especial_{num_esc_d or '1'}.docx",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )

            with st.expander("💒 Aviso Circunstanciado Matrimonio Civil RENAP (Art. 102 CC)"):
                st.caption(f"Plazo: {PLAZOS_NOTARIALES_GT['MATRIMONIO_RENAP']}")
                mc1, mc2 = st.text_input("Contrayente 1 (Varón):", key="renap_c1"), st.text_input("DPI Contrayente 1:", key="renap_d1")
                mc3, mc4 = st.text_input("Contrayente 2 (Mujer):", key="renap_c2"), st.text_input("DPI Contrayente 2:", key="renap_d2")
                reg_ec = st.selectbox(
                    "Régimen Económico:",
                    ["Comunidad de Gananciales", "Separación Absoluta de Bienes", "Comunidad Absoluta de Bienes"],
                    key="renap_reg",
                )
                muni_cel = st.text_input("Municipio/Depto celebración:", "Guatemala, Guatemala", key="renap_mun")
                fecha_m = st.date_input("Fecha del matrimonio:", value=datetime.date.today(), key="renap_fec")
                doc_renap = generar_aviso_matrimonio_renap(
                    {
                        "notario": notario_aviso,
                        "colegiado": colegiado_cfg,
                        "clave_notario": clave_cfg,
                        "nombre_contrayente_1": mc1 or "___",
                        "dpi_contrayente_1": mc2,
                        "nombre_contrayente_2": mc3 or "___",
                        "dpi_contrayente_2": mc4,
                        "regimen_economico": reg_ec,
                        "municipio_celebracion": muni_cel,
                        "fecha_matrimonio": fecha_m,
                    }
                )
                st.download_button(
                    "📄 Descargar Aviso Matrimonio RENAP (.docx)",
                    doc_renap,
                    "Aviso_Matrimonio_RENAP.docx",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )

        with c_av2:
            st.subheader("📊 Ficha Ejecutiva, Trimestral y Calculadoras")

            if reg_sel:
                with st.expander("📑 Dictamen y Resumen Ejecutivo para el Cliente / Bufete", expanded=True):
                    st.write(f"**Resumen Registrado:** {reg_sel.get('resumen_forense', 'Acto notarial formal.')}")
                    doc_bytes_ficha = generar_resumen_juridico_ejecutivo(reg_sel)
                    st.download_button(
                        "📥 Descargar Ficha Ejecutiva en Word (.docx)",
                        doc_bytes_ficha,
                        f"Dictamen_Ejecutivo_{reg_sel.get('numero_expediente', 'caso')}.docx",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        type="primary",
                        use_container_width=True,
                    )

            with st.expander("🗓️ Aviso Notarial Trimestral AGP (Art. 37 lit. c CDN)", expanded=True):
                st.caption(f"Plazo: {PLAZOS_NOTARIALES_GT['AVISO_TRIMESTRAL']}")
                trim_def, anio_def = trimestre_actual_info()
                opciones_trim = [
                    "Primer Trimestre (enero a marzo)",
                    "Segundo Trimestre (abril a junio)",
                    "Tercer Trimestre (julio a septiembre)",
                    "Cuarto Trimestre (octubre a diciembre)",
                ]
                idx_trim = opciones_trim.index(trim_def) if trim_def in opciones_trim else 0
                trimestre = st.selectbox("Trimestre:", opciones_trim, index=idx_trim)
                ano_t = st.text_input("Año Fiscal:", str(anio_def), key="trim_anio")

                # Calcular rangos reales desde registros notariales de Bóveda
                nums_proto = [
                    int(re.sub(r"\D", "", str(r.get("numero_expediente", ""))))
                    for r in registros
                    if re.sub(r"\D", "", str(r.get("numero_expediente", ""))).isdigit()
                    and "PROTOCOLO" in str(r.get("categoria_documental", ""))
                ]
                p_num_def = str(min(nums_proto)) if nums_proto else "1"
                u_num_def = str(max(nums_proto)) if nums_proto else "1"
                tot_def = str(len(nums_proto)) if nums_proto else "0"

                t_c1, t_c2, t_c3 = st.columns(3)
                p_num_in = t_c1.text_input("Primer Instrumento:", p_num_def, key="trim_pnum")
                u_num_in = t_c2.text_input("Último Instrumento:", u_num_def, key="trim_unum")
                tot_in = t_c3.text_input("Total Autorizados:", tot_def, key="trim_tot")
                canc_in = st.text_input("Instrumentos Cancelados:", "Ninguno", key="trim_canc")
                fec_ult = st.text_input("Fecha Último Instrumento:", datetime.date.today().strftime("%d/%m/%Y"), key="trim_fult")

                datos_trim = {
                    "trimestre": trimestre,
                    "ano": ano_t,
                    "notario": notario_aviso,
                    "colegiado": colegiado_cfg,
                    "clave_notario": clave_cfg,
                    "primer_num": p_num_in,
                    "ultimo_num": u_num_in,
                    "total_autorizados": tot_in,
                    "cancelados": canc_in,
                    "fecha_ultimo": fec_ult,
                }
                doc_bytes_trim = generar_aviso_trimestral_agp(datos_trim)
                st.download_button(
                    "📄 Descargar Aviso Trimestral (.docx)",
                    doc_bytes_trim,
                    f"Aviso_Trimestral_{ano_t}.docx",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                )

            with st.expander("🧮 Calculadora Notarial de Timbres y Aranceles (Guatemala)", expanded=True):
                op_calc = st.selectbox(
                    "Tipo de Acto o Contrato:",
                    [
                        ("SEGUNDA_COMPRAVENTA", "Segunda o Subsiguiente Compraventa Inmueble (3% Timbre Fiscal)"),
                        ("PRIMERA_VENTA_IVA", "Primera Venta Inmueble / Factura Desarrolladora (12% IVA)"),
                        ("PROMESA_COMPRAVENTA", "Promesa de Compraventa de Inmueble (Q.50 Fiscal fijo)"),
                        ("MANDATO_GENERAL", "Mandato General (Q.10 Fiscal + Q.10 Notarial)"),
                        ("MANDATO_ESPECIAL", "Mandato Especial (Q.2 Fiscal + Q.10 Notarial)"),
                        ("CARTA_PAGO", "Carta Total de Pago / Liberación Hipoteca (Exenta Fiscal)"),
                    ],
                    format_func=lambda x: x[1],
                )
                val_calc = st.number_input("Monto / Precio del Contrato (Q):", min_value=0.0, value=100000.0, step=1000.0, key="calc_monto")
                hojas_calc = st.number_input("Cantidad de Hojas del Testimonio / Memorial:", min_value=1, value=3, step=1, key="calc_hojas")
                res_imp = calcular_impuestos_testimonio_gt(val_calc, op_calc[0], hojas_calc)

                m_c1, m_c2 = st.columns(2)
                m_c1.metric("Impuesto 1er Testimonio", f"Q {res_imp['impuesto_primer_testimonio']:,.2f}")
                m_c2.metric("Timbre Notarial (Test. Esp.)", f"Q {res_imp['timbre_notarial_especial']:,.2f}")
                m_c3, m_c4 = st.columns(2)
                m_c3.metric("Timbre Fiscal Razón (Q0.50/hoja)", f"Q {res_imp['timbre_fiscal_razon_especial']:,.2f}")
                m_c4.metric("Si es Memorial: Timbre Forense", f"Q {res_imp['timbre_forense_por_hojas']:,.2f}")
                st.caption(f"**Fiscal:** {res_imp['concepto_fiscal']}  \n**Notarial:** {res_imp['detalle_timbre_notarial']}")

            with st.expander("🔤 Conversor Rápido DPI / Monto / Fecha a Letras"):
                dpi_test = st.text_input("DPI (13 dígitos):", placeholder="2456 78901 0101", key="conv_dpi")
                if dpi_test.strip():
                    ok_cui, msg_cui = validar_dpi(dpi_test)
                    if ok_cui:
                        st.success(dpi_a_letras(dpi_test, incluir_digitos=True))
                    else:
                        st.warning(msg_cui)

    # =========================================================================
    # PESTAÑA 4: ÍNDICE OFICIAL DE PROTOCOLO (ART. 92 CÓDIGO DE NOTARIADO)
    # =========================================================================
    with tabs[3]:
        st.header("📜 Generador Oficial del Índice de Protocolo Notarial")
        st.markdown(
            "Cumple con los **Artículos 15 y 92 del Código de Notariado de Guatemala**. "
            "Ordena numéricamente sus escrituras e incluye las 5 columnas reglamentarias, razón de cierre "
            "y nota de **Timbre Fiscal de Q. 0.50 por hoja** (Art. 5 num. 6 Dto. 37-92)."
        )

        historial = obtener_historial(bufete)
        if not historial.empty:
            notariales = historial[historial["categoria_documental"] == "PROTOCOLO_NOTARIAL"].copy()
            if notariales.empty:
                notariales = historial[historial["folio_protocolo"] != "N/A"].copy()

            if not notariales.empty:
                notariales["_ord"] = notariales["numero_expediente"].map(_clave_orden_instrumento)
                notariales = notariales.sort_values(by="_ord", ascending=True).drop(columns=["_ord"])

                tabla_indice = pd.DataFrame()
                tabla_indice["No. Orden"] = notariales["numero_expediente"]
                tabla_indice["Lugar y Fecha"] = "Guatemala, " + notariales["fecha_resolucion"].astype(str)
                tabla_indice["Otorgantes"] = (
                    notariales["demandante"].astype(str) + " / " + notariales["demandado"].astype(str)
                )
                tabla_indice["Objeto del Instrumento"] = notariales["tipo_proceso"]
                tabla_indice["Folio (A/R)"] = notariales["folio_protocolo"]

                st.dataframe(tabla_indice, use_container_width=True, hide_index=True)

                idx_col1, idx_col2 = st.columns(2)
                with idx_col1:
                    indice_docx = generar_indice_protocolo_docx(
                        notariales.to_dict("records"),
                        anio=datetime.date.today().year,
                        notario=notario_aviso,
                        colegiado=colegiado_cfg,
                        clave_notario=clave_cfg,
                    )
                    st.download_button(
                        "📄 Descargar Índice Oficial Art. 92 en Word (.docx)",
                        indice_docx,
                        f"Indice_Protocolo_Oficial_{datetime.date.today().year}.docx",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        type="primary",
                        use_container_width=True,
                    )
                with idx_col2:
                    csv_indice = dataframe_a_csv_seguro(tabla_indice)
                    st.download_button(
                        "📥 Descargar Índice en CSV / Excel",
                        csv_indice,
                        "indice_protocolo_oficial.csv",
                        "text/csv",
                        use_container_width=True,
                    )
            else:
                st.info("Aún no ha procesado escrituras de protocolo notarial en esta bóveda.")
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
                "📥 Exportar Toda la Bóveda a Excel/CSV",
                dataframe_a_csv_seguro(hist),
                "boveda_completa_despacho.csv",
                "text/csv",
            )
        else:
            st.info("No hay registros almacenados todavía.")

    # =========================================================================
    # PESTAÑA 6: ADMINISTRACIÓN SAAS Y GESTIÓN MULTI-EMPRESA
    # =========================================================================
    if es_admin:
        with tabs[5]:
            es_super_admin = abogado_activo == "admin"
            st.header("⚙️ Gobernanza, Control de Accesos y Aislamiento de Bufetes")
            if es_super_admin:
                st.caption(
                    "👑 **Modo Super-Admin Maestro (`admin`):** Cada empresa/bufete creado queda aislado. "
                    "Si ingresa un nombre repetido (ej. `A`), el sistema asignará automáticamente `A1`, `A2`, etc."
                )
            else:
                st.caption(f"🏢 Administración aislada de **{bufete}**.")

            col_admin_a, col_admin_b = st.columns([1, 1.3])

            with col_admin_a:
                st.subheader("➕ Alta de Empresa o Colaborador")
                modo_alta = "👤 Colaborador en este Bufete"
                emp_existente_sel = bufete
                if es_super_admin:
                    modo_alta = st.radio(
                        "Tipo de Registro:",
                        ["🏢 Nueva Empresa / Bufete Independiente", "👤 Colaborador en Bufete Existente"],
                        horizontal=True,
                        key="lex_modo_alta",
                    )
                    if modo_alta == "👤 Colaborador en Bufete Existente":
                        empresas_disp = obtener_empresas_activas() or [bufete]
                        emp_existente_sel = st.selectbox(
                            "Bufete / Empresa Destino:",
                            empresas_disp,
                            key="lex_emp_destino",
                        )

                with st.form("form_crear_usuario"):
                    emp_nueva_in = ""
                    if es_super_admin and modo_alta.startswith("🏢"):
                        emp_nueva_in = st.text_input(
                            "Nombre de la Nueva Empresa / Bufete:",
                            placeholder="Ej. Bufete A (si existe creará A1)",
                        )
                    nuevo_id = st.text_input("ID o Correo de Usuario:")
                    nuevo_pass = st.text_input("Contraseña Temporal (mín. 6 caracteres):", type="password")
                    roles_opc = (
                        ["Administrador", "Abogado Asociado", "Secretaria / Procurador"]
                        if (es_super_admin and modo_alta.startswith("🏢"))
                        else ["Abogado Asociado", "Secretaria / Procurador", "Administrador"]
                    )
                    nuevo_rol = st.selectbox("Nivel de Acceso / Rol:", roles_opc)

                    if st.form_submit_button("Crear Credencial de Acceso", type="primary", use_container_width=True):
                        if not nuevo_id.strip() or len(nuevo_pass.strip()) < 6:
                            st.warning("⚠️ Ingrese usuario válido y contraseña de al menos 6 caracteres.")
                        elif es_super_admin and modo_alta.startswith("🏢"):
                            if not emp_nueva_in.strip():
                                st.warning("⚠️ Escriba el nombre de la nueva empresa o bufete.")
                            else:
                                ok, emp_final, msg = registrar_nueva_empresa_usuario(
                                    nuevo_id.strip(), nuevo_pass.strip(), emp_nueva_in.strip(), nuevo_rol
                                )
                                if ok:
                                    st.success(f"✅ {msg} Usuario: `{nuevo_id.strip()}` (`{emp_final}`).")
                                    time.sleep(1.2)
                                    st.rerun()
                                else:
                                    st.error(f"❌ {msg}")
                        else:
                            if registrar_usuario(nuevo_id.strip(), nuevo_pass.strip(), emp_existente_sel, nuevo_rol):
                                st.success(f"✅ Usuario '{nuevo_id.strip()}' creado en '{emp_existente_sel}'.")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ Error: Ese usuario ya se encuentra registrado en el sistema.")

            with col_admin_b:
                st.subheader("📋 Nómina de Usuarios Activos")
                df_usuarios = obtener_todos_usuarios() if es_super_admin else obtener_usuarios_empresa(bufete)
                if not df_usuarios.empty:
                    if es_super_admin and "empresa" in df_usuarios.columns:
                        st.caption(f"Bufetes/Empresas aisladas activas: **{df_usuarios['empresa'].nunique()}**")
                    st.dataframe(df_usuarios, use_container_width=True, hide_index=True)

                    if es_super_admin and "empresa" in df_usuarios.columns:
                        opciones_u = list(zip(df_usuarios["usuario"].tolist(), df_usuarios["empresa"].tolist()))
                        fmt_u = lambda par: f"{par[0]}  [{par[1]}]"
                    else:
                        opciones_u = [(u, bufete) for u in df_usuarios["usuario"].tolist()]
                        fmt_u = lambda par: par[0]

                    st.write("---")
                    st.subheader("🔑 Soporte Técnico: Restablecer Contraseña Olvidada")
                    with st.form("form_reset_pass"):
                        sel_reset = st.selectbox("Seleccione usuario:", opciones_u, format_func=fmt_u)
                        p_nueva = st.text_input("Nueva Contraseña Temporal (mín. 6 caracteres):", type="password")

                        if st.form_submit_button("Forzar Cambio de Contraseña", type="primary", use_container_width=True):
                            if len(p_nueva.strip()) < 6:
                                st.warning("⚠️ La contraseña temporal debe tener al menos 6 caracteres.")
                            else:
                                u_r, emp_r = sel_reset
                                actualizar_password(u_r, p_nueva.strip(), empresa=emp_r)
                                st.success(f"✅ Contraseña de '{u_r}' ({emp_r}) restablecida con éxito.")

                    st.write("---")
                    st.subheader("🚫 Revocar Acceso / Eliminar Usuario")
                    with st.form("form_eliminar_u"):
                        sel_del = st.selectbox("Seleccione usuario a dar de baja:", opciones_u, format_func=fmt_u)
                        u_eliminar, emp_eliminar = sel_del
                        if u_eliminar == "admin":
                            st.caption("🔒 El usuario Maestro 'admin' está protegido y no puede ser eliminado.")
                        elif u_eliminar == abogado_activo:
                            st.caption("🔒 No puede revocar su propia sesión activa.")

                        if st.form_submit_button("Eliminar Acceso Permanentemente", use_container_width=True):
                            if u_eliminar == "admin" or u_eliminar == abogado_activo:
                                st.error("❌ Acción denegada: No puede eliminar al Administrador Maestro ni su usuario activo.")
                            else:
                                eliminar_usuario(u_eliminar, empresa=emp_eliminar, actor=abogado_activo)
                                st.warning(f"⚠️ Acceso de '{u_eliminar}' ({emp_eliminar}) revocado de forma permanente.")
                                time.sleep(1)
                                st.rerun()
                else:
                    st.info("No hay colaboradores registrados todavía.")


if __name__ == "__main__":
    if not st.session_state["auth"]:
        login()
    else:
        main()
