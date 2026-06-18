"""Hacker News channel — developer pain/taste + Show HN launches.

Uses the public Algolia HN Search API (no auth, reliable).
"""
from __future__ import annotations

import urllib.parse
from typing import Dict, List

from .base import Channel, Doc, fetch_json

SEARCH_URL = "https://hn.algolia.com/api/v1/search"


class ChannelHackerNews(Channel):
    name = "hackernews"

    def harvest(self, seed: Dict) -> List[Doc]:
        kw = self._keywords(seed)
        if not kw:
            return []
        query = " ".join(kw[:4])
        url = (f"{SEARCH_URL}?tags=story&hitsPerPage={min(self.max_results,20)}"
               f"&query={urllib.parse.quote(query)}")
        data = fetch_json(url, self.http)
        if not data or "hits" not in data:
            return []
        docs: List[Doc] = []
        for hit in data.get("hits", [])[: self.max_results]:
            title = (hit.get("title") or hit.get("story_title") or "").strip()
            if not title:
                continue
            oid = hit.get("objectID")
            docs.append(Doc(
                channel=self.name, doc_type="post", title=title,
                url=hit.get("url") or f"https://news.ycombinator.com/item?id={oid}",
                content=(hit.get("story_text") or "")[:2000] or hit.get("url", ""),
                signals={"points": hit.get("points", 0), "comments": hit.get("num_comments", 0),
                         "date": hit.get("created_at", "")},
                credibility=0.6,
            ))
        return docs
