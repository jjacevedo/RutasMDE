---
title: "RutasMDE: copiloto de movilidad para Medellín con A* y un agente LLM con RAG"
subtitle: "Proyecto final, SI3003 Inteligencia Artificial, Universidad EAFIT, 2026-2"
author: "Juan José Acevedo Otálvaro, Santiago Arellano y Juan Esteban Peña"
lang: es
---

Repositorio: <https://github.com/jjacevedo/RutasMDE>

## 1. Problema

Moverse por el Valle de Aburrá exige combinar información dispersa: qué ruta tomar en carro, qué estación del Metro queda cerca, cuánto cuesta el pasaje, a qué hora opera cada línea y si el vehículo tiene pico y placa. RutasMDE reúne eso en una sola interfaz. El usuario escribe en lenguaje natural de dónde a dónde quiere ir; el sistema calcula la ruta en la red vial con A\*, la dibuja en un mapa y responde preguntas sobre transporte público, tarifas, horarios, pico y placa, EnCicla y normas de tránsito a partir de un corpus con fuentes.

El proyecto combina una técnica de la Parte 1 del curso (búsqueda A\*) con una de la Parte 2 (agente LLM con RAG y herramientas). La unión no es decorativa: el agente decide cuándo llamar al A\*, y su resultado alimenta tanto la respuesta como el mapa.

## 2. Datos

- **Red vial.** OpenStreetMap, descargada con `osmnx` para Medellín, Envigado, Itagüí y Bello (red para vehículos). Se conserva la mayor componente fuertemente conexa: 25.457 nodos y 58.821 aristas. `osmnx` asigna a cada arista una velocidad y un tiempo de recorrido a partir del tipo de vía.
- **Estaciones.** 47 estaciones del sistema Metro (Metro, tranvía y cables) y 86 de EnCicla, extraídas de OpenStreetMap, para las capas del mapa.
- **Geocodificación.** Nominatim (OpenStreetMap), restringida al área metropolitana, con una caché versionada en el repositorio para que la aplicación funcione aunque el servicio falle.
- **Corpus RAG.** 11 documentos en Markdown escritos por el equipo a partir de fuentes públicas: Metro de Medellín, Secretaría del Senado (Ley 769 de 2002), El Colombiano, Telemedellín y Wikipedia, entre otras. Cada documento declara en su encabezado las URL y la fecha de consulta (noviembre de 2026). Dos documentos, lugares de referencia y corredores viales, son recopilación propia y lo indican.

El grafo no se versiona por su tamaño (37 MB); el README indica cómo descargarlo con `python routing/download_graph.py`.

## 3. Método de la Parte 1: búsqueda A\*

El A\* está implementado por el equipo en `routing/astar.py`, con una cola de prioridad (`heapq`) y un conjunto de nodos cerrados; no se usa la función de rutas de `networkx`. Soporta dos costos:

- **Distancia** (metros). Heurística: distancia haversine en línea recta hasta el destino. Es admisible porque ninguna vía es más corta que la línea recta.
- **Tiempo** (segundos). Heurística: distancia haversine dividida por la velocidad máxima del grafo. Es admisible porque ningún recorrido puede ir más rápido que esa velocidad.

La función pública `compute_route(origen, destino, criterio)` geocodifica los dos lugares, los ajusta al nodo más cercano del grafo, ejecuta A\* y devuelve las coordenadas de la ruta (siguiendo la geometría real de las calles), la distancia, el tiempo y los nodos expandidos.

**Línea base y métrica.** Se compara contra Dijkstra, que es el mismo algoritmo con heurística cero, en 15 pares de nodos aleatorios por cada costo (semilla fija). La corrección se verifica contra el costo óptimo que reporta `networkx`, usado solo como referencia. El script es `python -m routing.test_astar`.

| Costo | Rutas óptimas | Nodos expandidos A\* | Nodos expandidos Dijkstra | Tiempo A\* | Tiempo Dijkstra |
|---|---|---|---|---|---|
| Distancia | 15/15 | 4.043 | 12.252 | 23,8 ms | 49,0 ms |
| Tiempo | 15/15 | 5.658 | 9.698 | 31,7 ms | 38,7 ms |

A\* encuentra siempre la ruta óptima y expande el 33 % de los nodos de Dijkstra por distancia y el 58 % por tiempo. La heurística de tiempo es menos informativa porque divide por la velocidad máxima de todo el grafo, que la mayoría de las vías no alcanza.

## 4. Diseño del agente y del RAG

**Índice.** Cada sección de los documentos es un fragmento autocontenido (69 en total), con el título del documento antepuesto para que conserve su contexto. Los embeddings se calculan con `paraphrase-multilingual-MiniLM-L12-v2`, un modelo multilingüe, y se guardan normalizados en un índice FAISS de producto interno (similitud coseno).

**Recuperación híbrida.** Los embeddings solos fallaban con nombres propios como "EAFIT". Cada consulta combina 20 candidatos de búsqueda semántica y 20 de BM25 (texto sin tildes ni palabras vacías), fusionados con Reciprocal Rank Fusion (k = 60). El agente recibe los 4 mejores fragmentos con sus fuentes.

**Herramientas.**

- `calcular_ruta(origen, destino, criterio)`: llama a `compute_route()`.
- `consultar_movilidad(pregunta)`: consulta el retriever híbrido.

