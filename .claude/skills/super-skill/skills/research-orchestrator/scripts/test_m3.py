"""M3 tests: new channels + gap_analyzer + quality_gate. Run: python test_m3.py"""
import json, sys, pathlib, traceback
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from channels.base import Doc  # noqa: E402
from channels.hackernews import ChannelHackerNews  # noqa: E402
from channels.npm_pypi import ChannelNpmPypi  # noqa: E402
from channels.appstore import ChannelAppStore  # noqa: E402
from channels.producthunt import ChannelProductHunt  # noqa: E402
from channels.googletrends import ChannelGoogleTrends  # noqa: E402
from channels.competitor_site import ChannelCompetitorSite  # noqa: E402
import gap_analyzer as gap  # noqa: E402
import quality_gate as qg  # noqa: E402

SEED = {"summary": "offline markdown notes", "persona": "developer",
        "pain": "notes scattered", "success_form": "desktop app",
        "value_hypothesis": "local-first fast", "competitor_urls": ["https://acme.dev"]}


def _http(routes):
    """routes: dict url-substring -> (status, text)."""
    def h(url):
        for key, val in routes.items():
            if key in url:
                return val
        return 404, ""
    return h


def test_hackernews_parses():
    payload = {"hits": [{"title": "Show HN: a markdown notes app", "url": "https://x.com",
                         "points": 120, "num_comments": 40, "objectID": "1", "created_at": "x"}]}
    ch = ChannelHackerNews(http=_http({"hn.algolia": (200, json.dumps(payload))}))
    docs = ch.harvest(SEED)
    assert len(docs) == 1 and docs[0].signals["points"] == 120


def test_npm_parses():
    payload = {"objects": [{"package": {"name": "marklib", "description": "md lib",
                         "version": "1.0.0", "date": "x", "links": {"npm": "u"}}}]}
    ch = ChannelNpmPypi(http=_http({"registry.npmjs": (200, json.dumps(payload)), "pypi.org": (404, "")}))
    docs = ch.harvest(SEED)
    assert any(d.title == "marklib" for d in docs)


def test_appstore_parses_price():
    payload = {"results": [{"trackName": "Acme Notes", "description": "d",
                            "price": 9.99, "primaryGenreName": "Productivity",
                            "averageUserRating": 4.5, "userRatingCount": 300}]}
    ch = ChannelAppStore(http=_http({"itunes.apple": (200, json.dumps(payload))}))
    docs = ch.harvest(SEED)
    assert docs and docs[0].signals["price_usd"] == 9.99


def test_producthunt_degrades_without_token(monkeypatch_none=None):
    import os
    os.environ.pop("PRODUCTHUNT_TOKEN", None)
    ch = ChannelProductHunt(http=lambda u: (200, "{}"))
    docs = ch.harvest(SEED)
    assert len(docs) == 1 and docs[0].doc_type == "degraded"


def test_googletrends_always_degrades():
    ch = ChannelGoogleTrends(http=lambda u: (200, ""))
    docs = ch.harvest(SEED)
    assert docs[0].doc_type == "degraded"


def test_competitor_site_extracts_prices():
    html = "<html><title>Acme Pricing</title><body>Pro plan $29/mo Team $99/month Free $0</body></html>"
    ch = ChannelCompetitorSite(http=_http({"acme.dev/pricing": (200, html), "acme.dev": (200, html)}))
    docs = ch.harvest(SEED)
    assert docs
    mentions = []
    for d in docs:
        mentions.extend(d.signals.get("price_mentions", []))
    assert any("$" in m for m in mentions)


# ---- gap analysis ----
def test_gap_analysis_flags_missing_pricing_and_demand():
    docs = [
        Doc("github", "repo", "r1", "u", "c" * 30, {"stars": 100}),
        Doc("github", "repo", "r2", "u", "c" * 30, {"stars": 50}),
        Doc("sogou_wechat", "article", "a1", "u", "c" * 30, {}),
        Doc("sogou_wechat", "article", "a2", "u", "c" * 30, {}),
        Doc("hackernews", "post", "p1", "u", "c" * 30, {}),
    ]
    rep = gap.analyze(docs)
    dims_covered = {c.dimension: c.covered for c in rep.coverage}
    assert dims_covered["competitors"] is True
    assert dims_covered["problem"] is True
    assert dims_covered["pricing"] is False
    assert "pricing" in rep.gaps
    assert rep.differentiation_possible is True


def test_gap_research_recommendations():
    docs = [Doc("github", "repo", "r1", "u", "c", {"stars": 1})]
    rep = gap.analyze(docs)
    dims = {r["dimension"] for r in rep.re_research}
    assert "problem" in dims and "pricing" in dims


# ---- quality gate ----
def test_quality_gate_passes_on_rich_docket():
    docs = [Doc("github", "repo", f"r{i}", "u", "x" * 30, {"stars": i}, credibility=0.8)
            for i in range(6)]
    res = qg.evaluate(docs)
    assert res.passed is True


def test_quality_gate_fails_when_mostly_degraded():
    docs = [Doc("x", "degraded", "d", "", "", credibility=0.1) for _ in range(5)]
    docs += [Doc("github", "repo", "r", "u", "x" * 30, {}, credibility=0.8)]
    res = qg.evaluate(docs)
    assert res.passed is False
    assert any("degraded" in w for w in res.warnings)


def test_quality_gate_fails_low_credibility():
    docs = [Doc("x", "post", f"p{i}", "u", "x" * 30, {}, credibility=0.1) for i in range(6)]
    assert qg.evaluate(docs).passed is False


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for fn in fns:
        try:
            fn(); print(f"PASS {fn.__name__}")
        except Exception:
            failed += 1; print(f"FAIL {fn.__name__}"); traceback.print_exc()
    print(f"\n{len(fns)-failed}/{len(fns)} passed")
    sys.exit(1 if failed else 0)
