# CRM de práctica — Seguimiento Comercial con Asistente de IA

Mini CRM de seguimiento comercial construido como prueba técnica para **LABS IA · APIUX**.
Permite registrar, consultar, actualizar y analizar oportunidades de negocio a través de una
interfaz web (Angular), un backend con API REST (Django REST Framework), persistencia en
SQLite y un **asistente de IA** conectado a los datos reales del CRM.

---

## 1. Características

**Frontend (Angular 17)**
- Listado de oportunidades comerciales con tablero de métricas del pipeline.
- Crear, editar y desactivar (soft delete) oportunidades.
- Detalle de cada oportunidad.
- Filtros por etapa, prioridad, responsable y búsqueda por texto.
- Chat con el asistente de IA.

**Backend (Django REST Framework)**
- API REST completa: `GET/POST/PATCH/DELETE /api/opportunities/`.
- Filtros por `stage`, `priority`, `owner`, `search` e `is_active`.
- Endpoint de métricas: `GET /api/opportunities/stats/`.
- Endpoint del asistente: `POST /api/assistant/chat/`.
- Registros de interacción, conversaciones, mensajes, prompts y evaluaciones.

**Base de datos (SQLite)**
- Persistencia real. Datos semilla con las 5 oportunidades de ejemplo del enunciado.

**Asistente de IA**
- Tool calling / function calling.
- RAG sobre los datos del CRM.
- Memoria conversacional.
- Logs de interacciones.
- Evaluación de respuestas (thumbs up/down).
- Prompt de sistema versionado.
- Control de alucinaciones: solo responde con datos reales y explica el origen.
- **Modo offline**: sin API key, un motor basado en reglas consulta los datos reales
  del CRM y responde las preguntas del enunciado sin necesidad de un modelo externo.

---

## 2. Estructura del proyecto

```
.
├── backend/                # Django REST Framework + SQLite
│   ├── config/             # settings, urls
│   ├── crm/                # modelo Opportunity, CRUD, stats, seed
│   └── assistant/          # chat, conversaciones, logs, prompts, evaluaciones
│       └── services/       # llm, tool_registry, rag, memory, hallucination
├── frontend/               # Angular 17
│   └── src/app/
│       ├── components/     # chat, opportunities, logs, prompts
│       └── services/       # crm.service, chat.service
├── .env.example            # variables de entorno documentadas
└── README.md
```

---

## 3. Requisitos

- Python 3.10+
- Node.js 18+
- Angular CLI: `npm install -g @angular/cli`

---

## 4. Ejecución local

### Backend

```bash
cd backend
python -m venv .venv            # opcional
pip install -r requirements.txt

# variables de entorno (opcional; hay valores por defecto para desarrollo)
copy .env.example .env          # en Windows
# cp .env.example .env          # en Linux/macOS

python manage.py migrate
python manage.py seed_data      # carga 5 oportunidades + prompt v1
python manage.py runserver
```

El backend corre en `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
ng serve --proxy-config proxy.conf.json
```

El frontend corre en `http://localhost:4200`. El proxy redirige `/api/*` al backend.

> Sin `OPENAI_API_KEY`, el asistente usa el **modo offline basado en reglas**
> que consulta los datos reales de la base de datos. Para usar OpenAI, define
> `OPENAI_API_KEY` y `OPENAI_MODEL` en `backend/.env`.

### Datos de prueba

```bash
cd backend
python manage.py seed_data
```

El comando es idempotente: puede ejecutarse varias veces sin duplicar datos.

---

## 5. Variables de entorno

| Variable | Descripción | Default |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Clave secreta de Django | valor de desarrollo |
| `DJANGO_DEBUG` | Modo debug (`True`/`False`) | `True` |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos separados por coma | `*` |
| `OPENAI_API_KEY` | API key de OpenAI (vacía = modo offline) | *(vacío)* |
| `OPENAI_MODEL` | Modelo del asistente | `gpt-4o-mini` |

