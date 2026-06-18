"""Reddit channel — real user pain in domain subreddits.

Uses reddit.com/search.json (often works unauthenticated; rate-limits/403 degrade).
"""
from __future__ import annotations

import urllib.parse
from typing import Dict, List

from .base import Channel, Doc, fetch_json


class ChannelReddit(Channel):
    name = "reddit"

    def harvest(self, seed: Dict) -> List[Dict] if False else List[Doc]:
        kw = self._keywords(seed)
        if not kw:
            return []
        query = " ".join(kw[:4])
        url = (f"https://www.reddit.com/search.json?q={urllib.parse.quote(query)}"
               f"&sort=relevance&limit={min(self.max_results, 20)}")
        data = fetch_json(url, self.http)
        if not data or "data" not in data:
            return []
        docs: List[Doc] = []
        for child in data.get("data", {}).get("children", []):
            d = child.get("data", {})
            title = (d.get("title") or "").strip()
            if not title:
                continue
            docs.append(Doc(
                channel=self.name, doc_type="post", title=title,
                url=f"https://reddit.com{d.get('permalink', '')}",
                content=(d.get("selftext") or "")[:2000],
                signals={"subreddit": d.get("subreddit", ""), "upvotes": d.get("ups", 0),
                         "comments": d.get("num_comments", 0)},
                credibility=0.55,
            ))
        return docs
