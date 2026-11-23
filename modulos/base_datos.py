import hashlib
import hmac
import os
import secrets
import sqlite3
from typing import Optional, Tuple

import pandas as pd
import streamlit as st

try:
    import psycopg2
except ImportError:
    psycopg2 = None


def _obtener_database_url() -> Optional[str]:
    """Devuelve DATABASE_URL desde Streamlit Secrets o variables de entorno si existe."""
    try:
        if "DATABASE_URL" in st.secrets and str(st.secrets["DATABASE_URL"]).strip():
            return str(st.secrets["DATABASE_URL"]).strip()
    except Exception:
        pass
    env_url = os.environ.get("DATABASE_URL", "").strip()
    return env_url or None


def _es_postgres() -> bool:
    return bool(_obtener_database_url() and psycopg2 is not None)


def _ph() -> str:
    """Placeholder de parámetros según motor activo."""
    return "%s" if _es_postgres() else "?"


def conectar():
    """Conecta a PostgreSQL (Neon) si DATABASE_URL está configurada; si no, usa SQLite local."""
    db_url = _obtener_database_url()
    if db_url and psycopg2 is not None:
        return psycopg2.connect(db_url, connect_timeout=10)
    return sqlite3.connect("lex_ia_360.db")


def encriptar_password(password: str) -> str:
    """Hash seguro con salt usando PBKDF2-HMAC-SHA256."""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000).hex()
    return f"pbkdf2${salt}${dk}"


def _verificar_password(password: str, stored_hash: str) -> Tuple[bool, bool]:
    """Verifica contraseña soportando PBKDF2 moderno y SHA-256 legacy. Retorna (valida, necesita_rehash)."""
    if not stored_hash:
        return False, False
    if stored_hash.startswith("pbkdf2$"):
        partes = stored_hash.split("$")
        if len(partes) != 3:
            return False, False
        _, salt, expected_dk = partes
        calc_dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000).hex()
        return hmac.compare_digest(calc_dk, expected_dk), False
    legacy_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
    return hmac.compare_digest(legacy_hash, stored_hash), True


@st.cache_resource
def inicializar_db_una_vez() -> bool:
    """Inicializa esquema e índices una sola vez por ciclo de vida del servidor."""
    inicializar_db()
    return True


def inicializar_db():
    conexion = conectar()
    cursor = conexion.cursor()
    es_pg = _es_postgres()

    id_col = "SERIAL PRIMARY KEY" if es_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
    real_col = "DOUBLE PRECISION" if es_pg else "REAL"

    try:
        cursor.execute(f"""CREATE TABLE IF NOT EXISTS expedientes (
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
        )""")

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
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_exp_bufete ON expedientes (bufete_propietario, fecha_registro DESC)"
            )
        else:
            cursor.execute("PRAGMA table_info(expedientes)")
            columnas_actuales = [row[1] for row in cursor.fetchall()]
            for col_nom, col_tipo in columnas_nuevas:
                if col_nom not in columnas_actuales:
                    try:
                        cursor.execute(f"ALTER TABLE expedientes ADD COLUMN {col_nom} {col_tipo}")
                    except Exception:
                        pass

        cursor.execute(f"""CREATE TABLE IF NOT EXISTS usuarios (
            id {id_col},
            usuario TEXT UNIQUE,
            password TEXT,
            empresa TEXT,
            rol TEXT
        )""")

        cursor.execute("SELECT COUNT(*) FROM usuarios")
        if cursor.fetchone()[0] == 0:
            pass_admin = encriptar_password("admin123")
            p = _ph()
            cursor.execute(
                f"INSERT INTO usuarios (usuario, password, empresa, rol) VALUES ({p}, {p}, {p}, {p})",
                ("admin", pass_admin, "Firma Legal Principal", "Administrador"),
            )

        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()


