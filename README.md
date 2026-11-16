# RutasMDE

Copiloto de movilidad para Medellín con A*, agente LLM y RAG. Proyecto final
de SI3003 Inteligencia Artificial, Universidad EAFIT.

## Equipo

- Juan José Acevedo Otálvaro
- Santiago Arellano
- Juan Esteban Peña

## Instalación

```bash
python -m venv venv
# Linux/macOS: source venv/bin/activate
# Windows PowerShell: venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Crea `.env` a partir de `.env.example` y configura `GROQ_API_KEY` con tu clave
de Groq. `GROQ_MODEL` es opcional; si no se define, el agente usa
`openai/gpt-oss-120b`. No publiques `.env` ni incluyas secretos en el repositorio.

```bash
# Linux/macOS
cp .env.example .env
```

```powershell
# Windows PowerShell
Copy-Item .env.example .env
```

## Preparar los recursos

Desde la raíz del repositorio:

```bash
python routing/download_graph.py
python rag/build_index.py
```

El primer comando genera `routing/data/medellin.graphml` desde OpenStreetMap y
requiere conexión a internet. El segundo crea `rag/faiss_index/` y descarga el
modelo multilingüe de Sentence Transformers si aún no está en caché. Estos
recursos no están incluidos en el repositorio. Los lugares ya conocidos usan
`routing/data/geocode_cache.json`; para lugares nuevos, el geocodificador puede
consultar Nominatim.

## Instalacion y ejecucion en Windows PowerShell

Ejecuta los siguientes comandos desde la carpeta del repositorio:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
python routing/download_graph.py
python rag/build_index.py
python -m streamlit run app.py
```

En `.env`, reemplaza el valor de ejemplo de `GROQ_API_KEY` por tu clave real.
`GROQ_MODEL` es opcional. Guarda el archivo antes de iniciar Streamlit. Los
scripts y rutas anteriores existen en el proyecto.

Si PowerShell bloquea la activacion del entorno, abre una nueva terminal
PowerShell con la politica de ejecucion apropiada para tu equipo o ejecuta los
comandos de Python mediante `venv\Scripts\python.exe`.

## Ejecutar el dashboard

```bash
streamlit run app.py
```

En PowerShell, si el entorno virtual está activado, los comandos anteriores
funcionan igual. También puedes ejecutar `python -m streamlit run app.py`.

La aplicación ofrece chat en español con el agente, consulta RAG y rutas viales
calculadas por A*. Cuando existe una ruta, presenta los nombres, distancia y
tiempo devueltos por el enrutador. El mapa dibuja el recorrido y sus extremos.
Las capas activables de Metro, tranvía, cables y EnCicla muestran los puntos de
los JSON disponibles; son referencias geográficas, no rutas multimodales.
Preguntas generales no requieren una ruta activa.

Si falta la clave de Groq, el dashboard aún inicia, pero no puede consultar al
agente. Si falta el grafo o el índice RAG, prepara esos recursos con los comandos
anteriores. Un error al construir el mapa no bloquea el chat.
