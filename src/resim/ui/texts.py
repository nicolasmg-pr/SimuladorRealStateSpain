"""All explanatory copy for the UI, in Spanish.

Three blocks:
- CHART_HELP: how to read each chart (keyed by chart id used in app.py).
- POLICY_SUMMARIES: plain-language description of each lever + its causal chain.
- ACTOR_REACTIONS: per lever, how each actor changes behaviour and what that does
  to the market. Content is distilled from docs/policies/*.md and docs/actors/*.md —
  if it disagrees with those dossiers, the dossier wins.

app.py renders these; it never invents copy inline.
"""

from __future__ import annotations

CHART_HELP: dict[str, str] = {
    "precios": (
        "**Qué muestra:** el precio medio de compra de una vivienda en cada tipo de "
        "zona, trimestre a trimestre. No son precios de anuncio: salen de las "
        "compraventas que se cierran dentro de la simulación.\n\n"
        "**Cómo leerlo:** cada línea es un tipo de zona. Si la línea sube, comprar en "
        "esa zona se encarece. La línea vertical discontinua marca el trimestre en que "
        "entra la política.\n\n"
        "**En qué fijarse:** ¿cambia la pendiente después de la política? ¿Se separan "
        "las zonas (la política solo aplica en algunas)? Pasa el ratón por encima para "
        "ver el valor exacto y su año."
    ),
    "alquileres": (
        "**Qué muestra:** el alquiler mensual de los contratos *nuevos* que se firman "
        "cada trimestre, por zona. Los inquilinos que ya tienen contrato no aparecen "
        "aquí: su renta solo cambia cuando se mudan o renuevan.\n\n"
        "**Cómo leerlo:** igual que el de precios. Ojo: un tope de alquiler puede bajar "
        "esta línea y, a la vez, reducir cuántos pisos se ofrecen — eso se ve en el "
        "gráfico de volúmenes, no en este.\n\n"
        "**En qué fijarse:** el efecto inmediato tras la línea de inicio, y si el "
        "alquiler 'rebota' con el tiempo (los caseros se adaptan)."
    ),
    "accesibilidad": (
        "**Qué muestra:** de cada 100 hogares que *no* tienen vivienda en propiedad "
        "(inquilinos y buscadores), cuántos podrían comprar la vivienda mediana de su "
        "zona si lo intentaran hoy: el banco les pasa el filtro real de concesión "
        "(ahorros para la entrada e impuestos, y cuota ≤35% de la renta neta), sin "
        "contar avales públicos.\n\n"
        "**Cómo leerlo:** más alto = comprar está al alcance de más gente. No es "
        "cuántos compran (eso son las compraventas), sino cuántos *podrían*. Se mueve "
        "cuando cambian los precios, los tipos de interés o los ingresos y ahorros de "
        "quienes no tienen casa.\n\n"
        "**En qué fijarse:** una política puede bajar el precio y aun así no mover "
        "esta línea (si la barrera es la entrada, no la cuota), o al revés. Compárala "
        "con el esfuerzo teórico del panel de indicadores."
    ),
    "diff_precio": (
        "**Qué muestra:** la diferencia de precios entre el escenario con política y "
        "la simulación base (misma semilla, sin política). Es la respuesta directa a "
        "«¿qué ha cambiado por culpa de la política?».\n\n"
        "**Cómo leerlo:** 0 = ningún efecto. Por debajo de 0, la política abarató la "
        "vivienda respecto a no hacer nada; por encima, la encareció. Antes del inicio "
        "de la política la línea es 0 por construcción.\n\n"
        "**En qué fijarse:** el signo (¿abarata o encarece?), el tamaño (¿€500 o "
        "€20.000?) y si el efecto crece, se estabiliza o se revierte."
    ),
    "diff_alquiler": (
        "**Qué muestra:** lo mismo que el panel de la izquierda, pero para el alquiler "
        "de contratos nuevos (€/mes).\n\n"
        "**Cómo leerlo:** por debajo de 0, los nuevos contratos son más baratos que "
        "sin política. Cuidado con leer solo este gráfico: un alquiler más barato con "
        "muchos menos contratos firmados puede dejar a más gente sin vivienda.\n\n"
        "**En qué fijarse:** compáralo siempre con el Δ de volúmenes de abajo."
    ),
    "diff_volumenes": (
        "**Qué muestra:** cuántas compraventas y contratos de alquiler *más o menos* "
        "hay cada trimestre respecto a la base. Es el gráfico que delata los efectos "
        "secundarios: muchas políticas mueven poco los precios pero mucho la "
        "actividad.\n\n"
        "**Cómo leerlo:** por debajo de 0, la política redujo la actividad (menos "
        "operaciones); por encima, la aumentó.\n\n"
        "**En qué fijarse:** un Δ de contratos muy negativo con alquileres más bajos "
        "= el clásico dilema del tope: más barato para quien encuentra piso, más "
        "difícil encontrarlo."
    ),
    "volumenes": (
        "**Qué muestra:** la actividad del mercado — compraventas cerradas y contratos "
        "de alquiler firmados cada trimestre (unidades del modelo: 1 ≈ 2.000 hogares "
        "reales).\n\n"
        "**Cómo leerlo:** más actividad no es ni bueno ni malo por sí solo; es el "
        "termómetro de si el mercado se mueve o se congela.\n\n"
        "**En qué fijarse:** caídas bruscas tras una política (mercado congelado) o "
        "subidas (la política desbloquea operaciones)."
    ),
    "tenencia": (
        "**Qué muestra:** en qué situación vive cada hogar: propietario, inquilino o "
        "buscando vivienda (ni lo uno ni lo otro: jóvenes sin emancipar, recién "
        "llegados, expulsados del mercado).\n\n"
        "**Cómo leerlo:** las tres proporciones suman ~100%. «Buscando vivienda» es la "
        "cifra más social del panel: es la gente a la que el mercado no da salida.\n\n"
        "**En qué fijarse:** si una política baja los alquileres pero sube «buscando "
        "vivienda», el beneficio se lo llevan los que ya están dentro."
    ),
    "comparador": (
        "**Qué muestra:** el efecto de cada política sobre el indicador elegido, "
        "medido como diferencia frente a la misma base (misma semilla, sin política). "
        "Todas las políticas se ejecutan con sus parámetros por defecto (los puntos "
        "medios de la evidencia) y empiezan en el mismo trimestre.\n\n"
        "**Cómo leerlo:** cada línea es una política. 0 = sin efecto. La política "
        "«mejor» depende del indicador: baja los alquileres ≠ baja el número de "
        "hogares buscando vivienda.\n\n"
        "**En qué fijarse:** el orden de magnitud (¿qué política mueve de verdad la "
        "aguja?) y los tiempos (algunas actúan ya, otras tardan años). Para afinar los "
        "parámetros de una política concreta, usa la pestaña «Explorar»."
    ),
}

