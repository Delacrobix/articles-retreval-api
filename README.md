# Articles Retrieval API

## Endpoints

### 1. Health Check
```
GET /health
```
Verifica el estado de la API y la conexión con Elasticsearch.

### 2. Get Articles
```
GET /articles?size=50&page=1
```


## Instalación

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   ```

5. Execute the api:
   ```bash
   python main.py
   ```

   with Uvicorn:
   ```bash
   uvicorn main:app --reload
   ```

## Documentación

Once the server is running, access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
