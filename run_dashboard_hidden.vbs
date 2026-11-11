Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\USER\.gemini\antigravity\scratch\hyperliquid-vault-analyzer"
WshShell.Run """C:\Users\USER\AppData\Local\Programs\Python\Python310\python.exe"" -X utf8 ""C:\Users\USER\.gemini\antigravity\scratch\hyperliquid-vault-analyzer\ensure_dashboard_running.py""", 0, False
Set WshShell = Nothing
