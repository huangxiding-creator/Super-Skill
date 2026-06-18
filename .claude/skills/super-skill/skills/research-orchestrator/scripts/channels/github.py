"""GitHub channel — finds similar projects + extracts maturity signals.

Uses the public GitHub Search API (works unauthenticated, rate-limited).
Signals harvested feed proposal-forge's maturity-index.
Degrades to [] on rate-limit/block — never raises.
"""
from __future__ import annotations

import urllib.parse
from typing import Dict, List, Optional

from .base import Channel, Doc, fetch_json, now_iso


class ChannelGitHub(Channel):
    name = "github"

    SEARCH_URL = "https://api.github.com/search/repositories"

    def harvest(self, seed: Dict) -> List[Doc]:
        kw = self._keywords(seed)
        if not kw:
            return []
        query = self._build_query(kw, seed)
        per_page = min(self.max_results, 20)  # API caps at 100; keep payloads small
        url = (f"{self.SEARCH_URL}?q={urllib.parse.quote(query)}"
               f"&sort=stars&order=desc&per_page={per_page}")
        data = fetch_json(url, self.http)
        if not data or "items" not in data:
            return []  # rate-limited or blocked — degrade silently
        docs: List[Doc] = []
        for item in data.get("items", [])[: self.max_results]:
            docs.append(self._repo_to_doc(item))
        return docs

    @staticmethod
    def _build_query(keywords: List[str], seed: Dict) -> str:
        # Join strongest keywords; GitHub OR-matches broader space-separated terms.
        terms = [k for k in keywords if 2 <= len(k) <= 32][:4]
        q = " ".join(terms) or (seed.get("summary") or "")
        # bias toward actively maintained
        return f"{q} pushed:>2024-01-01 stars:>5"

    def _repo_to_doc(self, item: Dict) -> Doc:
        license_id = (item.get("license") or {}).get("spdx_id") or "NONE"
        signals = {
            "stars": item.get("stargazers_count", 0),
            "forks": item.get("forks_count", 0),
            "open_issues": item.get("open_issues_count", 0),
            "updated_at": item.get("updated_at", ""),
            "language": item.get("language") or "",
            "license": license_id,
            "topics": item.get("topics", []) or [],
            "full_name": item.get("full_name", ""),
        }
        title = item.get("full_name") or item.get("name") or "repo"
        desc = (item.get("description") or "").strip()
        content = desc + "\n\nTopics: " + ", ".join(signals["topics"]) if signals["topics"] else desc
        return Doc(
            channel=self.name,
            doc_type="repo",
            title=title,
            url=item.get("html_url", ""),
            content=content or title,
            signals=signals,
            credibility=0.8,
        )
