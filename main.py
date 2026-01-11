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


@app.get("/articles")
async def get_articles(
    size: int = Query(50, ge=1, le=100, description="Number of results to return"),
    page: int = Query(1, ge=1, description="Page number for pagination"),
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
        # Calculate from parameter for pagination
        from_param = (page - 1) * size

        # Build the search query
        search_query = {
            "size": size,
            "from": from_param,
            "_source": [
                "title",
                "meta_description",
                "url",
                "url_path_dir3",
                "meta_author",
                "meta_img",
                "article_content",
            ],
            "query": {
                "bool": {"filter": [{"term": {"meta_author.enum": "Jeffrey Rengifo"}}]}
            },
        }

        # Execute search
        response = es_client.search(index=ES_INDEX, body=search_query)

        print(response)

        # Format results
        articles = []
        for hit in response["hits"]["hits"]:
            source = hit["_source"]
            article = {
                "title": source.get("title", ""),
                "description": source.get("meta_description", ""),
                "coverImage": source.get("meta_img", ""),
                "link": source.get("url", ""),
                "slug": source.get("url_path_dir3", ""),
                "authors": (
                    [source.get("meta_author", "")] if source.get("meta_author") else []
                ),
                "body": source.get("body", ""),
            }
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
