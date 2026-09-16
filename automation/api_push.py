# -*- coding: utf-8 -*-
"""GitHub Git Data API 推送（第三层回退通道）。

背景：github.com:443 receive-pack 经机场代理常被污染（curl 200 而 git 死），
api.github.com 是不同 CDN 通道，gh CLI 直连实测可用（本机已登录
huangxiding-creator，凭据在系统 keyring——本脚本零凭据落盘）。

流程：取远端 ref → 校验本地为快进 → 逐变更文件建 blob（base64）→
base_tree 建树 → 建提交 → PATCH ref。等价一次 git push 单提交。
仅支持快进；分叉（远端有本地没有的提交）直接报错退出。

用法: python api_push.py [--repo OWNER/NAME] [--branch master]
      缺省从当前 git remote / 当前分支推导；cwd 须为目标仓库。
"""
from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    p = subprocess.run(["git", *args], cwd=str(REPO_ROOT),
                       capture_output=True, timeout=60,
                       creationflags=0x08000000)
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
                       timeout=120, creationflags=0x08000000)
    out = (p.stdout or b"").decode("utf-8", errors="replace")
    if body_file:
        Path(body_file.name).unlink(missing_ok=True)
    if p.returncode != 0:
        raise SystemExit(f"gh api {path} 失败: "
                         f"{(p.stderr or b'').decode('utf-8', 'replace')[:300]}")
    return json.loads(out) if out.strip() else {}


def main() -> int:
    parser = argparse.ArgumentParser(prog="api_push")
    parser.add_argument("--repo", default=None)
    parser.add_argument("--branch", default=None)
    args = parser.parse_args()

    repo = args.repo
    if not repo:
        url = git("remote", "get-url", "origin")
        m = __import__("re").search(r"github\.com[/:]([^/]+/[^/.]+)", url)
        if not m:
            raise SystemExit(f"无法从 origin 解析仓库: {url}")
        repo = m.group(1)
    branch = args.branch or git("rev-parse", "--abbrev-ref", "HEAD")
    local_sha = git("rev-parse", "HEAD")

    ref = gh_api("GET", f"repos/{repo}/git/ref/heads/{branch}")
    remote_sha = ref["object"]["sha"]
    if remote_sha == local_sha:
        print(f"[api_push] {repo}@{branch} 已同步于 {local_sha[:10]}")
        return 0

    # 仅支持快进：远端头必须是本地的祖先
    check = subprocess.run(
        ["git", "merge-base", "--is-ancestor", remote_sha, local_sha],
        cwd=str(REPO_ROOT), capture_output=True,
        creationflags=0x08000000)
    if check.returncode != 0:
        print(f"[api_push] 分叉：远端 {remote_sha[:10]} 非本地祖先，拒绝推送",
              file=sys.stderr)
        return 2

    diff = git("diff", "--name-status", f"{remote_sha}..{local_sha}")
    entries = []
    for line in diff.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status, path = parts[0], parts[-1].replace("\\", "/")
        if status.startswith("D"):
            entries.append({"path": path, "mode": "100644",
                            "type": "blob", "sha": None})
            continue
        if status.startswith("R"):  # R100 old new → 删旧 + 加新
            entries.append({"path": parts[1].replace("\\", "/"),
                            "mode": "100644", "type": "blob", "sha": None})
        blob = gh_api("POST", f"repos/{repo}/git/blobs", {
            "content": base64.b64encode(
                (REPO_ROOT / path).read_bytes()).decode("ascii"),
            "encoding": "base64"})
        entries.append({"path": path, "mode": "100644",
                        "type": "blob", "sha": blob["sha"]})
    if not entries:
        print("[api_push] 无文件差异但 SHA 不同（疑似空提交），放弃")
        return 3

    base_commit = gh_api("GET", f"repos/{repo}/git/commits/{remote_sha}")
    tree = gh_api("POST", f"repos/{repo}/git/trees", {
        "base_tree": base_commit["tree"]["sha"], "tree": entries})
    message = git("log", "-1", "--pretty=%B")
    commit = gh_api("POST", f"repos/{repo}/git/commits", {
        "message": message, "tree": tree["sha"],
        "parents": [remote_sha]})
    gh_api("PATCH", f"repos/{repo}/git/refs/heads/{branch}",
           {"sha": commit["sha"], "force": False})
    print(f"[api_push] 推送成功: {remote_sha[:10]} → {commit['sha'][:10]}"
          f"（{len(entries)} 个文件）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
