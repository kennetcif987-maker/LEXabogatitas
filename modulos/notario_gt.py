import datetime
import math
import re
from typing import Dict, List, Optional, Tuple


_TZ_GUATEMALA = datetime.timezone(datetime.timedelta(hours=-6))

_MUNICIPIOS_POR_DEPTO_GT: Dict[int, int] = {
    1: 17, 2: 8, 3: 16, 4: 16, 5: 14, 6: 14, 7: 19, 8: 8,
    9: 24, 10: 21, 11: 9, 12: 30, 13: 33, 14: 21, 15: 8,
    16: 17, 17: 14, 18: 5, 19: 11, 20: 11, 21: 7, 22: 17,
}

_UNIDADES = (
    "cero",
    "uno",
    "dos",
    "tres",
    "cuatro",
    "cinco",
    "seis",
    "siete",
    "ocho",
    "nueve",
)

_ESPECIALES_10_29 = {
    10: "diez",
    11: "once",
    12: "doce",
    13: "trece",
    14: "catorce",
    15: "quince",
    16: "dieciséis",
    17: "diecisiete",
    18: "dieciocho",
    19: "diecinueve",
    20: "veinte",
    21: "veintiuno",
    22: "veintidós",
    23: "veintitrés",
    24: "veinticuatro",
    25: "veinticinco",
    26: "veintiséis",
    27: "veintisiete",
    28: "veintiocho",
    29: "veintinueve",
}

_DECENAS = {
    3: "treinta",
    4: "cuarenta",
    5: "cincuenta",
    6: "sesenta",
    7: "setenta",
    8: "ochenta",
    9: "noventa",
}

_CENTENAS = {
    1: "ciento",
    2: "doscientos",
    3: "trescientos",
    4: "cuatrocientos",
    5: "quinientos",
    6: "seiscientos",
    7: "setecientos",
    8: "ochocientos",
    9: "novecientos",
}

_MESES_ES = {
    1: "enero",
    2: "febrero",
    3: "marzo",
    4: "abril",
    5: "mayo",
    6: "junio",
    7: "julio",
    8: "agosto",
    9: "septiembre",
    10: "octubre",
    11: "noviembre",
    12: "diciembre",
}

PLAZOS_NOTARIALES_GT: Dict[str, str] = {
    "DICABI": "15 días hábiles siguientes a la autorización o registro (Art. 38 Código de Notariado, Dto. 314; Art. 43 Ley del IUSI, Dto. 15-98)",
    "TESTIMONIO_ESPECIAL": "25 días hábiles siguientes al otorgamiento de la escritura (Art. 37 literal a, Dto. 314)",
    "AVISO_TRIMESTRAL": "25 días hábiles siguientes al vencimiento de cada trimestre del año calendario (Art. 37 literal c, Dto. 314)",
    "AVISO_CANCELACION": "25 días hábiles siguientes a la fecha de cancelación del instrumento (Art. 37 literal b, Dto. 314)",
    "MATRIMONIO_RENAP": "15 días hábiles siguientes a la celebración (Art. 102 Código Civil, Dto. Ley 106; hasta 30 días hábiles Art. 84 Ley del RENAP, Dto. 90-2005)",
}


def ahora_gt() -> datetime.datetime:
    """Fecha y hora actual en zona horaria oficial de Guatemala (UTC-6)."""
    return datetime.datetime.now(_TZ_GUATEMALA)


def hoy_gt() -> datetime.date:
    """Fecha actual en zona horaria oficial de Guatemala (UTC-6)."""
    return ahora_gt().date()


def limpiar_texto_xml(texto: object) -> str:
    """Elimina caracteres de control ilegales en XML 1.0 para evitar DoS en python-docx."""
    if texto is None:
        return ""
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", str(texto))


def sanitizar_nombre_archivo(nombre: object, fallback: str = "documento") -> str:
    """Sanea nombres de archivo para descargas seguras sin caracteres de ruta o cabecera."""
    limpio = re.sub(r"[^A-Za-z0-9._-]+", "_", str(nombre or "").strip()).strip("._-")
    return limpio[:80] if limpio else fallback


