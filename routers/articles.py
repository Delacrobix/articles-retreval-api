from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from config import es_client
from routers.labs_common import (
    ES_INDEX,
    VALID_FIELDS,
    build_article_query,
    build_top_authors_query,
    serialize_article,
    source_fields,
)

router = APIRouter()

LAB_SOURCE = "search-labs"


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
    Retrieve articles from Elasticsearch filtered by Jeffrey Rengifo
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

        es_fields = source_fields(requested_fields)
        from_param = (page - 1) * size

        search_query = build_article_query(
            LAB_SOURCE,
            size=size,
            offset=from_param,
            es_fields=es_fields,
        )

        response = es_client.search(index=ES_INDEX, body=search_query)

        articles = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            articles.append(serialize_article(source, requested_fields))

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
    Retrieve top authors by article count using Elasticsearch terms aggregation
    """

    if not es_client:
        raise HTTPException(
            status_code=500,
            detail="Elasticsearch client not configured. Please set ELASTICSEARCH_ENDPOINT and ES_API_KEY environment variables.",
        )

    try:
        search_query = build_top_authors_query(LAB_SOURCE, size=size)

        response = es_client.search(index=ES_INDEX, body=search_query)

        buckets = response["aggregations"]["top_authors"]["buckets"]
        authors = [{"author": b["key"], "count": b["doc_count"]} for b in buckets]

        return {"authors": authors, "total": len(authors)}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving top authors: {str(e)}"
        )