def autenticar_usuario(usuario, password):
    conexion = conectar()
    cursor = conexion.cursor()
    p = _ph()
    try:
        cursor.execute(
            f"SELECT id, usuario, password, empresa, rol FROM usuarios WHERE usuario = {p}",
            (usuario,),
        )
        res = cursor.fetchone()
        if not res:
            return None
        uid, usr, stored_hash, empresa, rol = res
        valida, necesita_rehash = _verificar_password(password, stored_hash)
        if not valida:
            return None
        if necesita_rehash:
            cursor.execute(
                f"UPDATE usuarios SET password = {p} WHERE id = {p}",
                (encriptar_password(password), uid),
            )
            conexion.commit()
        return {"usuario": usr, "empresa": empresa, "rol": rol}
    finally:
        cursor.close()
        conexion.close()


def _listar_empresas_en_cursor(cursor) -> list:
    empresas = set()
    cursor.execute("SELECT DISTINCT empresa FROM usuarios WHERE empresa IS NOT NULL AND TRIM(empresa) != ''")
    for (emp,) in cursor.fetchall():
        empresas.add(str(emp).strip())
    try:
        cursor.execute(
            "SELECT DISTINCT bufete_propietario FROM expedientes WHERE bufete_propietario IS NOT NULL AND TRIM(bufete_propietario) != ''"
        )
        for (emp,) in cursor.fetchall():
            empresas.add(str(emp).strip())
    except Exception:
        pass
    return sorted(empresas, key=lambda s: s.lower())


def obtener_empresas_activas() -> list:
    """Lista todas las empresas/bufetes existentes (para Super-Admin maestro)."""
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        return _listar_empresas_en_cursor(cursor)
    finally:
        cursor.close()
        conexion.close()


def resolver_nombre_empresa_unico(nombre_deseado: str, cursor=None) -> str:
    """
    Garantiza nombres de empresa/bufete 100% únicos sin distinción de mayúsculas.
    Si 'A' ya existe, asigna 'A1'; si 'A1' existe, 'A2', etc.
    """
    base = " ".join(str(nombre_deseado or "").split())
    if not base:
        base = "Despacho"

    cerrar = False
    conn = None
    if cursor is None:
        conn = conectar()
        cursor = conn.cursor()
        cerrar = True

    try:
        existentes = {e.strip().lower() for e in _listar_empresas_en_cursor(cursor)}
        if base.lower() not in existentes:
            return base
        i = 1
        while f"{base}{i}".lower() in existentes:
            i += 1
        return f"{base}{i}"
    finally:
        if cerrar and conn is not None:
            cursor.close()
            conn.close()


def registrar_nueva_empresa_usuario(u: str, p_raw: str, empresa_deseada: str, r: str) -> Tuple[bool, str, str]:
    """
    Crea una nueva empresa/bufete completamente aislada garantizando nombre único (A -> A1)
    y registra su usuario inicial dentro de la misma transacción.
    Retorna (exito, empresa_final_asignada, mensaje).
    """
    u_limpio = str(u or "").strip()
    emp_limpia = " ".join(str(empresa_deseada or "").split())
    if not u_limpio or not p_raw or not emp_limpia:
        return False, "", "Complete usuario, contraseña y nombre de empresa/bufete."

    conexion = conectar()
    cursor = conexion.cursor()
    p = _ph()
    err_types = (sqlite3.IntegrityError,) + ((psycopg2.IntegrityError,) if psycopg2 else ())
    try:
        empresa_final = resolver_nombre_empresa_unico(emp_limpia, cursor=cursor)
        cursor.execute(
            f"INSERT INTO usuarios (usuario, password, empresa, rol) VALUES ({p}, {p}, {p}, {p})",
            (u_limpio, encriptar_password(p_raw), empresa_final, r),
        )
        conexion.commit()
        if empresa_final.lower() != emp_limpia.lower():
            return (
                True,
                empresa_final,
                f"El nombre '{emp_limpia}' ya existía; se creó de forma aislada como '{empresa_final}'.",
            )
        return True, empresa_final, f"Empresa '{empresa_final}' creada y aislada correctamente."
    except err_types:
        conexion.rollback()
        return False, "", f"El ID de usuario '{u_limpio}' ya está en uso en el sistema."
    finally:
        cursor.close()
        conexion.close()


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


