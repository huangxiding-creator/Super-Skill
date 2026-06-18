"""Channel package — pluggable research sources for research-orchestrator."""
from .base import Channel, Doc, real_http, normalize_title  # noqa: F401
from .github import ChannelGitHub  # noqa: F401
from .sogou_wechat import ChannelSogouWechat  # noqa: F401

REGISTRY = {
    "github": ChannelGitHub,
    "sogou_wechat": ChannelSogouWechat,
}


def get_channel(name: str, **kw):
    cls = REGISTRY.get(name)
    return cls(**kw) if cls else None
