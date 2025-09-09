
# CETEC Assistant API

A FastAPI-based backend for a student chat system with document ingestion capabilities, routing through A2A servers and providing a teacher-facing ingestion UI.

## Features

- **Student Chat System**: Conversational interface for students to ask questions
- **Document Management**: Upload, manage, and track documents for different subjects
- **Vector Store Integration**: Automatic document ingestion into vector collections
- **A2A Server Routing**: Dynamic routing to appropriate AI/ML servers based on subject
- **Teacher Dashboard**: Interface for teachers to manage subjects and documents
- **Admin Panel**: Administrative controls for system configuration

## Architecture

The API is built with FastAPI and follows a modular architecture:

```
app/
├── core/           # Core functionality (config, auth, database)
├── models/         # Pydantic models for request/response schemas
├── routers/        # FastAPI route handlers organized by domain
├── services/       # Business logic layer
└── main.py         # FastAPI application factory
```

## API Endpoints

### Meta
- `GET /api/v1/healthz` - Health check
- `GET /api/v1/readyz` - Readiness check

### Authentication
- `GET /api/v1/me` - Get current user info

### Subjects
- `GET /api/v1/subjects` - List subjects
- `POST /api/v1/subjects` - Create subject
- `GET /api/v1/subjects/{slug}` - Get subject details
- `PATCH /api/v1/subjects/{slug}` - Update subject
- `DELETE /api/v1/subjects/{slug}` - Delete subject

### Documents
- `GET /api/v1/subjects/{slug}/documents` - List documents
- `POST /api/v1/subjects/{slug}/uploads/presign` - Get presigned upload URLs
- `POST /api/v1/subjects/{slug}/uploads/complete` - Complete uploads
- `GET /api/v1/subjects/{slug}/documents/{id}` - Get document
- `DELETE /api/v1/subjects/{slug}/documents/{id}` - Delete document

### Ingestion
- `POST /api/v1/subjects/{slug}/ingestions` - Start ingestion job
- `GET /api/v1/subjects/{slug}/ingestions` - List ingestion jobs
- `GET /api/v1/ingestions/{id}` - Get ingestion job status
- `POST /api/v1/ingestions/{id}/cancel` - Cancel ingestion job

### Chat
- `POST /api/v1/conversations` - Create conversation
- `GET /api/v1/conversations` - List conversations
- `GET /api/v1/conversations/{id}` - Get conversation
- `DELETE /api/v1/conversations/{id}` - Delete conversation
- `POST /api/v1/conversations/{id}/messages` - Send message
- `GET /api/v1/conversations/{id}/messages` - Get message history
- `POST /api/v1/conversations/{id}/messages/stream` - Stream message response

### A2A & Routing
- `GET /api/v1/routing/policy` - Get routing policy
- `PATCH /api/v1/routing/policy` - Update routing policy
- `GET /api/v1/a2a/servers` - List A2A servers
- `POST /api/v1/a2a/servers` - Register A2A server
- `GET /api/v1/a2a/servers/{id}/health` - Check server health

### Webhooks
- `POST /api/v1/webhooks/s3` - S3 event notifications
- `POST /api/v1/webhooks/a2a/{id}/callback` - A2A server callbacks

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

   Or with uvicorn directly:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Configuration

Key environment variables:

