"""
Módulo de Catálogo de Plantillas Legales y Formato Español de Protocolo (Guatemala)
Cumple con los requisitos del Código de Notariado (Decreto 314), Código Civil y Procesal.
Incluye 20 plantillas maestras organizadas por ramas: Notarial, Civil, Familia y Penal.
"""

CATALOGO_PLANTILLAS = {
    "NOTARIAL": [
        {
            "id": "not_compraventa",
            "nombre": "Contrato de Compraventa de Bien Inmueble Urbano",
            "soporte": "Papel Sellado Especial de Protocolo (25 líneas)",
            "descripcion": "Traspaso definitivo de propiedad con saneamiento de ley y aceptación expresa.",
            "campos": ["numero_escritura", "fecha_letras", "notario", "vendedor", "dpi_vendedor", "comprador", "dpi_comprador", "finca_letras", "folio_letras", "libro_letras", "precio_letras"],
            "redaccion": """NÚMERO {numero_escritura}. En la ciudad de Guatemala, el {fecha_letras}, Ante Mí: {notario}, Notaria, comparecen: por una parte, el señor {vendedor}, de datos de identificación personal conocidos en este instrumento, quien se identifica con el Documento Personal de Identificación con Código Único de Identificación {dpi_vendedor}, extendido por el Registro Nacional de las Personas; y por la otra parte, el señor {comprador}, quien se identifica con el Documento Personal de Identificación {dpi_comprador}. Los comparecientes me aseguran hallarse en el libre ejercicio de sus derechos civiles y que por el presente acto otorgan CONTRATO DE COMPRAVENTA DE BIEN INMUEBLE URBANO, contenido en las siguientes cláusulas: PRIMERA: Manifiesta el señor {vendedor} que es legítimo propietario de la finca urbana inscrita en el Registro General de la Propiedad de la Zona Central al número {finca_letras}, folio {folio_letras}, del libro {libro_letras} de Guatemala, con las medidas y colindancias que le aparecen en su respectiva inscripción de dominio. SEGUNDA: Manifiesta el vendedor que por este acto, y por el precio de {precio_letras}, que tiene por recibidos a su entera satisfacción, VENDE, CEDE Y TRASPASA la totalidad del bien inmueble identificado en la cláusula anterior a favor del señor {comprador}, incluyendo todo cuanto de hecho y por derecho le corresponde al mismo. TERCERA: Que sobre el bien inmueble objeto de este contrato no pesan gravámenes, anotaciones ni limitaciones que puedan perjudicar los derechos del comprador, obligándose en todo caso al saneamiento de ley. CUARTA: Por su parte, el comprador manifiesta que en los términos consignados ACEPTA expresamente la venta que se le hace. Yo, la Notaria, DOY FE: a) De todo lo expuesto; b) De haber tenido a la vista los documentos de identificación y el título de propiedad; y c) Leída íntegramente la presente escritura, la ratifican, aceptan y firman."""
        },
        {
            "id": "not_mandato",
            "nombre": "Mandato General con Representación y Cláusula Especial",
            "soporte": "Papel Sellado Especial de Protocolo (25 líneas)",
            "descripcion": "Facultad amplia para administrar bienes y cláusula especial para disponer o enajenar.",
            "campos": ["numero_escritura", "fecha_letras", "notario", "mandante", "dpi_mandante", "mandatario", "dpi_mandatario"],
            "redaccion": """NÚMERO {numero_escritura}. En la ciudad de Guatemala, el {fecha_letras}, Ante Mí: {notario}, Notaria, comparecen: el señor {mandante}, quien se identifica con el DPI {dpi_mandante}; y el señor {mandatario}, quien se identifica con el DPI {dpi_mandatario}. Los comparecientes me aseguran hallarse en el libre ejercicio de sus derechos civiles y otorgan MANDATO GENERAL CON REPRESENTACIÓN Y CLÁUSULA ESPECIAL, conforme las cláusulas: PRIMERA: Manifiesta el mandante que confiere mandato general con representación a favor de {mandatario} para que en su nombre y representación atienda, dirija y administre la totalidad de sus negocios e intereses en la República de Guatemala. SEGUNDA: Continúa manifestando el mandante que de manera expresa otorga CLÁUSULA ESPECIAL para que el mandatario pueda vender, enajenar, hipotecar, transigir, someter a arbitraje y disponer de sus bienes. TERCERA: El mandatario manifiesta que en los términos relacionados acepta el mandato que se le otorga y promete desempeñarlo fielmente y apegado a la ley. Doy fe."""
        },
        {
            "id": "not_arrendamiento",
            "nombre": "Contrato de Arrendamiento de Inmueble con Fiador",
            "soporte": "Papel Protocolo o Documento con Firmas Legalizadas",
            "descripcion": "Arrendamiento de vivienda o local comercial fijando renta, depósito y fiador mancomunado.",
            "campos": ["fecha_letras", "notario", "arrendador", "arrendatario", "fiador", "renta_letras", "plazo_letras", "direccion_inmueble"],
            "redaccion": """En la ciudad de Guatemala, el {fecha_letras}, comparecen: por una parte, {arrendador} (Arrendador); por la otra, {arrendatario} (Arrendatario); y como fiador mancomunado y solidario, {fiador}. Los comparecientes otorgan CONTRATO DE ARRENDAMIENTO de bien inmueble ubicado en {direccion_inmueble}, sujeto a las estipulaciones: PRIMERA: El Arrendador cede el uso y goce del inmueble indicado al Arrendatario. SEGUNDA: El plazo forzoso del arrendamiento será de {plazo_letras}. TERCERA: La renta mensual pactada es de {renta_letras}, pagadera por mes anticipado. CUARTA: El fiador se constituye en fiador solidario y mancomunado por todas las obligaciones derivadas del presente contrato. Aceptan las partes y firman."""
        },
        {
            "id": "not_matrimonio",
            "nombre": "Acta Notarial de Matrimonio Civil",
            "soporte": "Papel Bond Común (Acta Notarial Extraprotocolar)",
            "descripcion": "Celebración de matrimonio civil ante Notario con declaración de régimen económico.",
            "campos": ["lugar_fecha_letras", "notario", "contrayente_varon", "edad_varon", "dpi_varon", "contrayente_mujer", "edad_mujer", "dpi_mujer", "regimen_economico"],
            "redaccion": """En la ciudad de Guatemala, el {lugar_fecha_letras}, Yo, {notario}, Notaria, me encuentro constituida en la sede de mi oficina profesional a requerimiento de: {contrayente_varon}, de {edad_varon} años de edad, soltero, guatemalteco, quien se identifica con el DPI {dpi_varon}; y {contrayente_mujer}, de {edad_mujer} años de edad, soltera, guatemalteca, quien se identifica con el DPI {dpi_mujer}, con el objeto de que AUTORICE SU MATRIMONIO CIVIL. PRIMERO: Los requirentes, bajo juramento prestado de conformidad con la ley, declaran sobre sus nombres, apellidos, edad, estado civil y nacionalidad, y que no están unidos con tercera persona ni ligados por vínculo matrimonial anterior. SEGUNDO: Hago saber a los contrayentes los deberes y derechos que nacen del matrimonio civil y el contenido de los artículos setenta y ocho y del ciento ocho al ciento catorce del Código Civil. TERCERO: Manifiestan que adoptan como régimen económico del matrimonio el de {regimen_economico}. CUARTO: Preguntados por separado si consienten en unirse en matrimonio civil, responden afirmativamente. En consecuencia, en nombre de la ley, los declaro formalmente unidos en MATRIMONIO CIVIL. Termino la presente acta en el mismo lugar y fecha, la cual leída es firmada por los contrayentes y la Notaria que autoriza y da fe."""
        },
        {
            "id": "not_autentica",
            "nombre": "Acta Notarial de Legalización de Firma (Auténtica)",
            "soporte": "Papel Bond adherido al documento matriz",
            "descripcion": "Certificación de firma estampada o reconocida a presencia del Notario.",
            "campos": ["lugar_fecha_letras", "notario", "firmante", "dpi_firmante", "documento_referencia"],
            "redaccion": """En la ciudad de Guatemala, el {lugar_fecha_letras}, como Notaria, DOY FE: Que la firma que antecede es AUTÉNTICA, por haber sido puesta el día de hoy en mi presencia por el señor {firmante}, quien se identifica con el Documento Personal de Identificación con Código Único de Identificación {dpi_firmante}, y calza un documento que se refiere a {documento_referencia}. La persona signataria firma nuevamente la presente acta de legalización conjuntamente con la Notaria que autoriza."""
        }
    ],

    "CIVIL": [
        {
            "id": "civ_promesa",
            "nombre": "Contrato de Promesa Bilateral de Compraventa",
            "soporte": "Papel Protocolo o Bond",
            "descripcion": "Compromiso de celebrar compraventa futura dentro de un plazo legal no mayor a 2 años.",
            "campos": ["fecha_letras", "promitente_vendedor", "promitente_comprador", "precio_total_letras", "enganche_letras", "plazo_letras"],
            "redaccion": """Comparecen {promitente_vendedor} y {promitente_comprador} celebrando PROMESA DE COMPRAVENTA: El promitente vendedor promete vender y el promitente comprador promete comprar el inmueble relacionado, por el precio de {precio_total_letras}, entregando en este acto la cantidad de {enganche_letras} como anticipo, pactando formalizar la escritura definitiva en el plazo forzoso de {plazo_letras}. Cláusula penal pactada por incumplimiento."""
        },
        {
            "id": "civ_mutuo",
            "nombre": "Contrato de Mutuo con Garantía Hipotecaria",
            "soporte": "Papel Sellado de Protocolo",
            "descripcion": "Préstamo de dinero con interés y constitución de hipoteca sobre bien inmueble.",
            "campos": ["acreedor", "deudor", "monto_prestamo_letras", "interes_porcentaje", "plazo_mutuo", "finca_hipoteca"],
            "redaccion": """Contrato de mutuo bancario/particular donde {acreedor} entrega a {deudor} la suma de {monto_prestamo_letras}, con una tasa de interés mensual de {interes_porcentaje}, pagadera en {plazo_mutuo}. Para garantizar el cumplimiento de la obligación, el deudor constituye primera hipoteca sobre la finca número {finca_hipoteca}."""
        },
        {
            "id": "civ_servicios",
            "nombre": "Contrato de Prestación de Servicios Profesionales",
            "soporte": "Papel Bond Común",
            "descripcion": "Contratación de servicios técnicos, legales o contables fijando honorarios.",
            "campos": ["cliente", "profesional", "objeto_servicio", "honorarios_letras", "forma_pago"],
            "redaccion": """{cliente} contrata los servicios profesionales de {profesional} para realizar {objeto_servicio}. Se pacta como contraprestación la suma de {honorarios_letras}, liquidada conforme {forma_pago}, sujetándose a las normas de entrega y confidencialidad."""
        },
        {
            "id": "civ_demanda_sumario",
            "nombre": "Demanda de Juicio Sumario de Desahucio y Cobro de Rentas",
            "soporte": "Memorial Judicial (Papel Bond membretado)",
            "descripcion": "Acción judicial ante Juzgado de Paz o Instancia Civil por falta de pago de rentas.",
            "campos": ["juzgado", "actor", "demandado", "meses_atraso", "monto_adeudado_letras"],
            "redaccion": """SEÑOR JUEZ DE PRIMERA INSTANCIA DEL RAMO CIVIL. {actor}, promueve JUICIO SUMARIO DE DESAHUCIO Y COBRO DE RENTAS ATRASADAS en contra de {demandado}, por adeudar {meses_atraso} meses de renta equivalentes a {monto_adeudado_letras}. Se solicita ordenar el desahucio y embargo precautorio."""
        },
        {
            "id": "civ_ejecutivo",
            "nombre": "Demanda de Juicio Ejecutivo en la Vía de Apremio",
            "soporte": "Memorial Judicial",
            "descripcion": "Ejecución judicial con base en título de crédito, escritura pública o saldo deudor.",
            "campos": ["juzgado", "ejecutante", "ejecutado", "titulo_ejecutivo", "saldo_reclamado"],
            "redaccion": """SEÑOR JUEZ DE PRIMERA INSTANCIA CIVIL. {ejecutante}, deduce JUICIO EJECUTIVO EN LA VÍA DE APREMIO contra {ejecutado}, fundado en el testimonio de escritura pública que contiene mutuo con garantía hipotecaria ({titulo_ejecutivo}), por el saldo líquido y exigible de Q. {saldo_reclamado}. Solicito mandamiento de ejecución y remate."""
        }
    ],

    "FAMILIA": [
        {
            "id": "fam_convenio_alimentos",
            "nombre": "Convenio de Pensión Alimenticia y Régimen de Relaciones",
            "soporte": "Documento Notarial o Memorial al Juzgado de Familia",
            "descripcion": "Fijación voluntaria de pensión mensual para hijos menores de edad y visitas.",
            "campos": ["padre_alimentante", "madre_representante", "hijos_menores", "monto_pension_letras", "forma_deposito"],
            "redaccion": """CONVENIO DE FIJACIÓN DE PENSIÓN ALIMENTICIA voluntaria otorgado entre {padre_alimentante} y {madre_representante} a favor de sus hijos {hijos_menores}. Se conviene como pensión la cantidad de {monto_pension_letras} mensuales, depositados en {forma_deposito}, más vestimenta y educación."""
        },
        {
            "id": "fam_demanda_alimentos",
            "nombre": "Demanda de Juicio Oral de Fijación de Pensión Alimenticia",
            "soporte": "Memorial Judicial",
            "descripcion": "Demanda ante Juzgado de Familia con solicitud de pensión provisional y arraigo.",
            "campos": ["juzgado_familia", "demandante", "demandado", "hijos", "pension_pretendida"],
            "redaccion": """JUZGADO DE PRIMERA INSTANCIA DE FAMILIA. {demandante}, en representación de sus hijos menores {hijos}, promueve JUICIO ORAL DE FIJACIÓN DE PENSIÓN ALIMENTICIA en contra de {demandado}. Petición: Se fije pensión alimenticia provisional de Q. {pension_pretendida}, se decrete el arraigo y embargo de salario."""
        },
        {
            "id": "fam_divorcio_mutuo",
            "nombre": "Convenio de Divorcio por Mutuo Consentimiento",
            "soporte": "Escritura de Convenio de Bases de Divorcio",
            "descripcion": "Bases de divorcio voluntario: alimentos, liquidación de bienes y patria potestad.",
            "campos": ["conyuge_a", "conyuge_b", "fecha_matrimonio", "pension_entre_conyuges", "liquidacion_bienes"],
            "redaccion": """CONVENIO DE BASES DE DIVORCIO VOLUNTARIO: {conyuge_a} y {conyuge_b}, contrajeron matrimonio el {fecha_matrimonio}. Convienen: 1) Patria potestad y guarda; 2) Pensión de cónyuges: {pension_entre_conyuges}; 3) Liquidación del patrimonio conyugal: {liquidacion_bienes}. Solicitan la disolución del vínculo conyugal."""
        },
        {
            "id": "fam_patrimonio_familiar",
            "nombre": "Constitución de Patrimonio Familiar sobre Vivienda",
            "soporte": "Escritura Pública en Protocolo",
            "descripcion": "Inafectabilidad de la vivienda familiar para proteger el techo de los hijos.",
            "campos": ["constituyente", "beneficiarios", "finca_familiar", "plazo_patrimonio"],
            "redaccion": """CONSTITUCIÓN DE PATRIMONIO FAMILIAR otorgado por {constituyente} a favor de {beneficiarios}, sobre la finca {finca_familiar}, con el objeto de que sea inembargable y destinada exclusivamente a morada y subsistencia familiar durante el plazo de {plazo_patrimonio}."""
        },
        {
            "id": "fam_tutela",
            "nombre": "Discernimiento y Aceptación de Cargo de Tutor",
            "soporte": "Acta Notarial o Diligencia Judicial",
            "descripcion": "Aceptación solemne del cargo de tutor y protutor para administración de menor.",
            "campos": ["notario_o_juez", "tutor", "menor_pupilo", "bienes_inventario"],
            "redaccion": """En la ciudad de Guatemala, comparece {tutor} para aceptar formalmente el cargo de TUTOR de {menor_pupilo}, prestando juramento de ley para cuidar diligentemente de su persona y administrar los bienes descritos en {bienes_inventario}."""
        }
    ],

    "PENAL": [
        {
            "id": "pen_querella",
            "nombre": "Querella Penal con Constitución en Querellante Adhesivo",
            "soporte": "Memorial Judicial ante Juez de Primera Instancia Penal",
            "descripcion": "Denuncia/querella formal con petición de persecución penal y medidas cautelares.",
            "campos": ["juzgado_penal", "querellante", "sindicado", "delito_imputado", "relacion_hechos"],
            "redaccion": """SEÑOR JUEZ DE PRIMERA INSTANCIA PENAL, NARCOACTIVIDAD Y DELITOS CONTRA EL AMBIENTE. {querellante}, promueve formal QUERELLA PENAL y constitución de QUERELLANTE ADHESIVO en contra de {sindicado}, por el delito de {delito_imputado}. Relación de Hechos: {relacion_hechos}. Petición: Se admita la querella y se cite o decrete orden de aprehensión."""
        },
        {
            "id": "pen_denuncia_mp",
            "nombre": "Memorial de Denuncia ante el Ministerio Público (Fiscalía)",
            "soporte": "Memorial ante Oficina de Atención Permanente del MP",
            "descripcion": "Puesta en conocimiento de hechos constitutivos de delito para inicio de investigación.",
            "campos": ["fiscalia", "denunciante", "denunciado", "delito", "pruebas_ofrecidas"],
            "redaccion": """SEÑOR AGENTE FISCAL DEL MINISTERIO PÚBLICO ({fiscalia}). Comparece {denunciante} interponiendo DENUNCIA PENAL en contra de {denunciado} por la posible comisión del delito de {delito}. Medios de convicción que se ofrecen: {pruebas_ofrecidas}."""
        },
        {
            "id": "pen_medidas_desjudicializadoras",
            "nombre": "Solicitud de Criterio de Oportunidad o Suspensión Condicional",
            "soporte": "Memorial ante Juzgado de Paz / Instancia Penal",
            "descripcion": "Mecanismo alterno de solución del conflicto penal con reparación digna del daño.",
            "campos": ["juzgado", "abogado_defensor", "imputado", "acuerdo_reparatorio"],
            "redaccion": """SEÑOR JUEZ DE PRIMERA INSTANCIA PENAL. La defensa técnica del sindicado {imputado}, solicita la aplicación de un CRITERIO DE OPORTUNIDAD conforme al artículo 25 del Código Procesal Penal, en virtud de haberse llegado a un acuerdo de reparación digna consistente en: {acuerdo_reparatorio}."""
        },
        {
            "id": "pen_oposicion_medidas",
            "nombre": "Oposición a Medida de Coerción y Solicitud de Medida Sustitutiva",
            "soporte": "Memorial de Audiencia de Primera Declaración",
            "descripcion": "Petición de arresto domiciliario o fianza económica demostrando arraigo.",
            "campos": ["juez_control", "sindicado", "delito", "documentos_arraigo"],
            "redaccion": """SEÑOR JUEZ DE CONTROL DE GARANTÍAS. En el proceso penal que se instruye contra {sindicado} por el delito de {delito}, solicito la reforma del auto de prisión preventiva o imposición de MEDIDAS SUSTITUTIVAS de arresto domiciliario y caución económica, habiendo acreditado fehacientemente arraigo domiciliar, familiar y laboral mediante: {documentos_arraigo}."""
        },
        {
            "id": "pen_desistimiento_criterio",
            "nombre": "Desistimiento de la Acción Penal y Extinción de Responsabilidad",
            "soporte": "Memorial Penal con Firma Legalizada o Ratificación",
            "descripcion": "Desistimiento en delitos de acción privada o mediante satisfacción de la pretensión civil.",
            "campos": ["juez_penal", "agraviado", "imputado", "causa_penal"],
            "redaccion": """SEÑOR JUEZ DE PRIMERA INSTANCIA PENAL. {agraviado}, en la causa penal número {causa_penal}, manifiesta que ha sido enteramente resarcido de los daños y perjuicios ocasionados por {imputado}, por lo que formalmente DESISTE de la acción penal y de su participación como querellante adhesivo, solicitando el sobreseimiento."""
        }
    ]
}
