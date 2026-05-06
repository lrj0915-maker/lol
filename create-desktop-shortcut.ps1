$ErrorActionPreference = 'Stop'
$desktop = [Environment]::GetFolderPath('Desktop')
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$target = Join-Path $root 'start-assistant.bat'
$shortcut = Join-Path $desktop 'LOL战绩助手.lnk'

$wsh = New-Object -ComObject WScript.Shell
$s = $wsh.CreateShortcut($shortcut)
$s.TargetPath = $target
$s.WorkingDirectory = $root
$s.IconLocation = "$env:SystemRoot\System32\shell32.dll, 220"
$s.Save()

Write-Host "Created shortcut: $shortcut"
