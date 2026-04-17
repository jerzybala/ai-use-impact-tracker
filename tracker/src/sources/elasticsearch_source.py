"""
Elasticsearch source adapter — Phase 2 stub.

NOT IMPLEMENTED YET. This file exists to document the adapter contract
and make the swap from CSVSource → ElasticsearchSource a one-line change
in main.py's config, once Sapien Labs' Elasticsearch credentials are
wired in.

Expected implementation sketch (for reference):

    from elasticsearch import Elasticsearch
    from elasticsearch.helpers import scan

    class ElasticsearchSource(Source):
        def __init__(self, config: ElasticsearchSourceConfig):
            self.es = Elasticsearch(
                hosts=[config.host],
                api_key=config.api_key,
            )

        def fetch(self) -> pd.DataFrame:
            query = {
                "_source": REQUIRED_COLUMNS + list(self.config.extra_columns),
                "query": {"range": {"submit_date_utc": {...}}},
            }
            hits = scan(self.es, index=self.config.index, query=query)
            df = pd.DataFrame([h["_source"] for h in hits])
            return self.validate(df)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from .base import Source, SourceConfig


@dataclass
class ElasticsearchSourceConfig(SourceConfig):
    host: str = ""
    index: str = "gmp"
    api_key: str | None = None
    extra_columns: tuple[str, ...] = field(default_factory=tuple)


class ElasticsearchSource(Source):
    def __init__(self, config: ElasticsearchSourceConfig):
        super().__init__(config)
        self.config: ElasticsearchSourceConfig = config

    def fetch(self):
        raise NotImplementedError(
            "ElasticsearchSource is a Phase 2 placeholder. "
            "Implement when Sapien Labs ES credentials are available. "
            "See module docstring for implementation sketch."
        )
