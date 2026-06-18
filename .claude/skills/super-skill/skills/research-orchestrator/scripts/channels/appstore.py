"""App Store channel — competitor discovery + feature-gap signal.

Uses the public iTunes Search API (entity=software), auth-free & reliable.
Great for surfacing existing apps the idea competes with.
"""
from __future__ import annotations

import urllib.parse
from typing import Dict, List

from .base import Channel, Doc, fetch_json

SEARCH_URL = "https://itunes.apple.com/search"


class ChannelAppStore(Channel):
    name = "appstore"

    def harvest(self, seed: Dict) -> List[Doc]:
        kw = self._keywords(seed)
        if not kw:
            return []
        query = " ".join(kw[:4])
        url = (f"{SEARCH_URL}?term={urllib.parse.quote(query)}&entity=software"
               f"&limit={min(self.max_results, 20)}")
        data = fetch_json(url, self.http)
        if not data or "results" not in data:
            return []
        docs: List[Doc] = []
        for r in data.get("results", [])[: self.max_results]:
            name = r.get("trackName") or r.get("sellerName") or ""
            if not name:
                continue
            docs.append(Doc(
                channel=self.name, doc_type="app", title=name,
                url=r.get("trackViewUrl", r.get("sellerUrl", "")),
                content=(r.get("description") or "")[:1500],
                signals={"price_usd": r.get("price", 0.0),
                         "genre": r.get("primaryGenreName", ""),
                         "seller": r.get("sellerName", ""),
                         "rating": r.get("averageUserRating", 0.0),
                         "rating_count": r.get("userRatingCount", 0)},
                credibility=0.75,
            ))
        return docs