def _menor_de_mil(n: int, apocopar: bool = False) -> str:
    """Convierte un entero 0..999 a español estándar notarial de Guatemala."""
    if n == 0:
        return "cero"
    if n == 100:
        return "cien"

    partes: List[str] = []
    centena, resto = divmod(n, 100)
    if centena:
        partes.append(_CENTENAS[centena])

    if resto > 0:
        if resto < 10:
            if resto == 1 and apocopar:
                partes.append("un")
            else:
                partes.append(_UNIDADES[resto])
        elif resto <= 29:
            if resto == 21 and apocopar:
                partes.append("veintiún")
            else:
                partes.append(_ESPECIALES_10_29[resto])
        else:
            decena, unidad = divmod(resto, 10)
            if unidad == 0:
                partes.append(_DECENAS[decena])
            else:
                u_txt = "un" if (unidad == 1 and apocopar) else _UNIDADES[unidad]
                partes.append(f"{_DECENAS[decena]} y {u_txt}")

    return " ".join(partes)


def entero_a_letras(n: int, apocopar: bool = False) -> str:
    """Convierte un entero no negativo (hasta 999,999,999,999) a letras en español."""
    if n < 0:
        return f"menos {entero_a_letras(-n, apocopar=apocopar)}"
    if n == 0:
        return "cero"
    if n < 1000:
        return _menor_de_mil(n, apocopar=apocopar)

    grupos: List[str] = []
    millones, resto_millon = divmod(n, 1_000_000)

    if millones > 0:
        if millones == 1:
            grupos.append("un millón")
        else:
            grupos.append(f"{entero_a_letras(millones, apocopar=True)} millones")

    miles, unidades = divmod(resto_millon, 1000)
    if miles > 0:
        if miles == 1:
            grupos.append("mil")
        else:
            grupos.append(f"{_menor_de_mil(miles, apocopar=True)} mil")

    if unidades > 0:
        grupos.append(_menor_de_mil(unidades, apocopar=apocopar))

    return " ".join(grupos)


def _bloque_con_ceros_a_letras(bloque: str) -> str:
    """Convierte un bloque numérico (ej. '0101', '0045', '0000') conservando ceros a la izquierda."""
    limpio = re.sub(r"\D", "", str(bloque or ""))
    if not limpio:
        return ""
    if set(limpio) == {"0"}:
        return " ".join(["cero"] * len(limpio))

    ceros_izq = 0
    for ch in limpio:
        if ch == "0":
            ceros_izq += 1
        else:
            break

    valor = int(limpio)
    prefijo = ["cero"] * ceros_izq
    texto_num = entero_a_letras(valor, apocopar=False)
    return " ".join(prefijo + [texto_num])


def normalizar_dpi(raw: str) -> str:
    """Extrae los 13 dígitos de un DPI/CUI si es válido; de lo contrario retorna cadena vacía."""
    texto = str(raw or "").strip()
    if not texto or texto.lower() in ("n/a", "no detectado", "no consignado", "cf", "none", "---"):
        return ""
    if re.search(r"[A-Za-z]", texto):
        m = re.search(r"(?<!\d)(\d{4})[\s\-]*(\d{5})[\s\-]*(\d{4})(?!\d)", texto)
        return "".join(m.groups()) if m else ""
    solo_digitos = re.sub(r"\D", "", texto)
    if len(solo_digitos) == 13:
        return solo_digitos
    return ""


def validar_dpi(raw: str, validar_verificador: bool = False) -> Tuple[bool, str]:
    """
    Valida formato oficial de DPI/CUI de Guatemala (RENAP):
    - 13 dígitos exactos (4 + 5 + 4).
    - Código de departamento entre 01 y 22 y municipio dentro del catálogo real de 340 municipios.
    - Si validar_verificador=True, verifica además el dígito verificador Módulo 11 (9.º dígito).
    """
    cui = normalizar_dpi(raw)
    if not cui or len(cui) != 13:
        return False, "Debe contener exactamente 13 dígitos (formato 0000 00000 0000)."
    depto = int(cui[9:11])
    muni = int(cui[11:13])
    max_muni = _MUNICIPIOS_POR_DEPTO_GT.get(depto)
    if max_muni is None:
        return False, f"Código de departamento '{cui[9:11]}' fuera de rango en Guatemala (01–22)."
    if muni < 1 or muni > max_muni:
        return False, f"Código de municipio '{cui[11:13]}' inválido para departamento {cui[9:11]} (máx. {max_muni:02d})."
    if validar_verificador:
        suma = sum(int(cui[i]) * (i + 2) for i in range(8))
        esperado = suma % 11
        if esperado >= 10 or esperado != int(cui[8]):
            return False, f"El dígito verificador RENAP del CUI '{cui[:4]} {cui[4:9]} {cui[9:13]}' no coincide."
    return True, f"{cui[:4]} {cui[4:9]} {cui[9:13]}"


