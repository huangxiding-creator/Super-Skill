"""Channel package — pluggable research sources for research-orchestrator."""
from .base import Channel, Doc, real_http, normalize_title  # noqa: F401
from .github import ChannelGitHub  # noqa: F401
from .sogou_wechat import ChannelSogouWechat  # noqa: F401
from .hackernews import ChannelHackerNews  # noqa: F401
from .npm_pypi import ChannelNpmPypi  # noqa: F401
from .appstore import ChannelAppStore  # noqa: F401
from .reddit import ChannelReddit  # noqa: F401
from .producthunt import ChannelProductHunt  # noqa: F401
from .googletrends import ChannelGoogleTrends  # noqa: F401
from .competitor_site import ChannelCompetitorSite  # noqa: F401

REGISTRY = {
    "github": ChannelGitHub,
    "sogou_wechat": ChannelSogouWechat,
    "hackernews": ChannelHackerNews,
    "npm_pypi": ChannelNpmPypi,
    "appstore": ChannelAppStore,
    "reddit": ChannelReddit,
    "producthunt": ChannelProductHunt,
    "googletrends": ChannelGoogleTrends,
    "competitor_site": ChannelCompetitorSite,
}


def get_channel(name: str, **kw):
    cls = REGISTRY.get(name)
    return cls(**kw) if cls else None
