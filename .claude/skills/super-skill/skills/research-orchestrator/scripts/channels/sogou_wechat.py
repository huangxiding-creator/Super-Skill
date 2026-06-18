"""Sogou WeChat channel — real Chinese user pain points & existing solutions.

Searches weixin.sogou.com (WeChat article index). Anti-bot frequently blocks
automated access; this channel degrades honestly: on block it returns a single
*degradation note* doc so the orchestrator records that live harvesting failed
and the LLM can fall back to its own knowledge / a manual fetch.

In ResearchFactory-Eng this is handled by the Node.js SouGouWeDown2 tool; here we
implement a lightweight stdlib fetcher with the same 3-level fallback contract.
"""
from __future__ import annotations

import html as html_lib
import re
import urllib.parse
from typing import Dict, List

from .base import Channel, Doc, now_iso, DEFAULT_UA

SEARCH_URL = "https://weixin.sogou.com/weixin"


class ChannelSogouWechat(Channel):
    name = "sogou_wechat"

    def harvest(self, seed: Dict) -> List[Doc]:
        kw = self._keywords(seed)
        query = " ".join(kw[:4]) or seed.get("summary", "")
        if not query:
            return []
        url = f"{SEARCH_URL}?type=2&query={urllib.parse.quote(query)}"
        try:
            status, text = self.http(url)
        except Exception:
            return [self._degraded(query, "network error")]
        if status >= 400 or "antispider" in text.lower() or "用户你好" in text:
            return [self._degraded(query, f"blocked (status {status})")]
        return self._parse(text, query) or [self._degraded(query, "no results parsed")]

    def _parse(self, text: str, query: str) -> List[Doc]:
        """Best-effort parse of Sogou WeChat article links. Returns [] on miss.

        Robust to markup drift: anchors on Sogou article redirects carry
        ``link?url=`` in their href — we key off that signature rather than a
        fragile parent-div structure.
        """
        docs: List[Doc] = []
        anchors = re.findall(
            r'<a[^>]*href="([^"]*link\?url=[^"]*)"[^>]*>(.*?)</a>',
            text, flags=re.S,
        )
        for href, raw_title in anchors[: self.max_results]:
            title = html_lib.unescape(re.sub(r"<[^>]+>", "", raw_title)).strip()
            if len(title) < 4:
                continue
            docs.append(Doc(
                channel=self.name,
                doc_type="article",
                title=title,
                url=href if href.startswith("http") else "https://weixin.sogou.com" + href,
                content="",  # snippet not on listing page; fetch detail on demand
                signals={"query": query},
                credibility=0.6,
            ))
        return docs

    @staticmethod
    def _degraded(query: str, reason: str) -> Doc:
        return Doc(
            channel="sogou_wechat",
            doc_type="degraded",
            title=f"[Sogou WeChat degraded: {reason}] query={query}",
            url="",
            content=("Live Sogou WeChat harvesting was blocked or failed. "
                     "The LLM should substitute known user-pain signals from its own "
                     "knowledge of this domain, or the user may run the manual "
                     "SouGouWeDown2 fetcher from ResearchFactory-Eng."),
            signals={"query": query, "degraded": reason},
            credibility=0.1,
        )