# --- Policy explanations -----------------------------------------------------
# Distilled from docs/policies/*.md. Each summary: what the policy is, the causal
# chain into the market, and the honest caveat about disputed evidence.

POLICY_SUMMARIES: dict[str, str] = {
    "tope de alquiler": (
        "**Qué es:** el tope de la Ley 12/2023 en zonas tensionadas: el alquiler de un "
        "contrato nuevo no puede superar el del contrato anterior (o el índice de "
        "referencia para grandes tenedores).\n\n"
        "**Cadena causal:** alquileres nuevos ↓ en la zona regulada → parte de los "
        "caseros retira pisos (venta, vacío o alquiler de temporada, que no está "
        "topado) → menos contratos firmados y más competencia por cada piso. El "
        "efecto en precio es rápido (1 trimestre); la retirada de oferta tarda 4–6 "
        "trimestres.\n\n"
        "**Lo que se discute:** cuánta oferta se retira. Es EL parámetro en disputa "
        "del modelo (elasticidad 0–2): tres estudios sobre los mismos datos catalanes "
        "llegan a conclusiones opuestas. La versión de 2025 de Monràs y García-Montalvo "
        "estima ≈2 por variables instrumentales (1,6–3,2) pero 0,07 por mínimos "
        "cuadrados: el rango del modelo es exactamente esa horquilla.\n\n"
        "**Cobertura:** la ley se declara municipio a municipio. A julio de 2026 hay 317 "
        "municipios tensionados en 5 CCAA (9,3M de personas, el 19% del país); la zona "
        "tensionada del modelo es mayor, así que el deslizador de cobertura escala qué "
        "parte de ella está realmente bajo la ley."
    ),
    "impuesto de transmisiones (ITP)": (
        "**Qué es:** el impuesto que paga el comprador de vivienda usada (6–13% según "
        "CCAA). La palanca cambia el tipo en puntos porcentuales.\n\n"
        "**Cadena causal:** subirlo baja lo que el comprador puede ofrecer → los "
        "precios *transaccionados* bajan (el vendedor absorbe gran parte del "
        "impuesto) y se cierran muchas menos operaciones (−4% a −15% por cada punto). "
        "Ojo: el coste total para el comprador (precio + impuesto) apenas mejora — "
        "que «baje el precio» es en parte un espejismo estadístico.\n\n"
        "**Lo que se discute:** cuánto del impuesto absorbe el vendedor (40% a "
        ">100%). No existe ningún estudio causal español: toda la evidencia es "
        "importada (Reino Unido, Alemania, Canadá…).\n\n"
        "**Por tipo de comprador:** España ya grava distinto según quién compra. "
        "Cataluña cobra un 20% en compras de edificios enteros y de grandes tenedores "
        "(Ley 11/2026), y el Gobierno propuso un impuesto del 100% a compradores "
        "extracomunitarios (atascado en el Congreso). Los dos recargos están en la "
        "palanca; los compradores al contado los sufren como una cuña sobre su "
        "presupuesto, no como un filtro de crédito."
    ),
    "impuesto a la vivienda vacía": (
        "**Qué es:** recargo del IBI (hasta 150%) sobre viviendas vacías más de 2 "
        "años de propietarios con 4+ inmuebles, si el ayuntamiento lo activa.\n\n"
        "**Cadena causal:** las viviendas detectadas y gravadas vuelven al mercado "
        "(alquiler o venta) → más oferta → los alquileres solo bajan si el volumen "
        "movilizado es relevante. En España suele no serlo: pocos ayuntamientos lo "
        "aplican, casi la mitad de la vivienda vacía está en pueblos donde nadie "
        "busca piso, y esquivar la detección es barato (empadronar a un familiar "
        "basta).\n\n"
        "**Lo que se discute:** cuánta vivienda se moviliza — Francia −13%, Vancouver "
        "−21% a −67%, pero con tipos hasta 10 veces más altos que el recargo español. "
        "Legazpi lo derogó en 2025 tras diez años sin resultados."
    ),
    "vivienda pública": (
        "**Qué es:** construcción de vivienda pública/protegida de alquiler (Plan "
        "Estatal 2026–2030, Sepes, traspaso de Sareb).\n\n"
        "**Cadena causal:** cada vivienda pública añade oferta, menos la obra privada "
        "que desplaza (compiten por el mismo suelo y la misma mano de obra) → los "
        "alquileres de mercado solo bajan cuando el parque público alcanza una escala "
        "relevante (Viena: ~43% del parque, alquileres ~−15%; España hoy: ~2,5%).\n\n"
        "**Lo que se discute:** el desplazamiento de obra privada (0 a 0,8 viviendas "
        "privadas por cada pública). Y el gran fallo histórico: >765.000 VPO han "
        "perdido la protección desde 2000 — sin protección permanente, el parque se "
        "escurre.\n\n"
        "**Tiempos:** la palanca más lenta junto al suelo — de suelo a llaves, 3–8 "
        "años."
    ),
    "restricción de pisos turísticos": (
        "**Qué es:** extinción de licencias de vivienda turística (VUT), estilo "
        "Barcelona 2028: las ~10.100 licencias no se renuevan.\n\n"
        "**Cadena causal:** el piso turístico pierde su licencia → el dueño elige "
        "entre volver al alquiler habitual, venderlo, dejarlo vacío… o disfrazarlo de "
        "alquiler de temporada (la vía de escape: 71% de las VUT ilegales detectadas "
        "en Barcelona en 2025). Solo la parte que vuelve al alquiler habitual añade "
        "oferta.\n\n"
        "**Lo que se discute:** esa proporción de conversión (10–50%). Nueva York "
        "eliminó >80% de los anuncios y los alquileres NO bajaron; Berlín 2016 sí "
        "recuperó oferta. El efecto depende de cuánto piso turístico había: mucho en "
        "el centro tensionado, ~0 en zonas rurales."
    ),
    "ayudas a la demanda (avales)": (
        "**Qué es:** avales ICO — el Estado garantiza la parte de la hipoteca por "
        "encima del 80%, permitiendo comprar sin ahorro previo (jóvenes <36, primera "
        "vivienda).\n\n"
        "**Cadena causal:** más compradores con más capacidad de puja, sin ninguna "
        "vivienda nueva → en zonas donde la oferta no puede crecer (tensionadas), la "
        "ayuda se capitaliza en precios y acaba en el bolsillo del vendedor; en zonas "
        "con oferta elástica, genera construcción con poco efecto en precio.\n\n"
        "**Lo que se discute:** cuánto se capitaliza (0% a >100% del valor de la "
        "ayuda — en Londres los precios subieron MÁS que el valor del subsidio). "
        "También la escala: el aval ICO real cubre <2% de las compraventas anuales."
    ),
    "liberación de suelo": (
        "**Qué es:** más suelo finalista (listo para construir) y/o trámites más "
        "rápidos. España tiene planeamiento sobre papel para ~7M de viviendas, pero "
        "<0,5% del suelo residencial disponible es finalista.\n\n"
        "**Cadena causal:** más suelo → la oferta responde mejor a los precios → "
        "contención de precios *a largo plazo* y solo donde el suelo es la "
        "restricción activa. A corto plazo, efecto nulo por diseño: de planeamiento a "
        "vivienda pasan 10–20 años.\n\n"
        "**Lo que se discute:** el aviso histórico es la Ley 6/1998 («todo "
        "urbanizable»): el suelo urbanizable creció ~30% y los precios subieron ~180% "
        "en 1997–2007 — la demanda arrasó con el efecto oferta. La ganancia de la "
        "recalificación se la lleva el propietario del suelo."
    ),
    "shock de tipos": (
        "**Qué es:** un cambio del euríbor, el tipo al que se referencian las "
        "hipotecas. No es una política de vivienda: es el experimento que reproduce "
        "2022–23.\n\n"
        "**Cadena causal:** euríbor ↑ → cuota hipotecaria ↑ → menos hogares pasan el "
        "filtro de crédito del banco → menos compraventas y menos presión de precios; "
        "parte de los compradores frustrados se queda en el alquiler, empujando las "
        "rentas al alza.\n\n"
        "**Para qué sirve:** comprobar que el modelo reproduce la firma de la subida "
        "de tipos real antes de fiarse de sus predicciones sobre otras políticas."
    ),
}

