#!/usr/bin/env python3
"""
会议 AI 一体化控制台
功能：录音 / 转录 / 摘要 / 朗读 / 文件管理
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import threading
import time
import os
import re
import signal
from pathlib import Path
from datetime import datetime

HOME = Path.home()
APP_DIR = HOME / "meeting-ai"
RECORDINGS_DIR = APP_DIR / "recordings"
OUTPUT_DIR = APP_DIR / "output"
SCRIPTS_DIR = APP_DIR / "scripts"
WHISPER_PY = APP_DIR / "whisper-env" / "bin" / "python"
TTS_PY = APP_DIR / "tts-env" / "bin" / "python"

# 修复 GUI 启动时 PATH 不全的问题
os.environ["PATH"] = "/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:" + os.environ.get("PATH", "")

# 找 ffmpeg 的绝对路径
def find_executable(name):
    for prefix in ["/opt/homebrew/bin", "/usr/local/bin", "/usr/bin"]:
        p = Path(prefix) / name
        if p.exists():
            return str(p)
    return name  # fallback

FFMPEG = find_executable("ffmpeg")

for d in (RECORDINGS_DIR, OUTPUT_DIR):
    d.mkdir(parents=True, exist_ok=True)


class MeetingAIDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("🎙️ 会议 AI 控制台")
        self.root.geometry("820x680")
        self.root.configure(bg="#f5f5f7")

        self.recording_proc = None
        self.recording_start = None
        self.recording_file = None
        self.timer_id = None

        self.setup_ui()
        self.refresh_files()

    # ---------- UI ----------

    def setup_ui(self):
        # 标题
        title = tk.Label(self.root, text="🎙️  会议 AI 控制台",
                         font=("PingFang SC", 22, "bold"),
                         bg="#f5f5f7", fg="#1d1d1f")
        title.pack(pady=(20, 5))
        sub = tk.Label(self.root, text="录音 → 转录 → 摘要 → 朗读 · 全本地运行",
                       font=("PingFang SC", 12),
                       bg="#f5f5f7", fg="#6e6e73")
        sub.pack(pady=(0, 20))

        # === 录音区 ===
        rec_frame = tk.LabelFrame(self.root, text="  📼 录音控制  ",
                                   font=("PingFang SC", 13, "bold"),
                                   bg="#ffffff", fg="#1d1d1f",
                                   padx=20, pady=15)
        rec_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.record_btn = tk.Button(rec_frame, text="🎙️  开始录音",
                                     font=("PingFang SC", 16, "bold"),
                                     bg="#ff3b30", fg="white",
                                     activebackground="#ff453a",
                                     activeforeground="white",
                                     relief="flat", borderwidth=0,
                                     padx=30, pady=12,
                                     command=self.toggle_recording)
        self.record_btn.pack(side="left")

        self.timer_label = tk.Label(rec_frame, text="00:00",
                                     font=("Menlo", 28, "bold"),
                                     bg="#ffffff", fg="#1d1d1f")
        self.timer_label.pack(side="left", padx=20)

        self.status_label = tk.Label(rec_frame, text="● 待机",
                                      font=("PingFang SC", 13),
                                      bg="#ffffff", fg="#34c759")
        self.status_label.pack(side="right")

        # === 文件管理区 ===
        files_frame = tk.LabelFrame(self.root, text="  📁 文件管理  ",
                                     font=("PingFang SC", 13, "bold"),
                                     bg="#ffffff", fg="#1d1d1f",
                                     padx=15, pady=12)
        files_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        # tab 切换：录音 / 输出文件
        tabs = ttk.Notebook(files_frame)
        tabs.pack(fill="both", expand=True)

        # 录音文件 tab
        rec_tab = tk.Frame(tabs, bg="#ffffff")
        tabs.add(rec_tab, text="  🎙️ 录音文件  ")
        self.rec_listbox = tk.Listbox(rec_tab, font=("Menlo", 11),
                                       bg="#ffffff", borderwidth=1,
                                       relief="solid", selectmode="single",
                                       highlightthickness=0)
        self.rec_listbox.pack(fill="both", expand=True, side="left")
        rec_scroll = tk.Scrollbar(rec_tab, command=self.rec_listbox.yview)
        rec_scroll.pack(side="right", fill="y")
        self.rec_listbox.config(yscrollcommand=rec_scroll.set)

        # 输出文件 tab
        out_tab = tk.Frame(tabs, bg="#ffffff")
        tabs.add(out_tab, text="  📄 输出文件  ")
        self.out_listbox = tk.Listbox(out_tab, font=("Menlo", 11),
                                       bg="#ffffff", borderwidth=1,
                                       relief="solid", selectmode="single",
                                       highlightthickness=0)
        self.out_listbox.pack(fill="both", expand=True, side="left")
        out_scroll = tk.Scrollbar(out_tab, command=self.out_listbox.yview)
        out_scroll.pack(side="right", fill="y")
        self.out_listbox.config(yscrollcommand=out_scroll.set)

        self.tabs = tabs

        # 操作按钮一排
        btn_row = tk.Frame(files_frame, bg="#ffffff")
        btn_row.pack(fill="x", pady=(10, 0))

        tk.Button(btn_row, text="🔄 刷新", font=("PingFang SC", 11),
                  bg="#e5e5ea", relief="flat", padx=12, pady=6,
                  command=self.refresh_files).pack(side="left", padx=(0, 5))
        tk.Button(btn_row, text="📂 打开目录", font=("PingFang SC", 11),
                  bg="#e5e5ea", relief="flat", padx=12, pady=6,
                  command=self.open_current_folder).pack(side="left", padx=5)
        tk.Button(btn_row, text="✏️ 重命名", font=("PingFang SC", 11),
                  bg="#e5e5ea", relief="flat", padx=12, pady=6,
                  command=self.rename_file).pack(side="left", padx=5)
        tk.Button(btn_row, text="📥 导入文件", font=("PingFang SC", 11),
                  bg="#e5e5ea", relief="flat", padx=12, pady=6,
                  command=self.import_file).pack(side="left", padx=5)
        tk.Button(btn_row, text="🗑️ 删除", font=("PingFang SC", 11),
                  bg="#e5e5ea", relief="flat", padx=12, pady=6,
                  command=self.delete_file).pack(side="left", padx=5)

        # === 操作区 ===
        action_frame = tk.LabelFrame(self.root, text="  ⚡ 处理操作  ",
                                      font=("PingFang SC", 13, "bold"),
                                      bg="#ffffff", fg="#1d1d1f",
                                      padx=20, pady=15)
        action_frame.pack(fill="x", padx=20, pady=(0, 20))

        action_row = tk.Frame(action_frame, bg="#ffffff")
        action_row.pack(fill="x")

        tk.Button(action_row, text="📝 转录 + 摘要",
                  font=("PingFang SC", 13, "bold"),
                  bg="#007aff", fg="white", activebackground="#0051d5",
                  activeforeground="white", relief="flat", padx=18, pady=10,
                  command=lambda: self.process_file(mode="full")).pack(side="left", padx=(0, 8))

        tk.Button(action_row, text="⚡ 仅转录",
                  font=("PingFang SC", 13),
                  bg="#5ac8fa", fg="white", activebackground="#34aadc",
                  activeforeground="white", relief="flat", padx=15, pady=10,
                  command=lambda: self.process_file(mode="transcribe")).pack(side="left", padx=8)

        tk.Button(action_row, text="🔊 中文朗读",
                  font=("PingFang SC", 13),
                  bg="#34c759", fg="white", activebackground="#28a745",
                  activeforeground="white", relief="flat", padx=15, pady=10,
                  command=lambda: self.read_file(lang="zh")).pack(side="left", padx=8)

        tk.Button(action_row, text="🔊 英文朗读",
                  font=("PingFang SC", 13),
                  bg="#af52de", fg="white", activebackground="#9341cc",
                  activeforeground="white", relief="flat", padx=15, pady=10,
                  command=lambda: self.read_file(lang="en")).pack(side="left", padx=8)

        # 底部状态栏
        self.bottom_status = tk.Label(self.root, text="✅ 就绪",
                                       font=("PingFang SC", 11),
                                       bg="#f5f5f7", fg="#6e6e73",
                                       anchor="w")
        self.bottom_status.pack(fill="x", side="bottom", padx=20, pady=(0, 10))

    # ---------- 录音 ----------

    def toggle_recording(self):
        if self.recording_proc is None:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.recording_file = RECORDINGS_DIR / f"会议_{ts}.wav"

        # 用 ffmpeg 录默认输入设备（麦克风）
        cmd = [
            FFMPEG, "-y",
            "-f", "avfoundation",
            "-i", ":0",  # 默认音频输入
            "-ar", "44100", "-ac", "1",
            str(self.recording_file)
        ]
        try:
            self.recording_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.PIPE
            )
        except Exception as e:
            messagebox.showerror("录音失败", str(e))
            return

        self.recording_start = time.time()
        self.record_btn.config(text="⏹  停止录音", bg="#5ac8fa")
        self.status_label.config(text="🔴 录音中", fg="#ff3b30")
        self.update_timer()

    def stop_recording(self):
        if self.recording_proc:
            try:
                self.recording_proc.stdin.write(b"q")
                self.recording_proc.stdin.flush()
                self.recording_proc.wait(timeout=5)
            except Exception:
                self.recording_proc.terminate()
            self.recording_proc = None

        if self.timer_id:
            self.root.after_cancel(self.timer_id)
            self.timer_id = None

        self.record_btn.config(text="🎙️  开始录音", bg="#ff3b30")
        self.status_label.config(text=f"✅ 已保存", fg="#34c759")

        if self.recording_file and self.recording_file.exists():
            self.bottom_status.config(text=f"✅ 录音已保存：{self.recording_file.name}")
            self.refresh_files()
            self.tabs.select(0)  # 切到录音 tab
        self.recording_start = None

    def update_timer(self):
        if self.recording_start:
            elapsed = int(time.time() - self.recording_start)
            mins, secs = divmod(elapsed, 60)
            self.timer_label.config(text=f"{mins:02d}:{secs:02d}")
            self.timer_id = self.root.after(1000, self.update_timer)
        else:
            self.timer_label.config(text="00:00")

    # ---------- 文件管理 ----------

    def refresh_files(self):
        # 录音文件
        self.rec_listbox.delete(0, tk.END)
        rec_files = sorted(RECORDINGS_DIR.glob("*"),
                           key=lambda p: p.stat().st_mtime, reverse=True)
        for f in rec_files:
            if f.is_file() and f.suffix.lower() in {".wav", ".mp3", ".m4a", ".mp4", ".mov", ".aac"}:
                size_mb = f.stat().st_size / 1024 / 1024
                t = datetime.fromtimestamp(f.stat().st_mtime).strftime("%m-%d %H:%M")
                self.rec_listbox.insert(tk.END, f"{t}  {f.name}  ({size_mb:.1f} MB)")

        # 输出文件 — 改为按会议文件夹显示
        self.out_listbox.delete(0, tk.END)
        meeting_dirs = sorted([d for d in OUTPUT_DIR.iterdir() if d.is_dir()],
                              key=lambda p: p.stat().st_mtime, reverse=True)
        for d in meeting_dirs:
            files_in = list(d.iterdir())
            has_transcript = any("逐字稿" in f.name or f.name.endswith(".txt") for f in files_in)
            has_summary = any("纪要" in f.name or f.name.endswith(".md") for f in files_in)
            has_audio = any(f.suffix.lower() == ".mp3" for f in files_in)
            badges = []
            badges.append("📝 逐字稿" if has_transcript else "・・・・")
            badges.append("📋 纪要" if has_summary else "・・・")
            badges.append("🔊 朗读" if has_audio else "・・・")
            t = datetime.fromtimestamp(d.stat().st_mtime).strftime("%m-%d %H:%M")
            line = f"{t}  📁 {d.name}    [{' '.join(badges)}]"
            self.out_listbox.insert(tk.END, line)

    def get_current_listbox(self):
        idx = self.tabs.index(self.tabs.select())
        if idx == 0:
            return self.rec_listbox, RECORDINGS_DIR
        return self.out_listbox, OUTPUT_DIR

    def get_selected_file(self):
        """录音 tab 返回音频文件，输出 tab 返回会议文件夹"""
        listbox, dirpath = self.get_current_listbox()
        sel = listbox.curselection()
        if not sel:
            messagebox.showinfo("提示", "请先选中一项")
            return None
        line = listbox.get(sel[0])
        idx = self.tabs.index(self.tabs.select())

        if idx == 0:  # 录音 tab → 解析文件名
            parts = line.split("  ")
            if len(parts) < 2:
                return None
            return dirpath / parts[1].strip()
        else:  # 输出 tab → 解析文件夹名
            # 格式："05-08 00:57  📁 会议_xxx    [...]"
            m = re.search(r"📁\s+(.+?)\s+\[", line)
            if m:
                return dirpath / m.group(1)
            return None

    def open_current_folder(self):
        """录音 tab：打开 recordings/；输出 tab：打开选中的会议文件夹"""
        idx = self.tabs.index(self.tabs.select())
        if idx == 1:
            # 输出 tab — 如果有选中的会议，打开那个会议文件夹
            sel = self.out_listbox.curselection()
            if sel:
                target = self.get_selected_file()  # 文件夹
                if target and target.exists():
                    subprocess.run(["open", str(target)])
                    return
        _, dirpath = self.get_current_listbox()
        subprocess.run(["open", str(dirpath)])

    def rename_file(self):
        f = self.get_selected_file()
        if not f or not f.exists():
            return
        new_name = tk.simpledialog.askstring("重命名",
                                              f"原名：{f.name}\n输入新名（含扩展名）：",
                                              initialvalue=f.name)
        if new_name and new_name != f.name:
            new_path = f.parent / new_name
            f.rename(new_path)
            self.refresh_files()
            self.bottom_status.config(text=f"✅ 已重命名为 {new_name}")

    def delete_file(self):
        f = self.get_selected_file()
        if not f or not f.exists():
            return
        if f.is_dir():
            msg = f"确认删除会议文件夹 {f.name} 及其内全部文件？\n（这个操作不能撤销）"
        else:
            msg = f"确认删除 {f.name}？"
        if messagebox.askyesno("确认删除", msg):
            if f.is_dir():
                import shutil
                shutil.rmtree(f)
            else:
                f.unlink()
            self.refresh_files()
            self.bottom_status.config(text=f"🗑️ 已删除 {f.name}")

    def import_file(self):
        path = filedialog.askopenfilename(
            title="选择音视频文件导入",
            filetypes=[("音视频", "*.mp4 *.m4a *.wav *.mp3 *.mov *.aac"), ("所有", "*.*")]
        )
        if path:
            src = Path(path)
            dst = RECORDINGS_DIR / src.name
            try:
                import shutil
                shutil.copy2(src, dst)
                self.refresh_files()
                self.tabs.select(0)
                self.bottom_status.config(text=f"📥 已导入 {src.name}")
            except Exception as e:
                messagebox.showerror("导入失败", str(e))

    # ---------- 处理操作 ----------

    def process_file(self, mode):
        f = self.get_selected_file()
        if not f or not f.exists():
            return

        # 必须是录音文件
        if f.suffix.lower() not in {".wav", ".mp3", ".m4a", ".mp4", ".mov", ".aac"}:
            messagebox.showinfo("提示", "请在「录音文件」标签页选音频/视频")
            return

        if mode == "full":
            cmd = [str(SCRIPTS_DIR / "meeting.sh"), str(f)]
            label = "转录 + 摘要"
        else:
            cmd = [str(SCRIPTS_DIR / "transcribe_fast.sh"), str(f)]
            label = "仅转录"

        self.bottom_status.config(text=f"⏳ {label}中：{f.name}（请等待）")
        threading.Thread(target=self._run_subprocess,
                          args=(cmd, label), daemon=True).start()

    def read_file(self, lang):
        f = self.get_selected_file()
        if not f or not f.exists():
            return

        # 输出 tab 选中的是文件夹 → 自动找里面的 3-纪要.md
        if f.is_dir():
            target = f / "3-纪要.md"
            if not target.exists():
                # 退而求其次找 2-清理版.txt 或 1-逐字稿.txt
                for fallback in ["2-清理版.txt", "1-逐字稿.txt"]:
                    if (f / fallback).exists():
                        target = f / fallback
                        break
                else:
                    messagebox.showinfo("提示", "这个会议文件夹里还没有可朗读的文本")
                    return
            f = target

        if lang == "en":
            cmd = [str(SCRIPTS_DIR / "translate-read.sh"), str(f)]
            label = "翻译 + 英文朗读"
        else:
            cmd = [str(SCRIPTS_DIR / "read.sh"), str(f)]
            label = "中文朗读"

        self.bottom_status.config(text=f"⏳ {label}中：{f.name}（请等待）")
        threading.Thread(target=self._run_subprocess,
                          args=(cmd, label), daemon=True).start()

    def _run_subprocess(self, cmd, label):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            if result.returncode == 0:
                self.root.after(0, lambda: self._on_done(label, success=True))
            else:
                err = result.stderr[-500:] if result.stderr else "未知错误"
                self.root.after(0, lambda: self._on_done(label, success=False, err=err))
        except Exception as e:
            self.root.after(0, lambda: self._on_done(label, success=False, err=str(e)))

    def _on_done(self, label, success, err=""):
        if success:
            self.bottom_status.config(text=f"✅ {label}完成！结果在「输出文件」标签页", fg="#34c759")
            subprocess.run(["afplay", "/System/Library/Sounds/Glass.aiff"], check=False)
            self.refresh_files()
            self.tabs.select(1)
        else:
            self.bottom_status.config(text=f"❌ {label}失败：{err[:80]}", fg="#ff3b30")
            messagebox.showerror(f"{label}失败", err)


if __name__ == "__main__":
    import tkinter.simpledialog
    root = tk.Tk()
    app = MeetingAIDashboard(root)
    root.mainloop()