def formatear_dpi_espaciado(raw: str) -> str:
    """Devuelve 'XXXX XXXXX XXXX' si tiene 13 dígitos; si no, retorna el texto original."""
    cui = normalizar_dpi(raw)
    if len(cui) == 13:
        return f"{cui[:4]} {cui[4:9]} {cui[9:13]}"
    return str(raw or "").strip()


def dpi_a_letras(raw: str, incluir_digitos: bool = True) -> str:
    """
    Convierte un CUI / DPI guatemalteco (13 dígitos en bloques 4-5-4) al formato notarial obligatorio
    en letras (Art. 13 num. 4 y Art. 29 num. 4 del Código de Notariado, Decreto 314).

    Ejemplo:
        2456789010101 ->
        "dos mil cuatrocientos cincuenta y seis, espacio, setenta y ocho mil novecientos uno,
         espacio, cero ciento uno (2456 78901 0101)"
    """
    cui = normalizar_dpi(raw)
    if len(cui) != 13:
        limpio = str(raw or "").strip()
        return limpio if limpio else "No consignado"

    b1, b2, b3 = cui[:4], cui[4:9], cui[9:13]
    l1 = _bloque_con_ceros_a_letras(b1)
    l2 = _bloque_con_ceros_a_letras(b2)
    l3 = _bloque_con_ceros_a_letras(b3)

    en_letras = f"{l1}, espacio, {l2}, espacio, {l3}"
    if incluir_digitos:
        return f"{en_letras} ({b1} {b2} {b3})"
    return en_letras


def validar_nit_m11(nit: str) -> Tuple[bool, str]:
    """Valida dígito verificador SAT de Guatemala (Módulo 11). Soporta NITs hasta 13 dígitos y 'CF'."""
    limpio = str(nit or "").strip().upper().replace("-", "").replace(" ", "")
    if not limpio:
        return False, ""
    if limpio in ("CF", "C/F", "CONSUMIDORFINAL"):
        return True, "CF"
    sin_ceros = limpio.lstrip("0") or limpio
    if not re.match(r"^\d{1,12}[\dK]$", sin_ceros) or len(sin_ceros) < 2:
        return False, limpio
    cuerpo, dv = sin_ceros[:-1], sin_ceros[-1]
    suma = sum(int(d) * (len(cuerpo) + 1 - i) for i, d in enumerate(cuerpo))
    esperado_num = (11 - (suma % 11)) % 11
    esperado = "K" if esperado_num == 10 else str(esperado_num)
    return (dv == esperado), sin_ceros


def monto_a_letras(
    monto: float,
    moneda: str = "GTQ",
    incluir_cifra: bool = True,
    mayusculas: bool = False,
) -> str:
    """
    Convierte una cantidad monetaria a redacción notarial guatemalteca.
    Ejemplo: 1000000.0 -> "un millón de quetzales exactos (Q. 1,000,000.00)"
    """
    try:
        valor = round(float(monto or 0.0), 2)
    except (TypeError, ValueError):
        valor = 0.0

    negativo = valor < 0
    valor = abs(valor)
    entero = int(math.floor(valor + 1e-9))
    centavos = int(round((valor - entero) * 100))
    if centavos == 100:
        entero += 1
        centavos = 0

    mon = str(moneda or "GTQ").strip().upper()
    if mon == "USD":
        sing, plur, simb = (
            "dólar de los Estados Unidos de América",
            "dólares de los Estados Unidos de América",
            "US$.",
        )
    else:
        sing, plur, simb = ("quetzal", "quetzales", "Q.")

    txt_entero = entero_a_letras(entero, apocopar=True)
    unidad_mon = sing if entero == 1 else plur
    preposicion = " de " if (entero >= 1_000_000 and entero % 1_000_000 == 0) else " "

    if centavos == 0:
        exacto = "exacto" if entero == 1 else "exactos"
        frase = f"{txt_entero}{preposicion}{unidad_mon} {exacto}"
    else:
        txt_cent = entero_a_letras(centavos, apocopar=True)
        unidad_cent = "centavo" if centavos == 1 else "centavos"
        frase = f"{txt_entero}{preposicion}{unidad_mon} con {txt_cent} {unidad_cent}"

    if negativo:
        frase = f"menos {frase}"

    if mayusculas:
        frase = frase.upper()

    if incluir_cifra:
        signo = "-" if negativo else ""
        return f"{frase} ({signo}{simb} {valor:,.2f})"
    return frase


