import os
from typing import Any, Iterable


# Both Labs sections are crawled into the same Elasticsearch index and are
# distinguished by the custom `source` extraction field.
ES_INDEX = os.getenv("ES_INDEX", "search-observability-labs-index")

FIELD_MAPPING = {
    "title": ("title",),
    "description": ("meta_description",),
    "coverImage": ("meta_img",),
    "link": ("url",),
    "slug": ("url_path_dir3",),
    # The old crawl used meta_published_time; the new combined crawl uses
    # published_date. Prefer the new field while retaining old documents.
    "publishedAt": ("published_date", "meta_published_time"),
    "authors": ("meta_author",),
    # Fall back to the crawler's standard body when the custom extraction rule
    # has not populated article_content.
    "body": ("article_content", "body_content"),
}

VALID_FIELDS = list(FIELD_MAPPING.keys())


def source_fields(requested_fields: Iterable[str]) -> list[str]:
    """Return all Elasticsearch fields needed for the requested API fields."""
    fields: list[str] = []
    for api_field in requested_fields:
        for es_field in FIELD_MAPPING[api_field]:
            if es_field not in fields:
                fields.append(es_field)
    return fields


def first_value(source: dict[str, Any], api_field: str) -> Any:
    """Return the first populated Elasticsearch value for an API field."""
    for es_field in FIELD_MAPPING[api_field]:
        value = source.get(es_field)
        if value not in (None, "", []):
            return value
    return ""


def normalize_authors(value: Any) -> list[str]:
    """Flatten crawler author values into a stable list of author names."""
    authors: list[str] = []

    def collect(item: Any) -> None:
        if isinstance(item, (list, tuple)):
            for nested in item:
                collect(nested)
        elif isinstance(item, str):
            name = item.strip()
            if name and name not in authors:
                authors.append(name)

    collect(value)
    return authors


def serialize_article(source: dict[str, Any], requested_fields: Iterable[str]) -> dict:
    article = {}
    for api_field in requested_fields:
        value = first_value(source, api_field)
        article[api_field] = (
            normalize_authors(value) if api_field == "authors" else value
        )
    return article


def source_filter(source: str) -> dict:
    """Restrict a query to one Labs section inside the combined index."""
    return {"term": {"source.enum": source}}


def article_sort() -> list[dict]:
    """Sort new and legacy crawler documents without failing on missing fields."""
    return [
        {
            "published_date": {
                "order": "desc",
                "missing": "_last",
                "unmapped_type": "date",
            }
        },
        {
            "meta_published_time": {
                "order": "desc",
                "missing": "_last",
                "unmapped_type": "date",
            }
        },
        {
            "last_crawled_at": {
                "order": "desc",
                "missing": "_last",
                "unmapped_type": "date",
            }
        },
    ]


def build_article_query(
    source: str,
    *,
    size: int,
    offset: int,
    es_fields: list[str],
) -> dict:
    return {
        "size": size,
        "from": offset,
        "_source": es_fields,
        "query": {
            "bool": {
                "filter": [
                    {"term": {"meta_author.enum": "Jeffrey Rengifo"}},
                    source_filter(source),
                ]
            }
        },
        "sort": article_sort(),
    }


def build_top_authors_query(source: str, *, size: int) -> dict:
    return {
        "size": 0,
        "query": {
            "bool": {
                "filter": [source_filter(source)],
                "must_not": [{"term": {"meta_author.enum": ""}}],
            }
        },
        "aggs": {
            "top_authors": {
                "terms": {
                    "field": "meta_author.enum",
                    "size": size,
                }
            }
        },
    }
