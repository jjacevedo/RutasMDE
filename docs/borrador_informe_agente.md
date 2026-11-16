# Borrador del informe: agente LLM, RAG y evaluación (Rol A)

Secciones para integrar en el informe final. Las cifras marcadas como pendientes se actualizan con la corrida definitiva, después de integrar el A* real.

## Diseño del agente y RAG

**Corpus.** 11 documentos en Markdown sobre movilidad en Medellín y el Valle de Aburrá: líneas A y B del Metro, tranvía de Ayacucho y Metrocables, Metroplús y buses, tarifas 2026, horarios, EnCicla, pico y placa del segundo semestre de 2026, normas para peatones y ciclistas (Ley 769 de 2002 y reformas), comunas y municipios, lugares de referencia y corredores viales. Cada documento declara en su encabezado el título, las URL de las fuentes oficiales y la fecha de consulta. Dos documentos (lugares de referencia y corredores viales) son recopilación propia y así lo indican.

**Índice.** Cada sección `##` es un fragmento autocontenido (69 en total), con el texto "Título - Sección" antepuesto para que el fragmento conserve su contexto. Los embeddings se calculan con `paraphrase-multilingual-MiniLM-L12-v2`, un modelo multilingüe; el plan inicial proponía `all-MiniLM-L6-v2`, que está entrenado solo en inglés. Los vectores normalizados se guardan en un `faiss.IndexFlatIP`, equivalente a similitud coseno.

**Recuperación híbrida.** Los embeddings solos fallaban con nombres propios (por ejemplo, "EAFIT"). Por eso cada consulta combina dos rankings de 20 candidatos: búsqueda semántica en FAISS y BM25 sobre texto sin tildes ni palabras vacías. Los rankings se fusionan con Reciprocal Rank Fusion (k = 60) y el agente recibe los 4 mejores fragmentos con sus fuentes.

**Herramientas.**

- `calcular_ruta(origen, destino, criterio)`: llama a `compute_route()`, que ejecuta A* sobre la red vial de OpenStreetMap con criterio de distancia o de tiempo.
- `consultar_movilidad(pregunta)`: consulta el retriever híbrido.

Ambas usan `content_and_artifact`: el LLM recibe un resumen corto (menos tokens) y el dashboard recibe los datos completos (coordenadas de la ruta y fragmentos con fuentes). Si una herramienta falla, el error vuelve al modelo como observación en lugar de detener el agente.

**Loop agéntico.** Grafo de LangGraph con dos nodos en ciclo, `modelo` y `herramientas`, controlado por `tools_condition`. El modelo es `openai/gpt-oss-120b` en Groq, con temperatura 0. El límite de pasos es 25 (T_max): si se supera, el agente pide reformular la pregunta. Además, hace hasta 6 reintentos cuando Groq devuelve límite de tasa.

**Prompt de sistema.** Reglas contra las alucinaciones observadas en la evaluación:

- Los datos del sistema solo pueden venir de `consultar_movilidad`.
- Responder solo lo que se pregunta, sin generalidades ("suele", "normalmente").
- No inventar rutas de bus ni tiempos de caminata.
- Describir los trayectos en Metro como estación de subida, dirección por terminal y estación de bajada.
- Aclarar que el tiempo de A* es en carro y sin tráfico.
- Rechazar las preguntas fuera de tema.

## Evaluación del agente

**Diseño.** 15 preguntas fijas en 8 categorías: rutas, tarifas, horarios, pico y placa, EnCicla, Metrocable, normas y comunas. Incluyen una pregunta fuera de tema y una cuyo dato no está en el corpus, para medir si el agente reconoce sus límites. El script `evaluation/run_eval.py` mide automáticamente, por pregunta:

- `ruta_ok`: devolvió una ruta cuando se esperaba (y no la devolvió cuando no).
- `herramientas_ok`: llamó a las herramientas esperadas.
- `datos_ok`: la respuesta contiene el dato clave (texto normalizado, con alternativas válidas).
- `fuente_ok`: entre las fuentes reportadas está el documento del corpus que contiene la respuesta.
- Latencia de punta a punta.

Además, el equipo revisa manualmente cada respuesta (campo `revision_manual`), porque las métricas automáticas no detectan datos incorrectos agregados al texto.

**Resultados.**

| Corrida | Herramientas | Datos clave | Fuente | Latencia media |
|---|---|---|---|---|
| 1 (versión inicial) | 13/15 | 10/13 | no medida | 17,7 s |
| 2 (prompt y corpus corregidos) | 15/15 | 12/13 | 11/11 (calculada después sobre la misma corrida) | 10,5 s |
| Definitiva (A* real) | pendiente | pendiente | pendiente | pendiente |

Las corridas 1 y 2 usaron una ruta simulada, así que no evalúan la calidad del A*.

**Lo que encontró la revisión manual.** El revisor automático marcaba como correctas respuestas con errores:

- "San Javier (línea A)", cuando San Javier es de la Línea B.
- Una ruta al Parque Arví con estaciones inventadas.

La causa era que algunos fragmentos dependían de su contexto y el modelo completaba con conocimiento propio. Se corrigió reescribiendo esos fragmentos para que fueran autocontenidos (por ejemplo, indicando la línea de cada estación) y endureciendo el prompt.

## Limitaciones

- **Alucinaciones residuales.** `gpt-oss-120b` a veces agrega datos de memoria aunque el prompt lo prohíbe. Las métricas automáticas no lo detectan, de ahí la revisión manual.
- **Límite de tasa.** El plan gratuito de Groq permite 8.000 tokens por minuto. Una pregunta de ruta consume unos 6.400 tokens en 4 llamadas al modelo, así que dos preguntas seguidas superan el límite y la respuesta se demora por los reintentos.
- **Fuentes con relleno.** El dashboard muestra los 2 primeros fragmentos de cada búsqueda, aunque alguno no se haya usado en la respuesta.
- **Alcance de `fuente_ok`.** Mide si se recuperó el documento correcto, no si la respuesta se apoya en él.
- **Corpus estático.** Tarifas, horarios y pico y placa tienen fecha de consulta y pueden cambiar. El orden de estaciones de la Línea A y los dos documentos de recopilación propia no tienen fuente oficial directa.
- **Alcance del sistema.** No es asesoría legal: las normas de tránsito se resumen con fines informativos.
