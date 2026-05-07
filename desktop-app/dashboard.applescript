-- 会议 AI 控制台 · 双击启动 GUI
on run
	set scriptPath to (POSIX path of (path to home folder)) & "meeting-ai/scripts/dashboard.py"
	set brewPython to "/opt/homebrew/bin/python3.11"

	tell application "System Events"
		if not (exists file scriptPath) then
			display dialog "找不到 dashboard.py" buttons {"OK"} default button 1 with icon stop
			return
		end if
	end tell

	-- 后台启动 GUI（不锁 Terminal，不阻塞）
	do shell script "nohup " & brewPython & " " & quoted form of scriptPath & " > /tmp/meeting-ai-dashboard.log 2>&1 &"
end run
