$ws = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
$lnk = $ws.CreateShortcut((Join-Path $desktop 'Recon Engine Pro.lnk'))
Write-Output ('Target=' + $lnk.TargetPath)
Write-Output ('WD=' + $lnk.WorkingDirectory)
Write-Output ('Args=' + $lnk.Arguments)
