import sqlite3
import pandas as pd
import hashlib

def conectar():
    return sqlite3.connect("lex_ia_360.db")

def encriptar_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def inicializar_db():
    conexion = conectar()
    cursor = conexion.cursor()
    
    # 🚀 TABLA ACTUALIZADA CON EL NUEVO ESPECTRO FORENSE
    cursor.execute('''CREATE TABLE IF NOT EXISTS expedientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bufete_propietario TEXT,
        usuario TEXT,
        archivo_origen TEXT,
        numero_expediente TEXT,
        juzgado TEXT,
        materia TEXT,
        tipo_proceso TEXT,
        demandante TEXT,
        dpi_demandante TEXT,
        nit_demandante TEXT,
        demandado TEXT,
        dpi_demandado TEXT,
        nit_demandado TEXT,
        monto_litigio REAL,
        fecha_resolucion TEXT,
        fecha_audiencia TEXT,
        plazo_procesal TEXT,
        anomalia TEXT,
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE,
        password TEXT,
        empresa TEXT,
        rol TEXT
    )''')
    
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        pass_admin = encriptar_password("admin123")
        cursor.execute("INSERT INTO usuarios (usuario, password, empresa, rol) VALUES (?, ?, ?, ?)", 
                       ("admin", pass_admin, "Firma Legal Principal", "Administrador"))
        
    conexion.commit()
    conexion.close()

def autenticar_usuario(usuario, password):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("SELECT usuario, empresa, rol FROM usuarios WHERE usuario = ? AND password = ?", 
                   (usuario, encriptar_password(password)))
    res = cursor.fetchone()
    conexion.close()
    return {"usuario": res[0], "empresa": res[1], "rol": res[2]} if res else None

def registrar_usuario(u, p, e, r):
    conexion = conectar()
    cursor = conexion.cursor()
    try:
        cursor.execute("INSERT INTO usuarios (usuario, password, empresa, rol) VALUES (?, ?, ?, ?)", 
                       (u, encriptar_password(p), e, r))
        conexion.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conexion.close()

def actualizar_password(usuario, nueva_p):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("UPDATE usuarios SET password = ? WHERE usuario = ?", (encriptar_password(nueva_p), usuario))
    conexion.commit()
    conexion.close()

def obtener_usuarios_empresa(empresa):
    conexion = conectar()
    df = pd.read_sql_query("SELECT usuario, rol FROM usuarios WHERE empresa = ?", conexion, params=(empresa,))
    conexion.close()
    return df

def eliminar_usuario(usuario):
    conexion = conectar()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM usuarios WHERE usuario = ? AND usuario != 'admin'", (usuario,))
    conexion.commit()
    conexion.close()

def guardar_expedientes(lista_datos, bufete, abogado_activo):
    conexion = conectar()
    cursor = conexion.cursor()
    guardadas = 0
    omitidas = 0
    
    for d in lista_datos:
        expediente_num = d.get('numero_expediente', 'No detectado')
        
        cursor.execute("SELECT 1 FROM expedientes WHERE bufete_propietario = ? AND numero_expediente = ? AND numero_expediente != 'No detectado'", 
                       (bufete, expediente_num))
        if cursor.fetchone():
            omitidas += 1
            continue
            
        # 🚀 INYECCIÓN DE LOS NUEVOS DATOS EN LA BASE DE DATOS
        cursor.execute('''INSERT INTO expedientes (
            bufete_propietario, usuario, archivo_origen, numero_expediente, juzgado, materia, 
            tipo_proceso, demandante, dpi_demandante, nit_demandante, demandado, dpi_demandado, 
            nit_demandado, monto_litigio, fecha_resolucion, fecha_audiencia, plazo_procesal, anomalia)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
            (bufete, abogado_activo, d.get('archivo_origen'), expediente_num, d.get('juzgado'), 
             d.get('materia', 'No detectada'), d.get('tipo_proceso'), d.get('demandante'), 
             d.get('documento_identificacion_demandante', d.get('dpi_demandante', 'No detectado')), 
             d.get('nit_demandante', 'No detectado'), 
             d.get('demandado'), 
             d.get('documento_identificacion_demandado', d.get('dpi_demandado', 'No detectado')), 
             d.get('nit_demandado', 'No detectado'), 
             float(d.get('monto_litigio', 0.0)), d.get('fecha_resolucion'), d.get('fecha_audiencia', 'N/A'), 
             d.get('plazo_procesal', 'N/A'), d.get('anomalia', 'ninguna')))
        guardadas += 1
        
    conexion.commit()
    conexion.close()
    return guardadas, omitidas

def obtener_historial(bufete):
    conexion = conectar()
    df = pd.read_sql_query("SELECT * FROM expedientes WHERE bufete_propietario = ? ORDER BY fecha_registro DESC", conexion, params=(bufete,))
    conexion.close()
    return df