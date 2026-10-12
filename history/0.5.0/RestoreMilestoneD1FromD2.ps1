$ErrorActionPreference='Stop'
$d2Report=Join-Path $PSScriptRoot 'reports\milestone-d2'
$d2Backup=(Get-Content (Join-Path $d2Report 'backup-path.txt') -Raw).Trim()
$d2Target='E:\SteamLibrary\steamapps\common\Slay the Spire 2\mods\RinArcherCore'
if(Get-CimInstance Win32_Process -Filter "Name='SlayTheSpire2.exe'"|Where-Object ExecutablePath -EQ 'E:\SteamLibrary\steamapps\common\Slay the Spire 2\SlayTheSpire2.exe'){throw 'Close the user game before restoring'}
$d2Installed=Get-Content (Join-Path $d2Report 'install-verification.json') -Raw|ConvertFrom-Json
if((Get-FileHash (Join-Path $d2Target 'RinArcherCore.dll')).Hash-ne$d2Installed.installedDllSha256){throw 'Installed DLL has changed; preserve it for review'}
if((Get-FileHash (Join-Path $d2Target 'RinArcherCore.json')).Hash-ne$d2Installed.installedManifestSha256){throw 'Installed manifest has changed; preserve it for review'}
foreach($d2Name in @('RinArcherCore.dll','RinArcherCore.json')){Copy-Item -LiteralPath (Join-Path $d2Backup "installed-mod\$d2Name") -Destination (Join-Path $d2Target $d2Name) -Force;if((Get-FileHash (Join-Path $d2Target $d2Name)).Hash-ne(Get-FileHash (Join-Path $d2Backup "installed-mod\$d2Name")).Hash){throw 'Restore readback failed'}}
Write-Output 'D1 v0.4.2 payload restored. Saves and other mods preserved. D2 manual runtime remains isolated.'