Ver `backend/.env.example`.

---

## 6. API

| Método | Ruta | Descripción |
| --- | --- | --- |
| `GET` | `/api/opportunities/` | Listar (filtros: `stage`, `priority`, `owner`, `search`, `is_active`) |
| `POST` | `/api/opportunities/` | Crear oportunidad |
| `GET` | `/api/opportunities/{id}/` | Detalle |
| `PATCH/PUT` | `/api/opportunities/{id}/` | Actualizar |
| `DELETE` | `/api/opportunities/{id}/` | Desactivar (soft delete) |
| `GET` | `/api/opportunities/stats/` | Métricas del pipeline |
| `POST` | `/api/opportunities/{id}/ai/` | Recomendación IA por oportunidad |
| `POST` | `/api/assistant/chat/` | Chat con el asistente |
| `GET` | `/api/assistant/conversations/` | Conversaciones |
| `GET` | `/api/assistant/logs/` | Logs de interacción |
| `GET` | `/api/assistant/system-prompts/` | Prompts versionados |

---

## 7. Asistente de IA

El asistente consulta los datos reales persistidos y **no inventa oportunidades**.

Flujo de una petición en `backend/assistant/views.py`:

1. Se registra el mensaje del usuario y se recupera la conversación (memoria).
2. El RAG (`services/rag.py`) recupera las oportunidades más relevantes de la BD.
3. Se invoca al LLM con las definiciones de herramientas (`services/tool_registry.py`):
   `search_opportunities`, `get_opportunity_details`, `update_opportunity_stage`,
   `get_crm_summary`, `get_follow_ups`.
4. Si el modelo solicita herramientas, se ejecutan contra la BD real y se devuelve
   el resultado al modelo para componer la respuesta.
5. El controlador de alucinaciones (`services/hallucination.py`) verifica que los
   datos mencionados (montos, etapas, prioridades, empresas) existan en el contexto.
6. La interacción se registra en `InteractionLog`.

Sin API key, `services/llm.py` usa `FallbackLLM`, un motor determinista basado en reglas
que detecta la intención de la pregunta, ejecuta las mismas herramientas sobre los datos
reales y compone la respuesta. Las preguntas fuera del alcance del CRM reciben una
respuesta controlada.

---

## 8. Decisiones técnicas

- **Django + DRF**: framework maduro con serializers que aportan validación de entrada,
  paginación y un CRUD completo de forma declarativa.
- **Angular 17 standalone**: componentes autocontenidos y carga perezosa por ruta.
- **SQLite**: base de datos real sin infraestructura, suficiente para la prueba y para
  ejecutar localmente sin pasos extra. Fácil de migrar a PostgreSQL vía settings.
- **Soft delete** (`is_active`) en lugar de borrado físico para preservar el historial.
- **Etapas y prioridades en español** según el enunciado (Lead nuevo, Contactado,
  Diagnóstico, Propuesta enviada, Negociación, Ganado, Perdido / Baja, Media, Alta, Crítica).
- **Separación de responsabilidades**: la lógica de negocio vive en `tool_registry.py` y
  los servicios; la capa de LLM está aislada en `llm.py` con un contrato `BaseLLM`.
- **Modo offline por defecto**: permite evaluar toda la solución sin depender de claves externas.

---

## 9. Mejoras futuras

- Autenticación y roles por usuario/equipo comercial.
- Migración a PostgreSQL y Docker Compose.
- Exportación a CSV.
- Despliegue en Vercel/Render/Railway.
- Streaming de respuestas del asistente (SSE).
- Embeddings reales para el RAG (vector store).
- Tests unitarios e integración ampliados.

---

## 10. Notas del entorno

- La base de datos local `backend/db.sqlite3` se regenera con `migrate` + `seed_data`.
- No subir al repositorio claves ni credenciales (ver `.gitignore` y `.env.example`).
