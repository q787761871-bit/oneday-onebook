#!/usr/bin/env python3
"""
filter_and_classify.py — 把 pool 过滤、去重、分池

输入：data/pool-YYYY-MM-DD.json + 已推清单
输出：data/candidates-YYYY-MM-DD.json
  按 3 个池：classic（经典）/ contemporary（严肃当代）/ crossdomain（跨域，留空）

过滤规则：
- 评分 ≥ 8.5 OR 来源含 top250
- 评价人数 ≥ 30
- 不在已推清单

分池规则：
- top250 来源 OR 出版年 ≤ 2010 → classic
- 出版年 ≥ 2021 → contemporary
- 中间（2011-2020）→ classic
- crossdomain 暂留空（v0.5 加学者豆列时填）
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
HISTORY_PATH = Path("/Users/jc/myclaude/memory-work/01 你的项目/一天一本书/_推过的书.md")


def load_history() -> set[str]:
    """从 _推过的书.md 解析已推过的书名。返回标准化书名集合。"""
    if not HISTORY_PATH.exists():
        return set()
    text = HISTORY_PATH.read_text()
    # 表格行：| 日期 | 书名 | ...
    names = set()
    for line in text.split("\n"):
        line = line.strip()
        if not line.startswith("|") or "---" in line:
            continue
        cells = [c.strip() for c in line.split("|")]
        if len(cells) >= 3:
            name = cells[2]
            if name and name not in ("书名",):
                names.add(name)
    return names


def normalize_name(name: str) -> str:
    """去掉副标题等噪声，便于匹配。"""
    return re.split(r"[:：]", name)[0].strip()


def classify(book: dict) -> str:
    """分到 classic / contemporary / crossdomain。"""
    if "top250" in book["source"]:
        return "classic"
    year = book.get("year")
    if year is None:
        return "classic"  # 年份未知，保守归经典
    if year >= 2021:
        return "contemporary"
    return "classic"


def main() -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    pool_path = ROOT / "data" / f"pool-{today}.json"
    if not pool_path.exists():
        sys.exit(f"Pool file not found: {pool_path}")
    pool = json.loads(pool_path.read_text())

    history_names = {normalize_name(n) for n in load_history()}
    print(f"History: {len(history_names)} books → {history_names}", file=sys.stderr)

    # 过滤
    filtered = []
    for b in pool:
        if b["votes"] < 30:
            continue
        if (b["rating"] or 0) < 8.5 and "top250" not in b["source"]:
            continue
        if normalize_name(b["name"]) in history_names:
            continue
        b["pool"] = classify(b)
        filtered.append(b)

    # 分池统计
    from collections import Counter
    by_pool = Counter(b["pool"] for b in filtered)
    print(f"\nFiltered: {len(filtered)} books", file=sys.stderr)
    for pool_name, count in by_pool.most_common():
        print(f"  {pool_name}: {count}", file=sys.stderr)

    out_path = ROOT / "data" / f"candidates-{today}.json"
    out_path.write_text(json.dumps(filtered, ensure_ascii=False, indent=2))
    print(f"\nWrote {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
