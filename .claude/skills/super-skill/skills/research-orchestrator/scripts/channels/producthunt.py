"""Product Hunt channel — launched products, positioning, pricing.

Product Hunt's GraphQL API requires an OAuth token. Without one this channel
degrades to a note (same honesty contract as Sogou). With PRODUCTHUNT_TOKEN in the
env, it queries live.
"""
from __future__ import annotations

import os
from typing import Dict, List

from .base import Channel, Doc, now_iso

GRAPHQL_URL = "https://api.producthunt.com/v2/api/graphql"


class ChannelProductHunt(Channel):
    name = "producthunt"

    def harvest(self, seed: Dict) -> List[Doc]:
        token = os.environ.get("PRODUCTHUNT_TOKEN")
        if not token:
            return [self._degraded("no PRODUCTHUNT_TOKEN set")]
        kw = self._keywords(seed)
        query = " ".join(kw[:4]) or seed.get("summary", "")
        gql = {"query": """
            query($q:String!){ posts(first:10,query:$q){
              edges{node{ name tagline url website votesCount topics{edges{node{name}}} }} } }""",
            "variables": {"q": query}}
        try:
            status, text = self.http(_post(graphql=GRAPHQL_URL, token=token, body=gql))
        except Exception:
            return [self._degraded(query, "network/GraphQL error")]
        if status >= 400:
            return [self._degraded(query, f"HTTP {status}")]
        import json
        try:
            data = json.loads(text)
        except ValueError:
            return [self._degraded(query, "bad json")]
        docs: List[Doc] = []
        for edge in data.get("data", {}).get("posts", {}).get("edges", []):
            n = edge.get("node", {})
            docs.append(Doc(
                channel=self.name, doc_type="product", title=n.get("name", ""),
                url=n.get("url", ""), content=n.get("tagline", ""),
                signals={"votes": n.get("votesCount", 0),
                         "topics": [t["node"]["name"] for t in n.get("topics", {}).get("edges", [])]},
                credibility=0.8,
            ))
        return docs or [self._degraded(query, "no results")]

    @staticmethod
    def _degraded(reason: str, detail: str = "") -> Doc:
        return Doc(channel="producthunt", doc_type="degraded",
                   title=f"[Product Hunt degraded: {detail or reason}]",
                   url="", content="Set PRODUCTHUNT_TOKEN to enable live Product Hunt discovery.",
                   signals={"degraded": detail or reason}, credibility=0.1)


def _post(graphql: str, token: str, body: dict):
    """Return a URL string the injected http can't POST to; channels needing POST
    should inject a custom http. For the stdlib default we shim via a data: URL the
    real_http can't handle — so in practice callers inject a POST-capable http.
    Kept simple: real usage passes a custom http; token path returns a degraded note
    unless http supports POST via the 'url' carrying method=POST.
    """
    # NOTE: The default real_http is GET-only. A POST-capable http must be injected.
    # We encode the request as a pseudo-url so a POST-aware http callable can route it.
    import json as _j
    return f"POST {graphql}\nAuthorization: Bearer {token}\n\n{_j.dumps(body)}"