def _parsear_fecha(fecha_raw: Optional[object]) -> Optional[datetime.date]:
    if isinstance(fecha_raw, datetime.datetime):
        return fecha_raw.date()
    if isinstance(fecha_raw, datetime.date):
        return fecha_raw
    txt = str(fecha_raw or "").strip()
    if not txt:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.datetime.strptime(txt[:10], fmt).date()
        except ValueError:
            continue
    return None


def extraer_anio_fecha(fecha_raw: Optional[object] = None) -> int:
    """Extrae el año fiscal de una fecha; si no es parseable retorna el año actual en Guatemala."""
    dt = _parsear_fecha(fecha_raw)
    if dt:
        return dt.year
    m = re.search(r"\b(19\d{2}|20\d{2})\b", str(fecha_raw or ""))
    if m:
        return int(m.group(1))
    return hoy_gt().year


def fecha_a_letras(fecha_raw: Optional[object] = None, incluir_anio_palabra: bool = True) -> str:
    """
    Convierte una fecha a redacción notarial en español (Art. 13 num. 4 Código de Notariado),
    usando zona horaria de Guatemala (UTC-6) por defecto.
    """
    if fecha_raw is None:
        dt = hoy_gt()
    else:
        dt = _parsear_fecha(fecha_raw)
        if dt is None:
            raw_str = str(fecha_raw).strip()
            if raw_str and re.search(r"[a-záéíóúñ]{4,}", raw_str, re.I) and not raw_str.lower().startswith("n/a"):
                return raw_str
            dt = hoy_gt()

    dia_txt = entero_a_letras(dt.day, apocopar=False)
    mes_txt = _MESES_ES[dt.month]
    anio_txt = entero_a_letras(dt.year, apocopar=False)
    if incluir_anio_palabra:
        return f"{dia_txt} de {mes_txt} del año {anio_txt}"
    return f"{dia_txt} de {mes_txt} de {anio_txt}"


def hora_a_letras(hora: Optional[datetime.time] = None) -> str:
    """Convierte una hora a formato notarial femenino correcto ('una hora con quince minutos')."""
    if hora is None:
        hora = ahora_gt().time()
    if hora.hour == 1:
        h_txt = "una"
    elif hora.hour == 21:
        h_txt = "veintiuna"
    else:
        h_txt = entero_a_letras(hora.hour, apocopar=False)
    h_lbl = "hora" if hora.hour == 1 else "horas"
    if hora.minute == 0:
        return f"{h_txt} {h_lbl} en punto"
    m_txt = entero_a_letras(hora.minute, apocopar=True)
    m_lbl = "minuto" if hora.minute == 1 else "minutos"
    return f"{h_txt} {h_lbl} con {m_txt} {m_lbl}"


def trimestre_actual_info(fecha_ref: Optional[datetime.date] = None) -> Tuple[str, int]:
    """Retorna (nombre_trimestre, anio) en zona horaria Guatemala."""
    dt = fecha_ref or hoy_gt()
    idx = (dt.month - 1) // 3
    nombres = (
        "Primer Trimestre (enero a marzo)",
        "Segundo Trimestre (abril a junio)",
        "Tercer Trimestre (julio a septiembre)",
        "Cuarto Trimestre (octubre a diciembre)",
    )
    return nombres[idx], dt.year