# Per policy: (actor, how it reacts and why it matters). Order: most affected first.
ACTOR_REACTIONS: dict[str, list[tuple[str, str]]] = {
    "tope de alquiler": [
        (
            "🔑 Hogares inquilinos",
            "Los que firman contrato nuevo en zona tensionada pagan menos (~−4% a "
            "−7%) y se mudan menos. A cambio, encontrar piso se vuelve más difícil: "
            "en Barcelona llegaron a competir ~65 familias por anuncio, y parte de la "
            "búsqueda se desvía al alquiler de temporada, que no está topado.",
        ),
        (
            "👤 Pequeños caseros",
            "Comparan la rentabilidad topada con su alternativa (bono + 3–5 puntos). "
            "Si el tope les come el margen, retiran el piso por tres vías: venderlo a "
            "un comprador, dejarlo vacío o pasarlo a alquiler de temporada. Los que "
            "estaban *por debajo* del índice suben la renta hasta el tope — el tope "
            "también es un imán.",
        ),
        (
            "🏢 Grandes inversores",
            "Sufren el tramo más estricto (índice de referencia). La respuesta "
            "documentada es vender cartera y rotar el capital a otros usos o "
            "ciudades: Albirana vendió ~1.500 pisos en 18 meses tras la regulación "
            "catalana.",
        ),
        (
            "🏗️ Promotores",
            "Recalculan los proyectos de construir-para-alquilar; en Barcelona esa "
            "promoción se paró o se convirtió en construir-para-vender. Menos "
            "vivienda de alquiler nueva en el futuro.",
        ),
        (
            "🏠 Hogares propietarios",
            "Absorben parte del stock retirado: los pisos que salen del alquiler "
            "hacia la venta acaban en manos de compradores. La tasa de propiedad "
            "tiende a subir un poco.",
        ),
    ],
    "impuesto de transmisiones (ITP)": [
        (
            "🏠 Hogares propietarios",
            "El coste de mudarse sube, así que se mudan menos (efecto cerrojo: ~−8% "
            "de movilidad por punto de ITP). Familias en casas que ya no encajan con "
            "su vida — el coste real es el des-ajuste, no el impuesto.",
        ),
        (
            "🔑 Compradores primerizos",
            "Pujan descontando el impuesto: con la misma capacidad de pago, ofrecen "
            "menos por la vivienda. Su coste total apenas cambia — pagan menos al "
            "vendedor y más a Hacienda.",
        ),
        (
            "👤🏢 Inversores",
            "El impuesto golpea directamente su rentabilidad de entrada; una subida "
            "los expulsa antes que a nadie (en Cataluña los grandes tenedores pagan "
            "un 20%). Menos demanda inversora en la zona.",
        ),
        (
            "🏗️ Promotores",
            "Salen ganando en términos relativos: la obra nueva no paga ITP (paga "
            "IVA), así que parte de la demanda se desvía hacia ella.",
        ),
        (
            "🏛️ Gobierno",
            "Recauda — el ITP es una fuente principal de ingresos autonómicos — pero "
            "con mucho daño colateral: ~1€ de actividad perdida por cada 8€ "
            "recaudados, mucho peor que un impuesto anual tipo IBI.",
        ),
    ],
    "impuesto a la vivienda vacía": [
        (
            "🏢 Grandes tenedores y bancos",
            "Son los contribuyentes reales (el recargo exige 4+ inmuebles): en "
            "Cataluña, ~80% de lo recaudado salía de tres entidades. Pero el importe "
            "(~€850–1.650/año) es pequeño frente a lo que ya les cuesta mantener un "
            "piso vacío, así que solo mueve a los indecisos.",
        ),
        (
            "👤 Pequeños propietarios",
            "Casi todos quedan fuera (solo ~5% de los dueños de vivienda vacía tiene "
            "4+ inmuebles), y los que no, esquivan barato: empadronar a un familiar o "
            "anunciar el piso a precio de no-venta basta para librarse.",
        ),
        (
            "🏛️ Gobierno municipal",
            "Debe declarar la vacancia piso a piso, con audiencia previa y "
            "verificación anual. Aquí muere la política: solo 222 de 8.131 municipios "
            "aplicaban el recargo en 2022. La probabilidad de detección es el "
            "deslizador que decide todo.",
        ),
        (
            "🔑 Hogares inquilinos",
            "Solo ganan si el stock movilizado aparece donde ellos buscan. Casi la "
            "mitad de la vivienda vacía española está en municipios pequeños sin "
            "demanda — el desajuste geográfico limita el efecto en zonas tensionadas.",
        ),
    ],
    "vivienda pública": [
        (
            "🔑 Hogares inquilinos",
            "Los adjudicatarios pagan ~40–60% menos que el mercado. Pero la cola es "
            "larga (180.000–250.000 hogares inscritos, esperas de hasta 5 años): al "
            "principio el beneficio llega a pocos, elegidos por registro y sorteo.",
        ),
        (
            "🏗️ Promotores",
            "Doble papel: construyen la mayoría de la VPO (74% en 2024) cuando los "
            "números salen, pero compiten con la obra pública por el mismo suelo y la "
            "misma mano de obra — de ahí el desplazamiento que ajustas con el "
            "deslizador.",
        ),
        (
            "👤🏢 Caseros e inversores",
            "Solo notan la competencia cuando el parque público alcanza escala. Con "
            "el ~2,5% actual de España, apenas les afecta; el efecto sobre alquileres "
            "de mercado crece con el *stock* acumulado, no con el ritmo anual.",
        ),
        (
            "🏛️ Gobierno",
            "Paga €120.000–200.000 por vivienda y tarda 3–8 años en entregarla. El "
            "riesgo histórico es la descalificación: >765.000 VPO perdieron la "
            "protección desde 2000 y salieron del parque.",
        ),
    ],
    "restricción de pisos turísticos": [
        (
            "👤 Pequeños caseros con licencia VUT",
            "Su licencia vale un 8–9% del precio del piso (estimación de Lisboa) y va "
            "camino de valer cero. Eligen: volver al alquiler habitual, vender, dejar "
            "vacío… o disfrazar el piso de alquiler de temporada — la vía de evasión "
            "dominante (71% de las VUT ilegales detectadas en Barcelona 2025).",
        ),
        (
            "🏢 Anfitriones profesionales",
            "Berlín 2016 enseña que solo cuando la norma golpea a los profesionales "
            "(multipropietarios) vuelve stock real al mercado de larga duración; los "
            "anfitriones ocasionales apenas aportan.",
        ),
        (
            "🔑 Hogares inquilinos",
            "Ganan solo la fracción de pisos que de verdad se convierte. En Nueva "
            "York la restricción eliminó >80% de los anuncios y los alquileres no "
            "bajaron: la mayoría de pisos se fue a estancias de 30+ días o se quedó a "
            "oscuras.",
        ),
        (
            "🏛️ Gobierno",
            "Su variable decisiva es la capacidad de inspección: Madrid anuncia "
            "~12.600 VUT y solo ~1.300 tienen registro — ~90% de incumplimiento. Sin "
            "inspectores, la licencia extinguida sigue alquilándose.",
        ),
    ],
    "ayudas a la demanda (avales)": [
        (
            "🔑 Compradores primerizos",
            "El aval elimina la barrera del ahorro (no la de ingresos: el filtro de "
            "cuota sigue). Solo ~1 de cada 3 compras avaladas es *adicional* — el "
            "resto habría comprado igual, ahora con más deuda.",
        ),
        (
            "🏠 Vendedores y 🏗️ promotores",
            "Los beneficiarios finales cuando la oferta no puede crecer: la puja "
            "extra se capitaliza en el precio. En el Help to Buy británico, el "
            "programa mejoró las cuentas de los promotores más que el acceso de los "
            "jóvenes.",
        ),
        (
            "🏦 Banco",
            "Presta al 95–100% de LTV con el Estado absorbiendo el riesgo de cola. "
            "Máximo apalancamiento sobre los prestatarios más jóvenes y frágiles: si "
            "los precios caen, hay patrimonio negativo.",
        ),
        (
            "🏛️ Gobierno",
            "Asume el pasivo contingente. El límite real es la escala: ~10.500 "
            "operaciones avaladas en 2025, <2% de las compraventas del año — con esa "
            "escala, mover el precio agregado es difícil.",
        ),
    ],
    "liberación de suelo": [
        (
            "🏗️ Promotores",
            "Los beneficiarios directos: desde 2008 solo compran suelo finalista, y "
            "eso es exactamente lo que la palanca añade. Trámites más rápidos les "
            "ahorran ~€50.000 por vivienda, dos tercios en costes financieros.",
        ),
        (
            "🏛️ Propietarios de suelo",
            "Se llevan la plusvalía de la recalificación — «los verdaderos ganadores» "
            "del boom 1997–2007, cuando el peso del suelo en el precio de la vivienda "
            "pasó del 25% al 46%.",
        ),
        (
            "🏦 Banco",
            "Financia suelo y promoción; en el auge acumula el riesgo que estalla en "
            "la crisis. Más suelo elástico = ciclos de construcción más amplios.",
        ),
        (
            "🔑🏠 Hogares",
            "A corto plazo, nada — y que no pase nada es un objetivo de validación "
            "del modelo: de planeamiento a llaves pasan 10–20 años. El alivio, si "
            "llega, es para la próxima década.",
        ),
    ],
    "shock de tipos": [
        (
            "🏦 Banco",
            "Traslada el euríbor a la cuota y endurece el filtro: con tipos altos, "
            "menos hogares pasan la prueba de esfuerzo (cuota ≤ ~35% de ingresos). Es "
            "el canal de transmisión principal.",
        ),
        (
            "🔑 Aspirantes a comprar",
            "Los que están al límite del filtro caen fuera y se quedan alquilando — "
            "la demanda frustrada de compra presiona los alquileres al alza.",
        ),
        (
            "🏠 Hogares con hipoteca variable",
            "Su cuota sube al revisarse; el consumo y el ahorro se resienten, y "
            "alguno vende. España es especialmente sensible: gran parte del stock "
            "hipotecario es variable.",
        ),
        (
            "👤🏢 Inversores",
            "Comparan rentabilidad del alquiler con el bono: con tipos altos, el "
            "ladrillo pierde atractivo relativo y compran menos — menos demanda de "
            "compra, más oferta en venta.",
        ),
    ],
}

