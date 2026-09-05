# Articles Retrieval API

API de solo lectura para consultar artículos de Elastic Search Labs y Elastic
Observability Labs escritos por Jeffrey Rengifo.

Todas las respuestas usan JSON.

## Rutas disponibles

| Colección | Estado | Artículos | Autores principales |
|---|---|---|---|
| Search Labs | `GET /health` | `GET /articles` | `GET /top-authors` |
| Observability Labs | `GET /obs/health` | `GET /obs/articles` | `GET /obs/top-authors` |

## Modelo de respuesta

Los artículos pueden contener los siguientes campos:

| Campo | Tipo | Descripción |
|---|---|---|
| `title` | string | Título del artículo |
| `description` | string | Descripción breve |
| `coverImage` | string | URL de la imagen de portada |
| `link` | string | URL pública del artículo |
| `slug` | string | Identificador del artículo en la URL |
| `publishedAt` | string | Fecha de publicación |
| `authors` | string[] | Lista de autores, sin duplicados |
| `body` | string | Contenido del artículo |

## Endpoints de Search Labs

### `GET /health`

Comprueba que el cliente de Elasticsearch esté configurado.

```json
{
  "status": "ok"
}
```

### `GET /articles`

Devuelve artículos de Search Labs escritos por Jeffrey Rengifo.

Parámetros:

| Parámetro | Valor predeterminado | Restricciones | Descripción |
|---|---:|---:|---|
| `size` | 50 | 1–100 | Resultados por página |
| `page` | 1 | >= 1 | Página solicitada |
| `fields` | todos | lista separada por comas | Campos que se devolverán |

Ejemplo:

```http
GET /articles?size=10&page=1&fields=title,coverImage,link,publishedAt,authors
```

Respuesta:

```json
{
  "articles": [
    {
      "title": "Example | Elasticsearch Labs",
      "coverImage": "https://static-www.elastic.co/.../cover.png",
      "link": "https://www.elastic.co/search-labs/blog/example",
      "publishedAt": "2026-09-01T00:00:00.000Z",
      "authors": ["Jeffrey Rengifo"]
    }
  ],
  "total": 1,
  "page": 1,
  "size": 10,
  "total_pages": 1
}
```

### `GET /top-authors`

Devuelve los autores con más artículos de Search Labs.

Parámetros:

| Parámetro | Valor predeterminado | Restricciones | Descripción |
|---|---:|---:|---|
| `size` | 10 | 1–100 | Número máximo de autores |

```http
GET /top-authors?size=10
```

Respuesta:

```json
{
  "authors": [
    {
      "author": "Jeffrey Rengifo",
      "count": 10
    }
  ],
  "total": 1
}
```

## Endpoints de Observability Labs

Los mismos endpoints se encuentran bajo `/obs` y devuelven resultados de
Observability Labs.

```http
GET /obs/health
GET /obs/articles?size=10&page=1
GET /obs/top-authors?size=10
```

`/obs/articles` también limita los resultados a `Jeffrey Rengifo`.

Los parámetros y formatos de respuesta son idénticos a los endpoints de Search
Labs descritos anteriormente.

## Orden de resultados

Los artículos se devuelven del más reciente al más antiguo. Los documentos sin
fecha de publicación aparecen al final.

## Errores

- `422`: un parámetro no cumple las restricciones indicadas.
- `500`: falta la configuración de Elasticsearch o Elasticsearch rechazó la
  consulta.

Los errores incluyen una explicación en `detail`:

```json
{
  "detail": "Error retrieving articles: ..."
}
```
