CATALOGO_PLANTILLAS = {
    "NOTARIAL": [
        {
            "id": "not_compraventa",
            "nombre": "Compraventa de Bien Inmueble al Contado (Protocolo)",
            "soporte": "Protocolo (Art. 29, 38 y 45 Código de Notariado, Dto. 314; Art. 1790 Código Civil)",
            "descripcion": "Escritura traslativa de dominio con comparecencia completa, DPI y datos registrales en letras, saneamiento de ley, cierre notarial y ANTE MÍ.",
            "campos": [
                "numero_escritura",
                "lugar_y_fecha_letras",
                "notario",
                "vendedor_nombre",
                "vendedor_edad_estado_prof_dom",
                "dpi_vendedor",
                "comprador_nombre",
                "comprador_edad_estado_prof_dom",
                "dpi_comprador",
                "finca",
                "folio",
                "libro",
                "departamento_registro",
                "direccion_inmueble",
                "monto_precio",
            ],
            "redaccion": (
                "NÚMERO {numero_escritura}. En {lugar_y_fecha_letras}, "
                "ANTE MÍ: {notario}, Notario, comparecen: por una parte, {vendedor_nombre}, "
                "{vendedor_edad_estado_prof_dom}, quien se identifica con el Documento Personal de Identificación "
                "con Código Único de Identificación número {dpi_vendedor}, extendido por el Registro Nacional de las "
                "Personas de la República de Guatemala; y por la otra parte, {comprador_nombre}, "
                "{comprador_edad_estado_prof_dom}, quien se identifica con el Documento Personal de Identificación "
                "con Código Único de Identificación número {dpi_comprador}, extendido por el Registro Nacional de las "
                "Personas de la República de Guatemala. Los comparecientes me aseguran hallarse en el libre ejercicio "
                "de sus derechos civiles y que por el presente instrumento otorgan CONTRATO DE COMPRAVENTA DE BIEN INMUEBLE "
                "AL CONTADO, de conformidad con las siguientes cláusulas: PRIMERA: Manifiesta {vendedor_nombre}, "
                "en lo sucesivo llamado La Parte Vendedora, bajo juramento solemne prestado conforme a la ley y advertido por el "
                "infrascrito Notario de las penas relativas al delito de perjurio, que es legítimo propietario de la finca "
                "rústica o urbana inscrita en el Registro General de la Propiedad bajo el número {finca}, folio {folio}, "
                "del libro {libro} de {departamento_registro}, ubicada en {direccion_inmueble}, con las medidas, área "
                "y colindancias que constan en su primera inscripción de dominio. SEGUNDA: Continúa manifestando La Parte Vendedora "
                "que por el precio de {monto_precio}, que tiene por recibidos a su entera satisfacción al contado, VENDE, "
                "CEDE Y TRASPASA a favor de {comprador_nombre} el bien inmueble identificado en la cláusula primera, "
                "con todo cuanto de hecho y por derecho le corresponde al mismo. TERCERA: De manera expresa declara La Parte "
                "Vendedora que sobre el inmueble objeto de la presente compraventa no pesan gravámenes, anotaciones ni "
                "limitaciones que puedan perjudicar los derechos de la parte compradora, obligándose en todo caso al "
                "saneamiento de ley. CUARTA: Por su parte manifiesta {comprador_nombre} que en los términos "
                "relacionados ACEPTA expresamente la venta que se le hace y se da por recibido del bien inmueble. "
                "Yo, el Notario, DOY FE: a) Que todo lo escrito me fue expuesto; b) Que tuve a la vista los Documentos "
                "Personales de Identificación relacionados y el título con que se acredita la propiedad del inmueble; "
                "c) Que advertí a los otorgantes de los efectos legales del presente contrato y de la obligación del "
                "pago del impuesto fiscal o del Impuesto al Valor Agregado según corresponda, así como del registro del "
                "testimonio respectivo y remisión de los avisos notariales de ley; y d) Que leí íntegramente lo escrito "
                "a los otorgantes, quienes bien enterados de su contenido, objeto, validez y demás efectos legales, lo "
                "ratifican, aceptan y firman juntamente con el Notario que autoriza.\n"
                "f) ____________________________    f) ____________________________\n"
                "ANTE MÍ:\n"
                "f) ____________________________  ({notario}, Notario)"
            ),
        },
        {
            "id": "not_mandato_general",
            "nombre": "Mandato General con Representación y Cláusula Especial (Protocolo)",
            "soporte": "Protocolo (Art. 29 CDN; Art. 1686-1704 Código Civil; Art. 5 num. 8 Dto. 37-92)",
            "descripcion": "Escritura de Mandato General con cláusula especial para enajenar o gravar, lista para Protocolo y Registro Electrónico de Poderes.",
            "campos": [
                "numero_escritura",
                "lugar_y_fecha_letras",
                "notario",
                "mandante_nombre",
                "mandante_edad_estado_prof_dom",
                "dpi_mandante",
                "mandatario_nombre",
                "mandatario_edad_estado_prof_dom",
                "dpi_mandatario",
                "parentesco_o_calidad",
                "facultades_especiales",
            ],
            "redaccion": (
                "NÚMERO {numero_escritura}. En {lugar_y_fecha_letras}, "
                "ANTE MÍ: {notario}, Notario, comparece {mandante_nombre}, {mandante_edad_estado_prof_dom}, "
                "quien se identifica con el Documento Personal de Identificación con Código Único de Identificación "
                "número {dpi_mandante}, extendido por el Registro Nacional de las Personas de la República de Guatemala. "
                "El compareciente me asegura encontrarse en el libre ejercicio de sus derechos civiles y que por este acto "
                "otorga MANDATO GENERAL CON REPRESENTACIÓN Y CLÁUSULA ESPECIAL, contenido en las cláusulas siguientes: "
                "PRIMERA: Manifiesta {mandante_nombre} que por este instrumento otorga MANDATO GENERAL CON "
                "REPRESENTACIÓN a favor de {mandatario_nombre} ({parentesco_o_calidad}), {mandatario_edad_estado_prof_dom}, "
                "identificado con el Documento Personal de Identificación con Código Único de Identificación número "
                "{dpi_mandatario}, para que en su nombre y representación administre todos sus bienes, derechos e intereses "
                "en la República de Guatemala. SEGUNDA: Además de las facultades inherentes al mandato general, El Mandante "
                "confiere CLÁUSULA ESPECIAL expresa al Mandatario conforme el Artículo mil seiscientos noventa y tres "
                "del Código Civil para que pueda: {facultades_especiales}, incluyendo vender, hipotecar, afianzar, transigir "
                "y otorgar los instrumentos públicos necesarios. TERCERA: El presente mandato se ejerce de manera gratuita "
                "o con la retribución que acuerden, obligándose el Mandatario a rendir cuentas de su gestión. Yo, el Notario, "
                "DOY FE: a) Que todo lo escrito me fue expuesto; b) Que tuve a la vista el Documento Personal de Identificación "
                "del otorgante; c) Que advertí al otorgante de la obligación de inscribir el testimonio de la presente escritura "
                "en el Registro Electrónico de Poderes del Archivo General de Protocolos y cubrir los timbres fiscales y "
                "notariales de ley; y d) Que leí lo escrito al otorgante, quien enterado de su contenido, objeto, validez y "
                "efectos legales, lo ratifica, acepta y firma.\n"
                "f) ____________________________\n"
                "ANTE MÍ:\n"
                "f) ____________________________  ({notario}, Notario)"
            ),
        },
        {
            "id": "not_declaracion_jurada",
            "nombre": "Acta Notarial de Declaración Jurada (Papel Bond / Fuera de Protocolo)",
            "soporte": "Acta Notarial (Art. 60-62 Código de Notariado; Timbre Fiscal Q.0.50/hoja + Notarial Q.10.00)",
            "descripcion": "Acta notarial bajo juramento solemne con advertencia de delito de perjurio (Art. 459 Código Penal), generada en formato de Acta Notarial.",
            "campos": [
                "ciudad_y_fecha",
                "hora_letras",
                "direccion_oficina",
                "notario",
                "requirente_nombre",
                "requirente_generales",
                "dpi_requirente",
                "hechos_declarados",
                "hora_cierre",
            ],
            "redaccion": (
                "En {ciudad_y_fecha}, siendo las {hora_letras}, situado en mi oficina profesional ubicada en "
                "{direccion_oficina}, YO: {notario}, Notario, soy requerido por {requirente_nombre}, "
                "{requirente_generales}, quien se identifica con el Documento Personal de Identificación con Código "
                "Único de Identificación número {dpi_requirente}, extendido por el Registro Nacional de las Personas de "
                "la República de Guatemala, con el objeto de hacer constar DECLARACIÓN JURADA, procediéndose para el efecto "
                "de la manera siguiente:\n\n"
                "PRIMERO: El requirente manifiesta que solicita mis servicios notariales para prestar declaración bajo "
                "juramento solemne de ley, por lo que procedo a juramentarlo de la forma siguiente: ¿Prometéis bajo "
                "juramento decir la verdad en lo que fuereis preguntado y manifestado?, a lo que responde: SÍ, BAJO "
                "JURAMENTO PROMETO DECIR LA VERDAD; seguidamente le hice saber lo relativo a las penas que la ley "
                "establece para el delito de perjurio (Artículo cuatrocientos cincuenta y nueve del Código Penal).\n\n"
                "SEGUNDO: Bajo el juramento prestado, declara libre y espontáneamente el requirente: {hechos_declarados}.\n\n"
                "TERCERO: No habiendo más que hacer constar, se da por terminada la presente acta notarial en el mismo "
                "lugar y fecha de su inicio, siendo las {hora_cierre}, la cual queda contenida en las hojas útiles de "
                "papel bond que se numeran, sellan y firman conforme al Artículo sesenta y dos del Código de Notariado, "
                "adhiriéndose los timbres fiscales y notariales de ley. Leo íntegramente lo escrito al requirente, quien "
                "enterado de su contenido, objeto, validez y efectos legales, la acepta, ratifica y firma juntamente con "
                "el infrascrito Notario que de todo lo actuado DOY FE."
            ),
        },
        {
            "id": "not_arrendamiento",
            "nombre": "Contrato de Arrendamiento de Bien Inmueble (Protocolo)",
            "soporte": "Protocolo (Art. 29 Código de Notariado; Art. 1880 Código Civil)",
            "descripcion": "Escritura de arrendamiento con generales completos (Art. 29 num. 2), plazo y rentas en letras, advertencias legales y ANTE MÍ.",
            "campos": [
                "numero_escritura",
                "lugar_y_fecha_letras",
                "notario",
                "arrendante_nombre",
                "arrendante_edad_estado_prof_dom",
                "dpi_arrendante",
                "arrendatario_nombre",
                "arrendatario_edad_estado_prof_dom",
                "dpi_arrendatario",
                "direccion_inmueble",
                "plazo_meses_letras",
                "renta_mensual",
                "deposito_garantia",
            ],
            "redaccion": (
                "NÚMERO {numero_escritura}. En {lugar_y_fecha_letras}, "
                "ANTE MÍ: {notario}, Notario, comparecen: por una parte, {arrendante_nombre}, "
                "{arrendante_edad_estado_prof_dom}, quien se identifica con Documento Personal de Identificación con Código "
                "Único de Identificación número {dpi_arrendante}, extendido por el Registro Nacional de las Personas; y por "
                "la otra parte, {arrendatario_nombre}, {arrendatario_edad_estado_prof_dom}, quien se identifica con Documento "
                "Personal de Identificación con Código Único de Identificación número {dpi_arrendatario}, extendido por el "
                "Registro Nacional de las Personas. Los comparecientes aseguran hallarse en el libre ejercicio de sus derechos "
                "civiles y otorgan CONTRATO DE ARRENDAMIENTO DE BIEN INMUEBLE conforme las cláusulas siguientes: PRIMERA: "
                "{arrendante_nombre} da en arrendamiento a {arrendatario_nombre} el inmueble ubicado en {direccion_inmueble}. "
                "SEGUNDA: El plazo del arrendamiento será de {plazo_meses_letras}, pudiendo prorrogarse por cruce de cartas "
                "con treinta días de anticipación. TERCERA: La renta mensual pactada es de {renta_mensual}, pagadera de forma "
                "anticipada dentro de los primeros cinco días de cada mes, entregando en este acto en calidad de depósito de "
                "garantía la cantidad de {deposito_garantia}. CUARTA: El inmueble será destinado exclusivamente para el uso "
                "convenido, quedando prohibido subarrendar total o parcialmente sin consentimiento escrito del arrendante; "
                "la falta de pago de dos mensualidades consecutivas dará derecho a dar por vencido el plazo y exigir la "
                "desocupación judicial. QUINTA: Ambos comparecientes aceptan el contenido del presente instrumento. Yo, el "
                "Notario, DOY FE: a) De todo lo expuesto; b) De haber tenido a la vista los documentos de identificación "
                "relacionados; c) De haber advertido a los otorgantes los efectos legales, fiscales y registrales cuando "
                "corresponda; y d) De haber leído íntegramente lo escrito a los otorgantes, quienes enterados de su contenido, "
                "objeto, validez y efectos legales, lo ratifican, aceptan y firman.\n"
                "f) ____________________________    f) ____________________________\n"
                "ANTE MÍ:\n"
                "f) ____________________________  ({notario}, Notario)"
            ),
        },
        {
            "id": "not_carta_pago",
            "nombre": "Carta Total de Pago y Liberación de Hipoteca (Protocolo)",
            "soporte": "Protocolo (Art. 29 CDN; Art. 841 Código Civil)",
            "descripcion": "Escritura unilateral con generales completos (Art. 29 num. 2), departamento RGP, solicitud de cancelación de hipoteca y ANTE MÍ.",
            "campos": [
                "numero_escritura",
                "lugar_y_fecha_letras",
                "notario",
                "acreedor_nombre",
                "acreedor_edad_estado_prof_dom",
                "dpi_acreedor",
                "deudor_nombre",
                "escritura_origen_num",
                "notario_origen",
                "fecha_origen",
                "finca",
                "folio",
                "libro",
                "departamento_registro",
                "monto_pagado",
            ],
            "redaccion": (
                "NÚMERO {numero_escritura}. En {lugar_y_fecha_letras}, "
                "ANTE MÍ: {notario}, Notario, comparece {acreedor_nombre}, {acreedor_edad_estado_prof_dom}, quien "
                "se identifica con Documento Personal de Identificación con Código Único de Identificación número "
                "{dpi_acreedor}, extendido por el Registro Nacional de las Personas de la República de Guatemala. "
                "El compareciente asegura encontrarse en el libre ejercicio de sus derechos civiles y otorga CARTA TOTAL DE "
                "PAGO Y LIBERACIÓN DE GRAVAMEN HIPOTECARIO, bajo las siguientes cláusulas: PRIMERA: Manifiesta el otorgante "
                "que mediante escritura pública número {escritura_origen_num}, autorizada el {fecha_origen} ante los oficios "
                "del Notario {notario_origen}, concedió mutuo con garantía hipotecaria a {deudor_nombre} por la suma de "
                "{monto_pagado}, garantizado con hipoteca inscrita sobre la finca número {finca}, folio {folio}, libro {libro} "
                "de {departamento_registro}. SEGUNDA: Declara expresamente el otorgante que a la presente fecha el deudor le "
                "ha cancelado totalmente capital e intereses pactados, sin que quede saldo alguno pendiente, por lo que otorga "
                "la más eficaz y total CARTA DE PAGO y solicita al Registrador General de la Propiedad se sirva cancelar "
                "totalmente la inscripción hipotecaria que pesa sobre la finca descrita. Yo, el Notario, DOY FE: a) De todo "
                "lo expuesto; b) De haber tenido a la vista el documento de identificación relacionado; c) De haber advertido "
                "al otorgante los efectos legales y la obligación de inscribir el testimonio respectivo en el Registro General "
                "de la Propiedad; y d) De haber leído lo escrito al otorgante, quien enterado de su contenido y efectos "
                "legales lo ratifica, acepta y firma.\n"
                "f) ____________________________\n"
                "ANTE MÍ:\n"
                "f) ____________________________  ({notario}, Notario)"
            ),
        },
    ],
    "CIVIL": [
        {
            "id": "civ_demanda_ejecutiva",
            "nombre": "Demanda de Juicio Ejecutivo Común (Título Ejecutivo)",
            "soporte": "Memorial Judicial (Art. 61, 63, 106, 327 y ss. Código Procesal Civil y Mercantil)",
            "descripcion": "Memorial inicial ejecutivo con hechos, fundamento de derecho, pruebas, peticiones de mandamiento de ejecución y embargo.",
            "campos": [
                "juzgado",
                "actor_nombre",
                "actor_generales",
                "dpi_actor",
                "abogado_auxiliante",
                "casillero_electronico",
                "demandado_nombre",
                "direccion_notificacion_demandado",
                "titulo_ejecutivo_desc",
                "monto_capital",
            ],
            "redaccion": (
                "JUICIO EJECUTIVO NUEVO.\n\n"
                "{actor_nombre}, {actor_generales}, me identifico con Documento Personal de Identificación con Código Único "
                "de Identificación número {dpi_actor}; actúo bajo la dirección y procuración del Abogado {abogado_auxiliante} "
                "y señalo lugar para recibir notificaciones el casillero electrónico {casillero_electronico}. Ante usted "
                "respetuosamente comparezco a promover JUICIO EJECUTIVO en contra de {demandado_nombre}, quien puede ser "
                "notificado en {direccion_notificacion_demandado}, con base en la siguiente relación de:\n\n"
                "I. HECHOS:\n"
                "A) Del Título Ejecutivo: Conforme consta en {titulo_ejecutivo_desc}, el hoy ejecutado se reconoció deudor "
                "liso y llano por la cantidad líquida, exigible y de plazo vencido de {monto_capital}, más intereses y costas.\n"
                "B) Incumplimiento: No obstante los múltiples requerimientos extrajudiciales efectuados, el ejecutado ha "
                "omitido el pago de la suma adeudada, haciéndose necesaria la presente acción ejecutiva.\n\n"
                "II. FUNDAMENTO DE DERECHO:\n"
                "Establece el Artículo 327 del Código Procesal Civil y Mercantil que procede el juicio ejecutivo cuando se "
                "promueve en virtud de los títulos allí enumerados, siempre que traigan aparejada la obligación de pagar "
                "cantidad de dinero líquida y exigible; y conforme al Artículo 329 del mismo cuerpo legal, promovido el juicio "
                "el Juez calificará el título y si lo considerare suficiente despachará mandamiento de ejecución.\n\n"
                "III. MEDIOS DE PRUEBA:\n"
                "1) DOCUMENTOS: El título ejecutivo consistente en {titulo_ejecutivo_desc}, que adjunto en original.\n"
                "2) Presunciones legales y humanas que de los hechos probados se deriven.\n\n"
                "IV. PETICIONES:\n"
                "DE TRÁMITE: 1) Se admita para su trámite la presente demanda de Juicio Ejecutivo y se forme el expediente; "
                "2) Se reconozca la dirección, procuración y casillero electrónico señalados; 3) Calificado el título, se "
                "despache mandamiento de ejecución ordenando el requerimiento de pago al ejecutado por la suma de {monto_capital} "
                "más un diez por ciento para costas procesales, y en caso de no pagar en el acto, se trabe embargo sobre bienes "
                "suficientes que alcancen a cubrir lo reclamado; 4) Se confiera audiencia al ejecutado por el plazo de cinco días "
                "para que se oponga o haga valer sus excepciones.\n"
                "DE FONDO: Que en su oportunidad procesal se dicte sentencia declarando CON LUGAR la presente demanda ejecutiva, "
                "haciendo trance y remate con los bienes embargados y pago al acreedor, condenando en costas al ejecutado.\n\n"
                "CITA DE LEYES: Artículos 28, 29, 44, 50, 61, 63, 66, 79, 106, 107, 177, 327, 328, 329, 330, 331 y 332 del Código "
                "Procesal Civil y Mercantil. Acompaño duplicado y dos copias del presente memorial y documentos adjuntos."
            ),
        },
        {
            "id": "civ_sumario_desahucio",
            "nombre": "Demanda Sumaria de Desocupación y Cobro de Rentas",
            "soporte": "Memorial Judicial (Art. 61, 63, 229 num. 1 y 237-243 CPCyM)",
            "descripcion": "Demanda en vía sumaria con generales Art. 61 num. 2, casillero electrónico y copias de ley.",
            "campos": [
                "juzgado",
                "actor_nombre",
                "actor_generales",
                "dpi_actor",
                "abogado_auxiliante",
                "casillero_electronico",
                "inquilino_nombre",
                "direccion_inmueble",
                "meses_adeudados",
                "monto_adeudado",
            ],
            "redaccion": (
                "JUICIO SUMARIO DE DESOCUPACIÓN Y COBRO DE RENTAS NUEVO.\n\n"
                "{actor_nombre}, {actor_generales}, identificado con DPI con CUI número {dpi_actor}, bajo la dirección "
                "y procuración del Abogado {abogado_auxiliante}, señalando casillero electrónico {casillero_electronico}, ante "
                "usted comparezco a promover JUICIO SUMARIO DE DESOCUPACIÓN Y COBRO DE RENTAS ATRASADAS en contra de "
                "{inquilino_nombre}, quien puede ser notificado en el propio inmueble arrendado ubicado en {direccion_inmueble}, "
                "exponiendo:\n\n"
                "I. HECHOS:\n"
                "Di en arrendamiento al demandado el inmueble ubicado en {direccion_inmueble}; sin embargo, a la fecha ha "
                "dejado de pagar {meses_adeudados} de renta, adeudando la suma total de {monto_adeudado}, razón por la cual "
                "procede judicialmente su desocupación y el pago de las rentas insolutas.\n\n"
                "II. FUNDAMENTO DE DERECHO:\n"
                "Conforme a los Artículos 229 numeral 1o. y 237 del Código Procesal Civil y Mercantil, se tramitarán en juicio "
                "sumario los asuntos de arrendamiento y desocupación.\n\n"
                "III. PETICIONES:\n"
                "DE TRÁMITE: Admitir la demanda y emplazar al demandado por el plazo de tres días bajo apercibimiento de que "
                "si no se opusiere se ordenará la desocupación sin más trámite; DE FONDO: En sentencia declarar con lugar "
                "la desocupación fijando el plazo de ley para desalojar bajo apercibimiento de lanzamiento a su costa, más el "
                "pago de {monto_adeudado} y costas.\n\n"
                "CITA DE LEYES: Artículos 61, 63, 106, 229, 230, 237, 238, 240 y 241 del CPCyM. Acompaño duplicado y dos copias."
            ),
        },
        {
            "id": "civ_ejecutivo_cambiario",
            "nombre": "Acción Cambiaria en Vía Directa (Pagaré / Cheque / Letra)",
            "soporte": "Memorial Judicial (Art. 615-630 Código de Comercio; Art. 61, 63 y 327 CPCyM)",
            "descripcion": "Demanda ejecutiva mercantil basada en título de crédito con generales completos y copias.",
            "campos": [
                "juzgado",
                "actor_nombre",
                "actor_generales",
                "dpi_actor",
                "abogado_auxiliante",
                "casillero_electronico",
                "deudor_nombre",
                "direccion_deudor",
                "titulo_credito_tipo_y_numero",
                "fecha_vencimiento",
                "monto_titulo",
            ],
            "redaccion": (
                "JUICIO EJECUTIVO EN EJERCICIO DE LA ACCIÓN CAMBIARIA NUEVO.\n\n"
                "{actor_nombre}, {actor_generales}, identificado con DPI con CUI número {dpi_actor}, bajo la dirección y procuración del Abogado "
                "{abogado_auxiliante} y casillero electrónico {casillero_electronico}, promuevo JUICIO EJECUTIVO en ejercicio "
                "de la ACCIÓN CAMBIARIA EN VÍA DIRECTA contra {deudor_nombre}, notificable en {direccion_deudor}:\n\n"
                "I. HECHOS: El demandado libró o aceptó a mi favor el título de crédito consistente en {titulo_credito_tipo_y_numero}, "
                "con vencimiento el {fecha_vencimiento}, por valor de {monto_titulo}, el cual no fue pagado a su presentación.\n\n"
                "II. FUNDAMENTO DE DERECHO: Artículos 615, 616, 621 y 630 del Código de Comercio y 327 del CPCyM.\n\n"
                "III. PETICIÓN: Se despache mandamiento de ejecución y embargo sobre bienes del demandado por la suma de "
                "{monto_titulo}, intereses moratorios y costas procesales; en sentencia, se declare con lugar la acción cambiaria.\n\n"
                "CITA DE LEYES: Artículos 615 al 630 del Código de Comercio; 61, 63, 106, 327, 329 y 331 del CPCyM. Acompaño duplicado y dos copias."
            ),
        },
        {
            "id": "civ_ampliacion_o_memorial_simple",
            "nombre": "Memorial de Evacuación de Audiencia / Subsanación de Previos",
            "soporte": "Memorial Judicial (Art. 61, 63 y 109 Código Procesal Civil y Mercantil)",
            "descripcion": "Escrito de trámite para cumplir previos o evacuar audiencia dentro de proceso iniciado.",
            "campos": [
                "juzgado",
                "numero_expediente_judicial",
                "oficial_notificador",
                "presentado_nombre",
                "abogado_auxiliante",
                "casillero_electronico",
                "contenido_cumplimiento",
            ],
            "redaccion": (
                "EXPEDIENTE NÚMERO: {numero_expediente_judicial} — OFICIAL: {oficial_notificador}.\n\n"
                "{presentado_nombre}, de datos de identificación personal conocidos dentro del expediente arriba identificado, "
                "actuando bajo la dirección y procuración del Abogado {abogado_auxiliante}, respetuosamente comparezco ante usted "
                "y para el efecto:\n\n"
                "EXPONGO:\n"
                "Que fui notificado de la resolución dictada por ese órgano jurisdiccional mediante la cual se me confiere audiencia "
                "o se imponen requisitos previos; por lo que estando dentro del plazo legal conferido, comparezco a evacuar "
                "y subsanar en los términos siguientes: {contenido_cumplimiento}.\n\n"
                "PETICIÓN:\n"
                "1) Se incorpore a sus antecedentes el presente memorial; 2) Se tenga por evacuada en tiempo la audiencia o por "
                "cumplidos los requisitos previos ordenados, continuándose el trámite que en derecho corresponde.\n\n"
                "CITA DE LEYES: Artículos 28 de la Constitución Política de la República; 61, 62, 63, 66, 79 y 109 del CPCyM. "
                "Acompaño duplicado y copias de ley."
            ),
        },
        {
            "id": "civ_voluntario_cambio_nombre",
            "nombre": "Diligencias Voluntarias Judiciales de Cambio de Nombre",
            "soporte": "Memorial Judicial (Art. 61, 63, 438-439 CPCyM; Dto. 54-77 si es vía notarial)",
            "descripcion": "Escrito inicial ante Juez de Primera Instancia Civil para autorización de cambio de nombre.",
            "campos": [
                "juzgado",
                "solicitante_nombre_actual",
                "solicitante_generales",
                "dpi_solicitante",
                "abogado_auxiliante",
                "casillero_electronico",
                "nuevo_nombre_propuesto",
                "motivos_cambio",
            ],
            "redaccion": (
                "DILIGENCIAS VOLUNTARIAS JUDICIALES DE CAMBIO DE NOMBRE NUEVO.\n\n"
                "{solicitante_nombre_actual}, {solicitante_generales}, identificado con DPI con CUI número {dpi_solicitante}, bajo la dirección y "
                "procuración del Abogado {abogado_auxiliante}, casillero electrónico {casillero_electronico}, ante usted "
                "promuevo DILIGENCIAS VOLUNTARIAS DE CAMBIO DE NOMBRE:\n\n"
                "I. HECHOS: Mi nacimiento se encuentra inscrito en el Registro Civil de las Personas del RENAP bajo el nombre "
                "de {solicitante_nombre_actual}. Por las razones siguientes: {motivos_cambio}, deseo adoptar el nombre de "
                "{nuevo_nombre_propuesto}, sin causar perjuicio a terceros.\n\n"
                "II. FUNDAMENTO DE DERECHO: Artículos 6 del Código Civil y 438 y 439 del CPCyM.\n\n"
                "III. PETICIONES: Se reciban los documentos probatorios (certificación de nacimiento, antecedentes penales y "
                "policíacos), se publiquen los edictos en el Diario Oficial por tres veces durante treinta días, y sin oposición "
                "se dicte auto declarando con lugar el cambio de nombre e inscribiéndose en RENAP.\n\n"
                "CITA DE LEYES: Artículos 6 y 7 del Código Civil; 61, 63, 401, 402, 438 y 439 del CPCyM. Acompaño duplicado y dos copias."
            ),
        },
    ],
    "FAMILIA": [
        {
            "id": "fam_fijacion_alimentos",
            "nombre": "Demanda Oral de Fijación de Pensión Alimenticia y Pensión Provisional",
            "soporte": "Memorial Judicial (Art. 61, 63, 199-216 CPCyM; Ley de Tribunales de Familia)",
            "descripcion": "Demanda en juicio oral de familia con generales Art. 61, pensión provisional y arraigo.",
            "campos": [
                "juzgado_familia",
                "madre_o_actora",
                "actora_generales",
                "dpi_actora",
                "menores_beneficiarios",
                "abogado_auxiliante",
                "casillero_electronico",
                "demandado_nombre",
                "direccion_demandado",
                "pension_solicitada",
            ],
            "redaccion": (
                "JUICIO ORAL DE FIJACIÓN DE PENSIÓN ALIMENTICIA NUEVO.\n\n"
                "{madre_o_actora}, {actora_generales}, identificada con DPI con CUI número {dpi_actora}, actuando en nombre propio y en "
                "representación legal de mis menores hijos {menores_beneficiarios}, bajo dirección y procuración del Abogado "
                "{abogado_auxiliante}, casillero electrónico {casillero_electronico}, promuevo JUICIO ORAL DE FIJACIÓN DE "
                "PENSIÓN ALIMENTICIA en contra de {demandado_nombre}, notificable en {direccion_demandado}:\n\n"
                "I. HECHOS: El demandado es padre de los menores mencionados según certificaciones de nacimiento adjuntas, y "
                "tiene capacidad económica suficiente, requiriéndose una pensión mensual acorde a sus necesidades básicas "
                "de sustento, habitación, vestido, educación y salud de {pension_solicitada}.\n\n"
                "II. FUNDAMENTO DE DERECHO: Artículos 278 al 292 del Código Civil; 199 y 212 al 216 del CPCyM.\n\n"
                "III. PETICIONES: DE TRÁMITE: 1) Se señale audiencia para juicio oral bajo apercibimiento de continuar en rebeldía "
                "y declararse confeso al demandado si no comparece; 2) Con carácter urgente se fije PENSIÓN PROVISIONAL por la "
                "cantidad de {pension_solicitada} y se decrete medida precautoria de arraigo contra el demandado. DE FONDO: En "
                "sentencia se fije pensión alimenticia definitiva garantizada conforme la ley.\n\n"
                "CITA DE LEYES: Artículos 51 y 55 de la Constitución; 278-292 del Código Civil; 61, 63, 199, 212, 213, 214 y 215 del CPCyM. "
                "Acompaño duplicado y dos copias."
            ),
        },
        {
            "id": "fam_divorcio_mutuo",
            "nombre": "Solicitud Voluntaria de Divorcio por Mutuo Consentimiento",
            "soporte": "Memorial Judicial (Art. 153-163 Código Civil; Art. 61, 63, 426-433 CPCyM)",
            "descripcion": "Memorial conjunto con generales completos, proyecto de bases de divorcio y copias de ley.",
            "campos": [
                "juzgado_familia",
                "conyuge_1",
                "generales_conyuge_1",
                "dpi_conyuge_1",
                "conyuge_2",
                "generales_conyuge_2",
                "dpi_conyuge_2",
                "abogado_auxiliante",
                "casillero_electronico",
                "fecha_matrimonio",
                "bases_convenio",
            ],
            "redaccion": (
                "DILIGENCIAS VOLUNTARIAS DE DIVORCIO POR MUTUO CONSENTIMIENTO.\n\n"
                "{conyuge_1}, {generales_conyuge_1}, con DPI CUI {dpi_conyuge_1}, y {conyuge_2}, {generales_conyuge_2}, "
                "con DPI CUI {dpi_conyuge_2}, bajo la dirección del Abogado {abogado_auxiliante}, casillero electrónico "
                "{casillero_electronico}, comparecemos voluntariamente:\n\n"
                "I. HECHOS: Contrajimos matrimonio civil el {fecha_matrimonio} ante el Registro Civil del RENAP. Por mutuo "
                "acuerdo hemos decidido disolver el vínculo conyugal presentando las siguientes BASES DEL CONVENIO DE DIVORCIO:\n"
                "{bases_convenio}\n\n"
                "II. FUNDAMENTO DE DERECHO: Artículos 153, 154 numeral 1o. y 163 del Código Civil; 426 al 431 del CPCyM.\n\n"
                "III. PETICIÓN: Se señale junta conciliatoria de ley, se apruebe el proyecto de convenio de bases y en sentencia "
                "se declare disuelto nuestro matrimonio civil librando certificación al RENAP.\n\n"
                "CITA DE LEYES: Artículos 153-163 del Código Civil; 61, 63 y 426-433 del CPCyM. Acompañamos duplicado y dos copias."
            ),
        },
        {
            "id": "fam_ejecutivo_alimentos",
            "nombre": "Juicio Ejecutivo en Vía de Apremio por Pensiones Atrasadas",
            "soporte": "Memorial Judicial (Art. 61, 63, 294 CPCyM; Art. 242 Código Penal)",
            "descripcion": "Ejecución directa en vía de apremio con liquidación de pensiones vencidas, casillero y certificación a MP.",
            "campos": [
                "juzgado_familia",
                "numero_expediente_familia",
                "ejecutante_nombre",
                "ejecutante_generales",
                "dpi_ejecutante",
                "abogado_auxiliante",
                "casillero_electronico",
                "ejecutado_nombre",
                "meses_atrasados",
                "total_adeudado",
            ],
            "redaccion": (
                "EJECUCIÓN EN VÍA DE APREMIO — EXPEDIENTE REF.: {numero_expediente_familia}.\n\n"
                "{ejecutante_nombre}, {ejecutante_generales}, identificada con DPI CUI {dpi_ejecutante}, bajo dirección del "
                "Abogado {abogado_auxiliante}, señalando casillero electrónico {casillero_electronico}, comparezco a promover "
                "EJECUCIÓN EN VÍA DE APREMIO en contra de {ejecutado_nombre}:\n\n"
                "I. HECHOS: En virtud de sentencia o convenio aprobado en autos, el ejecutado está obligado a pagar pensión "
                "alimenticia, encontrándose insolutas {meses_atrasados}, sumando la cantidad líquida y exigible de {total_adeudado}.\n\n"
                "II. PETICIONES: Se requiera de pago al ejecutado por {total_adeudado}; de no hacer efectivo el pago en el acto, "
                "se trabe embargo y, de persistir la negativa al quinto día, se certifique lo conducente al Ministerio Público "
                "por el delito de Negación de Asistencia Económica (Art. 242 del Código Penal).\n\n"
                "CITA DE LEYES: Artículos 61, 63, 294, 297 y 298 del CPCyM; Artículo 242 del Código Penal. Acompaño duplicado y dos copias."
            ),
        },
        {
            "id": "fam_relaciones_familiares",
            "nombre": "Demanda Oral de Fijación de Régimen de Relación y Convivencia Familiar",
            "soporte": "Memorial Judicial (Art. 61, 63, 199 CPCyM; Ley de Tribunales de Familia)",
            "descripcion": "Solicitud para regular días, horarios y vacaciones de convivencia con hijos menores.",
            "campos": [
                "juzgado_familia",
                "actor_nombre",
                "actor_generales",
                "dpi_actor",
                "abogado_auxiliante",
                "casillero_electronico",
                "demandado_nombre",
                "direccion_demandado",
                "menores_nombres",
                "horario_propuesto",
            ],
            "redaccion": (
                "JUICIO ORAL DE RELACIONES FAMILIARES NUEVO.\n\n"
                "{actor_nombre}, {actor_generales}, con DPI CUI {dpi_actor}, bajo dirección del Abogado {abogado_auxiliante}, "
                "casillero electrónico {casillero_electronico}, promuevo JUICIO ORAL DE FIJACIÓN DE RELACIONES FAMILIARES contra "
                "{demandado_nombre}, notificable en {direccion_demandado}:\n\n"
                "I. HECHOS: Soy padre o madre de los menores {menores_nombres}, a quienes se me ha limitado la convivencia regular, "
                "afectando su desarrollo afectivo. Propongo el siguiente régimen de visitas: {horario_propuesto}.\n\n"
                "II. PETICIÓN: Se fije régimen provisional inmediato durante el trámite y en sentencia se apruebe de forma "
                "definitiva en resguardo del interés superior del niño.\n\n"
                "CITA DE LEYES: Artículos 61, 63 y 199 del CPCyM; Convención sobre los Derechos del Niño; Ley PINA. Acompaño duplicado y dos copias."
            ),
        },
        {
            "id": "fam_violencia_intrafamiliar",
            "nombre": "Solicitud Urgente de Medidas de Seguridad (Violencia Intrafamiliar / Mujer)",
            "soporte": "Memorial Judicial (Dto. 97-96 Ley para Prevenir, Sancionar y Erradicar la Violencia Intrafamiliar)",
            "descripcion": "Acción inmediata para ordenar salida del agresor, prohibición de acercamiento y orden a PNC.",
            "campos": [
                "juzgado_familia",
                "solicitante_nombre",
                "solicitante_generales",
                "dpi_solicitante",
                "direccion_solicitante",
                "agresor_nombre",
                "hechos_urgentes",
                "medidas_solicitadas",
            ],
            "redaccion": (
                "SOLICITUD URGENTE DE MEDIDAS DE SEGURIDAD POR VIOLENCIA INTRAFAMILIAR.\n\n"
                "{solicitante_nombre}, {solicitante_generales}, identificada con DPI CUI {dpi_solicitante}, señalando lugar "
                "para recibir notificaciones en {direccion_solicitante}, comparezco con urgencia a solicitar MEDIDAS DE "
                "SEGURIDAD en contra de {agresor_nombre}:\n\n"
                "I. HECHOS URGENTES: {hechos_urgentes}.\n\n"
                "II. PETICIÓN URGENTE: Con fundamento en el Artículo 7 del Decreto 97-96, sin audiencia previa, se decreten "
                "de manera inmediata las siguientes medidas: {medidas_solicitadas}, ordenándose librar oficio a la Comisaría "
                "de la Policía Nacional Civil para protección inmediata de mi vida e integridad y la de mi núcleo familiar.\n\n"
                "CITA DE LEYES: Decreto 97-96 y Decreto 22-2008 del Congreso de la República. Acompaño duplicado y copias."
            ),
        },
    ],
    "PENAL": [
        {
            "id": "pen_denuncia_mp",
            "nombre": "Denuncia Escrita ante el Ministerio Público (Art. 297-299 CPP)",
            "soporte": "Denuncia MP (Art. 297-299 Código Procesal Penal, Dto. 51-92)",
            "descripcion": "Denuncia formal dirigida al Ministerio Público (sin encabezado judicial duplicado ni Timbre Forense).",
            "campos": [
                "juzgado",
                "denunciante_nombre",
                "dpi_denunciante",
                "direccion_denunciante",
                "abogado_auxiliante",
                "posible_sindico",
                "delito_presunto",
                "fecha_y_lugar_hecho",
                "relato_hechos",
            ],
            "redaccion": (
                "{denunciante_nombre}, mayor de edad, guatemalteco, identificado con DPI CUI {dpi_denunciante}, con residencia "
                "y lugar para notificaciones en {direccion_denunciante}, auxiliado (opcional) por {abogado_auxiliante}, "
                "respetuosamente presento DENUNCIA PENAL en contra de {posible_sindico}, por la posible comisión del delito "
                "de {delito_presunto}:\n\n"
                "I. RELATO CIRCUNSTANCIADO DE LOS HECHOS:\n"
                "El día y lugar siguiente: {fecha_y_lugar_hecho}, acontecieron los hechos constitutivos de ilícito penal: "
                "{relato_hechos}.\n\n"
                "II. ELEMENTOS DE CONVICCIÓN QUE SE APORTAN:\n"
                "Se acompañan copias simples de documentación de respaldo, grabaciones o datos de testigos presenciales.\n\n"
                "III. PETICIÓN:\n"
                "Se reciba la presente denuncia, se inicie la persecución penal pública practicando de urgencia las diligencias "
                "de investigación pertinentes conforme al Artículo 309 del Código Procesal Penal y se me tenga como agraviado.\n\n"
                "CITA DE LEYES: Artículos 28 y 251 de la Constitución Política; 117, 297, 298, 299 y 309 del Código Procesal Penal."
            ),
        },
        {
            "id": "pen_querellante_adhesivo",
            "nombre": "Memorial de Constitución como Querellante Adhesivo y Actor Civil",
            "soporte": "Memorial Judicial (Art. 116-124 Código Procesal Penal)",
            "descripcion": "Escrito ante Juez Contralor para intervenir activamente en el proceso penal y reclamar reparación digna.",
            "campos": [
                "juzgado_penal",
                "causa_mp_y_judicial",
                "agraviado_nombre",
                "dpi_agraviado",
                "abogado_auxiliante",
                "casillero_electronico",
                "sindicado_nombre",
                "delito_imputado",
            ],
            "redaccion": (
                "CAUSA PENAL NÚMERO: {causa_mp_y_judicial}.\n\n"
                "{agraviado_nombre}, identificado con DPI CUI {dpi_agraviado}, bajo la dirección y procuración del Abogado "
                "{abogado_auxiliante}, señalando casillero electrónico {casillero_electronico}, comparezco a solicitar mi "
                "CONSTITUCIÓN PROVISIONAL Y DEFINITIVA COMO QUERELLANTE ADHESIVO dentro del proceso penal instruido contra "
                "{sindicado_nombre} por el delito de {delito_imputado}:\n\n"
                "I. FUNDAMENTO DE LEGITIMACIÓN:\n"
                "En mi calidad de agraviado directo conforme al Artículo 117 del Código Procesal Penal, tengo interés legítimo "
                "en colaborar con el Ministerio Público para el esclarecimiento de la verdad histórica y el ejercicio de la "
                "reparación digna (Art. 124 CPP).\n\n"
                "II. PETICIÓN:\n"
                "Se admita la presente solicitud y se me otorgue intervención provisional como Querellante Adhesivo desde esta "
                "etapa preparatoria, notificándome todas las resoluciones y audiencias que se señalen.\n\n"
                "CITA DE LEYES: Artículos 116, 117, 118, 121 y 124 del Código Procesal Penal."
            ),
        },
        {
            "id": "pen_medida_sustitutiva",
            "nombre": "Solicitud de Revisión de Medida de Coerción (Medida Sustitutiva)",
            "soporte": "Memorial Judicial (Art. 264 y 277 Código Procesal Penal)",
            "descripcion": "Escrito de defensa técnica solicitando audiencia de revisión para sustituir prisión preventiva.",
            "campos": [
                "juzgado_penal",
                "causa_penal",
                "defensor_nombre",
                "sindicado_nombre",
                "arraigos_acreditados",
            ],
            "redaccion": (
                "CAUSA PENAL NÚMERO: {causa_penal}.\n\n"
                "{defensor_nombre}, Abogado Defensor Técnico del sindicado {sindicado_nombre}, atentamente solicito:\n\n"
                "AUDIENCIA DE REVISIÓN DE LA MEDIDA DE COERCIÓN:\n"
                "Que habiendo variado las circunstancias primitivas que motivaron la prisión preventiva y acreditándose "
                "plenamente el arraigo familiar, domiciliario y laboral mediante: {arraigos_acreditados}, no existe peligro "
                "de fuga ni de obstaculización a la averiguación de la verdad.\n\n"
                "PETICIÓN: Se señale audiencia oral de revisión de medida de coerción conforme al Artículo 277 del CPP, y en ella "
                "se otorguen las medidas sustitutivas contempladas en el Artículo 264 del mismo cuerpo legal.\n\n"
                "CITA DE LEYES: Artículos 12 y 14 de la Constitución Política; 259, 261, 262, 263, 264 y 277 del CPP."
            ),
        },
        {
            "id": "pen_criterio_oportunidad",
            "nombre": "Solicitud de Audiencia para Aplicación de Criterio de Oportunidad",
            "soporte": "Memorial Judicial (Art. 25, 25 bis y 286 Código Procesal Penal)",
            "descripcion": "Salida alterna desjudicializadora con reparación del daño o acuerdo conciliatorio.",
            "campos": [
                "juzgado_penal",
                "causa_penal",
                "sindicado_nombre",
                "abogado_defensor",
                "delito_atribuido",
                "acuerdo_reparacion",
            ],
            "redaccion": (
                "CAUSA PENAL NÚMERO: {causa_penal}.\n\n"
                "{sindicado_nombre}, auxiliado por el Abogado {abogado_defensor}, dentro del proceso por {delito_atribuido}:\n\n"
                "SOLICITO: Que concurriendo los requisitos del Artículo 25 del Código Procesal Penal, tratándose de delito con "
                "pena no mayor de cinco años o de mínima afectación social y habiendo satisfecho la reparación del daño mediante: "
                "{acuerdo_reparacion}, con anuencia del Ministerio Público, se señale audiencia para otorgar CRITERIO DE OPORTUNIDAD "
                "bajo las reglas de abstención de ley.\n\n"
                "CITA DE LEYES: Artículos 25, 25 bis, 25 ter y 286 del Código Procesal Penal."
            ),
        },
        {
            "id": "pen_exhibicion_personal",
            "nombre": "Recurso Constitucional de Exhibición Personal (Habeas Corpus)",
            "soporte": "Acción Constitucional (Art. 263 Constitución Política; Art. 82-113 Ley de Amparo, Dto. 1-86)",
            "descripcion": "Acción constitucional urgente exenta de formalidades, auxilio de abogado y Timbre Forense (Art. 85 Dto. 1-86).",
            "campos": [
                "juzgado_penal",
                "solicitante_nombre",
                "persona_agraviada",
                "autoridad_o_lugar_detencion",
                "hechos_detencion_ilegal",
            ],
            "redaccion": (
                "EXHIBICIÓN PERSONAL URGENTE.\n\n"
                "{solicitante_nombre}, sin sujeción a formalidad alguna de conformidad con el Artículo 85 de la Ley de Amparo, "
                "Exhibición Personal y de Constitucionalidad, interpongo EXHIBICIÓN PERSONAL a favor de {persona_agraviada}, "
                "quien se encuentra ilegalmente detenido o sufriendo vejámenes en {autoridad_o_lugar_detencion}:\n\n"
                "HECHOS: {hechos_detencion_ilegal}.\n\n"
                "PETICIÓN URGENTE: Se decrete de inmediato el auto de exhibición personal, constituyéndose el Juez Ejecutor en "
                "{autoridad_o_lugar_detencion} para verificar la integridad física de {persona_agraviada} y ordenar su libertad "
                "inmediata si fuere ilegal la detención.\n\n"
                "CITA DE LEYES: Artículos 263 y 264 de la Constitución Política; 82, 85, 88 y 90 del Decreto 1-86."
            ),
        },
    ],
}