MODEL_EXPLANATION = """
### ¿Qué es esto?

Un **modelo basado en agentes** del mercado de vivienda español. No es una bola de
cristal: es un laboratorio. Miles de hogares, caseros, inversores, promotores, un
banco y un gobierno simulados toman decisiones cada trimestre, y los precios y
alquileres **emergen** de sus transacciones — nunca se imponen desde fuera.

### Los actores

| Actor | Qué decide cada trimestre |
|---|---|
| 🏠 Hogar propietario | Quedarse, mudarse, vender |
| 🔑 Hogar inquilino / buscador | Seguir de alquiler, mudarse, intentar comprar |
| 👤 Pequeño casero / inversor | Alquilar, subir renta, vender, pasar a temporada |
| 🏢 Gran inversor | Comprar o vender cartera según rentabilidad |
| 🏗️ Promotor | Iniciar obra nueva si los márgenes salen |
| 🏦 Banco | Conceder o denegar hipotecas (filtro de esfuerzo) |
| 🏛️ Gobierno | Aplica la política que eliges en la barra lateral |

### Cómo funciona una simulación

1. **Escala:** 1 hogar del modelo ≈ 2.000 hogares reales (10.000 agentes ≈ 19,9M
   de hogares españoles). 1 tick = 1 trimestre.
2. **Tres zonas:** metro tensionado (Madrid/Barcelona y costa caliente), ciudad
   secundaria (Valladolid, Zaragoza, Murcia) y rural (la España vaciada: Soria,
   Teruel, Cuenca), con migración entre ellas. La mayoría de políticas solo
   muerde en la tensionada.
3. **Causalidad limpia:** cada escenario se compara con una base ejecutada con la
   **misma semilla** — el mismo mundo, la misma suerte, la única diferencia es la
   política. Los gráficos «escenario menos base» son efecto causal puro *dentro
   del modelo*.
4. **La semilla:** fija el azar. Cambiarla y repetir es la forma honesta de
   comprobar que una conclusión no es un golpe de suerte.

### Por qué hay deslizadores «en disputa»

Regla del proyecto: cuando los estudios serios no se ponen de acuerdo, el modelo
**no elige un bando**. El desacuerdo se convierte en un deslizador y tú exploras
ambos mundos. El ejemplo estrella: tres estudios sobre el tope de alquiler catalán,
con los mismos datos, concluyen desde «no se retiró oferta» hasta «−10% de
contratos». Ese deslizador (elasticidad 0–2) recorre exactamente ese rango.

### Límites que conviene recordar

- Los resultados son **condicionales a los deslizadores**: mueve los parámetros en
  disputa antes de creerte ninguna conclusión.
- Varios efectos clave no tienen estudio causal español (ITP, impuesto a la
  vivienda vacía, avales ICO): la evidencia es importada y los rangos, anchos.
- La base reproduce los objetivos de validación (docs/validation.md) antes de que
  ningún escenario se considere fiable.
- El modelo informa la discusión; no la sustituye.
"""

