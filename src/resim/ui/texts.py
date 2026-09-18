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
    "yields": (
        "**Qué muestra:** la rentabilidad bruta del alquiler por zona — alquiler anual "
        "dividido entre el precio de compra. Es una **salida** del modelo, no un ajuste: "
        "`ZoneConfig.gross_yield` sólo fija el punto de partida, y lo que el modelo hace "
        "después con él es una predicción.\n\n"
        "**Cómo leerlo:** las bandas publicadas (idealista + BdE RBA) son 4,7–5,6% en zona "
        "tensionada, 6,5–7,5% en ciudad secundaria y 7–9% en rural. Sube la línea = el "
        "alquiler se encarece respecto al precio, o el precio se abarata respecto al "
        "alquiler.\n\n"
        "**En qué fijarse:** la línea rural. Se va muy por encima de su banda — más del "
        "doble — y ése es el defecto que fase B tiene que cerrar. Las otras dos encajan."
    ),
    "alquileres_diag": (
        "**Qué muestra:** el mismo alquiler de contratos nuevos por zona que la pestaña "
        "«Explorar», pero aquí mirado como **diagnóstico**: en España los alquileres "
        "ordenan estrictamente tensionada > secundaria > rural, en toda base publicada "
        "(675 €/mes Madrid contra 277 € Extremadura, Funcas 104 cap.5).\n\n"
        "**Cómo leerlo:** si la línea rural cruza por encima de la tensionada, el modelo "
        "está produciendo algo que no ocurre en España.\n\n"
        "**En qué fijarse:** el cruce, alrededor del trimestre 35–40. La escalera de "
        "*precios* sí estaba gatillada por los tests; la de *alquileres* no lo estaba, y "
        "por eso este cruce sobrevivió sin que saltara nada."
    ),
    "migracion": (
        "**Qué muestra:** migración interna neta por zona y trimestre, en hogares a escala "
        "del modelo: entradas menos salidas. Positivo = la zona gana hogares de otras zonas "
        "españolas.\n\n"
        "**Cómo leerlo:** las tres líneas suman cero por construcción — nadie entra al país "
        "por aquí, sólo se mueven entre zonas.\n\n"
        "**En qué fijarse:** el **signo**. En España el flujo interno neto va rural → metro; "
        "el modelo lo tiene al revés porque la regla actual sólo deja bajar la escalera. No "
        "es una calibración floja: es imposible por construcción que salga positivo."
    ),
    "tenencia_zona": (
        "**Qué muestra:** qué proporción de los hogares de cada zona son inquilinos.\n\n"
        "**Cómo leerlo:** alquilar es una tenencia metropolitana en España, así que el orden "
        "esperado es tensionada > secundaria > rural (referencia: 0,27–0,30 / ≈0,20 / "
        "0,12–0,17).\n\n"
        "**En qué fijarse:** el orden se cumple, y eso es lo que está gatillado. Los "
        "*niveles* no lo están: la pata tensionada corre por encima de su banda, y una zona "
        "tensionada que agrupa el 45% de los hogares no es Madrid."
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
        "años.\n\n"
        "**Lo que este modelo NO puede decirte, medido el 2026-09-18:** cuánto baja el "
        "alquiler. No porque baje poco — porque no baja nada medible. Saturando la palanca "
        "(30 uds./trimestre, sin desplazamiento, ≈+8% del parque) sobre diez semillas, el "
        "alquiler de la zona tensionada se mueve de −197 a +92 €/mes alrededor de una media "
        "de −15: el signo cambia según la semilla. Lo que sí es consistente en las diez es la "
        "vivienda vacía, +4,3 pp. **La oferta se convierte en pisos vacíos, no en pisos más "
        "baratos.** La causa está identificada y es una sola línea: el único canal que lleva "
        "la holgura al precio pedido está topado en −2,5%, y la saturación lo rebasa en vez de "
        "recorrerlo (model-spec §7.6). No se arregla ajustando un parámetro.\n\n"
        "Ojo con la lectura contraria: esto **no** dice que la oferta no haga nada. En la "
        "palanca de suelo, con horizonte largo y el plazo de tramitación reformado, el precio "
        "de **venta** sí baja (−7,5% a −12,9%, docs/claims.md F-3). El mercado de compraventa "
        "tiene un término de tensión en su subasta; el de alquiler no. De esta palanca puedes "
        "leer la dirección de la vacancia y nada más."
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
        "recalificación se la lleva el propietario del suelo.\n\n"
        "**Lo que el modelo sí mide aquí, y lo que no.** Sobre 80 trimestres y diez semillas "
        "(docs/claims.md F-3) esta palanca **sí** baja el precio de venta: −7,5% con el plazo "
        "de tramitación a la mitad, −12,9% recortando además licencias, 0 de 10 semillas al "
        "alza. El cuello de botella es el plazo, que es justamente lo que la política puede "
        "cambiar. Pero **la renta sube ≈9%** en esas mismas ejecuciones: un programa de oferta "
        "creíble mata la expectativa de revalorización (−1,9 pp/año) y el retorno del casero "
        "se desplaza de plusvalía a rendimiento (+1,14 pp). Y no hay nada que lo compense: el "
        "único canal por el que la holgura bajaría el precio pedido del alquiler está topado "
        "en −2,5% (model-spec §7.6). Precio de venta: dirección y magnitud. Renta: nada."
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
    "restricción de crédito": (
        "**Qué es:** el cierre del grifo del crédito. No es una política de vivienda ni "
        "la elige nadie: es una condición de contorno, la mitad financiera de lo que pasó "
        "en 2008–13.\n\n"
        "**Cadena causal:** LTV y esfuerzo máximos bajan y el diferencial sube a la vez → "
        "menos hogares pasan el filtro → el volumen de compraventas cae primero y los "
        "precios después, despacio. Los tres se mueven juntos porque así ocurrió: barrer "
        "sólo uno sería barrer una combinación que nunca se dio.\n\n"
        "**Para qué sirve:** es una de las dos entradas del episodio 2008–13, que está "
        "**sellado** como validación fuera de muestra (fase E). Mirarlo aquí es mirar el "
        "mecanismo, no el resultado."
    ),
    "shock de desempleo": (
        "**Qué es:** un cambio del paro. Ojo con qué paro: el modelo trata cada hogar "
        "como **una sola unidad de renta**, así que la serie que usa es la del INE de "
        "hogares con *todos* sus activos en paro — 3,15% en 2007, 15,02% en 2013T1, "
        "5,28% en 2026T2. La tasa individual es aproximadamente el doble.\n\n"
        "**Cadena causal:** el hogar pierde su renta → cobra la prestación (70% y luego "
        "60%, con el tope legal, que a renta mediana es lo que ata) → si no llega a la "
        "cuota, entra en mora → a los 12 impagos el acreedor puede vencer el préstamo → "
        "o vende antes, o entrega la vivienda al banco, que la saca al mercado con "
        "descuento.\n\n"
        "**Lo que el modelo decide y lo que no:** la tasa agregada es un dato, nunca un "
        "resultado. Lo endógeno es **a quién** le toca — y con ello, qué hipotecas caen."
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
    "restricción de crédito": [
        (
            "🏦 Banco",
            "Es el actor que actúa: baja el LTV y el esfuerzo máximos y sube el "
            "diferencial. El racionamiento no es una decisión caso a caso, son los "
            "topes — y con ellos cae la capacidad de puja de todo el que necesita "
            "hipoteca.",
        ),
        (
            "🔑 Aspirantes a comprar",
            "Los que financiaban al límite dejan de poder pujar. El volumen cae antes "
            "que el precio: esa es la firma que el modelo tiene que reproducir.",
        ),
        (
            "🏠 Hogares con hipoteca",
            "Si además sube el diferencial, la cuota de los nuevos préstamos sube; los "
            "que ya tienen hipoteca viva sufren por el euríbor, no por este filtro.",
        ),
        (
            "🏗️ Promotor",
            "Sin compradores financiables, las preventas no cubren el umbral y los "
            "inicios de obra se paran — con ocho trimestres de retraso en la entrega, "
            "el ajuste de oferta llega tarde a todo.",
        ),
    ],
    "shock de desempleo": [
        (
            "🏠 Hogares con hipoteca",
            "Es donde pega. Pierden la renta salarial, cobran la prestación con su "
            "tope legal, tiran del ahorro y comprimen el consumo hasta el suelo de "
            "subsistencia; si aun así no llegan, entran en mora.",
        ),
        (
            "🏦 Banco",
            "Acumula mora, ejecuta cuando la ley se lo permite (12 cuotas, o 3 en el "
            "régimen anterior a 2019) y se queda con vivienda adjudicada que revende "
            "con descuento. Ese stock es el sobrante bancario de 2008–13.",
        ),
        (
            "🔑 Hogares ejecutados",
            "Vuelven a buscar vivienda como inquilinos y quedan fuera del crédito "
            "mientras el fichero de solvencia conserve el impago — hasta cinco años.",
        ),
        (
            "🏘️ Zonas",
            "El paro no cae igual en todas: el gradiente medido dice que el metro es "
            "la zona **menos** expuesta y que la brecha se abre en la crisis.",
        ),
    ],
}

MODEL_EXPLANATION = """
### ¿Qué es esto?

Un **laboratorio**, no una bola de cristal.

Dentro viven 10.000 hogares, caseros, inversores, promotores, un banco y un gobierno
simulados. Cada tres meses, cada uno toma una decisión pequeña y egoísta: si le sale mejor
alquilar que comprar, si le compensa vender, si el banco le concede la hipoteca o no.
**Nadie fija los precios desde fuera.** El precio es lo que queda cuando todas esas
decisiones chocan entre sí, igual que en un mercado real.

Sirve para preguntas del tipo *«¿y si...?»* que en la realidad no se pueden hacer, porque
España no se puede repetir dos veces. Ejemplo: topas el alquiler en la zona tensionada,
dejas correr quince años y miras qué pasó con la renta, con el número de contratos firmados
y con quién acaba viviendo dónde.

Lo que este modelo hace bien es **comparar dos mundos idénticos** en los que sólo cambia la
política. Lo que no hace es decirte el precio del metro cuadrado en Madrid en 2029.

### Quién decide qué

| Actor | Qué decide cada trimestre | Ejemplo |
|---|---|---|
| 🏠 Propietario | Quedarse, mudarse, vender | «Vale más que mi hipoteca y me mudo: vendo» |
| 🔑 Inquilino o buscador | Alquilar, mudarse, comprar | «Llego a la entrada: pido hipoteca» |
| 👤 Pequeño casero | Alquilar, subir la renta, vender | «Con el tope gano menos que vendiendo» |
| 🏢 Gran inversor | Comprar o vender cartera | «Fuera del metro renta un 7%: compro allí» |
| 🏗️ Promotor | Empezar obra nueva si salen las cuentas | «El precio cubre suelo y obra: arranco» |
| 🏦 Banco | Dar o denegar hipotecas, ejecutar | «Se iría al 45% de su renta: denegada» |
| 🏛️ Gobierno | Aplica la política que elijas | Tope de alquiler, vivienda pública, impuestos |

Desde la fase C los hogares también pueden **dejar de pagar**: si alguien se queda en paro
y la cuota no cabe después de comer, entra en mora, y si la mora dura lo que dice la ley
(artículo 24 de la Ley 5/2019) el banco puede quedarse la vivienda.

Por eso la barra lateral, además de las políticas, trae **condiciones de contorno**:
restricción de crédito, shock de desempleo y shock de tipos. No son políticas que nadie
elija — son cosas que le pasan a un país. Las dos primeras son, exactamente, las dos
entradas con las que se reconstruyó el episodio 2008–13.

### Las reglas del juego

1. **Un trimestre por paso.** Una simulación típica son 60 pasos, unos quince años.
2. **Un hogar del modelo equivale a 2.000 hogares reales** (10.000 agentes ≈ 19,9 millones
   de hogares españoles). Es lo que permite traducir a cifras oficiales: si el modelo
   termina 12 viviendas en un trimestre, son 12 × 2.000 × 4 ≈ **96.000 viviendas al año**,
   que es el orden de magnitud del dato real.
3. **Tres zonas, y se puede uno mudar entre ellas:** metro tensionado (Madrid, Barcelona y
   costa caliente), ciudad secundaria (Valladolid, Zaragoza, Murcia) y rural (Soria, Teruel,
   Cuenca). Casi todas las políticas sólo muerden en la tensionada.
4. **Comparación limpia:** cada escenario se ejecuta contra un mundo gemelo sin política, con
   la misma suerte. Cuando ves «escenario menos base», la única diferencia entre los dos
   mundos es la política. Dentro del modelo, eso es causalidad pura.
5. **La semilla es la suerte de ese mundo.** Quién se queda en paro, quién hereda, a quién le
   toca el piso bueno. Cambiar la semilla es repetir el experimento con otra tirada de dados.

### Por qué la app corre varios mundos a la vez

Porque un solo mundo engaña. Ejemplo medido en este modelo: un programa de vivienda pública
a saturación mueve el alquiler tensionado entre **−197 y +92 €/mes** según la semilla. Con
una sola semilla, la app te habría pintado una flecha verde grande o una roja grande, y las
dos habrían sido ruido.

Por eso el deslizador «Semillas a promediar» viene en **3** y gobierna todas las pestañas:
lo que ves es la **mediana** de esos mundos, con la distancia entre ellos al lado. Cuando el
efecto de la política es más pequeño que esa distancia, la app lo pinta **«≈ 0» en gris**:
significa «cambiando de semilla esta flecha cambia de sentido, no te la creas».

### Por qué hay deslizadores «en disputa»

Regla del proyecto: cuando los estudios serios no se ponen de acuerdo, el modelo **no elige
bando**. El desacuerdo se convierte en un deslizador y tú recorres los dos mundos.

El ejemplo estrella es el tope de alquiler catalán: tres equipos, los mismos datos, y
conclusiones que van desde «no se retiró ni un piso del mercado» hasta «−10% de contratos».
El deslizador que recoge ese desacuerdo ya no es una elasticidad abstracta, sino algo
concreto: **cuánto le cuesta al casero salirse** (la parte que vende por agencia, entre 0,40
y 0,85).

Y la letra pequeña, que es del propio modelo, medida el 18-09-2026: bajo la ley que esos
tres estudios evalúan (Ley 11/2020, el índice ata a **todos** los caseros), la **renta** sale
igual en todo el recorrido del deslizador — la mueve el nivel del tope, no el parámetro de
conducta: −6,84% en los cinco puntos del barrido, dentro de lo que coinciden las tres
evaluaciones. Así que **ese tamaño sí se puede citar**. Lo que el deslizador ya no recorre es
el desacuerdo sobre la **oferta**: el modelo da −7,24% de contratos, por debajo de todo lo
que mide Monràs. **Ese tamaño no se puede citar**; su signo sí
(`docs/experiments/rent-cap.md`).

### Límites que conviene recordar

- **Los resultados dependen de dónde dejes los deslizadores.** Muévelos antes de creerte
  ninguna conclusión: ésa es la forma de usar la herramienta, no un defecto de ella.
- **Hay efectos sin ningún estudio causal español** (ITP, impuesto a la vivienda vacía,
  avales ICO). Ahí la evidencia es importada y los rangos, anchos.
- **La base todavía falla en dos sitios**, y están escritos, no escondidos: los objetivos
  {xfail_targets}. El primero es que al metro no entra nunca nadie (el saldo migratorio sale
  bien por el motivo equivocado); el segundo, que casi nadie pierde la vivienda a manos del
  banco. Los tienes con su mecanismo en la pestaña «🔬 Diagnóstico del modelo».
- **La mitad de las cifras se leen sólo como dirección, no como cantidad.** Si un parámetro
  sin fuente explica más de una cuarta parte de la variación de un número, ese número se
  reporta como «sube» o «baja», nunca como «sube un 7%». Todo el lado del alquiler está en
  ese grupo. El desglose está en «Qué puede decir el modelo, y qué no», dentro de la pestaña
  de diagnóstico.
- **Más oferta no abarata el alquiler dentro de este modelo.** Es una limitación conocida y
  medida (18-09-2026): construir llena de pisos vacíos la zona, y la renta pedida casi no se
  mueve, porque el único canal por el que la oferta llega al alquiler está topado en −2,5%.
  Las viviendas se construyen y se alquilan de verdad —eso está comprobado—, pero el precio
  del alquiler no recoge la holgura. Léelo como un límite del modelo, no como un hallazgo
  sobre España.
- El modelo informa la discusión; no la sustituye.
"""

BDE_INTRO = """
Aquí el modelo pone sus cifras al lado de las cifras oficiales publicadas de lo mismo, para
que se vea dónde acierta el nivel y dónde no. Es un **chequeo**, no un examen: ningún ✅ es
un aprobado y ningún 🔽 es un suspenso.

**Primero, una advertencia útil fuera de esta app: el Banco de España no publica ninguna
previsión de vivienda.** Sus tablas de proyecciones no tienen ni una fila de vivienda — ni
precios, ni obra nueva, ni tipo hipotecario. Se comprobaron una a una
(`docs/external-forecasts.md` §1). Si alguien te enseña «la previsión de precios del BdE»,
no es del BdE.

Lo que el BdE sí publica son **datos observados y diagnósticos** — cuántas viviendas faltan,
cuánto se desvía el precio de sus fundamentales, cuánto responde la construcción al precio.
Eso sí es comparable, y es lo que hay en la tabla.

La mayoría de filas son del BdE. Las demás son series del INE (Censo y Encuesta de
Presupuestos Familiares) recopiladas en Funcas, *Estudios* 104 (2024): vivienda vacía por
tamaño de municipio, esfuerzo del alquiler, gasto medio en alquiler, compras sin hipoteca y
demanda embalsada. Cada fila lleva su fuente; ninguna es una previsión.

**Tres cosas distintas, a propósito separadas:**

| Dónde | Qué pregunta | ¿Es una puerta? |
|---|---|---|
| `docs/validation.md` | ¿La base reproduce la historia? | **Sí.** Si falla, no se reporta nada |
| **Esta pestaña** | ¿Los niveles se parecen a los oficiales? | No, es diagnóstico |
| `docs/external-forecasts.md` §4 | ¿Y frente a lo que proyectan otros? | No, y no es del BdE |

### Cómo leer la tabla sin equivocarse

- **Las bases se igualan antes de comparar, y cada fila dice cómo.** El modelo corre a
  escala 1:2.000 y por trimestres. Ejemplo: 12 viviendas terminadas en un trimestre del
  modelo son 12 × 2.000 × 4 ≈ 96.000 al año, y ése es el número que se compara con el
  oficial. Comparar sobre bases distintas es peor que no comparar.
- **El reloj del modelo no es un calendario.** El trimestre 60 no es 2026T4: son «quince
  años de un mercado parecido al español». Por eso se contrasta la **fase estabilizada** del
  modelo contra una ventana de varios años del BdE (2021–2025), nunca trimestre a trimestre.
- **Las dos filas de crecimiento (precio y alquiler) van con trampa, y se avisa.** Comparan
  un modelo ya estabilizado con 2025, el año más fuerte en dieciocho. Es como comparar la
  velocidad media de un coche en un viaje largo con la del adelantamiento: van a quedar por
  debajo, y eso no es un fallo. Para contrastar un auge hay que cargar un escenario de auge.
- **Con una sola semilla, varias filas bailan más que la propia banda publicada.** La
  formación de hogares es un sorteo, y una ventana de cinco años oscila ±10.000 hogares al
  año a escala nacional. Si vas a mirar esta tabla en serio, sube «Semillas a promediar».
- **La columna Δ relativa** es simplemente cuánto se separa el modelo del dato oficial, en
  tanto por ciento del dato oficial. −20% quiere decir que el modelo se queda una quinta
  parte corto.
"""

BDE_FORECAST_PANEL = """
### ¿Y si lo que quiero es comparar una *previsión*?

Entonces el BdE no sirve, porque no publica ninguna. Sí existen sendas de precio de vivienda
para España, pero de **bancos, agencias y organismos multilaterales**, y todas en PDF:
ninguna serie es legible por máquina (`docs/external-forecasts.md` §4).

| Institución | 2026 | 2027 | Sobre qué índice |
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
publicado para España que trae emparejado un escenario de crisis. Por eso es el contraste
natural de las condiciones de contorno de la barra lateral, «restricción de crédito» y
«shock de desempleo» — que no son políticas, sino las dos entradas con las que se
reconstruye el episodio 2008–13.

**Nota de honestidad, y conviene leerla antes de fiarse de cualquier panel de previsiones:**
el de 2026 **se quedó muy corto**. El índice de precios del INE cerró el primer semestre de
2026 en **+12,55% interanual de media** (1T +12,9%, 2T +12,2%, publicado el 7-sep-2026). Para
que se cumpliera una previsión del 7–9% haría falta un segundo semestre entre +3,5% y +5,7%;
sólo BBVA (+12,0%) queda cerca, y los índices de tasación corren aún por encima (Tinsa
ago-2026 +14,9%, Registradores +16,7%).

En **volumen** pasa lo contrario: el Notariado da −7,7% en el primer semestre de 2026 y
Registradores −7,7% en julio. Se vende más caro y se vende menos. Y el euríbor a doce meses
está en 2,95% (ago-2026), por encima de todas las sendas del panel.

Esto no es un tribunal para nadie; es contexto (`docs/kb-refresh-2026-09.md` §6). Y es el
mejor recordatorio de por qué esta app no publica un pronóstico fechado.
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
    "arrears_share": "Porcentaje de hogares **con hipoteca viva** que están en mora. "
    "Referencia real: la ratio de dudosos del crédito para compra de vivienda del Banco "
    "de España — 1,6% en 2026T1, 2,3–3,4% entre 2019 y 2024, y 6,28% en el pico de "
    "2014T1. El BdE cuenta euros de crédito y esto cuenta hogares: la comparación es de "
    "orden de magnitud, no exacta.",
    "foreclosure_rate": "Viviendas entregadas al acreedor al año por cada hipoteca viva, "
    "sumando entregas voluntarias, daciones y adjudicaciones judiciales. Referencia real: "
    "0,7%/año en 2014 (Banco de España) y ≈0,10% en el suelo de 2019.",
    "sale_discount_median": "Diferencia entre el precio de salida del anuncio y el precio de "
    "cierre, mediana de las ventas del trimestre. Referencia real: 6,2% de media (Cátedra "
    "Tecnocasa-UPF, 2S 2025), con sólo un 23% de las operaciones negociadas por encima del "
    "10% de rebaja (Fotocasa). Valores negativos = ventas por encima del precio de salida.",
    "bidders_per_listing": "Pujas por anuncio vendido. Es el canal por el que la competencia "
    "llega al precio: en una subasta ascendente el ganador paga lo que hace falta para "
    "superar al segundo. Referencia real: siete interesados por vivienda (Tecnocasa, 2S "
    "2025), el doble que dos años antes — pero eso cuenta interesados, no ofertas.",
    "sold_within_quarter_share": "Porcentaje de anuncios que se venden en el mismo trimestre "
    "en que salen. Referencia real: ≈53% de las viviendas se venden en menos de tres meses "
    "(idealista/data, 2T 2026).",
    "locked_in_share": "Porcentaje de propietarios con hipoteca que deben más de lo que el "
    "mercado pagaría por su vivienda. No pueden vender: la venta tiene que cancelar el "
    "préstamo. Es el bloqueo que explica que en una crisis caiga antes el número de "
    "operaciones que el precio.",
    "unemployment_rate": "Porcentaje de hogares con todos sus activos en paro. Es una "
    "**entrada** del modelo, no un resultado: lo que el modelo decide es a quién le toca.",
}


# --- Phase-0 diagnostic panel ------------------------------------------------
# Mirrors docs/validation.md "Phase-0 targets (2026-09-11)". Criteria and bands live in
# resim.diagnostics; this is only the framing the reader needs before the table.

DIAGNOSTICS_INTRO = """
Esta pestaña no explora ninguna política. Es la **lista de averías conocidas** del modelo:
qué se le ha pedido que reproduzca de la España real, qué reproduce y qué no.

**Cómo leer las tres columnas que importan:**

- **Criterio** — lo que dice la fuente oficial. Ejemplo: un piso en alquiler en una ciudad
  secundaria renta al propietario entre un 6,5% y un 7,5% bruto al año.
- **Encaja** — dónde cae **este run** (la mediana de las semillas que estés promediando en
  la barra lateral). ✅ dentro, 🔽 por debajo, 🔼 por encima.
- **Estado** — cómo está registrado el objetivo en el proyecto, que es lo que manda:
  - **✓ gatillado**: hay un test que lo vigila. Si el modelo se rompe por ahí, la suite falla.
  - **✗ xfail estricto**: fallo **registrado**. El test existe, se espera que falle y está
    escrito que falla; si algún día pasara, la suite avisaría también. Es lo contrario de
    esconder un defecto: es clavarlo en la pared.
  - **○ reportado**: se mide y se enseña, pero todavía no hay banda contra la que juzgarlo.

Las dos columnas pueden discrepar, y no es un error: **Encaja** habla de esta ejecución,
**Estado** de lo que la suite comprueba con diez semillas. Una fila puede salirte ✅ hoy y
seguir siendo un fallo registrado.

### Qué está roto hoy, en cristiano

Quedan **dos** fallos registrados vivos:

- **Objetivo 12 — al metro no entra nadie.** El saldo migratorio del metro sale negativo, que
  es lo correcto (España lleva desde 2017 perdiendo migración interna en las zonas
  tensionadas). El problema es *cómo* sale: en el modelo el saldo es negativo porque no entra
  nadie, cuando en la realidad entran muchos y salen algunos más. Es como decir que un bar
  pierde clientela porque no entra nadie, cuando lo que pasa es que entran cien y salen
  ciento treinta. Falta el motivo por el que la gente va al metro aunque sea caro: **dónde
  está el empleo** (§7.5).
- **Objetivo 15 — casi nadie pierde la casa.** El modelo entrega al banco 2 viviendas por
  cada 10.000 hipotecas al año (0,02%), contra las 10–16 por cada 10.000 (0,10–0,16%) que se
  observan en años tranquilos. El motivo: en el modelo, el hogar que no puede pagar siempre
  encuentra comprador a tiempo y vende. En la realidad no siempre puede — si debes más de lo
  que vale el piso, la venta no cancela la hipoteca, y además vender lleva meses. Esas
  fricciones faltan, y son de las fases D y E.

### Qué se ha cerrado, y cuándo

- **Objetivos 9 y 11 (rentabilidad del alquiler por zona y orden de alquileres) están
  gatillados desde el 17-09-2026.** Durante meses el modelo daba un alquiler rural por encima
  del metropolitano y una rentabilidad rural al doble de lo publicado. Los dos eran el mismo
  agujero visto por dos lados, y se cerraron juntos.
- **El objetivo 12 cambió de signo el 14-09-2026, y no por el modelo.** La ficha pedía
  migración interna *hacia* el metro. Los datos del INE dicen lo contrario en todos los años
  desde 2017. El modelo acertaba y la ficha lo contaba como fallo; se corrigió la ficha.

⚠️ **Esto sigue sin ser la puerta de validación.** La puerta es la suite
(`tests/test_validation.py`), que promedia **diez** semillas sobre los últimos 20 de 60
trimestres. Esta pestaña mide lo que tengas puesto en la barra lateral — desde el 18-09-2026
la mediana de las semillas promediadas, no una sola, salvo que bajes el deslizador a 1. Las
bandas de aquí están **copiadas** de las aserciones de los tests, no recalculadas.
"""

DIAGNOSTICS_OUTRO = """
**Por qué no se ensancha la banda cuando algo falla.** Es la regla que sostiene toda esta
pestaña: cuando el modelo entrega 2 viviendas al acreedor por cada 10.000 hipotecas y el dato
observado son 10–16, se reporta el fallo. Bajar la banda hasta que el modelo entre sería
convertir la medida en decoración: **la banda es el dato**, no un ajuste del modelo.

**El objetivo 15 tiene dos patas y se comportan distinto.** La **mora** (hogares hipotecados
que dejan de pagar) pasa contra el ratio de dudosos del Banco de España y está gatillada. Las
**entregas de vivienda al acreedor** fallan desde que nacieron. Que una pata pase y la otra no
es informativo: el impago existe y muerde en el orden de magnitud correcto, pero el modelo lo
resuelve casi siempre con una venta voluntaria en lugar de con una ejecución.

**Antes de la fase C esto ni siquiera se podía medir.** El impago no existía —el código
absorbía cualquier cuota que no cupiera— y poner un fallo registrado sobre un mecanismo
ausente habría sido decorado. La fase C metió riesgo de renta sobre una senda de paro, mora
contra un suelo de consumo en el umbral de pobreza, ejecución por la Ley 5/2019, vivienda
adjudicada al banco, y las condiciones de contorno de la barra lateral.

**Los tres gráficos de abajo son salidas del modelo, no ajustes.** Nadie fija el yield, ni el
alquiler por zona, ni quién se muda: son consecuencia de las decisiones de los agentes, y por
eso sirven para juzgar si las reglas de comportamiento están bien.
"""


# What the variance rule (model-spec §13.2) leaves reportable, after the phase-G Sobol run of
# 2026-09-15. On screen because a slider invites reading every number as an estimate, and half
# of them are not.
REPORTING_CONTRACT = """
**Qué se puede leer como cifra y qué sólo como signo.** La regla es simple: si un parámetro
sin fuente explica más de una cuarta parte de la variación de un número, ese número se
reporta como dirección («sube», «baja») y nunca como cantidad («sube un 7%»). Sale de 1.792
evaluaciones que reparten la varianza entre parámetros (`model-spec §13.2`).

- **Se pueden leer como cantidad** — precio y precio sobre renta, transacciones, viviendas
  terminadas, morosidad, tiempo de venta y pujas por anuncio. Van con su banda: el precio
  sobre renta es 8,13, y 7,2–9,1 recorriendo los rangos que la evidencia admite.
- **Sólo dirección** — todo el lado del alquiler (nivel de renta, vacancia tensionada,
  sobrecarga), la tasa de propiedad, la relación de precios entre zonas, la cuota de compras
  al contado y el margen de negociación. De éstos lee el sentido y en cuántas semillas se
  repite, nunca el tamaño.
- **Ni cantidad ni dirección: las políticas de oferta sobre el alquiler.** Medido el
  18-09-2026: construir a saturación llena de pisos vacíos la zona (+4,3 puntos de vacancia
  tensionada, en las diez semillas) y deja la renta pedida donde estaba (entre −197 y +92
  €/mes según la semilla). El único canal que llevaría la oferta al alquiler está topado en
  −2,5%. La vacancia sí se puede leer como dirección; la renta, ni eso.
"""
