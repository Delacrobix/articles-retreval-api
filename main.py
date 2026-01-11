import os
from typing import List, Optional

from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI(title="Articles Retrieval API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Elasticsearch configuration
ELASTICSEARCH_ENDPOINT = os.getenv("ELASTICSEARCH_ENDPOINT")
ES_API_KEY = os.getenv("ES_API_KEY")
ES_INDEX = os.getenv("ES_INDEX", "articles")


# Initialize Elasticsearch client
es_client = (
    Elasticsearch(ELASTICSEARCH_ENDPOINT, api_key=ES_API_KEY)
    if ELASTICSEARCH_ENDPOINT and ES_API_KEY
    else None
)


@app.get("/health")
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


# Available fields mapping (API field -> ES field)
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


@app.get("/articles")
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
        # Parse requested fields
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

        # Get ES fields for the requested API fields
        es_fields = [FIELD_MAPPING[f] for f in requested_fields]

        # Calculate from parameter for pagination
        from_param = (page - 1) * size

        # Build the search query
        search_query = {
            "size": size,
            "from": from_param,
            "_source": es_fields,
            "query": {
                "bool": {"filter": [{"term": {"meta_author.enum": "Jeffrey Rengifo"}}]}
            },
            "sort": [{"meta_published_time": {"order": "desc"}}],
        }

        # Execute search
        response = es_client.search(index=ES_INDEX, body=search_query)

        # Format results
        articles = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            article = {}

            for api_field in requested_fields:
                es_field = FIELD_MAPPING[api_field]

                if api_field == "authors":
                    article[api_field] = (
                        [source.get(es_field, "")] if source.get(es_field) else []
                    )
                else:
                    article[api_field] = source.get(es_field, "")

            articles.append(article)

        # Return results with pagination metadata
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
