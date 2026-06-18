"""Competitor-site channel — fetches pricing/feature pages for data-driven pricing.

Takes candidate URLs (from seed.competitor_urls or GitHub repo homepages already
harvested) and returns their raw page text so the LLM can extract pricing tables.
Not a search engine — a fetcher. Degrades on fetch failure.
"""
from __future__ import annotations

import html as html_lib
import re
from typing import Dict, List

from .base import Channel, Doc


class ChannelCompetitorSite(Channel):
    name = "competitor_site"

    def harvest(self, seed: Dict) -> List[Doc]:
        urls: List[str] = list(seed.get("competitor_urls") or [])
        # also probe a /pricing path when only a homepage is known
        expanded = []
        for u in urls:
            expanded.append(u)
            if u.rstrip("/").endswith((".com", ".io", ".dev", ".org", ".net")):
                expanded.append(u.rstrip("/") + "/pricing")
        docs: List[Doc] = []
        for url in expanded[: self.max_results * 2]:
            try:
                status, text = self.http(url)
            except Exception:
                continue
            if status >= 400:
                continue
            docs.append(self._to_doc(url, text))
        return docs

    @staticmethod
    def _to_doc(url: str, html: str) -> Doc:
        # strip tags, collapse whitespace; keep enough for pricing extraction
        title_m = re.search(r"<title[^>]*>(.*?)</title>", html, flags=re.S | re.I)
        title = html_lib.unescape(re.sub(r"\s+", " ", title_m.group(1))).strip() if title_m else url
        body = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S | re.I)
        text = html_lib.unescape(re.sub(r"<[^>]+>", " ", body))
        text = re.sub(r"\s+", " ", text).strip()
        prices = re.findall(r"(?:[$￥¥€£]\s?\d+(?:\.\d{1,2})?|\d+(?:\.\d{1,2})?\s?(?:USD|CNY|RMB|/mo|/month|per month))", text)
        return Doc(
            channel="competitor_site", doc_type="pricing" if "/pricing" in url else "page",
            title=title[:120], url=url, content=text[:4000],
            signals={"price_mentions": prices[:20]},
            credibility=0.65,
        )
