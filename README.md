# Dr. Matrícula - Chatbot de la UBE

**Dr. Matrícula** es un asistente virtual desarrollado en Python que actúa como **vendedor de carreras de la Universidad Bolivariana del Ecuador (UBE)**. Utiliza la API de Argo con modelos LLM (Google Gemini) y Streamlit para la interfaz web.

El chatbot puede responder preguntas sobre:

- Información general de las carreras (grado y postgrado)
- Información de los grupos disponibles de una carrera específica
- Información de la malla de una carrera (pendiente de integración)

---

## Tecnologías utilizadas

- Python 3.13+
- [Argo](https://pypi.org/project/argo/) - integración con LLMs y habilidades de chat
- [Streamlit](https://streamlit.io/) - interfaz web
- Requests - para consumir la API de la UBE
- Pydantic - para validar y estructurar los datos de la API

---

## Instalación

1. Clonar el repositorio:

```bash
git clone https://github.com/tu-usuario/dr-matricula.git
cd dr-matricula
Crear un entorno virtual:
```

2. Crear un entorno virtual:
```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Crear variables de entorno:
```
TOKEN=tu_token_de_openrouter
API_URL=endpoint
```

----

## Uso
Ejecutar la aplicación con Streamlit:
```bash
streamlit run app.py
```

Interactuar con el chatbot desde la interfaz web.
Ejemplos de preguntas:
- "Muéstrame las carreras disponibles"
- "Quiero los grupos de la carrera Derecho"
- "Información sobre la malla"

---

## Estructura del proyecto

```bash
.
├─ app/
│  └─ agent.py          # Código principal del chatbot y definición del agente
├─ schemas/
│  ├─ carreras.py       # Modelos Pydantic para carreras
│  └─ grupos.py         # Modelos Pydantic para grupos
├─ .env                 # Variables de entorno
├─ requirements.txt
└─ README.md

```

