#!/usr/bin/env python3
"""
view_summary.py
读取指定文件夹下所有 .json（或 .with_summary.json）文件，
打印 <文件名, Summary> 列表。
"""

import argparse
import json
from pathlib import Path

try:
    # 推荐装一下 tabulate，输出会更美观；无需也能正常跑
    from tabulate import tabulate
    USE_TABULATE = True
except ImportError:
    USE_TABULATE = False


def collect_summaries(folder: Path) -> list[tuple[str, str]]:
    """遍历目录，返回 (文件名, Summary) 列表；若缺 Summary 字段则跳过"""
    rows = []
    for fp in sorted(folder.glob("*.json")):           # 也可改成 **/*.json 递归
        try:
            with fp.open(encoding="utf-8") as f:
                data = json.load(f)
            summary = data.get("Summary")
            if summary:
                rows.append((fp.name, summary))
        except json.JSONDecodeError as e:
            print(f"⚠️  跳过 {fp.name}: JSON 解析失败 - {e}")
    return rows


def print_rows(rows: list[tuple[str, str]]):
    if not rows:
        print("❌ 未找到包含 Summary 的 JSON 文件")
        return

    if USE_TABULATE:
        # 自动按列对齐，长文本折行
        print(tabulate(rows, headers=["File", "Summary"], tablefmt="pretty", maxcolwidths=[30, 100]))
    else:
        # 简单手动打印
        for fn, smy in rows:
            print(f"{fn}:\n  {smy}\n")


def main():
    parser = argparse.ArgumentParser(description="Display summaries in JSON story files")
    parser.add_argument("dir", nargs="?", default="story", help="目录路径 (默认: story/)")
    args = parser.parse_args()

    folder = Path(args.dir)
    if not folder.is_dir():
        parser.error(f"目录不存在: {folder}")

    rows = collect_summaries(folder)
    print_rows(rows)


if __name__ == "__main__":
    main()
