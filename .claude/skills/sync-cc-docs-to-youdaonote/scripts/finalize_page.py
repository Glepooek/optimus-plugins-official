#!/usr/bin/env python3
"""Step 4 的确定性收尾环节：post_process → verify → verify_quality → 上传有道云笔记
→ 更新 folder-map.json → 清理临时文件。

翻译本身（Read raw → LLM 翻译 → Write 译文）不在这个脚本的职责内——那一步需要 agent
的语言理解能力，没法脚本化。这个脚本只负责"译文已经产出之后"那条纯机械、最容易被
agent 漏掉某一步（尤其是清理临时文件、更新 folder-map.json）的收尾链路。

任何一步失败都会原样退出非零码，不清理 raw 文件、不更新 folder-map.json，方便排查；
是否继续处理下一篇由调用方（SKILL.md 编排）决定，本脚本只对"这一篇"负责。
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from resolve_category import MAP_PATH, REPO_ROOT, load_folder_map, save_folder_map, youdaonote_list

WEB_TO_MD_SCRIPTS = REPO_ROOT / "plugins" / "optimus-office-plugin" / "skills" / "web-to-markdown" / "scripts"
POST_PROCESS = WEB_TO_MD_SCRIPTS / "post_process.py"
VERIFY = WEB_TO_MD_SCRIPTS / "verify.py"
VERIFY_QUALITY = WEB_TO_MD_SCRIPTS / "verify_quality.py"

TITLE_RE = re.compile(r'^#\s+(.+?)\s*$')


class FinalizeError(Exception):
    """携带面向用户的错误信息，由 CLI 层捕获后打印到 stderr 并以对应 exit code 退出。"""
    def __init__(self, message, exit_code=1):
        super().__init__(message)
        self.exit_code = exit_code


def extract_title(translated_path):
    with open(translated_path, encoding="utf-8") as f:
        for line in f:
            m = TITLE_RE.match(line)
            if m:
                return m.group(1)
    return None


def run_post_process(translated_path, base_url):
    cmd = [sys.executable, str(POST_PROCESS), str(translated_path)]
    if base_url:
        cmd += ["--base-url", base_url]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")


def run_verify(raw_path, translated_path):
    return subprocess.run(
        [sys.executable, str(VERIFY), str(raw_path), str(translated_path)],
        capture_output=True, text=True, encoding="utf-8",
    )


def run_verify_quality(raw_path, translated_path, base_url):
    cmd = [sys.executable, str(VERIFY_QUALITY), str(raw_path), str(translated_path)]
    if base_url:
        cmd += ["--base-url", base_url]
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")


def youdaonote_save(title, content_file, parent_id):
    payload = json.dumps(
        {"title": title, "type": "md", "contentFile": str(content_file), "parentId": parent_id},
        ensure_ascii=False,
    )
    return subprocess.run(
        ["youdaonote", "-s", "ydn", "save", "--json"],
        input=payload, capture_output=True, text=True, encoding="utf-8",
    )


def _run_step(fn, step_name, *args):
    result = fn(*args)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise FinalizeError(f"{step_name} 未通过（exit {result.returncode}）：{detail}")
    return result


def finalize(
    raw_path, translated_path, group_id, tab_zh, group_en, url,
    base_url=None, title=None,
    post_process_fn=run_post_process, verify_fn=run_verify,
    verify_quality_fn=run_verify_quality, list_fn=youdaonote_list,
    save_fn=youdaonote_save, load_map_fn=load_folder_map,
    save_map_fn=save_folder_map, map_path=MAP_PATH,
    delete_raw=True,
):
    """核心编排逻辑，所有副作用点都通过参数注入，便于测试。
    成功返回 summary dict；失败抛出 FinalizeError，raw 文件和 folder-map.json 保持不动。
    """
    raw_path = Path(raw_path)
    translated_path = Path(translated_path)
    if not raw_path.is_file():
        raise FinalizeError(f"--raw 文件不存在：{raw_path}", exit_code=2)
    if not translated_path.is_file():
        raise FinalizeError(f"--translated 文件不存在：{translated_path}", exit_code=2)

    _run_step(post_process_fn, "post_process.py 后处理", translated_path, base_url)
    _run_step(verify_fn, "verify.py 结构数量核对", raw_path, translated_path)
    _run_step(verify_quality_fn, "verify_quality.py 内容质量核对", raw_path, translated_path, base_url)

    resolved_title = title or extract_title(translated_path)
    if not resolved_title:
        raise FinalizeError("未指定 --title，且未能从译文首行提取到 # 标题")

    try:
        before_ids = {entry_id for _, entry_id, _ in list_fn(group_id)}
    except subprocess.CalledProcessError as e:
        raise FinalizeError(f"上传前拉取目录列表失败：{e.stderr}")

    save_result = save_fn(resolved_title, translated_path, group_id)
    if save_result.returncode != 0:
        raise FinalizeError(f"youdaonote save 失败：{save_result.stderr}")

    try:
        after_ids = {entry_id for _, entry_id, _ in list_fn(group_id)}
    except subprocess.CalledProcessError as e:
        raise FinalizeError(f"上传后拉取目录列表失败，无法确认 fileId：{e.stderr}")

    new_ids = after_ids - before_ids
    if len(new_ids) == 0:
        raise FinalizeError("save 后未在目标目录发现新增笔记，可能上传失败")
    if len(new_ids) > 1:
        raise FinalizeError(
            f"目标目录同时新增了 {len(new_ids)} 篇笔记，无法唯一确定本次上传的 fileId，"
            f"需人工核实：{sorted(new_ids)}"
        )
    file_id = next(iter(new_ids))

    folder_map = load_map_fn(map_path)
    tab_entry = folder_map.setdefault("tabs", {}).setdefault(tab_zh, {"groups": {}})
    group_entry = tab_entry.setdefault("groups", {}).setdefault(group_en, {"pages": {}})
    group_entry.setdefault("pages", {})[url] = {"title": resolved_title, "fileId": file_id}
    save_map_fn(map_path, folder_map)

    if delete_raw:
        raw_path.unlink()

    return {
        "title": resolved_title, "fileId": file_id, "url": url,
        "raw_cleaned_up": delete_raw, "folder_map_updated": True,
    }


def main():
    parser = argparse.ArgumentParser(prog="finalize_page.py")
    parser.add_argument("--raw", required=True, help="抓取到的原文临时文件路径")
    parser.add_argument("--translated", required=True, help="翻译后的译文文件路径")
    parser.add_argument("--group-id", required=True, help="目标有道文件夹 ID")
    parser.add_argument("--tab-zh", required=True, help="Tab 中文名，用于定位 folder-map.json")
    parser.add_argument("--group-en", required=True, help="英文分组名，用于定位 folder-map.json")
    parser.add_argument("--url", required=True, help="站点相对 URL，作为 folder-map.json 里 pages 的 key")
    parser.add_argument("--base-url", default=None, help="站内相对链接前缀，如 https://code.claude.com/docs")
    parser.add_argument("--title", default=None, help="笔记标题，不传则从译文首行 # 标题提取")
    args = parser.parse_args()

    try:
        summary = finalize(
            args.raw, args.translated, args.group_id, args.tab_zh, args.group_en, args.url,
            base_url=args.base_url, title=args.title,
        )
    except FinalizeError as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(e.exit_code)

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
