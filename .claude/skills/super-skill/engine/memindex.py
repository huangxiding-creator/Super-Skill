#!/usr/bin/env python3
"""Retrieval over markdown project memory (claude-mem style 3-layer disclosure).

Layer 1 ``search``   -> compact hits: id, path, heading, one-line summary, score
Layer 2 ``timeline`` -> neighbouring chunks of one hit (same file)
Layer 3 ``get``      -> full chunk text for chosen ids only

Index: SQLite at ``<project>/.super-skill/memindex.sqlite``. Markdown files are
chunked by headings (<= ~1500 chars, long sections split on paragraphs) and
indexed incrementally keyed by (path, mtime, size). Playbook active bullets and
ledger ``note`` records are indexed as virtual documents.

Full-text engine is picked at runtime, degrading gracefully:
``fts5 trigram`` (good for Chinese) -> ``fts5 unicode61`` -> plain ``LIKE``.
Query tokens that the chosen engine cannot match (e.g. < 3 chars under
trigram, CJK under unicode61) are scored with LIKE and merged.
Score = normalised bm25 relevance + small recency boost (higher is better).
"""
from __future__ import annotations

import argparse
import glob as _glob
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ss_common import force_utf8_stdio, read_jsonl, sdir, short_hash  # noqa: E402

DB_NAME = "memindex.sqlite"
SCHEMA = "1"
MAX_CHUNK = 1500
MAX_FILE_BYTES = 2 * 1024 * 1024
RECENCY_WEIGHT = 0.1
DEFAULT_GLOBS = (
    "KNOWLEDGE_BASE/**/*.md",
    "*.md",
    "docs/solutions/**/*.md",
    ".super-skill/handoff.md",
    ".super-skill/progress.txt",
)
VIRTUAL_PLAYBOOK = "virtual:playbook"
VIRTUAL_LEDGER = "virtual:ledger-notes"

_CJK_RE = re.compile(r"[぀-ヿ㐀-䶿一-鿿가-힯豈-﫿]")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


# ---------------------------------------------------------------- db

def db_path(root: Path) -> Path:
    return sdir(root) / DB_NAME


def _probe_mode(conn: sqlite3.Connection) -> str:
    for mode, tok in (("trigram", "trigram"), ("unicode61", "unicode61 remove_diacritics 2")):
        try:
            conn.execute(f"CREATE VIRTUAL TABLE temp._probe_{mode} USING fts5(x, tokenize='{tok}')")
            conn.execute(f"DROP TABLE temp._probe_{mode}")
            return mode
        except sqlite3.Error:
            continue
    return "like"


def _connect(root: Path, force_mode: str | None = None) -> tuple:
    path = db_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT)")
    row = conn.execute("SELECT v FROM meta WHERE k='mode'").fetchone()
    schema = conn.execute("SELECT v FROM meta WHERE k='schema'").fetchone()
    if force_mode:
        want = force_mode
    elif row is not None and schema is not None and schema["v"] == SCHEMA:
        want = row["v"]  # keep whatever engine the existing index was built with
        if want != "like" and _probe_mode(conn) == "like":
            want = "like"
    else:
        want = _probe_mode(conn)
    if row is None or row["v"] != want or schema is None or schema["v"] != SCHEMA:
        _reset(conn, want)
    return conn, want


def _reset(conn: sqlite3.Connection, mode: str) -> None:
    for t in ("chunks_fts", "chunks", "files"):
        try:
            conn.execute(f"DROP TABLE IF EXISTS {t}")
        except sqlite3.Error:
            pass
    conn.execute("CREATE TABLE files (src TEXT PRIMARY KEY, mtime REAL, size INTEGER)")
    conn.execute(
        "CREATE TABLE chunks (id TEXT PRIMARY KEY, src TEXT, seq INTEGER, heading TEXT,"
        " text TEXT, mtime REAL)"
    )
    conn.execute("CREATE INDEX chunks_src ON chunks(src, seq)")
    if mode == "trigram":
        conn.execute("CREATE VIRTUAL TABLE chunks_fts USING fts5(id UNINDEXED, heading, text,"
                     " tokenize='trigram')")
    elif mode == "unicode61":
        conn.execute("CREATE VIRTUAL TABLE chunks_fts USING fts5(id UNINDEXED, heading, text,"
                     " tokenize='unicode61 remove_diacritics 2')")
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('mode', ?)", (mode,))
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('schema', ?)", (SCHEMA,))
    conn.commit()


# ---------------------------------------------------------------- chunking

