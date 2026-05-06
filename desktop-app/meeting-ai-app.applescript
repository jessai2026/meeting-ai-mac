-- 会议 AI 助手
-- 拖拽视频/音频文件到此图标即可自动处理

property kAppName : "会议 AI 助手"

-- 拖拽文件触发
on open theFiles
	set fileCount to count of theFiles
	if fileCount = 0 then return

	-- 构造命令
	set cmdHeader to "clear && printf '\\n🎙️  会议 AI 助手\\n════════════════════════════════════\\n准备处理 " & fileCount & " 个文件\\n\\n'"

	set cmdProcess to ""
	set i to 1
	repeat with aFile in theFiles
		set filePath to POSIX path of aFile
		set fileName to do shell script "basename " & quoted form of filePath
		set cmdProcess to cmdProcess & " && printf '────────────────────────────────────\\n[" & i & "/" & fileCount & "] " & fileName & "\\n────────────────────────────────────\\n' && cd $HOME/meeting-ai/scripts && ./meeting.sh " & quoted form of filePath & " --hf-token \"$HF_TOKEN\""
		set i to i + 1
	end repeat

	set cmdEnd to " && printf '\\n✅ 全部完成！打开输出文件夹...\\n' && open $HOME/meeting-ai/output && printf '\\n（按 回车 关闭窗口）' && read"

	set fullCmd to cmdHeader & cmdProcess & cmdEnd

	-- 在 Terminal 显示实时进度
	tell application "Terminal"
		activate
		do script fullCmd
	end tell
end open

-- 直接双击启动（没拖文件）
on run
	set msg to "🎙️ 会议 AI 助手 · 使用方法

▸ 把录音 / 视频文件拖到这个 App 的图标上即可自动处理

支持的格式：
  mp4 · m4a · wav · mp3 · mov · aac

会自动产出 4 份文件到 ~/meeting-ai/output/：
  • 逐字稿（带时间戳）
  • SRT 字幕文件
  • 去口水词版
  • 结构化会议纪要"

	display dialog msg buttons {"打开输出文件夹", "知道了"} default button 2 with title kAppName
	if button returned of result is "打开输出文件夹" then
		do shell script "open $HOME/meeting-ai/output"
	end if
end run
