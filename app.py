"""RutasMDE mobility assistant dashboard."""

from __future__ import annotations

import os

import streamlit as st
from streamlit_folium import st_folium
from dotenv import load_dotenv

from dashboard.map_utils import build_route_map, load_encicla_stations, load_metro_stations
from dashboard.state import add_message, clear_conversation, initialize_state

st.set_page_config(page_title="RutasMDE · Movilidad", page_icon="🧭", layout="wide", initial_sidebar_state="expanded")
load_dotenv()
initialize_state(st.session_state)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');
  :root { --ink:#14243a; --muted:#607086; --brand:#176b5b; --line:#e5ebef; }
  html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
  .stApp { background:linear-gradient(180deg,#f4f8f7 0,#f7f9fb 280px); color:var(--ink); }
  h1,h2,h3 { font-family:'Manrope',sans-serif; letter-spacing:-.035em; }
  .hero { padding:1.1rem 0 .65rem; }
  .eyebrow { color:#176b5b; font-size:.74rem; font-weight:700; letter-spacing:.13em; text-transform:uppercase; }
  .hero h1 { font-size:2.35rem; margin:.15rem 0 .25rem; }
  .hero p { color:#607086; margin:0; }
  [data-testid="stMetric"] { background:white; border:1px solid #e5ebef; padding:1rem 1.1rem; border-radius:16px; box-shadow:0 5px 18px #213d4a0a; }
  [data-testid="stMetricLabel"] { color:#607086; }
  div[data-testid="stVerticalBlockBorderWrapper"] { border-radius:16px; }
  .stButton button, .stFormSubmitButton button { border-radius:11px; font-weight:600; }
  .small-note { color:#718096; font-size:.83rem; }
  @media (max-width: 760px) { .hero h1 { font-size:1.8rem; } }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="eyebrow">Tu copiloto de movilidad</div>
  <h1>Muévete mejor por Medellín</h1>
  <p>Pregunta por una ruta o resuelve dudas sobre el transporte del Valle de Aburrá.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🧭 RutasMDE")
    st.caption("Asistente de movilidad · EAFIT")
    st.divider()
    st.markdown("**Capas del mapa**")
    st.session_state.show_metro = st.checkbox("Metro, tranvía y cables", value=st.session_state.show_metro)
    st.session_state.show_encicla = st.checkbox("Estaciones EnCicla", value=st.session_state.show_encicla)
    st.caption(f"{len(load_metro_stations())} estaciones de transporte · {len(load_encicla_stations())} puntos EnCicla")
    st.divider()
    if st.button("Nueva conversación", use_container_width=True):
        clear_conversation(st.session_state)
        st.rerun()
    st.markdown("<p class='small-note'>Las rutas se calculan sobre el grafo vial disponible. Las capas de transporte son puntos de referencia; no representan una ruta multimodal.</p>", unsafe_allow_html=True)

route = st.session_state.last_route
metric_cols = st.columns(3)
if route:
    metric_cols[0].metric("Distancia", f"{route['distance_km']:.2f} km" if isinstance(route.get("distance_km"), (int, float)) else "—")
    metric_cols[1].metric("Tiempo estimado", f"{route['time_min']:.1f} min" if isinstance(route.get("time_min"), (int, float)) else "—")
    metric_cols[2].metric("Recorrido", f"{route.get('origin_name') or 'Origen'} → {route.get('dest_name') or 'Destino'}")
else:
    metric_cols[0].metric("Distancia", "—", help="Aparecerá cuando el agente calcule una ruta")
    metric_cols[1].metric("Tiempo estimado", "—", help="Aparecerá cuando el agente calcule una ruta")
    metric_cols[2].metric("Ruta activa", "Sin ruta")

map_col, chat_col = st.columns([1.55, 1], gap="large")
with map_col:
    st.subheader("Mapa de movilidad")
    st.caption("Ruta vial calculada por A* y estaciones cercanas de referencia.")
    try:
        route_map = build_route_map(
            route,
            show_metro=st.session_state.show_metro,
            show_encicla=st.session_state.show_encicla,
        )
        st_folium(
            route_map,
            height=570,
            use_container_width=True,
            returned_objects=[],
            key="rutasmde_map",
        )
    except Exception as map_error:
        st.warning("No fue posible cargar el mapa. El chat sigue disponible.")
        with st.expander("Detalle técnico"):
            st.exception(map_error)

with chat_col:
    st.subheader("Chat de movilidad")
    st.caption("Ejemplo: ¿Cómo llego desde EAFIT hasta Parque Berrío?")
    history_box = st.container(height=405, border=True)
    with history_box:
        if not st.session_state.messages:
            st.info("Hola. Puedo ayudarte con rutas viales, Metro, EnCicla, horarios y otros temas de movilidad.")
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message.get("sources"):
                    st.caption("Fuentes: " + " · ".join(message["sources"]))

    with st.form("mobility_chat", clear_on_submit=True):
        prompt = st.text_input("Tu pregunta", placeholder="Escribe tu pregunta de movilidad…", label_visibility="collapsed")
        submitted = st.form_submit_button("Enviar mensaje", type="primary", use_container_width=True)

    if submitted and prompt.strip():
        st.session_state.loading = True
        st.session_state.error = None
        add_message(st.session_state, "user", prompt.strip())
        # Rol A expects prior turns only; this prompt is passed separately.
        conversation = [
            {"role": message["role"], "content": message["content"]}
            for message in st.session_state.messages[:-1]
            if message["role"] in {"user", "assistant"}
        ]
        try:
            if not os.getenv("GROQ_API_KEY"):
                raise RuntimeError("Falta configurar GROQ_API_KEY. Agrégala al archivo .env y reinicia la aplicación.")
            from agent.agent import run_agent

            with st.spinner("Consultando el asistente…"):
                result = run_agent(prompt.strip(), conversation)
            if not isinstance(result, dict):
                raise ValueError("El asistente devolvió una respuesta con formato inesperado.")
            response = result.get("response")
            if isinstance(response, list):
                response = "\n\n".join(str(part.get("text", part)) if isinstance(part, dict) else str(part) for part in response)
            response = str(response or "No recibí una respuesta. Intenta de nuevo con otras palabras.")
            route_data = result.get("route")
            tools_used = result.get("tools") or []
            route_was_requested = isinstance(tools_used, (list, tuple, set)) and "calcular_ruta" in tools_used
            if isinstance(route_data, dict) and route_data.get("coords"):
                st.session_state.last_route = route_data
            else:
                if route_was_requested:
                    st.session_state.last_route = None
                if route_data is not None:
                    response += "\n\nNo pude mostrar una ruta porque el resultado llegó incompleto."
            add_message(st.session_state, "assistant", response, sources=result.get("sources") or [], tools=tools_used)
        except Exception as error:
            friendly = str(error)
            if "medellin.graphml" in friendly or "download_graph.py" in friendly:
                friendly = "El grafo vial aún no está preparado. Ejecuta `python routing/download_graph.py` y vuelve a intentar la ruta."
            elif "No encontré" in friendly or "No encontre" in friendly:
                friendly = "No encontré uno de esos lugares. Prueba con un nombre más conocido o agrega la ciudad."
            elif "No hay camino" in friendly:
                friendly = "No se encontró un recorrido entre esos puntos en el grafo disponible."
            st.session_state.error = friendly
            add_message(st.session_state, "assistant", f"No pude completar la consulta. {friendly}")
        finally:
            st.session_state.loading = False
        st.rerun()
    elif submitted:
        st.warning("Escribe una pregunta antes de enviarla.")

if st.session_state.error:
    st.error(st.session_state.error)

if route:
    with st.expander("Detalles de la ruta"):
        st.write(f"**Origen:** {route.get('origin_name') or 'No disponible'}")
        st.write(f"**Destino:** {route.get('dest_name') or 'No disponible'}")
        if isinstance(route.get("nodes_expanded"), (int, float)):
            st.caption(f"Nodos expandidos por A*: {route['nodes_expanded']}")

