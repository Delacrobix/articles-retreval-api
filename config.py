import os

from dotenv import load_dotenv
from elasticsearch import Elasticsearch

load_dotenv()

ELASTICSEARCH_ENDPOINT = os.getenv("ELASTICSEARCH_ENDPOINT")
ES_API_KEY = os.getenv("ES_API_KEY")

es_client = (
    Elasticsearch(ELASTICSEARCH_ENDPOINT, api_key=ES_API_KEY)
    if ELASTICSEARCH_ENDPOINT and ES_API_KEY
    else None
)