- `MONGODB_URI`: MongoDB connection string
- `JWT_SECRET_KEY`: Secret key for JWT tokens
- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`: AWS credentials for S3
- `S3_BUCKET`: S3 bucket for document storage
- `FRONTEND_URL`: Frontend application URL for CORS

## Development

1. **API Documentation**: Available at `/api/v1/docs` when running
2. **Testing**: Run tests with `pytest tests/`
3. **Database**: MongoDB with collections for subjects, documents, conversations, etc.
4. **Authentication**: JWT-based with Google OAuth support

## Project Structure

```
cetec-asistente-backend/
├── app/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── auth.py          # Authentication logic
│   │   ├── config.py        # Configuration settings
│   │   └── database.py      # Database connection
│   ├── models/
│   │   ├── __init__.py
│   │   ├── auth.py          # User models
│   │   ├── subjects.py      # Subject models
│   │   ├── documents.py     # Document models
│   │   ├── ingestion.py     # Ingestion models
│   │   ├── chat.py          # Chat models
│   │   └── a2a.py           # A2A server models
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── meta.py          # Health checks
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── subjects.py      # Subject management
│   │   ├── documents.py     # Document operations
│   │   ├── ingestion.py     # Ingestion jobs
│   │   ├── chat.py          # Chat functionality
│   │   ├── a2a.py           # A2A server management
│   │   └── webhooks.py      # Webhook handlers
│   ├── services/
│   │   ├── __init__.py
│   │   ├── subject_service.py
│   │   ├── document_service.py
│   │   ├── ingestion_service.py
│   │   ├── chat_service.py
│   │   └── a2a_service.py
│   └── main.py              # FastAPI app factory
├── tests/
│   ├── __init__.py
│   └── test_api.py          # Basic API tests
├── docs/
│   └── apidesign.yaml       # OpenAPI specification
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── env.example             # Environment variables template
└── README.md               # This file
```

Este es el back-end del CETEC Asistente construido en Python utilizando el framework web FastAPI. Está diseñado para el uso de los alumnos de la Facultad de Ingeniería de la Universidad de Buenos Aires. Este documento detalla las instrucciones para su configuración, ejecución y uso.

<div align="center">
  <img src="https://user-images.githubusercontent.com/75450615/228704389-a2bcdf3e-d4d6-4236-b1c6-57fd9e545625.png#gh-dark-mode-only" width="50%" align="center">
</div>

### Requisitos previos

Antes de ejecutar este back-end, asegúrese de tener instalado lo siguiente:

- Python 3.7+ (se recomienda utilizar la última versión estable de Python)
- Pip (administrador de paquetes de Python)

## Configuración del entorno

1. **Crea un entorno virtual**

```bash
python3 -m venv .venv
```

2. **Activa el entorno virtual**

En Ubuntu:

```bash
source .venv/bin/activate
```

En Windows:

```bash
.venv\Scripts\activate
```

3. **Instala las dependencias**

```bash
pip install -r requirements.txt
```

4. **Configura las variables de entorno**

Crea un archivo `.env` en el directorio raíz del proyecto y define las siguientes variables:

```env
MONGODB_KEY=<tu_clave_de_mongodb>
FRONTEND_URL=<url_del_frontend>
GOOGLE_CLIENT_ID='id_de_cliente_de_google'
GOOGLE_CLIENT_SECRET='secret_de_cliente_de_google'
AUTH_SECRET='secret_de_autenticascióm'

```

5. **Ejecuta el servidor**

```bash
uvicorn main:app --reload
```

## Endpoints disponibles

### Documentación interactiva

FastAPI genera automáticamente una documentación interactiva en `http://127.0.0.1:8000/docs`. Aquí puedes explorar y probar los endpoints disponibles.

```http
GET /docs
```

### Endpoints principales

#### (GET) `/history`

Obtiene el historial de chat.

#### (POST) `/ask`

Realiza una consulta al asistente

- **Body**:
  ```json
  {
    "question": "¿Qué es la física?",
  }
  ```

## Dependencias

Las dependencias del proyecto están listadas en el archivo `requirements.txt`:

```plaintext
fastapi==0.111.1
pydantic==2.8.2
pymongo==3.13.0
uvicorn==0.20.0
python-decouple==3.8
dnspython==2.3.0
```

Instálalas ejecutando:

```bash
pip install -r requirements.txt
```

---

## Notas adicionales

- **Integración con asistente**: En desarrollo

---

## Contacto

Para consultas o soporte, puedes contactarte con el desarrollador a través de [mcollazo@fi.uba.ar](mailto:mcollazo@fi.uba.ar).

![Footer](https://user-images.githubusercontent.com/75450615/175360883-72efe4c4-1f14-4b11-9a7c-55937563cffa.png)