def actualizar_password(usuario, nueva_p, empresa=None):
    conexion = conectar()
    cursor = conexion.cursor()
    p = _ph()
    try:
        if empresa:
            cursor.execute(
                f"UPDATE usuarios SET password = {p} WHERE usuario = {p} AND empresa = {p}",
                (encriptar_password(nueva_p), usuario, empresa),
            )
        else:
            cursor.execute(
                f"UPDATE usuarios SET password = {p} WHERE usuario = {p}",
                (encriptar_password(nueva_p), usuario),
            )
        conexion.commit()
    finally:
        cursor.close()
        conexion.close()


def obtener_usuarios_empresa(empresa):
    conexion = conectar()
    cursor = conexion.cursor()
    p = _ph()
    try:
        cursor.execute(
            f"SELECT usuario, rol FROM usuarios WHERE empresa = {p} ORDER BY usuario",
            (empresa,),
        )
        columnas = [desc[0] for desc in cursor.description]
        return pd.DataFrame(cursor.fetchall(), columns=columnas)
    finally:
        cursor.close()
        conexion.close()


def obtener_todos_usuarios() -> pd.DataFrame:
    """Retorna todos los usuarios con su empresa/bufete asignado (solo para Super-Admin 'admin')."""
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        cursor.execute("SELECT usuario, empresa, rol FROM usuarios ORDER BY empresa, usuario")
        columnas = [desc[0] for desc in cursor.description]
        return pd.DataFrame(cursor.fetchall(), columns=columnas)
    finally:
        cursor.close()
        conexion.close()


def eliminar_usuario(usuario, empresa=None, actor=None):
    if usuario == "admin" or (actor and usuario == actor):
        return False
    conexion = conectar()
    cursor = conexion.cursor()
    p = _ph()
    try:
        if empresa:
            cursor.execute(
                f"DELETE FROM usuarios WHERE usuario = {p} AND empresa = {p} AND usuario != 'admin'",
                (usuario, empresa),
            )
        else:
            cursor.execute(
                f"DELETE FROM usuarios WHERE usuario = {p} AND usuario != 'admin'",
                (usuario,),
            )
        conexion.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conexion.close()


def guardar_expedientes(lista_datos, bufete, abogado_activo):
    conexion = conectar()
    cursor = conexion.cursor()
    p = _ph()
    guardadas = 0
    omitidas = 0

    try:
        cursor.execute(
            f"""
            SELECT numero_expediente, folio_protocolo
            FROM expedientes
            WHERE bufete_propietario = {p}
            AND numero_expediente NOT IN ('No detectado', 'N/A', '')
            """,
            (bufete,),
        )
        existentes = {(str(r[0]).strip(), str(r[1]).strip()) for r in cursor.fetchall()}

        for d in lista_datos:
            exp_num = str(d.get("numero_expediente", "No detectado")).strip()
            fol_num = str(d.get("folio_protocolo", "N/A")).strip()

            if exp_num not in ("No detectado", "N/A", "") and (exp_num, fol_num) in existentes:
                omitidas += 1
                continue

            if exp_num not in ("No detectado", "N/A", ""):
                existentes.add((exp_num, fol_num))

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
    except Exception:
        conexion.rollback()
        raise
    finally:
        cursor.close()
        conexion.close()
    return guardadas, omitidas


def obtener_historial(bufete):
    conexion = conectar()
    cursor = conexion.cursor()
    p = _ph()
    try:
        cursor.execute(
            f"SELECT * FROM expedientes WHERE bufete_propietario = {p} ORDER BY fecha_registro DESC",
            (bufete,),
        )
        columnas = [desc[0] for desc in cursor.description]
        return pd.DataFrame(cursor.fetchall(), columns=columnas)
    finally:
        cursor.close()
        conexion.close()
