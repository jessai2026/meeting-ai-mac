-- 会议 AI 助手 v2
-- 拖拽视频/音频文件到此图标即可自动处理
-- 新增：完成后系统通知 + 提示音

property kAppName : "会议 AI 助手"

on open theFiles
	set fileCount to count of theFiles
	if fileCount = 0 then return

	-- 显示开始通知
	display notification "已开始处理，预计 1-5 分钟" with title kAppName subtitle "处理中... 切到 Terminal 看进度"

	-- 构造 shell 命令
	set cmdHeader to "clear && printf '\\n🎙️  会议 AI 助手\\n════════════════════════════════════\\n准备处理 " & fileCount & " 个文件\\n\\n'"

	set cmdProcess to ""
	set i to 1
	repeat with aFile in theFiles
		set filePath to POSIX path of aFile
		set fileName to do shell script "basename " & quoted form of filePath
		set cmdProcess to cmdProcess & " && printf '────────────────────────────────────\\n[" & i & "/" & fileCount & "] " & fileName & "\\n────────────────────────────────────\\n' && cd $HOME/meeting-ai/scripts && ./meeting.sh " & quoted form of filePath & " --hf-token \"$HF_TOKEN\""
		set i to i + 1
	end repeat

	-- 完成后：响铃 + 通知 + 打开文件夹
	set cmdEnd to " && printf '\\n✅ 全部完成！\\n' && afplay /System/Library/Sounds/Glass.aiff && osascript -e 'display notification \"会议处理完成，输出文件夹已打开\" with title \"" & kAppName & "\" sound name \"Glass\"' && open $HOME/meeting-ai/output && printf '\\n（可以关闭这个窗口了）\\n'"

	set fullCmd to cmdHeader & cmdProcess & cmdEnd

	tell application "Terminal"
		activate
		do script fullCmd
	end tell
end open

-- 直接双击启动
on run
	set msg to "🎙️ 会议 AI 助手 · 使用方法

▸ 把录音 / 视频文件拖到这个 App 的图标上即可自动处理

支持的格式：
  mp4 · m4a · wav · mp3 · mov · aac

会自动产出 4 份文件到 ~/meeting-ai/output/：
  • 逐字稿（带时间戳）
  • SRT 字幕文件
  • 去口水词版
  • 结构化会议纪要

完成时会有「叮」的提示音和系统通知。"

	display dialog msg buttons {"打开输出文件夹", "知道了"} default button 2 with title kAppName
	if button returned of result is "打开输出文件夹" then
		do shell script "open $HOME/meeting-ai/output"
	end if
end run
