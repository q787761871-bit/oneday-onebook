#!/usr/bin/env python3
"""OpenClaw-native onebook daily runner.

This runner keeps cron deterministic: shell prepares data, OpenClaw model
inference is one bounded local call with a non-Codex fallback chain, and all
artifacts are validated before stdout is considered deliverable.
"""

from __future__ import annotations

import argparse
import errno
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


HISTORY_REL = Path("01 你的项目/一天一本书/_推过的书.md")
PRIVATE_DAILY_REL = Path("02 你的阅读/笔记/_dailybook")
PAGES_ROOT = "https://q787761871-bit.github.io/oneday-onebook"


@dataclass
class Paths:
    project_dir: Path
    private_root: Path
    run_dir: Path
    final_file: Path
    prompt_file: Path

    @property
    def history_path(self) -> Path:
        return self.private_root / HISTORY_REL

    @property
    def private_daily_dir(self) -> Path:
        return self.private_root / PRIVATE_DAILY_REL


def log(message: str) -> None:
    print(f"[onebook-openclaw] {message}", file=sys.stderr)


def fail(message: str) -> None:
    log(f"ERROR: {message}")
    raise SystemExit(1)


def run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    timeout: int = 120,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    log("$ " + " ".join(cmd))
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        env=env,
    )


def materialize(paths: list[Path]) -> None:
    brctl = shutil.which("brctl") or "/usr/bin/brctl"

    def download(path: Path) -> None:
        if Path(brctl).exists():
            subprocess.run([brctl, "download", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def verify(path: Path) -> str | None:
        # iCloud/Document providers can briefly return EDEADLK while a cron
        # process opens a just-materialized file. Treat that as transient.
        transient = {errno.EDEADLK, errno.EBUSY, errno.ETIMEDOUT}
        last_error: OSError | None = None
        for attempt in range(1, 9):
            if attempt > 1:
                time.sleep(min(0.25 * attempt, 1.5))
                download(path)
            try:
                if path.is_dir():
                    path.stat()
                    return None
                if path.is_file():
                    path.read_bytes()
                    return None
                return None
            except OSError as exc:
                last_error = exc
                if exc.errno not in transient:
                    break
        return f"{path}: {last_error}"

    if Path(brctl).exists():
        for path in paths:
            download(path)

    unreadable: list[str] = []
    for path in paths:
        error = verify(path)
        if error:
            unreadable.append(error)
    if unreadable:
        fail("required file is not readable after materialization: " + "; ".join(unreadable))


def normalize_name(name: str) -> str:
    return re.split(r"[:：]", name or "")[0].strip()


def safe_filename(value: str) -> str:
    value = re.sub(r"[\\/:*?\"<>|#\[\]]+", "", value).strip()
    value = re.sub(r"\s+", "", value)
    return value[:80] or "untitled"


def yaml_quote(value: Any) -> str:
    return json.dumps("" if value is None else str(value), ensure_ascii=False)


def strip_top_h1(markdown: str) -> str:
    lines = markdown.strip().splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    if lines and lines[0].lstrip().startswith("# "):
        lines.pop(0)
    return "\n".join(lines).strip() + "\n"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def history_names(history_path: Path) -> set[str]:
    if not history_path.exists():
        return set()
    names: set[str] = set()
    for line in history_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip().startswith("|") or "---" in line:
            continue
        cells = [c.strip() for c in line.split("|")]
        if len(cells) >= 4 and cells[2] and cells[2] != "书名":
            names.add(normalize_name(cells[2]))
    return names


def score_book(book: dict[str, Any]) -> dict[str, Any]:
    name = book.get("name", "")
    source = book.get("source", "")
    oneliner = book.get("oneliner") or ""

    veto = [
        ("教材", "教材/课程类"),
        ("教程", "教程类"),
        ("导读", "导读类"),
        ("讲义", "讲义类"),
        ("读本", "读本类"),
        ("指南", "指南类"),
        ("十五讲", "综述讲座类"),
        ("通史", "通史类"),
        ("简史", "简史/科普类"),
        ("入门", "入门类"),
        ("概论", "概论类"),
        ("原理", "教材类"),
        ("基础", "基础教材类"),
        ("回忆录", "回忆录类"),
    ]
    for needle, reason in veto:
        if needle in name:
            return enrich_score(book, 4, f"强否决: {reason}")

    if "小说" in name or "诗集" in name or "传记" in name:
        return enrich_score(book, 5, "强否决: 文学/传记类")

    high = [
        ("利维坦", 9, "主权/社会契约问题域有强生成性"),
        ("阿伦特", 8, "政治行动与公共性问题域"),
        ("罗尔斯", 8, "正义论传统的核心问题域"),
        ("拉康", 8, "主体/欲望结构的高密度问题域"),
        ("黑格尔", 8, "精神/历史结构的高密度问题域"),
        ("维特根斯坦", 8, "语言与世界关系的核心问题域"),
        ("保守主义", 7, "政治观念谱系"),
        ("自由主义", 7, "政治观念谱系"),
        ("历史主义", 7, "历史解释的方法论问题"),
        ("深描", 8, "解释人类学核心方法"),
        ("人类学", 7, "社会事实与田野机理"),
        ("现象学", 8, "经验结构的原创方法"),
        ("资本", 8, "现代社会生成机制"),
        ("科学革命", 8, "范式与知识变迁"),
    ]
    haystack = f"{name}\n{oneliner}"
    for needle, score, reason in high:
        if needle in haystack:
            return enrich_score(book, score, reason)

    if "tag:哲学" in source or "tag:政治哲学" in source:
        return enrich_score(book, 7, "哲学/政治哲学类，思想密度较高")
    if "tag:社会学" in source or "tag:人类学" in source:
        return enrich_score(book, 7, "社会学/人类学类，有理论或田野价值")
    if "tag:文学批评" in source:
        return enrich_score(book, 7, "文学批评类，适合做范畴与方法提炼")
    if "tag:历史" in source and any(x in name for x in ("观念", "思想", "文化", "权利", "帝国")):
        return enrich_score(book, 7, "历史类但指向观念/制度机理")

    rating = book.get("rating") or 0
    votes = book.get("votes") or 0
    if rating >= 9.2 and votes >= 100:
        return enrich_score(book, 7, "高评分且有一定评价基数")
    return enrich_score(book, 6, "学术著作，但原创机理标记不强")


def enrich_score(book: dict[str, Any], score: int, reason: str) -> dict[str, Any]:
    keep = {
        "subject_id": book.get("subject_id"),
        "name": book.get("name"),
        "author": book.get("author") or "",
        "publisher": book.get("publisher") or "",
        "year": book.get("year"),
        "rating": book.get("rating"),
        "votes": book.get("votes") or 0,
        "oneliner": book.get("oneliner") or "",
        "source": book.get("source") or "",
        "pool": book.get("pool") or "classic",
        "score": score,
        "reason": reason,
    }
    return keep


def prepare_book(paths: Paths, run_date: str) -> dict[str, Any]:
    materialize(
        [
            paths.project_dir / "prompts",
            paths.project_dir / "scripts/filter_and_classify.py",
            paths.project_dir / "scripts/pick_today.py",
            paths.project_dir / "data",
            paths.history_path,
        ]
    )

    if os.environ.get("ONEBOOK_WRITE_ARTIFACTS", "1") == "0" and os.environ.get("ONEBOOK_REFRESH_CANDIDATES") != "1":
        log("ONEBOOK_WRITE_ARTIFACTS=0, not refreshing project candidates")
        (paths.run_dir / "filter.stdout").write_text("", encoding="utf-8")
        (paths.run_dir / "filter.stderr").write_text("candidate refresh skipped in no-write mode\n", encoding="utf-8")
    else:
        result = run(["/usr/bin/python3", "scripts/filter_and_classify.py"], cwd=paths.project_dir, timeout=180)
        (paths.run_dir / "filter.stdout").write_text(result.stdout, encoding="utf-8")
        (paths.run_dir / "filter.stderr").write_text(result.stderr, encoding="utf-8")
        if result.returncode != 0:
            fail(f"filter_and_classify.py failed: {result.stderr.strip()}")

    candidate_path = paths.project_dir / "data" / f"candidates-{run_date}.json"
    if not candidate_path.exists():
        candidates = sorted((paths.project_dir / "data").glob("candidates-*.json"), key=lambda p: p.stat().st_mtime)
        if not candidates:
            fail("no candidates file produced")
        candidate_path = candidates[-1]

    candidates = load_json(candidate_path)
    pushed = history_names(paths.history_path)
    prefiltered = [
        b
        for b in candidates
        if "tag:" in (b.get("source") or "")
        and (b.get("rating") or 0) >= 8.8
        and (b.get("votes") or 0) >= 30
        and normalize_name(b.get("name") or "") not in pushed
    ]
    if not prefiltered:
        fail("no tag-sourced candidates after prefilter")

    scored = [score_book(b) for b in prefiltered]
    qualified = [b for b in scored if (b.get("score") or 0) >= 7]
    if not qualified:
        fail("no qualified scored candidates")

    # Deterministic but not always the single highest-vote item: pick from the
    # top band using a date seed so reruns are idempotent for the day.
    top_score = max(int(b["score"]) for b in qualified)
    top_band = [b for b in qualified if int(b["score"]) >= max(7, top_score - 1)]
    top_band.sort(key=lambda b: (int(b.get("score") or 0), int(b.get("votes") or 0), b.get("name") or ""), reverse=True)
    rng = random.Random(run_date)
    book = rng.choice(top_band[: min(12, len(top_band))])

    if os.environ.get("ONEBOOK_WRITE_ARTIFACTS", "1") != "0":
        write_json(paths.project_dir / "data" / f"scored-{run_date}.json", scored)
        write_json(paths.project_dir / "data" / "today.json", book)
    write_json(paths.run_dir / "today.json", book)
    log(f"selected {book.get('name')} score={book.get('score')} reason={book.get('reason')}")
    return book


def public_slug(book: dict[str, Any]) -> str:
    sid = str(book.get("subject_id") or "").strip()
    if sid:
        return f"book-{sid}"
    ascii_name = re.sub(r"[^a-z0-9]+", "-", (book.get("name") or "book").lower()).strip("-")
    return ascii_name or "book"


def public_url(run_date: str, slug: str) -> str:
    yyyy, mm, dd = run_date.split("-")
    return f"{PAGES_ROOT}/{yyyy}/{mm}/{dd}/{slug}/"


def fetch_reviews(book: dict[str, Any], run_dir: Path) -> str:
    sid = str(book.get("subject_id") or "").strip()
    if not sid:
        return ""
    url = f"https://r.jina.ai/https://book.douban.com/subject/{sid}/reviews"
    req = urllib.request.Request(url, headers={"User-Agent": "oneday-onebook/0.6"})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            text = resp.read(24000).decode("utf-8", errors="ignore")
    except Exception as exc:
        text = f"未拉到豆瓣长评：{exc}"
    (run_dir / "reviews.md").write_text(text, encoding="utf-8")
    return text[:8000]


def build_prompt(paths: Paths, book: dict[str, Any], run_date: str, final_url: str, reviews: str) -> str:
    engine_summary = """
写作框架：
1. 暗门：指出作者真正回答的灵魂之问，必须落到历史处境和对话对象。
2. 三根力：把全书降到 3 个可生成现象的机制，每根力都包含反直觉案例、必然性、推到极端的后果。
3. 新增范畴：提炼 4 个不是书中现成术语的新范畴，并给日常用法。
4. 他者之眼：只基于真实评论材料；如果材料不足，明确写“未拉到足够立场分散的评论”，不要模拟评论者。
5. 一句话带走：30-50 字。
"""
    prompt = f"""
你是“一天一本书”的 OpenClaw 原生日报写作器。只输出一个 JSON 对象，不要 Markdown 代码块，不要解释。

今日日期：{run_date}
最终 URL：{final_url}

今日书籍 JSON：
{json.dumps(book, ensure_ascii=False, indent=2)}

{engine_summary}

真实评论材料（可能为空或很脏，只能据此使用，不要伪造）：
{reviews}

输出 JSON schema：
{{
  "subtitle": "灵魂之问，一句话，35 字以内",
  "tags": ["2-5 个短标签"],
  "post_markdown": "正文 Markdown，不要 frontmatter，不要 H1。控制在 1400-2200 个中文字符。必须包含小标题：暗门、三根力、新增范畴、他者之眼、一句话带走。",
  "final_text": "严格按格式：📖 今日推荐\\n\\n《书名》 — 作者 · 出版年\\n灵魂之问一句话\\n\\n→ {final_url}"
}}

硬约束：
- final_text 必须包含《{book.get('name') or ''}》和 {final_url}
- 不要输出进度、调试日志或外层包装。
- 如果作者或年份为空，用“佚名”或“年份不详”，不要编造。
""".strip()
    paths.prompt_file.write_text(prompt + "\n", encoding="utf-8")
    return prompt


def first_json_object(text: str) -> Any:
    decoder = json.JSONDecoder()
    for idx, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            obj, _ = decoder.raw_decode(text[idx:])
            return obj
        except json.JSONDecodeError:
            continue
    raise ValueError("no JSON object found")


def model_text_from_output(stdout: str) -> str:
    outer = first_json_object(stdout)
    outputs = outer.get("outputs") or []
    if not outputs or not outputs[0].get("text"):
        raise ValueError("OpenClaw model output has no text")
    return outputs[0]["text"]


def generation_from_text(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    data = first_json_object(cleaned)
    if not isinstance(data, dict):
        raise ValueError("model generation is not an object")
    for key in ("subtitle", "post_markdown", "final_text"):
        if not str(data.get(key) or "").strip():
            raise ValueError(f"model generation missing {key}")
    return data


def run_model(prompt: str, model_chain: str, openclaw_bin: str, run_dir: Path) -> tuple[dict[str, Any], str]:
    if os.environ.get("ONEBOOK_SKIP_MODEL") == "1":
        data = {
            "subtitle": "一套思想怎样改变我们看见问题的方式？",
            "tags": ["自动测试", "机理还原"],
            "post_markdown": "## 暗门\n\n这是一份测试模式正文，用于验证 runner 的文件写入、最终消息校验和 cron wrapper，不代表正式日报内容。它模拟正式文章的结构：先把一本书压缩成一个核心问题，再把问题拆成能解释现象的机制链，最后生成可投递的短消息。\n\n## 三根力\n\n第一根力是把问题压到机制层：不问作者说了什么，而问这套思想为什么会在当时出现。第二根力是让概念能够反向解释现象：一个概念必须能回到生活现场，解释我们平时看不清的秩序。第三根力是把结论推回日常判断：读者看完后，应该能多一把识别问题的切刀。\n\n## 新增范畴\n\n- **机制灯**：用来照亮事件背后的生成规则。日常用法：判断一个现象是否只是表象。\n- **概念回声**：一个理论离开原书以后，还能在别的场景里反复响起。日常用法：检验一本书是否真的改变了观察方式。\n\n## 他者之眼\n\n测试模式未拉取真实评论，因此这里只说明验证边界：正式运行必须基于真实评论材料，不得模拟评论者立场，也不能把空材料写成热闹争论。\n\n## 一句话带走\n\n好的自动化先收窄边界，再谈自由发挥。",
            "final_text": "",
        }
        return data, "skip-model"

    timeout = int(os.environ.get("ONEBOOK_MODEL_TIMEOUT_SECONDS", "300"))
    retries = int(os.environ.get("ONEBOOK_MODEL_RETRIES", "2"))
    models = [m for m in model_chain.split() if m.strip()]
    errors: list[str] = []
    for model in models:
        for attempt in range(1, retries + 1):
            out_path = run_dir / f"model-{model.replace('/', '_')}-attempt-{attempt}.json"
            cmd = [
                openclaw_bin,
                "--log-level",
                "error",
                "infer",
                "model",
                "run",
                "--local",
                "--model",
                model,
                "--thinking",
                "off",
                "--prompt",
                prompt,
                "--json",
            ]
            try:
                proc = run(cmd, timeout=timeout)
            except subprocess.TimeoutExpired:
                errors.append(f"{model} attempt {attempt}: subprocess timeout after {timeout}s")
                continue
            out_path.write_text(proc.stdout + "\n--- STDERR ---\n" + proc.stderr, encoding="utf-8")
            if proc.returncode != 0:
                errors.append(f"{model} attempt {attempt}: exit {proc.returncode}: {proc.stderr.strip() or proc.stdout[-500:]}")
                continue
            try:
                text = model_text_from_output(proc.stdout)
                (run_dir / f"model-{model.replace('/', '_')}-attempt-{attempt}.text").write_text(text, encoding="utf-8")
                data = generation_from_text(text)
                return data, model
            except Exception as exc:
                errors.append(f"{model} attempt {attempt}: parse failed: {exc}")
    fail("all OpenClaw model attempts failed: " + " | ".join(errors[-6:]))


def render(paths: Paths, book: dict[str, Any], data: dict[str, Any], run_date: str, model_used: str) -> str:
    title = str(book.get("name") or "未命名").strip()
    author = str(book.get("author") or "佚名").strip() or "佚名"
    year = str(book.get("year") or "年份不详").strip()
    slug = public_slug(book)
    url = public_url(run_date, slug)

    subtitle = str(data.get("subtitle") or book.get("oneliner") or "一套思想怎样改变我们看见问题的方式？").strip()
    tags = data.get("tags") if isinstance(data.get("tags"), list) else []
    tags = [str(t).strip() for t in tags if str(t).strip()][:6] or ["一天一本书"]

    final_text = str(data.get("final_text") or "").strip()
    if title not in final_text or url not in final_text:
        final_text = f"📖 今日推荐\n\n《{title}》 — {author} · {year}\n{subtitle}\n\n→ {url}"
    if len(final_text) > 500:
        final_text = f"📖 今日推荐\n\n《{title}》 — {author} · {year}\n{subtitle[:80]}\n\n→ {url}"

    post_markdown = strip_top_h1(str(data.get("post_markdown") or ""))
    if len(post_markdown.strip()) < 300:
        fail("generated post_markdown is too short")

    private_name = f"{run_date}_{safe_filename(title)}.md"
    private_path = paths.private_daily_dir / private_name
    public_path = paths.project_dir / "_posts" / f"{run_date}-{slug}.md"
    paths.private_daily_dir.mkdir(parents=True, exist_ok=True)
    public_path.parent.mkdir(parents=True, exist_ok=True)

    tag_yaml = "\n".join(f"  - {yaml_quote(t)}" for t in tags)
    private_body = f"""---
title: {yaml_quote(title)}
author: {yaml_quote(author)}
year: {yaml_quote(year)}
date: {run_date}
source: 一天一本书 · OpenClaw runner
version: v0.6
model: {yaml_quote(model_used)}
tags:
{tag_yaml}
---

# {title}

{post_markdown}
"""
    public_body = f"""---
layout: post
title: {yaml_quote(title)}
subtitle: {yaml_quote(subtitle)}
author_name: {yaml_quote(author)}
year: {yaml_quote(year)}
date: {run_date}
slug: {yaml_quote(slug)}
tags:
{tag_yaml}
---

{post_markdown}
"""

    if os.environ.get("ONEBOOK_WRITE_ARTIFACTS", "1") == "0":
        private_path = paths.run_dir / private_name
        public_path = paths.run_dir / f"{run_date}-{slug}.md"

    private_path.write_text(private_body, encoding="utf-8")
    public_path.write_text(public_body, encoding="utf-8")
    paths.final_file.write_text(final_text + "\n", encoding="utf-8")

    publish_warning: str | None = None
    if os.environ.get("ONEBOOK_WRITE_ARTIFACTS", "1") != "0":
        update_history(paths.history_path, run_date, title, author, private_path)
        publish_warning = publish_public_post(paths.project_dir, public_path, run_date, title, paths.run_dir)

    write_json(
        paths.run_dir / "artifact.json",
        {
            "date": run_date,
            "title": title,
            "author": author,
            "year": year,
            "slug": slug,
            "url": url,
            "model": model_used,
            "privatePath": str(private_path),
            "publicPath": str(public_path),
            "finalPath": str(paths.final_file),
            "publishWarning": publish_warning,
        },
    )
    return final_text


def update_history(history_path: Path, run_date: str, title: str, author: str, private_path: Path) -> None:
    rel = private_path
    try:
        rel = private_path.relative_to(history_path.parents[2])
    except Exception:
        pass
    row = f"| {run_date} | {title} | {author} | v0.6 OpenClaw 自动 | `{rel}` |"
    text = history_path.read_text(encoding="utf-8", errors="replace") if history_path.exists() else ""
    if f"| {run_date} | {title} |" in text:
        return
    if text and not text.endswith("\n"):
        text += "\n"
    history_path.write_text(text + row + "\n", encoding="utf-8")


def publish_public_post(project_dir: Path, public_path: Path, run_date: str, title: str, run_dir: Path) -> str | None:
    def warn(message: str) -> str:
        log(f"WARN: public publish skipped: {message}")
        return message

    if os.environ.get("ONEBOOK_SKIP_PUBLISH") == "1":
        log("ONEBOOK_SKIP_PUBLISH=1, not committing/pushing public repo")
        return None
    last_error: str | None = None
    for attempt in range(1, 4):
        if attempt > 1:
            log(f"publish attempt {attempt}/3 after: {last_error}")
            time.sleep(10)
        last_error = publish_public_post_once(project_dir, public_path, run_date, title, run_dir)
        if last_error is None:
            return None
    return warn(last_error)


def publish_public_post_once(project_dir: Path, public_path: Path, run_date: str, title: str, run_dir: Path) -> str | None:
    git_index = run_dir / "git-index"
    git_index.unlink(missing_ok=True)
    git_env = {**os.environ, "GIT_INDEX_FILE": str(git_index)}
    read_tree = run(["git", "read-tree", "HEAD"], cwd=project_dir, timeout=120, env=git_env)
    if read_tree.returncode != 0:
        return f"git read-tree failed: {read_tree.stderr.strip() or read_tree.stdout.strip()}"

    # 整个 _posts 目录一起 add，前一天发布失败遗留的未提交文章会被自动补上。
    # data/ 已 gitignore 但 today.json 仍被跟踪——pathspec 落在 ignored 目录下时
    # git add 即使成功暂存也会 exit 1，必须用 -f 才能拿到干净的退出码。
    add_paths = [str(project_dir / "_posts")]
    today_json = project_dir / "data" / "today.json"
    if today_json.exists():
        add_paths.append(str(today_json))
    add = run(["git", "add", "-f", "--", *add_paths], cwd=project_dir, timeout=120, env=git_env)
    if add.returncode != 0:
        return f"git add failed: {add.stderr.strip()}"
    diff = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=str(project_dir), env=git_env)
    if diff.returncode == 0:
        log("no public repo changes to commit")
        return None
    if diff.returncode != 1:
        return f"git diff --cached failed with exit code {diff.returncode}"
    commit = run(["git", "commit", "-m", f"daily: {title} ({run_date})"], cwd=project_dir, timeout=120, env=git_env)
    if commit.returncode != 0:
        return f"git commit failed: {commit.stderr.strip() or commit.stdout.strip()}"
    push = run(["git", "push"], cwd=project_dir, timeout=180, env=git_env)
    if push.returncode != 0:
        return f"git push failed: {push.stderr.strip() or push.stdout.strip()}"
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--private-root", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--final-file", required=True)
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--openclaw-bin", required=True)
    parser.add_argument("--model-chain", required=True)
    args = parser.parse_args()

    paths = Paths(
        project_dir=Path(args.project_dir),
        private_root=Path(args.private_root),
        run_dir=Path(args.run_dir),
        final_file=Path(args.final_file),
        prompt_file=Path(args.prompt_file),
    )
    paths.run_dir.mkdir(parents=True, exist_ok=True)

    book = prepare_book(paths, args.date)
    slug = public_slug(book)
    url = public_url(args.date, slug)
    reviews = fetch_reviews(book, paths.run_dir)
    prompt = build_prompt(paths, book, args.date, url, reviews)
    generation, model_used = run_model(prompt, args.model_chain, args.openclaw_bin, paths.run_dir)
    final = render(paths, book, generation, args.date, model_used)
    print(final)


if __name__ == "__main__":
    start = time.time()
    try:
        main()
    finally:
        log(f"duration={time.time() - start:.1f}s")
