"""npm + PyPI channel — adoption signal for technical approaches/libs.

npm registry search is reliable & auth-free. PyPI has no free search, so we do a
metadata lookup per candidate package name (best-effort) — missing names degrade
silently.
"""
from __future__ import annotations

import urllib.parse
from typing import Dict, List

from .base import Channel, Doc, fetch_json

NPM_SEARCH = "https://registry.npmjs.org/-/v1/search"
PYPI_META = "https://pypi.org/pypi/{pkg}/json"


class ChannelNpmPypi(Channel):
    name = "npm_pypi"

    def harvest(self, seed: Dict) -> List[Doc]:
        kw = self._keywords(seed)
        if not kw:
            return []
        docs = self._npm(" ".join(kw[:4]))
        # PyPI: try a couple of candidate package names from keywords
        for cand in kw[:3]:
            docs.extend(self._pypi(cand))
        return docs[: self.max_results]

    def _npm(self, text: str) -> List[Doc]:
        url = f"{NPM_SEARCH}?size={min(self.max_results, 15)}&text={urllib.parse.quote(text)}"
        data = fetch_json(url, self.http)
        if not data or "objects" not in data:
            return []
        docs: List[Doc] = []
        for o in data.get("objects", []):
            pkg = o.get("package", {})
            name = pkg.get("name", "")
            if not name:
                continue
            docs.append(Doc(
                channel=self.name, doc_type="package", title=name,
                url=pkg.get("links", {}).get("npm", f"https://www.npmjs.com/package/{name}"),
                content=(pkg.get("description") or "")[:1000],
                signals={"registry": "npm", "version": pkg.get("version", ""),
                         "date": pkg.get("date", "")},
                credibility=0.7,
            ))
        return docs

    def _pypi(self, name: str) -> List[Doc]:
        if not name or len(name) < 2:
            return []
        data = fetch_json(PYPI_META.format(pkg=urllib.parse.quote(name)), self.http)
        if not data or "info" not in data:
            return []
        info = data["info"]
        releases = data.get("releases") or {}
        return [Doc(
            channel=self.name, doc_type="package", title=info.get("name", name),
            url=info.get("project_url", "") or f"https://pypi.org/project/{name}/",
            content=(info.get("summary") or "")[:1000],
            signals={"registry": "pypi", "version": info.get("version", ""),
                     "release_count": len(releases), "license": info.get("license", "")},
            credibility=0.7,
        )]
