#!/usr/bin/env python3
"""
pick_today.py — 加权抽样选今天的书

用法：
  从 stdin 读评分后的候选 JSON：
    cat scored.json | python3 pick_today.py
  或指定 seed（测试用）：
    cat scored.json | python3 pick_today.py --seed 42

输入 JSON 格式（评分由 cron payload 中的 LLM 完成后传入）：
  [
    {"name": "...", "author": "...", "subject_id": "...",
     "pool": "classic|contemporary",
     "score": 8.5, "reason": "...",
     "year": 2024, "oneliner": "..."},
    ...
  ]

输出 JSON（写到 stdout）：
  {"name": "...", "author": "...", "subject_id": "...",
   "pool": "...", "score": 8.5, "reason": "...",
   "year": ..., "oneliner": "..."}

抽样规则：
- 按 70/25 池比例抽出"今天从哪个池抽"（crossdomain 暂空，重分到 classic+contemporary）
- 在该池内按"评分平方"加权随机抽 1 本
- 评分 < 6 分的全部排除
"""

import json
import random
import sys

POOL_RATIOS = {"classic": 0.70, "contemporary": 0.25, "crossdomain": 0.05}
MIN_SCORE = 7.0  # v0.5 提高门槛避免教材级入选


def pick(scored, seed=None):
    rng = random.Random(seed)
    # 排除低分
    qualified = [b for b in scored if (b.get("score") or 0) >= MIN_SCORE]
    if not qualified:
        sys.exit("No qualified candidates (score >= 6.0)")

    # 决定从哪个池抽（crossdomain 暂空 → classic + contemporary 重分）
    classic_p = POOL_RATIOS["classic"] / (POOL_RATIOS["classic"] + POOL_RATIOS["contemporary"])
    target_pool = "classic" if rng.random() < classic_p else "contemporary"

    pool_cands = [b for b in qualified if b.get("pool") == target_pool]
    # 如果目标池空，回退到另一池
    if not pool_cands:
        target_pool = "contemporary" if target_pool == "classic" else "classic"
        pool_cands = [b for b in qualified if b.get("pool") == target_pool]
    if not pool_cands:
        sys.exit("Both pools empty among qualified")

    weights = [b["score"] ** 2 for b in pool_cands]
    chosen = rng.choices(pool_cands, weights=weights, k=1)[0]
    return chosen


def main() -> None:
    seed = None
    args = sys.argv[1:]
    if "--seed" in args:
        i = args.index("--seed")
        seed = int(args[i + 1])

    scored = json.load(sys.stdin)
    chosen = pick(scored, seed)
    json.dump(chosen, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == "__main__":
    main()