Las dos devuelven un resumen corto para el modelo y los datos completos para el dashboard (coordenadas de la ruta y fragmentos con fuentes). Si una herramienta falla, el error vuelve al modelo como observación y el agente lo explica al usuario en lugar de detenerse.

**Loop agéntico.** Grafo de LangGraph con dos nodos en ciclo, `modelo` y `herramientas`. El modelo es `openai/gpt-oss-120b` servido por Groq, con temperatura 0. El límite es de 25 pasos; si se supera, el agente pide reformular la pregunta. Hace hasta 6 reintentos ante el límite de tasa del proveedor.

**Prompt de sistema.** Obliga a tomar los datos del sistema solo de `consultar_movilidad`, a responder solo lo que se pregunta, a no inventar rutas de bus ni tiempos de caminata, a aclarar que el tiempo de A\* es en carro y sin tráfico, y a rechazar preguntas fuera de tema.

**Dashboard.** Aplicación Streamlit con un chat conectado al agente, un mapa Folium con la ruta calculada y capas activables de Metro y EnCicla, tarjetas con distancia, tiempo y recorrido, las fuentes de cada respuesta y el número de nodos expandidos por A\*.

## 5. Resultados de la evaluación del agente

Se usan 15 preguntas fijas en 8 categorías (rutas, tarifas, horarios, pico y placa, EnCicla, Metrocable, normas y comunas), con una pregunta fuera de tema y una cuyo dato no está en el corpus. El script `python -m evaluation.run_eval` mide por pregunta si devolvió ruta cuando se esperaba, si llamó a las herramientas correctas, si la respuesta contiene el dato clave, si entre las fuentes reportadas está el documento esperado y la latencia. Los resultados completos están en `evaluation/results.json`.

| Corrida | Ruta | Herramientas | Dato clave | Fuente | Latencia media |
|---|---|---|---|---|---|
| 1, versión inicial (ruta simulada) | no registrada | 13/15 | 10/13 | no medida | 17,7 s |
| 2, prompt y corpus corregidos (ruta simulada) | 13/13 | 15/15 | 12/13 | 11/11 | 10,5 s |
| Definitiva (A\* real) | 13/13 | 15/15 | 13/13 | 11/11 | 18,2 s |

Los denominadores cambian porque no todas las métricas aplican a todas las preguntas.

**Revisión manual.** Las métricas automáticas no detectan datos incorrectos agregados al texto, así que cada respuesta de la corrida definitiva se leyó y se contrastó con el corpus: 11 son correctas, 2 tienen imprecisiones menores y 2 tienen errores de contenido. Los dos errores:

- En la ruta de Laureles a El Poblado, el agente agregó una alternativa en Metro que nadie pidió y ubicó a Laureles junto a la estación Universidad (Línea A); según el corpus es Estadio (Línea B).
- En la ruta al Parque Arví, la secuencia de líneas es correcta, pero llamó a Acevedo "terminal de la Línea A", cuando las terminales son Niquía y La Estrella.

En las dos primeras corridas la revisión manual había encontrado errores del mismo tipo ("San Javier, línea A" y estaciones inventadas hacia Arví). Se corrigieron reescribiendo fragmentos del corpus para que fueran autocontenidos y endureciendo el prompt; el dato clave pasó de 10/13 a 13/13.

## 6. Limitaciones

- **Alucinaciones residuales.** El modelo a veces agrega datos de memoria aunque el prompt lo prohíbe (2 de 15 respuestas en la corrida definitiva). Las métricas automáticas marcaron esas respuestas como correctas.
- **Límite de tasa.** El plan gratuito de Groq permite 8.000 tokens por minuto y una pregunta de ruta consume cerca de 6.400. Dos preguntas seguidas obligan a esperar: la latencia máxima fue de 82,7 s.
- **Tiempos de viaje.** El tiempo de A\* supone velocidad libre por tipo de vía, sin tráfico ni semáforos, y solo aplica a carro. El sistema no calcula rutas multimodales: los trayectos en Metro salen del corpus.
- **Geocodificación.** Depende de Nominatim; algunos lugares conocidos no se encuentran por nombre (por ejemplo, "Parque Lleras") y el agente pide una dirección más precisa.
- **Fuentes mostradas.** Se reportan los 2 primeros fragmentos de cada búsqueda aunque alguno no se use en la respuesta. La métrica de fuente mide si se recuperó el documento correcto, no si la respuesta se apoya en él.
- **Datos que cambian.** Tarifas, horarios y pico y placa corresponden a la fecha de consulta. OpenStreetMap también cambia: una descarga nueva del grafo puede tener un número de nodos ligeramente distinto y variar un poco las rutas.
- **Alcance.** El sistema es informativo. No es asesoría legal ni de seguridad vial.

## 7. Equipo

| Integrante | Aporte |
|---|---|
| Juan José Acevedo Otálvaro | Corpus, índice y retriever, herramientas, agente LLM y evaluación |
| Santiago Arellano | Grafo vial, A\*, comparación con Dijkstra y geocodificación |
| Juan Esteban Peña | Dashboard Streamlit, mapa, integración y README |

La declaración de uso de IA generativa se entrega en `docs/declaracion_uso_ia.md`.
