"""Tests for research-orchestrator (orchestrator + channels + deduper + checkpoint).
Run: python test_orchestrator.py"""
import json, os, sys, tempfile, traceback, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import orchestrator as orch  # noqa: E402
from channels.base import Doc, normalize_title  # noqa: E402
from channels.github import ChannelGitHub  # noqa: E402
from channels.sogou_wechat import ChannelSogouWechat  # noqa: E402
from deduper import dedupe, content_hash  # noqa: E402
import checkpoint as ckpt  # noqa: E402

SEED = {
    "summary": "离线记账 SaaS for 跨境电商",
    "persona": "跨境电商运营",
    "pain": "选品手工比价每天2小时",
    "success_form": "桌面 SaaS + 浏览器插件",
    "value_hypothesis": "GPT-4o 多模态自动比价 10x faster",
}

GH_PAYLOAD = {
    "items": [
        {"full_name": "foo/bar", "html_url": "https://github.com/foo/bar",
         "description": "A bookkeeping tool", "stargazers_count": 1200,
         "forks_count": 90, "open_issues_count": 12, "updated_at": "2026-05-01T00:00:00Z",
         "language": "Python", "license": {"spdx_id": "MIT"}, "topics": ["fintech", "accounting"]},
        {"full_name": "baz/qux", "html_url": "https://github.com/baz/qux",
         "description": "Another bookkeeping tool", "stargazers_count": 50,
         "forks_count": 3, "open_issues_count": 2, "updated_at": "2026-04-01T00:00:00Z",
         "language": "Go", "license": {"spdx_id": "Apache-2.0"}, "topics": []},
    ]
}


def _mock_http_factory(blocked=False):
    """Return an http callable serving fake GH json + fake/locked Sogou html."""
    def http(url):
        if "api.github.com" in url:
            return 200, json.dumps(GH_PAYLOAD)
        if "weixin.sogou.com" in url:
            if blocked:
                return 403, "<html>antispider blocked 用户你好</html>"
            return 200, (
                '<div class="txt-box">'
                '<a href="/link?url=abc">跨境选品 automation 实战复盘</a>'
                '<p class="txt-info">每天翻5个平台比价太累，这里记录踩坑</p>'
                '</div>'
            )
        return 404, ""
    return http


def test_github_channel_parses_signals():
    ch = ChannelGitHub(http=_mock_http_factory())
    docs = ch.harvest(SEED)
    assert len(docs) == 2
    assert docs[0].signals["stars"] == 1200
    assert docs[0].signals["license"] == "MIT"
    assert docs[0].doc_type == "repo"


def test_github_channel_empty_seed_returns_empty():
    ch = ChannelGitHub(http=_mock_http_factory())
    assert ch.harvest({}) == []


def test_sogou_parses_when_not_blocked():
    ch = ChannelSogouWechat(http=_mock_http_factory(blocked=False))
    docs = ch.harvest(SEED)
    assert len(docs) == 1
    assert docs[0].doc_type == "article"
    assert "跨境" in docs[0].title or "选品" in docs[0].title


def test_sogou_degrades_when_blocked():
    ch = ChannelSogouWechat(http=_mock_http_factory(blocked=True))
    docs = ch.harvest(SEED)
    assert len(docs) == 1
    assert docs[0].doc_type == "degraded"
    assert docs[0].credibility < 0.2


def test_dedup_by_title_and_hash():
    d1 = Doc(channel="a", doc_type="x", title="Foo Bar!", url="u1", content="hello world")
    d2 = Doc(channel="b", doc_type="x", title="foo-bar", url="u2", content="different")  # same title norm
    d3 = Doc(channel="c", doc_type="x", title="Totally Different", url="u3", content="hello world")  # same hash
    d4 = Doc(channel="d", doc_type="x", title="Unique One", url="u4", content="unique body")
    res = dedupe([d1, d2, d3, d4])
    titles = [d.title for d in res.unique]
    assert "Foo Bar!" in titles and "Unique One" in titles
    assert res.duplicates == 2
    assert res.by_title == 1 and res.by_hash == 1


def test_orchestrator_end_to_end_persists_docket():
    with tempfile.TemporaryDirectory() as d:
        rep = orch.orchestrate(SEED, d, http=_mock_http_factory(blocked=False))
        assert rep.total_raw == 3  # 2 github + 1 sogou
        assert rep.unique == 3
        assert os.path.exists(os.path.join(d, "RESEARCH_DIGEST.md"))
        assert os.path.exists(os.path.join(d, "github", "_all.json"))
        assert os.path.exists(os.path.join(d, "_checkpoint.json"))
        cp = ckpt.load(d)
        assert cp.is_done("research")


def test_orchestrator_records_degraded_and_continues():
    with tempfile.TemporaryDirectory() as d:
        rep = orch.orchestrate(SEED, d, http=_mock_http_factory(blocked=True))
        assert "sogou_wechat" in rep.degraded
        assert rep.unique == 2  # only github survived as real docs


def test_normalize_title():
    assert normalize_title("Foo-Bar!") == "foo bar"
    assert normalize_title("  多个   空格 ") == "多个 空格"


def test_content_hash_stable():
    assert content_hash("hello  world") == content_hash("Hello World")


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
