Set shell = CreateObject("WScript.Shell")
batPath = Replace(WScript.ScriptFullName, "\launch-recon.vbs", "\launch-recon.bat")
shell.Run "cmd /c """ & batPath & """", 0, False