def _split_long(text: str, limit: int = MAX_CHUNK) -> list:
    if len(text) <= limit:
        return [text]
    parts, cur = [], ""
    for para in re.split(r"\n\s*\n", text):
        para = para.strip("\n")
        if not para.strip():
            continue
        while len(para) > limit:  # a single huge paragraph: hard split
            if cur:
                parts.append(cur)
                cur = ""
            parts.append(para[:limit])
            para = para[limit:]
        if cur and len(cur) + 2 + len(para) > limit:
            parts.append(cur)
            cur = para
        else:
            cur = f"{cur}\n\n{para}" if cur else para
    if cur.strip():
        parts.append(cur)
    return parts


def chunk_markdown(text: str, limit: int = MAX_CHUNK) -> list:
    """Split markdown into ``[(heading_breadcrumb, body)]`` chunks."""
    sections = []
    stack: list = []
    cur_lines: list = []
    cur_heading = ""
    in_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            in_fence = not in_fence
        m = None if in_fence else _HEADING_RE.match(line)
        if m:
            sections.append((cur_heading, cur_lines))
            level, title = len(m.group(1)), m.group(2).strip()
            stack = [(lv, t) for lv, t in stack if lv < level] + [(level, title)]
            cur_heading = " > ".join(t for _, t in stack)
            cur_lines = [line]
        else:
            cur_lines.append(line)
    sections.append((cur_heading, cur_lines))
    out = []
    for heading, lines in sections:
        body = "\n".join(lines).strip()
        content = [ln for ln in lines if ln.strip() and not _HEADING_RE.match(ln)]
        if not body or not content:
            continue  # empty section or heading-only section
        for part in _split_long(body, limit):
            out.append((heading, part))
    return out


# ---------------------------------------------------------------- sources

def _collect_files(root: Path, globs) -> dict:
    found = {}
    base = root.resolve()
    for pattern in globs:
        for p in _glob.glob(str(root / pattern), recursive=True):
            fp = Path(p)
            if not fp.is_file():
                continue
            try:
                rel = fp.resolve().relative_to(base).as_posix()
            except ValueError:
                rel = fp.as_posix()
            found[rel] = fp
    return found


def _stat(fp: Path):
    try:
        st = fp.stat()
        return st.st_mtime, st.st_size
    except OSError:
        return None


def _playbook_docs(root: Path) -> list:
    try:
        import playbook  # local module, optional
        items = playbook.bullets(root)
    except Exception:  # noqa: BLE001 - playbook missing / corrupt must not break indexing
        return []
    out = []
    for b in items:
        pat = f" `{b['pattern']}`" if b.get("pattern") else ""
        out.append((f"playbook/{b['section']} {b['id']}", f"{b['text']}{pat}"))
    return out


def _ledger_docs(root: Path) -> list:
    out = []
    for rec in read_jsonl(sdir(root) / "ledger.jsonl"):
        if rec.get("kind") != "note":
            continue
        text = rec.get("text") or rec.get("note") or rec.get("message") or rec.get("msg")
        if not text:
            rest = {k: v for k, v in rec.items() if k not in ("ts", "kind")}
            text = json.dumps(rest, ensure_ascii=False)
        out.append((f"note {rec.get('ts', '')}".strip(), str(text)))
    return out


def _delete_src(conn, mode: str, src: str) -> None:
    if mode != "like":
        conn.execute("DELETE FROM chunks_fts WHERE id IN (SELECT id FROM chunks WHERE src=?)",
                     (src,))
    conn.execute("DELETE FROM chunks WHERE src=?", (src,))
    conn.execute("DELETE FROM files WHERE src=?", (src,))


def _replace_src(conn, mode: str, src: str, chunks: list, mtime: float, size: int) -> int:
    _delete_src(conn, mode, src)
    for seq, (heading, body) in enumerate(chunks):
        cid = "m-" + short_hash(f"{src}#{seq}", 10)
        conn.execute("INSERT OR REPLACE INTO chunks VALUES (?,?,?,?,?,?)",
                     (cid, src, seq, heading, body, mtime))
        if mode != "like":
            conn.execute("INSERT INTO chunks_fts (id, heading, text) VALUES (?,?,?)",
                         (cid, heading, body))
    conn.execute("INSERT OR REPLACE INTO files VALUES (?,?,?)", (src, mtime, size))
    return len(chunks)


# ---------------------------------------------------------------- API

