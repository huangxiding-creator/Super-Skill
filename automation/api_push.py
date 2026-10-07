# -*- coding: utf-8 -*-
r"""GitHub Git Data API 推送（S5 第三层回退通道，gh api 版）。

背景：github.com:443 receive-pack 经机场代理常被污染（curl 200 而 git 死），
api.github.com 是不同 CDN 通道，gh CLI 直连实测可用（本机已登录，凭据在
系统 keyring——本脚本零凭据落盘）。

移植 E:\AI-Station\tools\api_push.py 的三处根治性修复（勿回退）：
1. **树比对**而非 git diff：远端可能含本地未知的 API 提交，git diff 对
   未知 SHA 静默失败返回空；逐文件 blob sha 比对不依赖共同历史。
2. **CJK 路径必须 quotepath=false**：否则 `\347\253\231` 转义致静默跳文件。
3. **上传 HEAD blob 原始字节**（git cat-file）而非工作区文件：autocrlf 下
   工作区 CRLF / HEAD 对象 LF，读工作区会造"blob sha ≠ 本地树 sha"幻影差异。

用法: python api_push.py [--repo OWNER/NAME] [--branch master]
      缺省从 origin remote 与当前分支推导；cwd 须为目标仓库。
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
NO_WINDOW = 0x08000000 if os.name == "nt" else 0  # creationflags 仅 Windows 支持


def git(*args):
    p = subprocess.run(["git", *args], cwd=str(REPO_ROOT), capture_output=True,
                       timeout=60, creationflags=NO_WINDOW)
    out = (p.stdout or b"").decode("utf-8", errors="replace").strip()
    if p.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} 失败: "
                         f"{(p.stderr or b'').decode('utf-8', 'replace')[:200]}")
    return out


def gh_api(method: str, path: str, payload: dict | None = None):
    """gh api 调用；payload 走临时文件规避参数长度/引号问题。"""
    argv = ["gh", "api", path, "--method", method]
    body_file = None
    if payload is not None:
        body_file = tempfile.NamedTemporaryFile(
            "w", suffix=".json", delete=False, encoding="utf-8")
        json.dump(payload, body_file, ensure_ascii=False)
        body_file.close()
        argv += ["--input", body_file.name]
    p = subprocess.run(argv, cwd=str(REPO_ROOT), capture_output=True,
                       timeout=120, creationflags=NO_WINDOW)
    out = (p.stdout or b"").decode("utf-8", errors="replace")
    if body_file:
        Path(body_file.name).unlink(missing_ok=True)
    if p.returncode != 0:
        raise SystemExit(f"gh api {path} 失败: "
                         f"{(p.stderr or b'').decode('utf-8', 'replace')[:300]}")
    return json.loads(out) if out.strip() else {}


STATE = REPO_ROOT / "automation" / "logs" / "api_push_state.json"


def _ok(*args) -> bool:
    return subprocess.run(["git", *args], cwd=str(REPO_ROOT), capture_output=True,
                          timeout=60, creationflags=NO_WINDOW).returncode == 0


def _remote_is_ours(remote_sha: str) -> bool:
    if _ok("cat-file", "-e", f"{remote_sha}^{{commit}}") and _ok("merge-base", "--is-ancestor", remote_sha, "HEAD"):
        return True
    try:
        last = json.loads(STATE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return (isinstance(last, dict) and last.get("remote_sha") == remote_sha
            and bool(last.get("local_head")) and _ok("merge-base", "--is-ancestor", last["local_head"], "HEAD"))


def _record_published(remote_sha: str) -> None:
    try:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps({"remote_sha": remote_sha, "local_head": git("rev-parse", "HEAD")}),
                         encoding="utf-8")
    except OSError:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(prog="api_push")
    parser.add_argument("--repo", default=None)
    parser.add_argument("--branch", default=None)
    args = parser.parse_args()

    repo = args.repo
    if not repo:
        m = re.search(r"github\.com[/:]([^/]+/[^/.]+)",
                      git("remote", "get-url", "origin"))
        if not m:
            raise SystemExit("无法从 origin 解析仓库")
        repo = m.group(1)
    branch = args.branch or git("rev-parse", "--abbrev-ref", "HEAD")

    ref = gh_api("GET", f"repos/{repo}/git/ref/heads/{branch}")
    remote_sha = ref["object"]["sha"]
    base_commit = gh_api("GET", f"repos/{repo}/git/commits/{remote_sha}")
    base_tree = base_commit["tree"]["sha"]

    # 防覆盖红线：本通道把"本地 HEAD 整棵树"提交到远端之上。远端若含本地没见过的提交
    # （另一台机器 / 每日自更新 / 人工 revert 或回滚），推上去就等于静默回滚别人的成果。
    # 只在两种情况放行：远端提交是本地 HEAD 的祖先；或远端正是本克隆上次经本通道推上去
    # 的那个提交（同树异 SHA），且当时的本地 HEAD 仍是现在 HEAD 的祖先。
    if not _remote_is_ours(remote_sha):
        print(f"[api_push] 拒绝推送：远端 {branch}@{remote_sha[:10]} 含本地历史中没有的提交，"
              "直接推送会覆盖它。请先 git pull（fetch + merge）再推。", file=sys.stderr)
        return 1

    # 修复①：远端树 vs 本地 HEAD 树逐条目比对（含修复② quotepath）；保留真实 mode，gitlink 照传
    rt = gh_api("GET", f"repos/{repo}/git/trees/{base_tree}?recursive=1")
    remote = {e["path"]: (e.get("mode"), e["sha"]) for e in rt.get("tree", [])
              if e.get("type") in ("blob", "commit")}
    ls = git("-c", "core.quotepath=false", "ls-tree", "-r", "HEAD")
    local = {}
    for line in ls.splitlines():
        meta, path = line.split("	", 1)
        mode, kind, sha = meta.split()
        local[path] = (mode, kind, sha)
    changed = [p for p, (mode, _, sha) in local.items() if remote.get(p) != (mode, sha)]
    deleted = [p for p in remote if p not in local]
    print(f"[api_push] {repo}@{branch} 变更 {len(changed)} 删除 {len(deleted)}")

    tree = []
    for path in deleted:  # 删除传播：sha=None 从 base_tree 摘除
        tree.append({"path": path, "mode": "100644", "type": "blob", "sha": None})
    for path in changed:
        mode, kind, sha = local[path]
        if kind == "commit" or (remote.get(path) or (None, None))[1] == sha:
            # 子模块 gitlink，或仅 mode 变化（blob 远端已有）：直接引用 sha
            tree.append({"path": path, "mode": mode, "type": kind, "sha": sha})
            continue
        # 修复③：上传 HEAD 对象原始字节而非工作区文件
        p = subprocess.run(["git", "cat-file", "blob", f"HEAD:{path}"],
                           cwd=str(REPO_ROOT), capture_output=True,
                           timeout=30, creationflags=NO_WINDOW)
        if p.returncode != 0:  # 宁可不推，也不推半棵树（半推之后防覆盖红线会永久卡死本通道）
            print(f"[api_push] 无法读取 {path}，放弃推送（远端未改动）", file=sys.stderr)
            return 1
        blob = gh_api("POST", f"repos/{repo}/git/blobs", {
            "content": base64.b64encode(p.stdout).decode("ascii"),
            "encoding": "base64"})
        tree.append({"path": path, "mode": mode, "type": "blob", "sha": blob["sha"]})
    if not tree:
        print(f"[api_push] 树已同步于 {git('rev-parse', 'HEAD')[:10]}（同树可异 SHA）")
        _record_published(remote_sha)
        return 0

    t = gh_api("POST", f"repos/{repo}/git/trees",
               {"base_tree": base_tree, "tree": tree})
    msg = git("log", "-1", "--pretty=%B")
    c = gh_api("POST", f"repos/{repo}/git/commits", {
        "message": msg, "tree": t["sha"], "parents": [remote_sha]})
    gh_api("PATCH", f"repos/{repo}/git/refs/heads/{branch}",
           {"sha": c["sha"], "force": False})
    _record_published(c["sha"])  # 先记账：远端已是我们的提交，下次即使校验失败也能自我修复

    # 硬校验：远端提交树必须与本地 HEAD 树逐 sha 等价（ref 相同≠内容等价）
    local_tree = git("rev-parse", "HEAD^{tree}")
    verify = gh_api("GET", f"repos/{repo}/git/ref/heads/{branch}")
    vc = gh_api("GET", f"repos/{repo}/git/commits/{verify['object']['sha']}")
    ok = vc.get("tree", {}).get("sha") == local_tree
    if not ok:
        print(f"[api_push] 树校验失败 remote={vc.get('tree', {}).get('sha')}"
              f" local={local_tree}", file=sys.stderr)
        return 1
    print(f"[api_push] 推送成功 → {verify['object']['sha'][:10]}"
          f"（{len(tree)} 个文件，树校验通过）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
