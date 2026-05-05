#!/usr/bin/env python3
"""
pick_today.py — 从评分后的候选里加权抽样选今天的书

评分由 LLM（在对话/Cli 里）给出，写在 SCORED 里。
本脚本只做：按 70/25 池比例 + 评分平方加权随机抽样。

v0.4 半自动版：评分手工填入；v0.5 接 API 后改成自动评分。
"""

import random
from typing import Literal

# 评分协议：每条 (name, author_or_publisher_hint, source_pool, llm_score_0_to_10, why)
# llm_score 反映"扩范畴价值"——是否原创范畴/给可迁移方法论/回答真问题/装新切刀
SCORED: list[tuple[str, str, Literal["classic", "contemporary"], float, str]] = [
    # ===== Classic 池（来自豆瓣 9 个 tag 的高分非 top250 + 部分 top250 思想类）=====
    ("利维坦", "霍布斯", "classic", 10.0, "西方政治哲学奠基；自然状态/社会契约/巨灵三个范畴是现代政治学入场券"),
    ("文化的阐释", "克利福德·格尔茨", "classic", 10.0, "'深描'概念是定性研究方法论基石，跨学科应用极广"),
    ("城邦与人", "施特劳斯", "classic", 8.5, "现代政治哲学的批判性重构，难度高但范畴深"),
    ("阿拉米斯，或对技术的爱", "拉图尔", "classic", 9.0, "ANT 理论入门，'非人行动者'反直觉范畴；用一个失败地铁项目讲故事"),
    ("潘多拉的希望", "拉图尔", "classic", 9.0, "科学论奠基，'实在的多重制造'范畴"),
    ("天使的精确性", "Marshall Berman 风格", "classic", 8.0, "跨域思想史，博尔赫斯/海森堡/康德对照看实在论"),
    ("我们如何理解这个世界 鲍曼对谈", "齐格蒙特·鲍曼", "classic", 8.5, "'流动现代性'晚年总结，社会理论范畴"),
    ("像女孩那样丢球", "Iris Marion Young", "classic", 8.5, "身体现象学+女性主义跨域，'被动综合'范畴"),
    ("剑桥大学人类学十五讲", "人类学导论", "classic", 7.5, "导论级，扩范畴密度高但偏综述"),
    ("科学哲学导论", "Alex Rosenberg", "classic", 7.5, "教材级，但是科学哲学入门最好的一本"),
    ("保守主义：为传统而战", "罗杰·斯克鲁顿", "classic", 7.5, "保守主义思想史导论"),
    ("圆的变形", "数学哲学", "classic", 7.0, "小众但跨域"),
    ("从数学到哲学", "王浩", "classic", 8.0, "王浩的逻辑哲学，跨域稀有"),
    ("奥威尔书评全集", "奥威尔", "classic", 7.0, "文学批评+政治评论"),
    ("亲密陷阱", "心理学+社会学", "classic", 7.0, "亲密关系的社会理论"),
    ("社会作为判决", "Didier Eribon", "classic", 8.0, "Eribon 自传式社会学，阶级范畴"),

    # ===== Contemporary 池（≥8.8 评分，2021 后出版）=====
    ("控制论与科学方法论", "金观涛、华国凡", "contemporary", 9.0, "控制论范畴对系统思维基石；中国少有跨域思想家"),
    ("写给非哲学家的哲学入门", "阿尔都塞", "contemporary", 9.0, "阿尔都塞导论级，结构主义马克思主义入门"),
    ("反俄狄浦斯", "德勒兹/加塔利", "contemporary", 9.0, "重磅，'欲望机器'范畴；但极难"),
    ("没有内容的人", "阿甘本", "contemporary", 8.5, "阿甘本美学/政治哲学交集"),
    ("自由主义", "李强", "contemporary", 8.0, "中国学者写自由主义思想史"),
    ("文学三篇：一个政治哲学视角", "洪涛", "contemporary", 8.0, "中国学者跨域，文学+政治哲学"),
    ("汉娜·阿伦特的爱与反抗", "斯通布里奇", "contemporary", 8.0, "阿伦特通俗解读"),
    ("绝望者的练习：齐奥朗访谈录", "齐奥朗", "contemporary", 7.5, "存在主义碎片，深刻但碎"),
    ("中产阶级的孩子们：六十年代与文化领导权", "程巍", "contemporary", 8.0, "中国学者写文化研究/葛兰西"),
    ("薄暮时分：养老院里的日常与脆弱", "吴心越", "contemporary", 7.0, "民族志，扩范畴但偏经验"),
    ("77街的神龛", "薛茗", "contemporary", 7.0, "人类学博物馆研究"),
]

POOL_RATIOS = {"classic": 0.70, "contemporary": 0.25, "crossdomain": 0.05}


def pick(seed: int | None = None) -> tuple[str, str, float, str]:
    """按 pool 比例 + 评分平方加权抽 1 本。"""
    rng = random.Random(seed)
    # crossdomain 池暂空，把它的概率重分到 classic + contemporary（按它们原比例）
    classic_p = POOL_RATIOS["classic"] / (POOL_RATIOS["classic"] + POOL_RATIOS["contemporary"])
    pool = "classic" if rng.random() < classic_p else "contemporary"
    cands = [b for b in SCORED if b[2] == pool]
    weights = [b[3] ** 2 for b in cands]
    chosen = rng.choices(cands, weights=weights, k=1)[0]
    return chosen[0], chosen[1], chosen[3], chosen[4]


if __name__ == "__main__":
    import sys
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else None
    name, author, score, why = pick(seed)
    print(f"\n📖 今日选书\n")
    print(f"  书名: {name}")
    print(f"  作者: {author}")
    print(f"  评分: {score}/10")
    print(f"  入选理由: {why}\n")
