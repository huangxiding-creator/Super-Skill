"""Google Trends channel — demand trajectory.

No official free API; unofficial endpoints are unreliable and ToS-hostile. This
channel degrades honestly and points the LLM at the manual / pytrends path.
"""
from __future__ import annotations

from typing import Dict, List

from .base import Channel, Doc


class ChannelGoogleTrends(Channel):
    name = "googletrends"

    def harvest(self, seed: Dict) -> List[Doc]:
        kw = self._keywords(seed)
        query = " ".join(kw[:3]) or seed.get("summary", "")
        return [Doc(
            channel=self.name, doc_type="degraded",
            title=f"[Google Trends: manual check recommended for '{query}']",
            url="https://trends.google.com/trends/explore",
            content=("Google Trends has no stable free API. The LLM should estimate "
                     "demand trajectory from GitHub/npm growth + Reddit/HN mention volume, "
                     "or the user runs pytrends manually."),
            signals={"query": query, "degraded": "no_stable_api"},
            credibility=0.1,
        )]
