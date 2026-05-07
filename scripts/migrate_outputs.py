#!/usr/bin/env python3
"""
一次性迁移脚本：把扁平的 output/ 文件按会议归类到子文件夹
旧：output/xxx.txt + xxx.srt + xxx_clean_*.txt + xxx_summary_*.md
新：output/xxx_时间戳/1-逐字稿.txt + 1-字幕.srt + 2-清理版.txt + 3-纪要.md
"""
import re
import shutil
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path.home() / "meeting-ai" / "output"

def main():
    files = [f for f in OUTPUT_DIR.iterdir() if f.is_file()]
    if not files:
        print("没有需要整理的文件")
        return

    # 按会议（基础名 + 时间戳）分组
    # 格式：xxx_20260507_020042.txt 或 xxx_20260507_020042_clean_20260507_021903.txt
    groups = {}

    for f in files:
        name = f.name
        # 找出第一个时间戳部分作为会议标识
        # 匹配 _YYYYMMDD_HHMMSS 模式
        m = re.match(r"^(.+?)_(\d{8}_\d{6})", name)
        if not m:
            continue
        meeting_key = f"{m.group(1)}_{m.group(2)}"
        groups.setdefault(meeting_key, []).append(f)

    print(f"找到 {len(groups)} 个会议，共 {sum(len(v) for v in groups.values())} 个文件\n")

    for meeting_key, file_list in groups.items():
        meeting_dir = OUTPUT_DIR / meeting_key
        meeting_dir.mkdir(exist_ok=True)
        print(f"📁 {meeting_key}/")

        for f in sorted(file_list):
            name = f.name
            # 判断文件类型，重命名
            if "_summary_" in name and name.endswith(".md"):
                new_name = "3-纪要.md"
            elif "_clean_" in name and name.endswith(".txt"):
                new_name = "2-清理版.txt"
            elif name.endswith(".srt"):
                new_name = "1-字幕.srt"
            elif name.endswith(".txt"):
                new_name = "1-逐字稿.txt"
            elif name.endswith(".mp3"):
                new_name = "4-朗读.mp3"
            else:
                new_name = name  # 不动

            target = meeting_dir / new_name
            if target.exists():
                # 同名文件存在（多次跑产生），加数字后缀
                stem, ext = target.stem, target.suffix
                i = 2
                while (meeting_dir / f"{stem}_{i}{ext}").exists():
                    i += 1
                target = meeting_dir / f"{stem}_{i}{ext}"

            shutil.move(str(f), str(target))
            print(f"   {name}  →  {new_name}")
        print()

    print(f"✅ 完成！现在 output/ 下有 {len(groups)} 个会议文件夹，每个里面有清晰的 1-逐字稿/2-清理版/3-纪要")

if __name__ == "__main__":
    main()
