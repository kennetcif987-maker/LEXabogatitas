import os
import sqlite3
import hashlib
import pandas as pd
import streamlit as st

try:
    import psycopg2
except ImportError:
    psycopg2 = None


def _obtener_database_url():
    """Devuelve DATABASE_URL desde Streamlit Secrets o variables de entorno si existe."""
    try:
        if "DATABASE_URL" in st.secrets and str(st.secrets["DATABASE_URL"]).strip():
            return str(st.secrets["DATABASE_URL"]).strip()
    except Exception:
        pass
    env_url = os.environ.get("DATABASE_URL", "").strip()
    return env_url or None


def _es_postgres():
    return bool(_obtener_database_url() and psycopg2 is not None)


def _ph():
    """Placeholder de parámetros según motor activo."""
    return "%s" if _es_postgres() else "?"


def conectar():
    """Conecta a PostgreSQL (Neon) si DATABASE_URL está configurada; si no, usa SQLite local."""
    db_url = _obtener_database_url()
    if db_url and psycopg2 is not None:
        return psycopg2.connect(db_url)
    return sqlite3.connect("lex_ia_360.db")


def encriptar_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def inicializar_db():
    conexion = conectar()
    cursor = conexion.cursor()
    es_pg = _es_postgres()

    id_col = "SERIAL PRIMARY KEY" if es_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
    real_col = "DOUBLE PRECISION" if es_pg else "REAL"

    cursor.execute(f'''CREATE TABLE IF NOT EXISTS expedientes (
        id {id_col},
        bufete_propietario TEXT,
        usuario TEXT,
        archivo_origen TEXT,
        categoria_documental TEXT DEFAULT 'EXPEDIENTE_JUDICIAL',
        numero_expediente TEXT,
        folio_protocolo TEXT DEFAULT 'N/A',
        juzgado TEXT,
        materia TEXT,
        tipo_proceso TEXT,
        demandante TEXT,
        dpi_demandante TEXT,
        nit_demandante TEXT,
        demandado TEXT,
        dpi_demandado TEXT,
        nit_demandado TEXT,
        monto_litigio {real_col} DEFAULT 0.0,
        timbre_notarial {real_col} DEFAULT 0.0,
        timbre_fiscal {real_col} DEFAULT 0.0,
        registro_destino TEXT DEFAULT 'Archivo General de Protocolos',
        fecha_resolucion TEXT,
        fecha_audiencia TEXT,
        plazo_procesal TEXT,
        semaforo TEXT DEFAULT '🟢 TRÁMITE',
        anomalia TEXT,
        resumen_forense TEXT,
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    columnas_nuevas = [
        ("categoria_documental", "TEXT DEFAULT 'EXPEDIENTE_JUDICIAL'"),
        ("folio_protocolo", "TEXT DEFAULT 'N/A'"),
        ("timbre_notarial", f"{real_col} DEFAULT 0.0"),
        ("timbre_fiscal", f"{real_col} DEFAULT 0.0"),
        ("registro_destino", "TEXT DEFAULT 'Archivo General de Protocolos'"),
        ("semaforo", "TEXT DEFAULT '🟢 TRÁMITE'"),
        ("resumen_forense", "TEXT"),
    ]
    if es_pg:
        for col_nom, col_tipo in columnas_nuevas:
            cursor.execute(
                f"ALTER TABLE expedientes ADD COLUMN IF NOT EXISTS {col_nom} {col_tipo}"
            )
    else:
        cursor.execute("PRAGMA table_info(expedientes)")
        columnas_actuales = [row[1] for row in cursor.fetchall()]
        for col_nom, col_tipo in columnas_nuevas:
            if col_nom not in columnas_actuales:
                try:
                    cursor.execute(
                        f"ALTER TABLE expedientes ADD COLUMN {col_nom} {col_tipo}"
                    )
                except Exception:
                    pass

    cursor.execute(f'''CREATE TABLE IF NOT EXISTS usuarios (
        id {id_col},
        usuario TEXT UNIQUE,
        password TEXT,
        empresa TEXT,
        rol TEXT
    )''')

    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        pass_admin = encriptar_password("admin123")
        p = _ph()
        cursor.execute(
            f"INSERT INTO usuarios (usuario, password, empresa, rol) VALUES ({p}, {p}, {p}, {p})",
            ("admin", pass_admin, "Firma Legal Principal", "Administrador"),
        )

    conexion.commit()
    cursor.close()
    conexion.close()


def autenticar_usuario(usuario, password):
    conexion = conectar()
    cursor = conexion.cursor()
    p = _ph()
    cursor.execute(
        f"SELECT usuario, empresa, rol FROM usuarios WHERE usuario = {p} AND password = {p}",
        (usuario, encriptar_password(password)),
    )
    res = cursor.fetchone()
    cursor.close()
    conexion.close()
    return {"usuario": res[0], "empresa": res[1], "rol": res[2]} if res else None


def registrar_usuario(u, p_raw, e, r):
    conexion = conectar()
    cursor = conexion.cursor()
    p = _ph()
    err_types = (sqlite3.IntegrityError,) + ((psycopg2.IntegrityError,) if psycopg2 else ())
    try:
        cursor.execute(
            f"INSERT INTO usuarios (usuario, password, empresa, rol) VALUES ({p}, {p}, {p}, {p})",
            (u, encriptar_password(p_raw), e, r),
        )
        conexion.commit()
        return True
    except err_types:
        conexion.rollback()
        return False
    finally:
        cursor.close()
        conexion.close()


def actualizar_password(usuario, nueva_p):
    conexion = conectar()
    cursor = conexion.cursor()
    p = _ph()
    cursor.execute(
        f"UPDATE usuarios SET password = {p} WHERE usuario = {p}",
        (encriptar_password(nueva_p), usuario),
    )
    conexion.commit()
    cursor.close()
    conexion.close()


def obtener_usuarios_empresa(empresa):
    conexion = conectar()
    cursor = conexion.cursor()
    p = _ph()
    cursor.execute(
        f"SELECT usuario, rol FROM usuarios WHERE empresa = {p}",
        (empresa,),
    )
    columnas = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(cursor.fetchall(), columns=columnas)
    cursor.close()
    conexion.close()
    return df


def eliminar_usuario(usuario):
    conexion = conectar()
    cursor = conexion.cursor()
    p = _ph()
    cursor.execute(
        f"DELETE FROM usuarios WHERE usuario = {p} AND usuario != 'admin'",
        (usuario,),
    )
    conexion.commit()
    cursor.close()
    conexion.close()


def guardar_expedientes(lista_datos, bufete, abogado_activo):
    conexion = conectar()
    cursor = conexion.cursor()
    p = _ph()
    guardadas = 0
    omitidas = 0

    for d in lista_datos:
        exp_num = str(d.get("numero_expediente", "No detectado")).strip()
        fol_num = str(d.get("folio_protocolo", "N/A")).strip()

        cursor.execute(
            f"""
            SELECT 1 FROM expedientes
            WHERE bufete_propietario = {p}
            AND numero_expediente = {p}
            AND folio_protocolo = {p}
            AND numero_expediente NOT IN ('No detectado', 'N/A', '')
            """,
            (bufete, exp_num, fol_num),
        )

        if cursor.fetchone():
            omitidas += 1
            continue

        placeholders = ", ".join([p] * 25)
        cursor.execute(
            f"""INSERT INTO expedientes (
                bufete_propietario, usuario, archivo_origen, categoria_documental, numero_expediente,
                folio_protocolo, juzgado, materia, tipo_proceso, demandante, dpi_demandante,
                nit_demandante, demandado, dpi_demandado, nit_demandado, monto_litigio,
                timbre_notarial, timbre_fiscal, registro_destino, fecha_resolucion,
                fecha_audiencia, plazo_procesal, semaforo, anomalia, resumen_forense)
                VALUES ({placeholders})""",
            (
                bufete,
                abogado_activo,
                d.get("archivo_origen"),
                d.get("categoria_documental", "EXPEDIENTE_JUDICIAL"),
                exp_num,
                fol_num,
                d.get("juzgado", "No detectado"),
                d.get("materia", "Civil"),
                d.get("tipo_proceso", "No detectado"),
                d.get("demandante", "Desconocido"),
                d.get("dpi_demandante", "No detectado"),
                d.get("nit_demandante", "No detectado"),
                d.get("demandado", "Desconocido"),
                d.get("dpi_demandado", "No detectado"),
                d.get("nit_demandado", "No detectado"),
                float(d.get("monto_litigio", 0.0)),
                float(d.get("timbre_notarial", 0.0)),
                float(d.get("timbre_fiscal", 0.0)),
                d.get("registro_destino", "Archivo General de Protocolos"),
                d.get("fecha_resolucion", "N/A"),
                d.get("fecha_audiencia", "N/A"),
                d.get("plazo_procesal", "N/A"),
                d.get("semaforo", "🟢 TRÁMITE"),
                d.get("anomalia", "ninguna"),
                d.get("resumen_forense", ""),
            ),
        )
        guardadas += 1

    conexion.commit()
    cursor.close()
    conexion.close()
    return guardadas, omitidas


def obtener_historial(bufete):
    conexion = conectar()
    cursor = conexion.cursor()
    p = _ph()
    cursor.execute(
        f"SELECT * FROM expedientes WHERE bufete_propietario = {p} ORDER BY fecha_registro DESC",
        (bufete,),
    )
    columnas = [desc[0] for desc in cursor.description]
    df = pd.DataFrame(cursor.fetchall(), columns=columnas)
    cursor.close()
    conexion.close()
    return df