def calcular_timbre_notarial_guatemala(
    monto: float,
    tipo_acto: str = "VALOR_DETERMINADO",
) -> Dict[str, object]:
    """
    Calcula el Timbre Notarial conforme al Art. 3 numeral II del Decreto 82-96 (Guatemala):
    - Contratos de valor determinado: 2‰ (0.002), mínimo Q. 1.00, máximo Q. 300.00,
      forzando las fracciones de quetzal a la unidad inmediata superior.
    - Valor indeterminado / actas / protocolaciones / mandatos: Q. 10.00 fijo.
    - Testamentos y donaciones por causa de muerte: Q. 25.00 fijo.
    - Resoluciones de jurisdicción voluntaria notarial (trámite / final): Q. 2.00 / Q. 10.00.
    """
    tipo = str(tipo_acto or "VALOR_DETERMINADO").strip().upper()
    try:
        m = max(0.0, float(monto or 0.0))
    except (TypeError, ValueError):
        m = 0.0

    if tipo in ("INDETERMINADO", "MANDATO", "ACTA", "PROTOCOLACION", "AUTENTICA"):
        return {
            "timbre_notarial": 10.00,
            "base_legal": "Art. 3 num. II literal b) y c) Decreto 82-96",
            "regla": "Cuota fija de Q. 10.00 (valor indeterminado / acta notarial / legalización / protocolación).",
        }
    if tipo in ("TESTAMENTO", "DONACION_CAUSA_MUERTE"):
        return {
            "timbre_notarial": 25.00,
            "base_legal": "Art. 3 num. II literal d) Decreto 82-96",
            "regla": "Cuota fija de Q. 25.00 en la cubierta del testamento cerrado / testimonio especial.",
        }
    if tipo == "RESOLUCION_JV_TRAMITE":
        return {
            "timbre_notarial": 2.00,
            "base_legal": "Art. 3 num. II literal e) Decreto 82-96",
            "regla": "Q. 2.00 por cada resolución de trámite en jurisdicción voluntaria.",
        }
    if tipo == "RESOLUCION_JV_FINAL":
        return {
            "timbre_notarial": 10.00,
            "base_legal": "Art. 3 num. II literal e) Decreto 82-96",
            "regla": "Q. 10.00 en resolución final o auto de jurisdicción voluntaria.",
        }

    bruto = m * 0.002
    redondeado = float(math.ceil(bruto - 1e-9)) if bruto > 0 else 1.0
    final = min(300.0, max(1.0, redondeado))
    return {
        "timbre_notarial": round(final, 2),
        "calculo_exacto_2x1000": round(bruto, 4),
        "base_legal": "Art. 3 num. II literal a) Decreto 82-96",
        "regla": (
            f"2‰ sobre Q. {m:,.2f} = Q. {bruto:,.2f}; aproximado a unidad de quetzal superior "
            f"con mínimo Q. 1.00 y tope máximo Q. 300.00 -> Q. {final:,.2f}."
        ),
    }


