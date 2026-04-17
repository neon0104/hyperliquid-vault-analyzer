Set fso = CreateObject("Scripting.FileSystemObject")
folderPath = "C:\Users\USER\.gemini\antigravity\scratch\hyperliquid-vault-analyzer"
batPath = folderPath & "\auto_run.bat"

Set WinScriptHost = CreateObject("WScript.Shell")
WinScriptHost.CurrentDirectory = folderPath
WinScriptHost.Run "cmd.exe /c """ & batPath & """", 0, False
Set WinScriptHost = Nothing
