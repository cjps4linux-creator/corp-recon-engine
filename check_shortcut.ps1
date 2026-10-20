$ws = New-Object -ComObject WScript.Shell
$lnk = $ws.CreateShortcut('C:\Users\user\Desktop\Recon Engine Pro.lnk')
Write-Output ('Target=' + $lnk.TargetPath)
Write-Output ('WD=' + $lnk.WorkingDirectory)
Write-Output ('Args=' + $lnk.Arguments)
