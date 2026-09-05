# Articles Retrieval API

API de solo lectura para los artículos de Elastic Search Labs y Elastic
Observability Labs escritos por Jeffrey Rengifo.

Ambas colecciones se almacenan en un único índice de Elasticsearch. Los
endpoints permanecen separados y utilizan el campo extraído `source` para
distinguir cada sección.

## Configuración

Variables de entorno requeridas:

```dotenv
ELASTICSEARCH_ENDPOINT=https://example.es.us-central1.gcp.cloud.es.io:443
ES_API_KEY=...
ES_INDEX=search-observability-labs-index
```

`ES_INDEX` es compartido por todos los endpoints. Su valor predeterminado es
`search-observability-labs-index`.

## Modelo de respuesta

Los artículos pueden contener los siguientes campos:

| Campo de la API | Campo principal en Elasticsearch | Fallback | Tipo |
|---|---|---|---|
| `title` | `title` | — | string |
| `description` | `meta_description` | — | string |
| `coverImage` | `meta_img` | — | string |
| `link` | `url` | — | string |
| `slug` | `url_path_dir3` | — | string |
| `publishedAt` | `published_date` | `meta_published_time` | string |
| `authors` | `meta_author` | — | string[] |
| `body` | `article_content` | `body_content` | string |

Los valores de `authors` se normalizan a una lista plana y sin duplicados,
incluso cuando el crawler almacena arrays anidados.

## Endpoints de Search Labs

### `GET /health`

Comprueba que el cliente de Elasticsearch esté configurado.

### `GET /articles`

Devuelve artículos que cumplen ambos filtros:

```text
meta_author.enum = Jeffrey Rengifo
source.enum      = search-labs
```

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

Devuelve los autores con más documentos cuyo `source.enum` sea `search-labs`.

```http
GET /top-authors?size=10
```

## Endpoints de Observability Labs

Los mismos endpoints se encuentran bajo `/obs` y aplican:

```text
source.enum = observability-labs
```

```http
GET /obs/health
GET /obs/articles?size=10&page=1
GET /obs/top-authors?size=10
```

`/obs/articles` también limita los resultados a `Jeffrey Rengifo`.

## Orden de resultados

Los artículos se ordenan de forma descendente mediante:

1. `published_date`
2. `meta_published_time`, para documentos del crawler anterior
3. `last_crawled_at`, cuando no existe una fecha de publicación

Los campos ausentes se colocan al final.

## Contrato del crawler

Los endpoints requieren que el crawler genere `source` con uno de estos valores
exactos:

```text
search-labs
observability-labs
```

### Regla `source` para Search Labs

```text
URL filter: Begins with /search-labs/blog/
Field name: source
Source: HTML
Selector: meta[property='og:url']
Content: A fixed value
Value: search-labs
Store as: String
```

### Regla `source` para Observability Labs

```text
URL filter: Begins with /observability-labs/blog/
Field name: source
Source: HTML
Selector: meta[property='og:url']
Content: A fixed value
Value: observability-labs
Store as: String
```

### Imagen

```text
Field name: meta_img
Source: HTML
Selector type: XPath
Selector: /html/head/meta[@property='og:image']/@content
Content: Extracted value
Store as: String
```

### Autor

```text
Field name: meta_author
Source: HTML
Selector type: XPath
Selector: //h1/following-sibling::div[.//time][1]//a[contains(@class, 'blog-author')]/text()
Content: Extracted value
Store as: Array
```

### Fecha de publicación

```text
Field name: published_date
Source: HTML
Selector type: XPath
Selector: //h1/following-sibling::div[.//time][1]//time/@datetime
Content: Extracted value
Store as: String
```

### Cuerpo del artículo

```text
Field name: article_content
Source: HTML
Selector type: XPath
Selector: //div[not(@class) and .//h2[@id] and parent::div[contains(@class, 'flex-col')]][1]
Content: Extracted value
Store as: String
```

Las extraction rules deben aplicarse solamente a URLs `/search-labs/blog/` o
`/observability-labs/blog/`. No sustituyen las crawl rules que controlan qué
páginas visita el crawler.

## Errores

- `400`: se solicitó un campo no admitido en `fields`.
- `500`: falta la configuración de Elasticsearch o Elasticsearch rechazó la
  consulta.

## Ejecución local

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Swagger UI estará disponible en `http://localhost:8000/docs`.
