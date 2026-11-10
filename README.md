# RutasMDE

Copiloto de movilidad para Medellín con A*, agente LLM y RAG.
Proyecto final de SI3003 Inteligencia Artificial, Universidad EAFIT.

## Equipo

- Juan José Acevedo Otálvaro
- Santiago Arellano
- Juan Esteban Peña

## Instalación

```bash
git clone https://github.com/jjacevedo/RutasMDE.git
cd RutasMDE
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Agregar la API key de Groq en `.env` (se obtiene gratis en console.groq.com).

## Ejecución

```bash
python routing/download_graph.py
python rag/build_index.py
streamlit run app.py
```
