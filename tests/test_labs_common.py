import unittest

from routers.labs_common import (
    article_sort,
    build_article_query,
    build_top_authors_query,
    first_value,
    normalize_authors,
    serialize_article,
    source_filter,
    source_fields,
)


class LabsCommonTests(unittest.TestCase):
    def test_normalize_authors_flattens_crawler_arrays(self):
        self.assertEqual(
            normalize_authors([["Jeffrey Rengifo"], ["Jane Doe", "Jeffrey Rengifo"]]),
            ["Jeffrey Rengifo", "Jane Doe"],
        )

    def test_new_and_legacy_field_fallbacks(self):
        source = {
            "published_date": "2026-09-01T00:00:00Z",
            "meta_published_time": "2025-01-01T00:00:00Z",
            "article_content": "",
            "body_content": "Crawler body",
        }
        self.assertEqual(first_value(source, "publishedAt"), "2026-09-01T00:00:00Z")
        self.assertEqual(first_value(source, "body"), "Crawler body")

    def test_source_fields_include_fallback_fields_once(self):
        self.assertEqual(
            source_fields(["publishedAt", "body", "publishedAt"]),
            [
                "published_date",
                "meta_published_time",
                "article_content",
                "body_content",
            ],
        )

    def test_serialize_article_returns_flat_authors(self):
        article = serialize_article(
            {"meta_author": [["Jeffrey Rengifo"]], "title": "Example"},
            ["title", "authors"],
        )
        self.assertEqual(article, {"title": "Example", "authors": ["Jeffrey Rengifo"]})

    def test_source_filter_uses_custom_source_keyword(self):
        self.assertEqual(
            source_filter("search-labs"),
            {"term": {"source.enum": "search-labs"}},
        )

    def test_sort_has_safe_fallbacks(self):
        self.assertEqual(
            [next(iter(item)) for item in article_sort()],
            ["published_date", "meta_published_time", "last_crawled_at"],
        )

    def test_article_query_uses_search_source_filter(self):
        query = build_article_query(
            "search-labs",
            size=10,
            offset=20,
            es_fields=["title", "meta_author"],
        )
        filters = query["query"]["bool"]["filter"]
        self.assertIn({"term": {"source.enum": "search-labs"}}, filters)
        self.assertEqual(query["from"], 20)
        self.assertEqual(query["size"], 10)

    def test_top_authors_query_uses_observability_source_filter(self):
        query = build_top_authors_query("observability-labs", size=25)
        filters = query["query"]["bool"]["filter"]
        self.assertIn({"term": {"source.enum": "observability-labs"}}, filters)
        self.assertEqual(query["aggs"]["top_authors"]["terms"]["size"], 25)


if __name__ == "__main__":
    unittest.main()
