# Articles Retrieval API

## Endpoints

### Articles

#### Health Check
```
GET /health
```
Verifica el estado de la API y la conexión con Elasticsearch.

#### Get Articles
```
GET /articles?size=50&page=1&fields=title,description,link
```
Retorna artículos paginados. Parámetros:
- `size` (default: 50) — cantidad de resultados por página (1-100)
- `page` (default: 1) — número de página
- `fields` (opcional) — campos a retornar separados por coma. Campos válidos: `title`, `description`, `coverImage`, `link`, `slug`, `publishedAt`, `authors`, `body`

Los artículos de Search Labs y Observability Labs se leen del mismo índice,
configurado mediante `ES_INDEX`. Este endpoint limita los resultados a
documentos cuyo campo `source` es `search-labs`.

#### Top Authors
```
GET /top-authors?size=10
```
Retorna los autores con más artículos. Parámetros:
- `size` (default: 10) — cantidad de autores a retornar (1-100)

### Observability Labs

Los mismos endpoints están disponibles bajo el prefijo `/obs`. Consultan el
mismo índice combinado, pero limitan los resultados a documentos cuyo campo
`source` es `observability-labs`.

Consulta [API.md](API.md) para ver el contrato completo de endpoints,
parámetros, respuestas y errores.

```
GET /obs/health
GET /obs/articles?size=50&page=1&fields=title,description,link
GET /obs/top-authors?size=10
```

## Estructura del proyecto

```
├── config.py              # Cliente de Elasticsearch compartido
├── main.py                # Entry point de la API
├── routers/
│   ├── articles.py        # Rutas de articles
│   └── observability.py   # Rutas de observability labs
```

## Instalación

1. Crear un virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Configurar variables de entorno:
   ```bash
   cp .env.example .env
   ```

4. Ejecutar la API:
   ```bash
   python main.py
   ```

   Con Uvicorn:
   ```bash
   uvicorn main:app --reload
   ```

## Documentación

Una vez el servidor esté corriendo, accede a la documentación en:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
