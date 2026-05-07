#!/usr/bin/env python3
"""
会议摘要脚本：调用本地 Ollama 对逐字稿进行去口水词 + 整理 + 摘要
用法：python summarize.py <逐字稿.txt> [--model qwen2.5:32b]
"""
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

CLEAN_PROMPT = """你是一位专业会议记录员。请对以下逐字稿进行清洗：
1. 删除所有口水词：嗯、啊、那个、就是说、然后然后、对对对、好好好、这个这个 等
2. 修正明显的语音识别错误（结合上下文判断）
3. 适当断句，让阅读更流畅
4. 严格保留每个说话人的标注（如【SPEAKER_00】），不要合并不同人的发言
5. 不要增加任何原文没有的内容

原始逐字稿：
---
{transcript}
---

输出格式：直接输出清洗后的逐字稿，不要添加说明文字。"""

SUMMARY_PROMPT = """你是一位专业会议助理。请根据以下会议逐字稿，生成一份结构化的会议纪要。

逐字稿：
---
{transcript}
---

请按以下格式输出：

## 会议概述
（1-2句话概括本次会议主题和参与方）

## 核心议题
（3-6条，每条一行，用 - 开头）

## 关键决策与结论
（已达成共识的决定，用 ✅ 开头）

## 待办事项
（格式：- 【负责人】事项内容，无法判断负责人则写【待定】）

## 分歧与待讨论事项
（尚未达成一致的问题，用 ⚠️ 开头，如无则写"无"）

## 下次跟进建议
（可选，如有明确后续计划）"""

def call_ollama(prompt, model):
    """调用 Ollama 本地模型"""
    result = subprocess.run(
        ["ollama", "run", model],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=300
    )
    if result.returncode != 0:
        raise RuntimeError(f"Ollama 调用失败：{result.stderr}")
    return result.stdout.strip()

def check_model(model):
    """检查模型是否已下载"""
    result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    models = [line.split()[0] for line in result.stdout.strip().split("\n")[1:] if line.strip()]
    available = [m.split(":")[0] for m in models]
    req = model.split(":")[0]
    return req in available or model in models

def main():
    parser = argparse.ArgumentParser(description="会议逐字稿整理与摘要")
    parser.add_argument("transcript", help="逐字稿文件路径")
    parser.add_argument("--model", default="qwen2.5:14b", help="Ollama 模型名称")
    parser.add_argument("--skip-clean", action="store_true", help="跳过去口水词步骤")
    parser.add_argument("--output-dir", default=str(Path.home() / "meeting-ai/output"))
    args = parser.parse_args()

    transcript_path = Path(args.transcript).expanduser().resolve()
    if not transcript_path.exists():
        print(f"错误：文件不存在：{transcript_path}", file=sys.stderr)
        sys.exit(1)

    # 自动降级：如果 32b 没下载完，用 14b
    model = args.model
    if not check_model(model):
        fallback = "qwen2.5-coder:14b"
        print(f"⚠️  模型 {model} 未就绪，使用 {fallback} 作为替代")
        model = fallback

    print(f"使用模型：{model}", flush=True)

    transcript = transcript_path.read_text(encoding="utf-8")
    output_dir = Path(args.output_dir)

    # 智能定位输出位置：
    # - 如果输入文件已经在某个会议子文件夹里 → 输出到同一文件夹
    # - 否则在 output 下创建新的会议文件夹
    if transcript_path.parent != output_dir and transcript_path.parent.parent == output_dir:
        # 已经在子文件夹里
        meeting_dir = transcript_path.parent
    else:
        # 兼容旧的扁平结构：建一个新文件夹
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        meeting_dir = output_dir / f"{transcript_path.stem}_{timestamp}"
        meeting_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: 去口水词
    if args.skip_clean:
        clean_text = transcript
        print("[跳过] 去口水词", flush=True)
    else:
        print("[1/2] 去口水词 + 修正转录错误...", flush=True)
        clean_text = call_ollama(CLEAN_PROMPT.format(transcript=transcript), model)
        clean_path = meeting_dir / "2-清理版.txt"
        clean_path.write_text(clean_text, encoding="utf-8")
        print(f"      清洗版本已保存：{clean_path}")

    # Step 2: 生成摘要
    print("[2/2] 生成会议纪要...", flush=True)
    summary = call_ollama(SUMMARY_PROMPT.format(transcript=clean_text), model)
    summary_path = meeting_dir / "3-纪要.md"
    summary_path.write_text(
        f"# 会议纪要\n**来源文件：** {transcript_path.name}  \n**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n**使用模型：** {model}\n\n---\n\n{summary}\n",
        encoding="utf-8"
    )

    print(f"\n完成！")
    print(f"  会议纪要：{summary_path}")

if __name__ == "__main__":
    main()
