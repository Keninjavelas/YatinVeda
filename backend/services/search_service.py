"""Elasticsearch integration for advanced full-text search.

Indexes users, charts, community posts, and practitioners for fast
querying with relevance scoring, autocomplete, and aggregation.

Set ELASTICSEARCH_URL to enable; falls back to SQLAlchemy LIKE queries
when Elasticsearch is unavailable.
"""

import os
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from elasticsearch import Elasticsearch, NotFoundError
    ES_AVAILABLE = True
except ImportError:
    ES_AVAILABLE = False
    logger.info("elasticsearch-py not installed — search will use DB fallback")

ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "")

# Index definitions
INDICES = {
    "users": {
        "settings": {"number_of_shards": 1, "number_of_replicas": 0},
        "mappings": {
            "properties": {
                "username": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "full_name": {"type": "text"},
                "email": {"type": "keyword"},
                "role": {"type": "keyword"},
                "bio": {"type": "text"},
                "specializations": {"type": "keyword"},
                "created_at": {"type": "date"},
            }
        },
    },
    "community_posts": {
        "settings": {"number_of_shards": 1, "number_of_replicas": 0},
        "mappings": {
            "properties": {
                "title": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "content": {"type": "text"},
                "author": {"type": "text"},
                "author_id": {"type": "integer"},
                "tags": {"type": "keyword"},
                "category": {"type": "keyword"},
                "likes_count": {"type": "integer"},
                "created_at": {"type": "date"},
            }
        },
    },
    "practitioners": {
        "settings": {"number_of_shards": 1, "number_of_replicas": 0},
        "mappings": {
            "properties": {
                "name": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "title": {"type": "text"},
                "bio": {"type": "text"},
                "specializations": {"type": "keyword"},
                "languages": {"type": "keyword"},
                "experience_years": {"type": "integer"},
                "rating": {"type": "float"},
                "price_per_hour": {"type": "integer"},
                "verified": {"type": "boolean"},
                "created_at": {"type": "date"},
            }
        },
    },
}


class SearchService:
    """Elasticsearch-backed search with graceful DB fallback."""

    def __init__(self) -> None:
        self.es: Optional[Any] = None
        self.enabled = False
        if ES_AVAILABLE and ELASTICSEARCH_URL:
            try:
                self.es = Elasticsearch(ELASTICSEARCH_URL)
                if self.es.ping():
                    self.enabled = True
                    self._ensure_indices()
                    logger.info("Elasticsearch connected: %s", ELASTICSEARCH_URL)
                else:
                    logger.warning("Elasticsearch ping failed — using DB fallback")
            except Exception as exc:
                logger.warning("Elasticsearch init failed (%s) — using DB fallback", exc)

    def _ensure_indices(self) -> None:
        for name, body in INDICES.items():
            index_name = f"yatinveda_{name}"
            if not self.es.indices.exists(index=index_name):
                self.es.indices.create(index=index_name, body=body)
                logger.info("Created ES index: %s", index_name)

    # ------------------------------------------------------------------
    # Indexing
    # ------------------------------------------------------------------
    def index_document(self, index: str, doc_id: str, body: Dict[str, Any]) -> bool:
        if not self.enabled:
            return False
        try:
            self.es.index(index=f"yatinveda_{index}", id=doc_id, body=body)
            return True
        except Exception as exc:
            logger.error("ES index error: %s", exc)
            return False

    def delete_document(self, index: str, doc_id: str) -> bool:
        if not self.enabled:
            return False
        try:
            self.es.delete(index=f"yatinveda_{index}", id=doc_id)
            return True
        except Exception:
            return False

    def bulk_index(self, index: str, documents: List[Dict[str, Any]]) -> int:
        if not self.enabled or not documents:
            return 0
        from elasticsearch.helpers import bulk
        actions = [
            {"_index": f"yatinveda_{index}", "_id": doc.pop("_id", None), "_source": doc}
            for doc in documents
        ]
        success, _ = bulk(self.es, actions, raise_on_error=False)
        return success

    # ------------------------------------------------------------------
    # Searching
    # ------------------------------------------------------------------
    def search(
        self,
        index: str,
        query: str,
        fields: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
    ) -> Dict[str, Any]:
        """Full-text search across specified index."""
        if not self.enabled:
            return {"hits": [], "total": 0, "page": page, "page_size": page_size}

        search_fields = fields or ["_all"]
        must_clauses: List[Dict] = []
        if query.strip():
            must_clauses.append({
                "multi_match": {
                    "query": query,
                    "fields": search_fields,
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                }
            })

        filter_clauses: List[Dict] = []
        if filters:
            for key, value in filters.items():
                if isinstance(value, list):
                    filter_clauses.append({"terms": {key: value}})
                else:
                    filter_clauses.append({"term": {key: value}})

        body: Dict[str, Any] = {
            "query": {
                "bool": {
                    "must": must_clauses or [{"match_all": {}}],
                    "filter": filter_clauses,
                }
            },
            "from": (page - 1) * page_size,
            "size": page_size,
        }

        if sort_by:
            body["sort"] = [{sort_by: {"order": sort_order}}]

        try:
            result = self.es.search(index=f"yatinveda_{index}", body=body)
            hits = [
                {**hit["_source"], "_id": hit["_id"], "_score": hit["_score"]}
                for hit in result["hits"]["hits"]
            ]
            total = result["hits"]["total"]
            total_count = total["value"] if isinstance(total, dict) else total
            return {"hits": hits, "total": total_count, "page": page, "page_size": page_size}
        except Exception as exc:
            logger.error("ES search error: %s", exc)
            return {"hits": [], "total": 0, "page": page, "page_size": page_size}

    def autocomplete(self, index: str, field: str, prefix: str, size: int = 10) -> List[str]:
        """Prefix-based autocomplete suggestions."""
        if not self.enabled:
            return []
        try:
            body = {
                "query": {"prefix": {f"{field}.keyword": {"value": prefix.lower()}}},
                "size": size,
                "_source": [field],
            }
            result = self.es.search(index=f"yatinveda_{index}", body=body)
            return [hit["_source"].get(field, "") for hit in result["hits"]["hits"]]
        except Exception:
            return []

    def aggregate(self, index: str, field: str, size: int = 20) -> List[Dict[str, Any]]:
        """Term aggregation on a keyword field."""
        if not self.enabled:
            return []
        try:
            body = {
                "size": 0,
                "aggs": {"field_agg": {"terms": {"field": field, "size": size}}},
            }
            result = self.es.search(index=f"yatinveda_{index}", body=body)
            return [
                {"key": b["key"], "count": b["doc_count"]}
                for b in result["aggregations"]["field_agg"]["buckets"]
            ]
        except Exception:
            return []


# Module-level singleton
_service: Optional[SearchService] = None


def get_search_service() -> SearchService:
    global _service
    if _service is None:
        _service = SearchService()
    return _service
