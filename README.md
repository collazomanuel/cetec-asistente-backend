
# CETEC Asistente

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
