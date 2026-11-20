# 📓 BITÁCORA DE ARQUITECTURA Y ESTADO DEL PROYECTO: LEX IA 360

> **INSTRUCCIÓN PARA AGENTES IA (Claude Code, OpenAI Codex, Cursor, Gemini):**  
> Lee este archivo antes de inspeccionar el código fuente. Contiene el esquema completo de la base de datos, módulos jurídicos, conexión con Gemini API y generadores de Word para **ahorrar tokens**.

---

## 📌 1. Ficha Técnica y Metadatos
* **Nombre:** `Lex IA 360 - Suite Jurídica y Notarial Forense`
* **Tipo:** SaaS Legaltech B2B para Abogados y Notarios en Guatemala.
* **Ruta de Trabajo Local:** `C:\Proyectos\Lex_IA_Produccion`
* **Stack Tecnológico:** Python 3.14, Streamlit 1.57, Google GenAI SDK (`from google import genai`), Pydantic (Structured Outputs), PyMuPDF (`fitz`), SQLite, `python-docx`.
* **Base de Datos Local:** `lex_ia_360.db` (SQLite relacional con multi-tenancy por bufete).
* **Lanzador de un clic:** `INICIAR_LEX_IA.bat` (abre la suite en el navegador con Streamlit).

---

## 🎯 2. Para qué sirve (Propuesta de Valor)
`Lex IA 360` automatiza el trabajo más tedioso y de alto riesgo para bufetes jurídicos y notariales:
1. **Auditoría Forense de Expedientes:** El abogado sube un PDF de una sentencia, amparo o demanda. La IA extrae con precisión matemática: partes (nombres, DPI, NIT), montos reclamados, juzgados, fechas clave, plazos procesales y anomalías jurídicas.
2. **Generador de Avisos Registrales Obligatorios:** Redacta y descarga en `.docx` de inmediato avisos para **DICABI**, **Archivo General de Protocolos (AGP)**, testimonios y avisos trimestrales conforme a la ley guatemalteca.
3. **Catálogo de 20 Plantillas Notariales (`catalogo_plantillas.py`):** Minutas legales pre-estructuradas (compraventas, mandatos, arrendamientos, donaciones, declaraciones juradas, etc.).
4. **Semáforo Procesal y Plazos:** Alertas de plazos legales de 3, 5 y 9 días para evitar preclusiones y caducidades procesales.
5. **Multi-Usuario / Bufetes:** Sistema de roles (Administrador, Abogado Asociado, Asistente) con base de datos compartida por empresa.

---

## 🏗️ 3. Módulos y Arquitectura del Sistema
* **`app.py`:** Interfaz visual con Streamlit (Tabs de Auditoría Forense, Expedientes Históricos, Generador de Avisos, Catálogo Notarial y Panel de Administración de Usuarios).
* **`modulos/conexion_api.py`:**
  * Conexión con Google GenAI SDK usando `st.secrets["GEMINI_API_KEY"]`.
  * Define esquemas Pydantic estrictos (`SujetoLegal`, `ExpedienteForense`) para garantizar que Gemini devuelva JSON validado sin errores de formato.
  * Extracción de texto y renderizado de páginas de PDF como imágenes vía `fitz` (PyMuPDF) para lectura multimodal.
* **`modulos/base_datos.py`:**
  * Gestiona las tablas `expedientes` y `usuarios` en `lex_ia_360.db`.
  * Hashing de contraseñas con SHA-256.
* **`modulos/generador_avisos.py`:**
  * Generación dinámica de documentos Word (`.docx`) formateados según estándares del Archivo General de Protocolos y DICABI.
* **`modulos/catalogo_plantillas.py`:**
  * Biblioteca de 20 contratos y memoriales legales listos para rellenar variables.
* **`modulos/formateador_legal.py`:**
  * Ajuste tipográfico formal para protocolos y memoriales judiciales (márgenes, numeración, cláusulas).

---

## 🗄️ 4. Esquema de Base de Datos (`lex_ia_360.db`)
* **Tabla `usuarios`:**
  * `id` (INTEGER PK), `usuario` (TEXT UNIQUE), `password` (TEXT HASH), `empresa` (TEXT), `rol` (TEXT).
* **Tabla `expedientes`:**
  * `id` (INTEGER PK), `bufete_propietario`, `usuario`, `archivo_origen`, `numero_expediente`, `juzgado`, `materia`, `tipo_proceso`, `demandante`, `dpi_demandante`, `nit_demandante`, `demandado`, `dpi_demandado`, `nit_demandado`, `monto_litigio`, `fecha_resolucion`, `fecha_audiencia`, `plazo_procesal`, `anomalia`, `fecha_registro`, `categoria_documental`, `folio_protocolo`, `timbre_notarial`, `timbre_fiscal`, `registro_destino`, `semaforo`, `resumen_forense`.

---

## 🗺️ 5. Mapa de Archivos Críticos
```
C:\Proyectos\Lex_IA_Produccion\
├── app.py                       # Interfaz Streamlit y orquestador de vistas
├── INICIAR_LEX_IA.bat           # Lanzador rápido en Windows
├── lex_ia_360.db                # Base de datos SQLite
├── requirements.txt             # Dependencias Python
├── .streamlit/
│   └── secrets.toml             # GEMINI_API_KEY
└── modulos/
    ├── base_datos.py            # CRUD SQLite y autenticación
    ├── conexion_api.py          # Extracción con Gemini + Pydantic
    ├── generador_avisos.py      # Generador de Word para DICABI/AGP
    ├── catalogo_plantillas.py   # Catálogo de 20 minutas legales
    └── formateador_legal.py     # Estilizado y formato de documentos
```

---

## 🚀 6. Comandos de Ejecución
* **Iniciar la aplicación:**
  ```bash
  python -m streamlit run app.py
  # O doble clic a INICIAR_LEX_IA.bat
  ```
  *URL de acceso:* `http://localhost:8501`

---

## 🔒 7. Reglas de Oro para Futuras IAs

0. 🚨 **REGLA SUPREMA: RECORDAR SIEMPRE OCULTAR LAS APIS Y SECRETS**:
   - **¡CERO EXPOSICIÓN DE KEYS!** Antes de cualquier push o commit, la IA debe recordarle al desarrollador que verifique que sus API Keys (Gemini, Supabase, Google Play, Stripe, etc.) NO estén expuestas en el código, ni en logs, ni en capturas.
   - Todo secret vive exclusivamente en `.env` o `.streamlit/secrets.toml`.
   - Verificar siempre que `.gitignore` contenga `secrets.toml` y `.env` para evitar fugas catastróficas en GitHub.
1. **Nunca exponer ni borrar `.streamlit/secrets.toml`**: Contiene la llave privada de la API de Google Gemini.
2. **Preservar los esquemas Pydantic en `conexion_api.py`**: El analizador depende de `BaseModel` para parsear los datos sin romper la inserción en la base de datos SQLite.
3. **Respetar la legislación guatemalteca en las plantillas**: No cambiar términos procesales (Código Notariado Decreto 314, timbres notariales, timbres fiscales).
