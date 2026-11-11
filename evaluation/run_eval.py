import json
import re
import time
import unicodedata
from pathlib import Path

from agent.agent import MODEL_NAME, run_agent

EVAL_DIR = Path(__file__).resolve().parent
PAUSE_SECONDS = 3


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"(?<=\d)[.,\s](?=\d)", "", text)


def check_route(expected: bool | None, route: dict | None) -> bool | None:
    if expected is None:
        return None
    return (route is not None) == expected


def check_tools(expected: list[str], used: list[str]) -> bool:
    if not expected:
        return not used
    return set(expected) <= set(used)


def check_facts(groups: list[list[str]], response: str) -> bool | None:
    if not groups:
        return None
    text = normalize(response)
    return all(any(normalize(option) in text for option in group) for group in groups)


def check_sources(expected: list[str], sources: list[str]) -> bool | None:
    if not expected:
        return None
    labels = [normalize(source) for source in sources]
    return any(normalize(title) in label for title in expected for label in labels)


def ask(question: str) -> dict:
    try:
        return run_agent(question, [])
    except Exception as error:
        return {"response": f"ERROR: {error}", "route": None, "sources": [], "tools": []}


def main() -> None:
    questions = json.loads((EVAL_DIR / "questions.json").read_text(encoding="utf-8"))
    results = []

    for question in questions:
        start = time.perf_counter()
        answer = ask(question["pregunta"])
        latency = time.perf_counter() - start
        route = answer["route"]

        result = {
            **question,
            "respuesta": answer["response"],
            "herramientas_usadas": answer["tools"],
            "fuentes": answer["sources"],
            "ruta_km": route["distance_km"] if route else None,
            "ruta_ok": check_route(question["espera_ruta"], route),
            "herramientas_ok": check_tools(question["herramientas"], answer["tools"]),
            "datos_ok": check_facts(question["datos_clave"], answer["response"]),
            "fuente_ok": check_sources(question["fuentes_esperadas"], answer["sources"]),
            "latencia_s": round(latency, 2),
            "revision_manual": "",
        }
        results.append(result)
        print(
            f"{question['id']:>2} {question['categoria']:<20} "
            f"ruta={result['ruta_ok']} herramientas={result['herramientas_ok']} "
            f"datos={result['datos_ok']} fuente={result['fuente_ok']} {latency:.1f}s"
        )
        time.sleep(PAUSE_SECONDS)

    summary = {}
    for key in ("ruta_ok", "herramientas_ok", "datos_ok", "fuente_ok"):
        evaluated = [result[key] for result in results if result[key] is not None]
        summary[key] = f"{sum(evaluated)}/{len(evaluated)}"
    summary["latencia_promedio_s"] = round(sum(r["latencia_s"] for r in results) / len(results), 2)

    output = {
        "modelo": MODEL_NAME,
        "fecha": time.strftime("%Y-%m-%d %H:%M"),
        "resumen": summary,
        "resultados": results,
    }
    (EVAL_DIR / "results.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(summary)


if __name__ == "__main__":
    main()
