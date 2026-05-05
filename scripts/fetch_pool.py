#!/usr/bin/env python3
"""
fetch_pool.py — 从豆瓣拉候选池

来源：
- 豆瓣 Top 250（全量）
- 9 个 tag 各取前 50：哲学/政治哲学/社会学/经济学/心理学/人类学/科学/历史/文学批评

输出：data/pool-YYYY-MM-DD.json
"""

import json
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

JINA_PREFIX = "https://r.jina.ai/"
TAGS = [
    "哲学", "政治哲学", "社会学", "经济学", "心理学",
    "人类学", "科学", "历史", "文学批评",
]
TOP250_URL = "https://book.douban.com/top250"


def fetch(url: str) -> str:
    full = JINA_PREFIX + url
    req = urllib.request.Request(full, headers={"User-Agent": "oneday-onebook/0.4"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="ignore")


# 锚点：每本书都有 subject/<id> 链接。把 markdown 按"出现 subject 链接的位置"切片，
# 每片向后取一段窗口做字段提取。
SUBJECT_ANCHOR = re.compile(r"https://book\.douban\.com/subject/(\d+)/?")

# 在窗口内提取各字段
NAME_RX = [
    # 1) 图片链接格式：[![Image N](...)](.../subject/ID/)[书名](.../subject/ID/ "书名")
    re.compile(r"\]\(https://book\.douban\.com/subject/\d+/?\s*\"[^\"]*\"\s*\)"),  # placeholder, real extraction below
    # 2) ## [书名](url "书名") 格式
]
# 评分行：8.5( 123人评价 ) 或 (少于10人评价)
RATING_RX = re.compile(r"([\d]\.\d)\s*\(\s*(\d+)\s*人评价\s*\)")
LOW_VOTES_RX = re.compile(r"\(\s*少于\s*\d+\s*人评价\s*\)")
# 元数据行：作者 / 译者 / 出版社 / 出版日期 / 价格
META_RX = re.compile(r"^([^/\n]+(?:/[^/\n]+){2,})$", re.MULTILINE)
YEAR_RX = re.compile(r"\b(19|20)\d{2}\b")


def extract_name(window: str, sid: str) -> str | None:
    """两种格式：① 图片格式末尾的 [书名](url 'name') ② ## [书名](url 'name')"""
    # 形如 [书名](https://book.douban.com/subject/SID/ "书名")
    m = re.search(
        rf"\[([^\]]+)\]\(https://book\.douban\.com/subject/{sid}/?\s*\"[^\"]*\"\s*\)",
        window,
    )
    if m:
        return m.group(1).strip()
    # 形如 ## [书名](url)（不带 title attr）
    m = re.search(
        rf"##\s*\[([^\]]+)\]\(https://book\.douban\.com/subject/{sid}/?\s*\)",
        window,
    )
    if m:
        return m.group(1).strip()
    # 兜底：找 subject 链接前最近的 [name](
    m = re.search(rf"\[([^\]]+)\]\(https://book\.douban\.com/subject/{sid}/?", window)
    if m:
        return m.group(1).strip()
    return None


def parse_meta_line(window: str) -> tuple[str, str, int | None] | None:
    """从窗口里找像 '作者 / 出版社 / 2012-1 / 价格' 的行。
    返回 (作者, 出版社, 年份)。"""
    for line in window.split("\n"):
        line = line.strip()
        if "/" not in line:
            continue
        if line.startswith("[") or line.startswith("!"):
            continue  # 图片/链接行
        parts = [p.strip() for p in line.split("/")]
        if len(parts) < 3:
            continue
        # 至少一段含年份
        year = None
        for p in parts:
            m = YEAR_RX.search(p)
            if m:
                year = int(m.group(0))
                break
        if year is None:
            continue
        author = parts[0]
        publisher = parts[-3] if len(parts) >= 4 else parts[-2]
        return author, publisher, year
    return None


def parse_rating(window: str) -> tuple[float | None, int]:
    m = RATING_RX.search(window)
    if m:
        return float(m.group(1)), int(m.group(2))
    if LOW_VOTES_RX.search(window):
        return None, 0
    return None, 0


def parse_oneliner(window: str, name: str | None) -> str | None:
    """元信息行下面、空行隔开的一行短文（小于 50 字、非链接、非元信息）。Top 250 才有。"""
    lines = [l.strip() for l in window.split("\n")]
    for i, line in enumerate(lines):
        if not line:
            continue
        if RATING_RX.search(line) or LOW_VOTES_RX.search(line):
            # 评分行的下一段非空、非元信息可能是简介
            for j in range(i + 1, min(i + 5, len(lines))):
                cand = lines[j]
                if not cand:
                    continue
                if cand.startswith("[") or cand.startswith("!") or cand.startswith("##"):
                    continue
                if "/" in cand and YEAR_RX.search(cand):
                    continue  # 下一本书的元信息
                if len(cand) > 80:
                    continue
                if name and name in cand:
                    continue
                return cand
            break
    return None


def parse_book_list(md: str, source: str) -> list[dict]:
    """以 subject_id 为锚点，向后取 800 字符窗口解析。"""
    seen_ids = set()
    books = []
    matches = list(SUBJECT_ANCHOR.finditer(md))
    for i, m in enumerate(matches):
        sid = m.group(1)
        if sid in seen_ids:
            continue
        seen_ids.add(sid)
        start = m.start()
        # 窗口：从这个 ID 第一次出现起，到下一个不同 ID 出现为止（避免吃到下一本）
        next_other_start = len(md)
        for nm in matches[i + 1:]:
            if nm.group(1) != sid:
                next_other_start = nm.start()
                break
        window = md[start:next_other_start]

        name = extract_name(window, sid)
        if not name or name.startswith("Image"):
            continue
        meta = parse_meta_line(window)
        rating, votes = parse_rating(window)
        oneliner = parse_oneliner(window, name)

        author, publisher, year = (meta if meta else ("", "", None))
        books.append({
            "subject_id": sid,
            "name": name,
            "author": author,
            "publisher": publisher,
            "year": year,
            "rating": rating,
            "votes": votes,
            "oneliner": oneliner,
            "source": source,
        })
    return books


def fetch_top250() -> list[dict]:
    out = []
    for start in range(0, 250, 25):
        url = f"{TOP250_URL}?start={start}"
        try:
            md = fetch(url)
            page = parse_book_list(md, "top250")
            out.extend(page)
            print(f"  top250 start={start}: {len(page)} books", file=sys.stderr)
        except Exception as e:
            print(f"  top250 start={start} FAILED: {e}", file=sys.stderr)
    return out


def fetch_tag(tag: str, limit: int = 50) -> list[dict]:
    encoded = urllib.parse.quote(tag)
    out = []
    for start in range(0, limit, 20):
        url = f"https://book.douban.com/tag/{encoded}?type=R&start={start}"
        try:
            md = fetch(url)
            page = parse_book_list(md, f"tag:{tag}")
            out.extend(page)
            print(f"  tag={tag} start={start}: {len(page)} books", file=sys.stderr)
        except Exception as e:
            print(f"  tag={tag} start={start} FAILED: {e}", file=sys.stderr)
    return out[:limit]


def dedupe_by_id(books: list[dict]) -> list[dict]:
    seen: dict[str, dict] = {}
    for b in books:
        sid = b["subject_id"]
        if sid in seen:
            existing = seen[sid]
            srcs = set(existing["source"].split(",")) | set(b["source"].split(","))
            existing["source"] = ",".join(sorted(srcs))
            # 字段补全：以非空为准
            for key in ("author", "publisher", "year", "rating", "oneliner"):
                if not existing.get(key) and b.get(key):
                    existing[key] = b[key]
            if (b.get("votes") or 0) > (existing.get("votes") or 0):
                existing["votes"] = b["votes"]
        else:
            seen[sid] = dict(b)
    return list(seen.values())


def main() -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    out_dir = Path(__file__).parent.parent / "data"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"pool-{today}.json"

    print("Fetching Top 250...", file=sys.stderr)
    pool = fetch_top250()
    for tag in TAGS:
        print(f"Fetching tag '{tag}'...", file=sys.stderr)
        pool.extend(fetch_tag(tag, limit=50))

    pool = dedupe_by_id(pool)
    out_path.write_text(json.dumps(pool, ensure_ascii=False, indent=2))
    print(f"\nDone. {len(pool)} unique books → {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
