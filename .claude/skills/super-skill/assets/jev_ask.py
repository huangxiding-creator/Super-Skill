#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""jev_ask —— Super-Skill 随身判断原语 CLI（Jev / TypeSafe System One）。

返回类型化答案+概率，不生成文本：判断给概率，选择给分布。
用法（无第三方依赖，Python 3.9+）：

  # 是否判断（Noul）→ 概率
  python jev_ask.py noul --state '{"claim":"已修复登录bug","evidence":"<测试输出>"}' \
      --instructions "证据是否支持该声称已经完成？" \
      --true "证据里有通过的测试/可复现的成功结果" --false "证据缺失或相反"

  # 选择判断（Choice）→ 选项+分布+置信度
  python jev_ask.py choice --state '{"ticket":"..."}' \
      --instructions "这张工单该路由给哪个处理流？" \
      --criteria '{"bug":"缺陷修复流","feature":"新功能流","question":"答疑流"}'

state 传 JSON 串或 @file.json；key 取 TYPESAFE_API_KEY 环境变量或
--key-file（ini 格式 [typesafe] api_key=...）。fail-soft：任何故障输出
{"ok": false, ...} 且退出码 0——调用方永远拿得到 JSON，自行降级。
定价量级 $0.0001/次（jev-1.13.0，360k 上下文）；免费模型优先铁律：
确定性检查（正则/行数/枚举）能用代码做就用代码，Jev 只占语义位。
"""
from __future__ import annotations

import argparse
import configparser
import json
import os
import sys
import urllib.error
import urllib.request

ENDPOINT = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-1.13.0"


def _emit(obj: dict) -> int:
    print(json.dumps(obj, ensure_ascii=False))
    return 0


def _load_key(args) -> str:
    env = os.environ.get("TYPESAFE_API_KEY", "").strip()
    if env:
        return env
    if args.key_file:
        cp = configparser.ConfigParser()
        cp.read(args.key_file, encoding="utf-8")
        return cp.get("typesafe", "api_key", fallback="").strip()
    return ""


def main() -> int:
    ap = argparse.ArgumentParser(prog="jev_ask")
    ap.add_argument("primitive", choices=["noul", "choice"])
    ap.add_argument("--state", required=True, help="JSON 串或 @file.json")
    ap.add_argument("--instructions", required=True)
    ap.add_argument("--true", dest="crit_true", help="Noul：为真的具体情形")
    ap.add_argument("--false", dest="crit_false", help="Noul：为假的具体情形")
    ap.add_argument("--criteria", help="Choice：JSON {选项:该选项的具体含义}")
    ap.add_argument("--key-file", help="ini 凭据文件（[typesafe] api_key）")
    ap.add_argument("--timeout", type=float, default=20.0)
    args = ap.parse_args()

    key = _load_key(args)
    if not key:
        return _emit({"ok": False, "error": "no_key",
                      "hint": "设 TYPESAFE_API_KEY 或 --key-file"})
    raw = args.state
    try:
        state = (json.loads(open(raw[1:], encoding="utf-8").read())
                 if raw.startswith("@") else json.loads(raw))
    except (OSError, json.JSONDecodeError) as exc:
        return _emit({"ok": False, "error": f"bad_state: {exc}"})

    if args.primitive == "noul":
        q = {"type": "noul", "instructions": args.instructions}
        if args.crit_true or args.crit_false:
            q["criteria"] = {"true": args.crit_true or "",
                             "false": args.crit_false or ""}
    else:
        try:
            criteria = json.loads(args.criteria or "{}")
        except json.JSONDecodeError as exc:
            return _emit({"ok": False, "error": f"bad_criteria: {exc}"})
        q = {"type": "choice", "instructions": args.instructions,
             "criteria": criteria}
    body = json.dumps({"state": state, "model": MODEL,
                       "questions": {"q": q}}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(ENDPOINT, data=body, method="POST", headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    for attempt in (0, 1):  # 429/网络抖动退避一发
        try:
            with urllib.request.urlopen(req, timeout=args.timeout) as resp:
                answers = json.loads(resp.read().decode("utf-8"))["answers"]["q"]
            if args.primitive == "noul":
                return _emit({"ok": True, "noul": float(answers["noul"])})
            return _emit({"ok": True, "choice": answers["choice"],
                          "probabilities": answers.get("probabilities"),
                          "confidence": float(answers.get("confidence", 0))})
        except (urllib.error.URLError, urllib.error.HTTPError, OSError,
                KeyError, TypeError, ValueError) as exc:
            if attempt == 0:
                import time
                time.sleep(2)
                continue
            return _emit({"ok": False, "error": f"api: {exc}"})
    return _emit({"ok": False, "error": "unreachable"})


if __name__ == "__main__":
    sys.exit(main())
