# RutasMDE

Copiloto de movilidad para Medellín. El usuario escribe de dónde a dónde quiere ir, la aplicación calcula la ruta en la red vial con A\*, la dibuja en un mapa y responde preguntas sobre Metro, tarifas, horarios, pico y placa, EnCicla y normas de tránsito a partir de un corpus con fuentes.

Proyecto final de SI3003 Inteligencia Artificial, Universidad EAFIT, 2026-2.

## Equipo

- Juan José Acevedo Otálvaro: corpus, índice y retriever, herramientas, agente LLM y evaluación.
- Santiago Arellano: grafo vial, A\*, comparación con Dijkstra y geocodificación.
- Juan Esteban Peña: dashboard Streamlit, mapa, integración y README.

## Documentos de la entrega

- Informe: [docs/informe.pdf](docs/informe.pdf)
- Declaración de uso de IA generativa: [docs/declaracion_uso_ia.md](docs/declaracion_uso_ia.md)
- Evaluación del agente (15 preguntas, con revisión manual): [evaluation/results.json](evaluation/results.json)
- Comparación de A\* contra Dijkstra: [routing/data/resultados_astar.txt](routing/data/resultados_astar.txt)

## Requisitos

- Python 3.14. Las versiones de `requirements.txt` están fijas y se probaron con Python 3.14.6 en macOS.
- Una clave de API de Groq. Es gratuita y se crea en <https://console.groq.com/keys>.
- Conexión a internet para descargar el grafo, el modelo de embeddings y consultar el LLM.

## Instalación

macOS y Linux:

```bash
git clone https://github.com/jjacevedo/RutasMDE.git
cd RutasMDE
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Windows PowerShell:

```powershell
git clone https://github.com/jjacevedo/RutasMDE.git
cd RutasMDE
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Abre `.env` y reemplaza el valor de `GROQ_API_KEY` por tu clave. `GROQ_MODEL` es opcional: si no se define, el agente usa `openai/gpt-oss-120b`. El archivo `.env` no se sube al repositorio.

## Preparar los recursos

Desde la raíz del repositorio, con el entorno activado:

```bash
python routing/download_graph.py
python rag/build_index.py
```

El primer comando descarga la red vial de Medellín, Envigado, Itagüí y Bello desde OpenStreetMap y la guarda en `routing/data/medellin.graphml` (37 MB). Tarda entre 4 y 11 minutos según el servidor de Overpass que responda; el script prueba varios.

El segundo construye el índice de búsqueda en `rag/faiss_index/` con los 11 documentos de `rag/corpus/`. La primera vez descarga el modelo de embeddings.

Ninguno de los dos recursos está en el repositorio. Solo hay que generarlos una vez.

## Ejecutar el dashboard

```bash
streamlit run app.py
```

Se abre en <http://localhost:8501>. Preguntas para probar:

- Ruta en carro de EAFIT al Parque Berrío
- ¿Cómo llego de EAFIT al Parque Explora?
- ¿Cuánto cuesta el pasaje del Metro para estudiantes?
- Mi carro tiene placa terminada en 4, ¿qué día tengo pico y placa?

Cuando el agente calcula una ruta, el mapa la dibuja y arriba aparecen la distancia, el tiempo y el recorrido. Las capas de Metro y EnCicla se activan en la barra lateral y son puntos de referencia, no rutas multimodales.

## Reproducir los resultados

Comparación de A\* contra Dijkstra en 15 pares de nodos por cada costo:

```bash
python -m routing.test_astar
```

Evaluación del agente con las 15 preguntas de `evaluation/questions.json`:

```bash
python -m evaluation.run_eval
```

La evaluación tarda cerca de 5 minutos por el límite de tasa de Groq. Los dos comandos sobrescriben los archivos de resultados del repositorio.

Los números pueden variar un poco frente a los del informe. OpenStreetMap cambia con el tiempo, así que un grafo descargado otro día tiene un número de nodos algo distinto, y el LLM no responde exactamente igual en cada corrida.

## Estructura

```
app.py              Dashboard Streamlit
dashboard/          Mapa Folium y estado de la conversación
agent/              Agente LangGraph, herramientas y prompt
rag/                Corpus, construcción del índice y retriever híbrido
routing/            Descarga del grafo, A*, geocodificación y compute_route()
evaluation/         Preguntas, script de evaluación y resultados
docs/               Informe y declaración de uso de IA
```

## Datos y fuentes

- Red vial y estaciones: OpenStreetMap, con `osmnx`.
- Geocodificación: Nominatim, con una caché en `routing/data/geocode_cache.json` para que los lugares conocidos funcionen aunque el servicio falle.
- Corpus: 11 documentos escritos por el equipo a partir de fuentes públicas. Cada documento lista sus URL y la fecha de consulta en el encabezado.

## Problemas comunes

- **"Falta configurar GROQ_API_KEY".** Falta el archivo `.env` o la clave no es válida.
- **"El grafo vial aún no está preparado".** Falta correr `python routing/download_graph.py`.
- **La respuesta tarda mucho.** El plan gratuito de Groq permite 8.000 tokens por minuto. Dos preguntas de ruta seguidas obligan a esperar; el agente reintenta solo.
- **No encuentra un lugar.** La geocodificación depende de Nominatim. Prueba con un nombre más conocido o con una dirección.
- **PowerShell bloquea la activación del entorno.** Ejecuta los comandos con `venv\Scripts\python.exe` en lugar de activar el entorno.

## Limitaciones

El tiempo de viaje supone velocidad libre por tipo de vía, sin tráfico, y solo aplica a carro. Tarifas, horarios y pico y placa corresponden a la fecha de consulta del corpus. El sistema es informativo y no reemplaza asesoría legal ni de seguridad vial. El detalle está en el informe.
