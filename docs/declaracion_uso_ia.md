# Declaración de uso de IA generativa

Proyecto final RutasMDE, SI3003 Inteligencia Artificial, Universidad EAFIT, 2026-2.
Equipo: Juan José Acevedo Otálvaro, Santiago Arellano y Juan Esteban Peña.

## Herramientas usadas

- **Claude (Anthropic)**, en la aplicación de chat y en Claude Code.
- **ChatGPT (OpenAI)**.

## Para qué se usaron

| Etapa | Uso |
|---|---|
| Planeación | Entender el enunciado, comparar las cinco ideas propuestas y elegir la más adecuada para el equipo. Dividir el trabajo en tres roles con contratos entre módulos. |
| Código | Revisión de código, generación de ciertas partes del código, detección y diagnóstico de errores (por ejemplo, el fallo de certificados en la geocodificación y la regla del prompt que ubicaba mal las estaciones). |
| Dashboard | Ayuda en el rediseño visual de la interfaz (tema, colores, tipografía y estilo del mapa), sin cambiar su lógica. |
| Evaluación | Apoyo para escribir el script de evaluación y una primera lectura de las 15 respuestas contra el corpus, que el equipo revisó. |
| Documentos | Ayuda inicial en la redacción del informe y de esta declaración a partir de la información del equipo, y revisión de redacción. |

## Lo que hizo el equipo

- Elegir la idea, definir el alcance y tomar las decisiones de diseño (A\* con dos costos, búsqueda híbrida, herramientas del agente).
- Recopilar las fuentes del corpus y verificar sus datos.
- Escribir y ejecutar el código, las pruebas y la evaluación en nuestros equipos, y revisar los resultados.
- Revisar y corregir lo que produjeron las herramientas antes de integrarlo al repositorio.

## Modelos que hacen parte del sistema

El agente del proyecto usa un modelo de lenguaje (`openai/gpt-oss-120b`, servido por Groq) y un modelo de embeddings (`paraphrase-multilingual-MiniLM-L12-v2`). Los dos son componentes del sistema entregado y están descritos en el informe. No los usamos como herramientas de apoyo para hacer el proyecto.

## Responsabilidad

Entendemos el código y los documentos que entregamos y respondemos por su contenido. Verificamos lo que produjeron las herramientas, y los errores que encontró la revisión manual de la evaluación están reportados en el informe.