def index(root, extra_globs=None, _mode: str | None = None) -> dict:
    """Incrementally (re)index memory sources. ``_mode`` forces an engine (tests)."""
    root = Path(root)
    conn, mode = _connect(root, _mode)
    stats = {"mode": mode, "files": 0, "indexed": 0, "skipped": 0, "removed": 0, "chunks": 0}
    try:
        known = {r["src"]: (r["mtime"], r["size"]) for r in conn.execute("SELECT * FROM files")}
        files = _collect_files(root, list(DEFAULT_GLOBS) + list(extra_globs or []))
        stats["files"] = len(files)
        seen = set()
        for rel, fp in sorted(files.items()):
            st = _stat(fp)
            if st is None or st[1] > MAX_FILE_BYTES:
                continue
            seen.add(rel)
            if known.get(rel) == st:
                stats["skipped"] += 1
                continue
            try:
                text = fp.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if fp.suffix.lower() in (".md", ".markdown"):
                chunks = chunk_markdown(text)
            else:
                chunks = [(fp.name, part) for part in _split_long(text.strip()) if part.strip()]
            stats["chunks"] += _replace_src(conn, mode, rel, chunks, st[0], st[1])
            stats["indexed"] += 1
        # virtual docs keyed on their backing jsonl file
        for vsrc, backing, loader in (
            (VIRTUAL_PLAYBOOK, sdir(root) / "playbook.jsonl", _playbook_docs),
            (VIRTUAL_LEDGER, sdir(root) / "ledger.jsonl", _ledger_docs),
        ):
            st = _stat(backing)
            if st is None:
                continue
            seen.add(vsrc)
            if known.get(vsrc) == st:
                stats["skipped"] += 1
                continue
            stats["chunks"] += _replace_src(conn, mode, vsrc, loader(root), st[0], st[1])
            stats["indexed"] += 1
        for src in set(known) - seen:
            _delete_src(conn, mode, src)
            stats["removed"] += 1
        conn.commit()
        stats["total_chunks"] = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    finally:
        conn.close()
    return stats


def _query_tokens(q: str) -> list:
    """Split a free-text query into unique tokens; CJK runs stay whole."""
    toks, seen = [], set()
    for t in _TOKEN_RE.findall(q or ""):
        t = t.strip("_")
        if t and t.lower() not in seen:
            seen.add(t.lower())
            toks.append(t)
    return toks


def _cjk_ngrams(tok: str) -> list:
    """For LIKE scoring of long CJK runs: overlapping bigrams."""
    if len(tok) <= 2 or not _CJK_RE.search(tok):
        return [tok]
    return [tok[i:i + 2] for i in range(len(tok) - 1)]


def _summary(text: str, terms: list, limit: int = 120) -> str:
    lines = [ln for ln in text.splitlines() if ln.strip() and not _HEADING_RE.match(ln)]
    flat = re.sub(r"[#*`>|]+", "", " ".join(lines) or text)
    flat = re.sub(r"\s+", " ", flat).strip()
    low = flat.lower()
    pos = -1
    for t in terms:
        i = low.find(t.lower())
        if i >= 0 and (pos < 0 or i < pos):
            pos = i
    start = max(0, pos - 30) if pos > 40 else 0
    snippet = flat[start:start + limit]
    if start > 0:
        snippet = "…" + snippet[1:]
    if start + limit < len(flat):
        snippet = snippet[:-1] + "…"
    return snippet


def _like_escape(s: str) -> str:
    return "%" + s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"


def search(root, q: str, k: int = 8, auto_index: bool = True) -> list:
    """Layer 1: compact ranked hits. Runs an incremental index first by default."""
    root = Path(root)
    if auto_index or not db_path(root).exists():
        index(root)
    toks = _query_tokens(q)
    if not toks:
        return []
    conn, mode = _connect(root)
    try:
        fts_toks, like_toks = [], []
        for t in toks:
            if mode == "trigram" and len(t) >= 3:
                fts_toks.append(t)
            elif mode == "unicode61" and not _CJK_RE.search(t):
                fts_toks.append(t)
            else:
                like_toks.append(t)
        fts_rel: dict = {}
        if fts_toks:
            terms = list(fts_toks)
            if mode == "trigram":  # long CJK runs: also match their trigrams (partial hits)
                for t in fts_toks:
                    if len(t) > 3 and _CJK_RE.search(t):
                        terms.extend(t[i:i + 3] for i in range(len(t) - 2))
            match = " OR ".join('"' + t.replace('"', '""') + '"' for t in dict.fromkeys(terms))
            try:
                rows = conn.execute(
                    "SELECT id, bm25(chunks_fts, 0.0, 2.0, 1.0) AS s FROM chunks_fts"
                    " WHERE chunks_fts MATCH ? ORDER BY s LIMIT 200", (match,)).fetchall()
                best = max((-r["s"] for r in rows), default=0.0)
                for r in rows:
                    fts_rel[r["id"]] = (max(0.0, -r["s"]) / best) if best > 0 else 1.0
            except sqlite3.Error:
                like_toks.extend(fts_toks)
                fts_toks = []
        like_cnt: dict = {}
        for t in like_toks:
            grams = _cjk_ngrams(t)
            for g in grams:
                pat = _like_escape(g)
                for r in conn.execute("SELECT id FROM chunks WHERE text LIKE ? ESCAPE '\\'"
                                      " OR heading LIKE ? ESCAPE '\\'", (pat, pat)):
                    like_cnt[r["id"]] = like_cnt.get(r["id"], 0.0) + 1.0 / len(grams)
        n = len(fts_toks) + len(like_toks)
        share = len(fts_toks) / n
        rel = {}
        for cid in set(fts_rel) | set(like_cnt):
            rel[cid] = fts_rel.get(cid, 0.0) * share + like_cnt.get(cid, 0.0) / n
        if not rel:
            return []
        ids = list(rel)
        meta = {}
        for i in range(0, len(ids), 500):
            part = ids[i:i + 500]
            qs = ",".join("?" * len(part))
            for r in conn.execute(f"SELECT id, src, heading, text, mtime FROM chunks"
                                  f" WHERE id IN ({qs})", part):
                meta[r["id"]] = r
        mts = [r["mtime"] or 0 for r in meta.values()]
        lo, hi = (min(mts), max(mts)) if mts else (0, 0)
        out = []
        for cid, score in rel.items():
            r = meta.get(cid)
            if r is None:
                continue
            recency = ((r["mtime"] or 0) - lo) / (hi - lo) if hi > lo else 0.0
            out.append({"id": cid, "path": r["src"], "heading": r["heading"] or "",
                        "summary": _summary(r["text"], toks),
                        "score": round(score + RECENCY_WEIGHT * recency, 4)})
        out.sort(key=lambda h: (-h["score"], h["path"], h["id"]))
        return out[:max(1, int(k))]
    finally:
        conn.close()