BDE_INTRO = """
**El Banco de España no publica ninguna previsión de vivienda.** Sus tablas de proyecciones
macro no tienen ni una fila de vivienda: ni precios, ni inversión residencial, ni viviendas
iniciadas, ni renta bruta disponible de los hogares, ni tipo hipotecario. Se verificó una a
una (`docs/external-forecasts.md` §1). Así que **no existe una «previsión del BdE» contra la
que comparar la proyección de este simulador**: si alguien te la ofrece, no es del BdE.

Lo que el BdE sí publica son **datos observados y diagnósticos estructurales** — un déficit
medido, una banda de sobrevaloración, una elasticidad de oferta. Eso sí es comparable, y es
lo que hay en esta tabla: las cifras nacionales del modelo frente a la cifra oficial de la
misma variable.

La mayoría de las filas son del BdE. El resto son series del INE (Censo y Encuesta de
Presupuestos Familiares) recopiladas en Funcas, *Estudios* 104, *Mercado inmobiliario y
política de la vivienda en España* (2024): vivienda vacía por tamaño de municipio, esfuerzo
del alquiler, gasto medio en alquiler, compras sin hipoteca y demanda embalsada. Cada fila
lleva su fuente; ninguna es una previsión. El detalle de qué es y qué no es cada cifra está
en `docs/funcas-104.md`.

Tres cosas distintas, a propósito separadas:

- **`docs/validation.md`** — ¿la base reproduce la historia? **Es una puerta**: ningún
  escenario se reporta si falla.
- **Esta pestaña** — ¿cómo quedan las cifras del modelo frente a las oficiales publicadas?
  **No es una puerta**, es diagnóstico.
- **`docs/external-forecasts.md` §4** — ¿nuestra senda cae dentro de lo que proyectan otros?
  No es una puerta, y no es del BdE.

Cómo leerla sin equivocarse:

- **Las bases se igualan explícitamente.** El modelo corre a escala 1:2.000 y por trimestres;
  cada fila dice en qué la convierte. Comparar sobre bases distintas es peor que no comparar.
- **El reloj del modelo no es un calendario.** 60 trimestres son «≈15 años de un mercado
  parecido al español», no 2011–2026. Por eso se contrasta la **fase estabilizada** del modelo
  contra la ventana plurianual del BdE (2021–2025), nunca trimestre a trimestre.
- **Las dos filas de crecimiento (precio y alquiler) van con trampa de fase**: comparan un
  estado estacionario del modelo con 2025, el año más fuerte en 18 años. Van a quedar por
  debajo, y eso no es un error. Para contrastar un auge, carga un escenario de auge.
"""

