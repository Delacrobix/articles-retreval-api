import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from config import es_client

router = APIRouter()

ES_INDEX = os.getenv("OBSERVABILITY_ES_INDEX", "search-observability-articles-index")

FIELD_MAPPING = {
    "title": "title",
    "description": "meta_description",
    "coverImage": "meta_img",
    "link": "url",
    "slug": "url_path_dir3",
    "publishedAt": "meta_published_time",
    "authors": "meta_author",
    "body": "article_content",
}

VALID_FIELDS = list(FIELD_MAPPING.keys())


@router.get("/health")
async def healthcheck():
    """
    Healthcheck endpoint
    """
    try:
        if es_client:
            return {"status": "ok"}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Elasticsearch connection error: {str(e)}"
        )


@router.get("/articles")
async def get_articles(
    size: int = Query(50, ge=1, le=100, description="Number of results to return"),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    fields: Optional[str] = Query(
        None,
        description="Comma-separated list of fields to return (e.g., 'title,description,link')",
    ),
):
    """
    Retrieve observability articles from Elasticsearch filtered by Jeffrey Rengifo
    """

    if not es_client:
        raise HTTPException(
            status_code=500,
            detail="Elasticsearch client not configured. Please set ELASTICSEARCH_ENDPOINT and ES_API_KEY environment variables.",
        )

    try:
        if fields:
            requested_fields = [f.strip() for f in fields.split(",")]
            invalid = [f for f in requested_fields if f not in VALID_FIELDS]

            if invalid:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid fields: {invalid}. Valid fields are: {VALID_FIELDS}",
                )
        else:
            requested_fields = VALID_FIELDS

        es_fields = [FIELD_MAPPING[f] for f in requested_fields]
        from_param = (page - 1) * size

        search_query = {
            "size": size,
            "from": from_param,
            "_source": es_fields,
            "query": {
                "bool": {"filter": [{"term": {"meta_author.enum": "Jeffrey Rengifo"}}]}
            },
            "sort": [{"published_date": {"order": "desc", "missing": "_last"}}],
        }

        response = es_client.search(index=ES_INDEX, body=search_query)

        articles = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            lab = {}

            for api_field in requested_fields:
                es_field = FIELD_MAPPING[api_field]

                if api_field == "authors":
                    lab[api_field] = (
                        [source.get(es_field, "")] if source.get(es_field) else []
                    )
                else:
                    lab[api_field] = source.get(es_field, "")

            articles.append(lab)

        return {
            "articles": articles,
            "total": response["hits"]["total"]["value"],
            "page": page,
            "size": size,
            "total_pages": (response["hits"]["total"]["value"] + size - 1) // size,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving articles: {str(e)}"
        )


@router.get("/top-authors")
async def get_top_authors(
    size: int = Query(10, ge=1, le=100, description="Number of top authors to return"),
):
    """
    Retrieve top authors by lab count using Elasticsearch terms aggregation
    """

    if not es_client:
        raise HTTPException(
            status_code=500,
            detail="Elasticsearch client not configured. Please set ELASTICSEARCH_ENDPOINT and ES_API_KEY environment variables.",
        )

    try:
        search_query = {
            "size": 0,
            "aggs": {
                "top_authors": {
                    "terms": {
                        "field": "meta_author.enum",
                        "size": size,
                    }
                }
            },
        }

        response = es_client.search(index=ES_INDEX, body=search_query)

        buckets = response["aggregations"]["top_authors"]["buckets"]
        authors = [{"author": b["key"], "count": b["doc_count"]} for b in buckets]

        return {"authors": authors, "total": len(authors)}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving top authors: {str(e)}"
        )