def timeline(root, cid: str, n: int = 2) -> list:
    """Layer 2: the chunk plus ``n`` neighbours on each side in the same file."""
    conn, _ = _connect(Path(root))
    try:
        row = conn.execute("SELECT src, seq FROM chunks WHERE id=?", (cid,)).fetchone()
        if row is None:
            return []
        rows = conn.execute(
            "SELECT id, src, seq, heading, text FROM chunks WHERE src=? AND seq BETWEEN ? AND ?"
            " ORDER BY seq", (row["src"], row["seq"] - n, row["seq"] + n)).fetchall()
        return [{"id": r["id"], "path": r["src"], "seq": r["seq"], "heading": r["heading"] or "",
                 "summary": _summary(r["text"], []), "current": r["id"] == cid} for r in rows]
    finally:
        conn.close()


def get(root, ids) -> list:
    """Layer 3: full text for the requested chunk ids (unknown ids are skipped)."""
    if isinstance(ids, str):
        ids = [ids]
    conn, _ = _connect(Path(root))
    try:
        out = []
        for cid in ids:
            r = conn.execute("SELECT id, src, heading, text FROM chunks WHERE id=?",
                             (cid,)).fetchone()
            if r is not None:
                out.append({"id": r["id"], "path": r["src"], "heading": r["heading"] or "",
                            "text": r["text"]})
        return out
    finally:
        conn.close()


# ---------------------------------------------------------------- CLI

def main(argv=None) -> int:
    force_utf8_stdio()
    ap = argparse.ArgumentParser(prog="memindex.py", description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--json", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("index")
    p.add_argument("--glob", action="append", default=[], help="extra glob (repeatable)")
    p = sub.add_parser("search")
    p.add_argument("q")
    p.add_argument("-k", type=int, default=8)
    p.add_argument("--no-index", action="store_true", help="skip incremental reindex")
    p = sub.add_parser("timeline")
    p.add_argument("id")
    p.add_argument("-n", type=int, default=2)
    p = sub.add_parser("get")
    p.add_argument("ids", nargs="+")
    a = ap.parse_args(argv)
    root = Path(a.root)

    def out(data, text):
        print(json.dumps(data, ensure_ascii=False, indent=2) if a.json else text)

    try:
        if a.cmd == "index":
            st = index(root, a.glob)
            out(st, " ".join(f"{k}={v}" for k, v in st.items()))
        elif a.cmd == "search":
            hits = search(root, a.q, a.k, auto_index=not a.no_index)
            out(hits, "\n".join(f"{h['id']}  {h['score']:.3f}  {h['path']} § {h['heading']}\n"
                                f"    {h['summary']}" for h in hits) or "no results")
        elif a.cmd == "timeline":
            items = timeline(root, a.id, a.n)
            out(items, "\n".join(f"{'>' if i['current'] else ' '} {i['id']} #{i['seq']}"
                                 f" {i['heading']} — {i['summary']}" for i in items)
                or "unknown id")
        elif a.cmd == "get":
            items = get(root, a.ids)
            out(items, "\n\n".join(f"=== {i['id']} {i['path']} § {i['heading']}\n{i['text']}"
                                   for i in items) or "unknown id(s)")
    except (sqlite3.Error, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