def calcular_impuestos_testimonio_gt(
    monto: float,
    operacion: str = "SEGUNDA_COMPRAVENTA",
    hojas_testimonio: int = 1,
) -> Dict[str, object]:
    """
    Estima impuestos fiscales, notariales y forenses vigentes en Guatemala
    (Dto. 27-92, Dto. 37-92 y Dto. 82-96).
    """
    try:
        m = max(0.0, float(monto or 0.0))
    except (TypeError, ValueError):
        m = 0.0
    hojas = max(1, int(hojas_testimonio or 1))
    op = str(operacion or "SEGUNDA_COMPRAVENTA").strip().upper()

    timbre_razon_especial = round(hojas * 0.50, 2)
    timbre_forense_memorial = round(hojas * 1.00, 2)

    if op == "PRIMERA_VENTA_IVA":
        impuesto_primer_test = round(m * 0.12, 2)
        concepto_fiscal = "IVA 12% sobre valor mayor entre precio pactado y matrícula fiscal (Dto. 27-92)"
        timbre_not = calcular_timbre_notarial_guatemala(m, "VALOR_DETERMINADO")
    elif op == "MANDATO_GENERAL":
        impuesto_primer_test = 10.00
        concepto_fiscal = "Timbre Fiscal fijo Q. 10.00 (Art. 5 num. 8 lit. a, Dto. 37-92)"
        timbre_not = calcular_timbre_notarial_guatemala(0, "MANDATO")
    elif op == "MANDATO_ESPECIAL":
        impuesto_primer_test = 2.00
        concepto_fiscal = "Timbre Fiscal fijo Q. 2.00 (Art. 5 num. 8 lit. b, Dto. 37-92)"
        timbre_not = calcular_timbre_notarial_guatemala(0, "MANDATO")
    elif op == "CARTA_PAGO":
        impuesto_primer_test = 0.00
        concepto_fiscal = "Exenta si proviene de crédito bancario/entidad exenta (Art. 11 Dto. 37-92; verificar Art. 2 num. 3 entre particulares)"
        timbre_not = calcular_timbre_notarial_guatemala(
            m, "VALOR_DETERMINADO" if m > 0 else "INDETERMINADO"
        )
    elif op == "PROMESA_COMPRAVENTA":
        impuesto_primer_test = 50.00
        concepto_fiscal = "Timbre Fiscal fijo Q. 50.00 (Promesa de compraventa de inmueble, Art. 5 num. 16 Dto. 37-92)"
        timbre_not = calcular_timbre_notarial_guatemala(m, "VALOR_DETERMINADO")
    elif op == "ACTA_NOTARIAL":
        impuesto_primer_test = timbre_razon_especial
        concepto_fiscal = "Timbre Fiscal Q. 0.50 por hoja del Acta Notarial (Art. 5 num. 6 Dto. 37-92)"
        timbre_not = calcular_timbre_notarial_guatemala(0, "ACTA")
    elif op == "AUTENTICA_LEGALIZACION":
        impuesto_primer_test = 5.00
        concepto_fiscal = "Timbre Fiscal Q. 5.00 por auténtica/legalización (Art. 5 num. 7 Dto. 37-92)"
        timbre_not = calcular_timbre_notarial_guatemala(0, "AUTENTICA")
    elif op == "TESTAMENTO":
        impuesto_primer_test = 0.00
        concepto_fiscal = "Sin Timbre Fiscal al otorgar (Q. 0.50 por hoja en Testimonio Especial)"
        timbre_not = calcular_timbre_notarial_guatemala(0, "TESTAMENTO")
    else:
        impuesto_primer_test = round(m * 0.03, 2)
        concepto_fiscal = (
            "Impuesto de Timbres Fiscales 3% (2da o subsiguiente venta, Art. 2 num. 9 y Art. 19 Dto. 37-92: "
            "base imponible es el valor MAYOR entre precio pactado, avalúo autorizado o matrícula fiscal)"
        )
        timbre_not = calcular_timbre_notarial_guatemala(m, "VALOR_DETERMINADO")

    return {
        "impuesto_primer_testimonio": impuesto_primer_test,
        "concepto_fiscal": concepto_fiscal,
        "timbre_notarial_especial": timbre_not["timbre_notarial"],
        "detalle_timbre_notarial": timbre_not["regla"],
        "timbre_fiscal_razon_especial": timbre_razon_especial,
        "timbre_forense_por_hojas": timbre_forense_memorial,
        "hojas": hojas,
    }


def sanitizar_celda_csv(valor: object) -> object:
    """Neutraliza CSV Formula Injection (CWE-1236) en Excel/LibreOffice incluyendo prefijos con saltos."""
    if isinstance(valor, str):
        limpio = valor.lstrip()
        if (valor and valor[0] in ("=", "+", "-", "@", "\t", "\r", "\n")) or (
            limpio and limpio[0] in ("=", "+", "-", "@")
        ):
            return f"'{valor}"
    return valor


def dataframe_a_csv_seguro(df) -> bytes:
    """Convierte un DataFrame a UTF-8-SIG sanitizando celdas contra inyección de fórmulas."""
    import pandas as pd

    copia = df.copy()
    for col in copia.columns:
        if pd.api.types.is_object_dtype(copia[col]) or pd.api.types.is_string_dtype(copia[col]):
            copia[col] = copia[col].map(sanitizar_celda_csv)
    return copia.to_csv(index=False).encode("utf-8-sig")
