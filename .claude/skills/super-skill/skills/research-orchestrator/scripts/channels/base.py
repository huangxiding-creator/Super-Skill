"""Channel framework for research-orchestrator (IdeaForge / Super-Skill V4.0).

A channel is anything that turns an IDEA_SEED into a list of :class:`Doc`.
All network access goes through an injectable ``http`` callable so channels are
unit-testable with no live network and degrade gracefully when an endpoint is
blocked (Sogou WeChat, rate-limited GitHub, etc.).
"""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Sequence

# An http callable: url -> (status, text). Raising is allowed; orchestrator catches.
HttpFunc = Callable[[str], "tuple[int, str]"]

DEFAULT_TIMEOUT = 15
DEFAULT_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class Doc:
    channel: str
    doc_type: str            # repo|article|issue|post|review|pricing|trend|...
    title: str
    url: str
    content: str = ""
    signals: Dict = field(default_factory=dict)
    retrieved_at: str = field(default_factory=now_iso)
    credibility: float = 0.5   # 0..1, channel-specific default

    def to_dict(self) -> Dict:
        return asdict(self)

    @property
    def dedup_key(self) -> str:
        return normalize_title(self.title) or self.url


def normalize_title(t: str) -> str:
    """Lowercase, strip punctuation/whitespace, collapse spaces. For dedup + match."""
    if not t:
        return ""
    import re
    t = t.lower()
    t = re.sub(r"[\s\-_·•|/\\:;,\.\!\?\(\)\[\]\{\}\"'`'""]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def real_http(url: str, *, timeout: int = DEFAULT_TIMEOUT, ua: str = DEFAULT_UA) -> "tuple[int, str]":
    """Default http callable using stdlib urllib. Returns (status, text).

    Raises on network/HTTP errors so the orchestrator can catch + degrade.
    """
    req = urllib.request.Request(url, headers={"User-Agent": ua,
                                               "Accept": "application/json, text/html, */*"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        encoding = resp.headers.get_content_charset() or "utf-8"
        return getattr(resp, "status", 200), raw.decode(encoding, errors="replace")


def fetch_json(url: str, http: Optional[HttpFunc] = None) -> Optional[Dict]:
    http = http or real_http
    try:
        status, text = http(url)
        if status >= 400:
            return None
        return json.loads(text)
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, OSError):
        return None


class Channel:
    """Base channel. Subclasses set ``name`` and implement :meth:`harvest`."""
    name: str = "base"
    fallback_levels: Sequence[str] = ("primary", "degraded", "stub")

    def __init__(self, http: Optional[HttpFunc] = None, max_results: int = 20):
        self.http = http or real_http
        self.max_results = max_results

    def harvest(self, seed: Dict) -> List[Doc]:
        """Return docs for this seed. Must not raise — return [] on failure."""
        raise NotImplementedError

    # Helpers for subclasses -------------------------------------------------
    def _keywords(self, seed: Dict) -> List[str]:
        """Derive search keywords from IDEA_SEED fields."""
        parts = []
        for k in ("summary", "pain", "success_form", "value_hypothesis"):
            v = seed.get(k)
            if v:
                parts.append(str(v))
        joined = " ".join(parts)
        import re
        # split CJK + latin into chunks; keep tokens 2+ chars
        tokens = [t for t in re.split(r"[\s,，、;；/]+", joined) if len(t) >= 2]
        if tokens:
            return tokens[:8]
        summary = seed.get("summary")
        return [str(summary)] if summary else []