BDE_FORECAST_PANEL = """
### ¿Y si quiero comparar una *proyección*?

Entonces el BdE no sirve, porque no la publica. Sí existen sendas de precio de vivienda
para España, pero de **entidades comerciales y multilaterales**, y todas en PDF: ninguna
serie es legible por máquina (`docs/external-forecasts.md` §4).

| Institución | 2026 | 2027 | Base |
|---|---|---|---|
| BBVA Research (jul 2026) | +12,0% | +5,7% | MIVAU valor tasado, nominal |
| CaixaBank Research (mar 2026) | +10,1% | +5,5% | INE IPV, nominal |
| S&P Global (jul 2026) | +9,1% | +7,4% | INE IPV, nominal |
| FMI / EBA — base (may 2026) | +7,6% | +6,7% | nominal, senda del test de estrés EBA |
| FMI / EBA — adverso | — | — | 2028 **−4,3%**, 2029 **−11,0%** |
| Comisión Europea (nov 2025) | +8,0% | — | Eurostat HPI |
| Fitch (dic 2025) | +8 a +10% | — | nominal |
| Bankinter (feb 2026) | +7,0% | +4,0% | INE vivienda libre |

El par **base + adverso del FMI/EBA** es el más útil de la lista: es el único camino
publicado para España con un escenario de crisis emparejado, así que es el contraste natural
para una intervención tipo `CreditCrunch` — que este modelo todavía no tiene
(`docs/validation.md`, hueco conocido).

Nota de honestidad: el panel de 2026 **subestimó mucho** el precio real. El IPV del INE
cerró el primer semestre de 2026 en **+12,55% interanual de media** (1T +12,9%, 2T +12,2%,
publicado el 7-sep-2026), así que toda previsión en la banda 7–9% necesitaría un segundo
semestre en +3,5/+5,7% para cumplirse; sólo BBVA (+12,0%, base valor tasado) queda cerca, y
las bases de tasación (Tinsa ago-2026 +14,9%, Registradores +16,7%) corren por encima. En
volumen ocurre lo contrario: el Notariado da 1S 2026 −7,7% y Registradores julio −7,7%. Y el
euríbor a 12 meses ya está en 2,95% (ago-2026), por encima de todas las sendas del panel. No
es un tribunal; es contexto (`docs/kb-refresh-2026-09.md` §6).
"""

