"""RutasMDE mobility assistant dashboard."""

from __future__ import annotations

import html
import os

import streamlit as st
from streamlit_folium import st_folium
from dotenv import load_dotenv

from dashboard.map_utils import build_route_map, load_encicla_stations, load_metro_stations
from dashboard.state import add_message, clear_conversation, initialize_state

st.set_page_config(page_title="RutasMDE · Movilidad", page_icon=":material/route:", layout="wide", initial_sidebar_state="auto")
load_dotenv()
initialize_state(st.session_state)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&display=swap');
  :root { --ink:#1C1B19; --muted:#6B665E; --accent:#33443A; --line:#E4DFD4; --surface:#FFFFFF; --metro:#8A5A44; --encicla:#4F6B7A; }
  h1, h2, h3 { letter-spacing:-.02em; font-weight:600; }
  .hero { padding:.5rem 0 1.25rem; }
  .hero h1 { font-size:2rem; line-height:1.15; margin:0 0 .35rem; padding:0; }
  .hero p { color:var(--muted); margin:0; max-width:60ch; }
  .brand { display:flex; align-items:center; gap:.55rem; font-weight:600; font-size:1.05rem; color:var(--ink); }
  .route-summary { display:grid; grid-template-columns:auto auto 1fr; background:var(--surface); border:1px solid var(--line); border-radius:.6rem; margin-bottom:1.5rem; }
  .route-summary > div { padding:.9rem 1.25rem; min-width:0; }
  .route-summary > div + div { border-left:1px solid var(--line); }
  .route-summary .k { display:block; color:var(--muted); font-size:.8rem; margin-bottom:.15rem; }
  .route-summary .v { display:block; font-size:1.35rem; font-weight:600; font-variant-numeric:tabular-nums; white-space:nowrap; }
  .route-summary .v.place { font-size:1rem; font-weight:500; white-space:normal; line-height:1.4; padding-top:.2rem; }
  .route-empty { color:var(--muted); background:var(--surface); border:1px solid var(--line); border-radius:.6rem; padding:.9rem 1.25rem; margin-bottom:1.5rem; }
  .chat-empty { color:var(--muted); margin:.25rem 0; line-height:1.6; }
  .legend { display:flex; flex-wrap:wrap; gap:.4rem 1.1rem; color:var(--muted); font-size:.82rem; margin-top:.5rem; }
  .legend span { display:inline-flex; align-items:center; gap:.4rem; }
  .legend i { width:.6rem; height:.6rem; border-radius:50%; display:inline-block; box-sizing:border-box; }
  .small-note { color:var(--muted); font-size:.83rem; line-height:1.5; }
  .stButton button, .stFormSubmitButton button { min-height:44px; font-weight:500; transition:transform .15s cubic-bezier(.2,.8,.2,1), background-color .15s; }
  .stButton button:active, .stFormSubmitButton button:active { transform:scale(.98); }
  .stButton button:focus-visible, .stFormSubmitButton button:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
  @media (max-width: 760px) {
    .hero h1 { font-size:1.6rem; }
    .route-summary { grid-template-columns:1fr 1fr; }
    .route-summary > div:nth-child(3) { grid-column:1 / -1; border-left:0; border-top:1px solid var(--line); }
  }
  @media (prefers-reduced-motion: reduce) { .stButton button, .stFormSubmitButton button { transition:none; } }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>Muévete mejor por Medellín</h1>
  <p>Pregunta por una ruta o resuelve dudas sobre el transporte del Valle de Aburrá.</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("""
<div class="brand">
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#1C1B19" stroke-width="1.75" stroke-linecap="round" aria-hidden="true">
    <circle cx="5" cy="18" r="2.2"/><circle cx="19" cy="6" r="2.2" fill="#1C1B19"/><path d="M7 17c5 0 3-10 10-10.5"/>
  </svg>
  RutasMDE
</div>
""", unsafe_allow_html=True)
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
if route:
    distance = f"{route['distance_km']:.2f} km" if isinstance(route.get("distance_km"), (int, float)) else "Sin dato"
    duration = f"{route['time_min']:.1f} min" if isinstance(route.get("time_min"), (int, float)) else "Sin dato"
    origin_name = html.escape(str(route.get("origin_name") or "Origen"))
    dest_name = html.escape(str(route.get("dest_name") or "Destino"))
    st.markdown(f"""
<div class="route-summary">
  <div><span class="k">Distancia</span><span class="v">{distance}</span></div>
  <div><span class="k">Tiempo en carro, sin tráfico</span><span class="v">{duration}</span></div>
  <div><span class="k">Recorrido</span><span class="v place">{origin_name} → {dest_name}</span></div>
</div>
""", unsafe_allow_html=True)
else:
    st.markdown(
        "<div class='route-empty'>Aún no hay ruta. Pide una en el chat y aquí verás la distancia, el tiempo y el recorrido.</div>",
        unsafe_allow_html=True,
    )

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
        st.markdown("""
<div class="legend">
  <span><i style="background:#33443A"></i>Ruta</span>
  <span><i style="background:#fff;border:2px solid #1C1B19"></i>Origen</span>
  <span><i style="background:#1C1B19"></i>Destino</span>
  <span><i style="background:#8A5A44"></i>Metro, tranvía y cables</span>
  <span><i style="background:#4F6B7A"></i>EnCicla</span>
</div>
""", unsafe_allow_html=True)
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
            st.markdown("<p class='chat-empty'>Pregunta por una ruta, por el Metro, EnCicla, tarifas, horarios o pico y placa.</p>", unsafe_allow_html=True)
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                if message.get("sources"):
                    st.caption("Fuentes: " + " · ".join(message["sources"]))

    with st.form("mobility_chat", clear_on_submit=True):
        prompt = st.text_input("Tu pregunta", placeholder="¿Cómo llego de EAFIT al Parque Berrío?")
        submitted = st.form_submit_button("Enviar", type="primary", use_container_width=True)

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