KPI_HELP: dict[str, str] = {
    "ownership_rate": "Porcentaje de hogares que son propietarios de su vivienda. "
    "España real: ~75%.",
    "price_to_income": "Años de renta disponible del hogar mediano necesarios para "
    "pagar la vivienda mediana. Más alto = menos asequible. España real: ~7,5.",
    "rent_overburden_share": "Porcentaje de inquilinos **a precio de mercado** que dedican "
    "más del 40% de sus ingresos al alquiler. Es el termómetro del esfuerzo de los que "
    "alquilan. Excluye la vivienda social, cuyo alquiler es administrado y no de mercado: "
    "es la misma base que el indicador de Eurostat con el que se valida (27–33% en España).",
    "buyer_access": "Accesibilidad de la vivienda: porcentaje de hogares no "
    "propietarios (inquilinos y buscadores) a los que el banco les concedería una "
    "hipoteca suficiente para la vivienda mediana de su zona, con los criterios "
    "reales de concesión (entrada, impuestos, esfuerzo ≤35% de la renta neta) y sin "
    "avales públicos. Más alto = comprar está al alcance de más gente.",
    "purchase_effort": "Esfuerzo teórico de compra: porcentaje de la renta disponible "
    "del hogar mediano que se iría en las cuotas del primer año de una hipoteca "
    "estándar (80% del precio, 25 años, tipo actual) sobre la vivienda mediana. "
    "España real: ~35–40% en 2024–25 (Banco de España).",
    "vacancy_rate": "Porcentaje del parque de viviendas sin ocupar (incluye retenidas "
    "y segundas residencias vacías).",
}
