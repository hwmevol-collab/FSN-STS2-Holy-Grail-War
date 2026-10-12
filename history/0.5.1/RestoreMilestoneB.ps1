$ErrorActionPreference='Stop'
$cBackup=(Get-Content -LiteralPath (Join-Path $PSScriptRoot 'reports\milestone-c\backup-path.txt') -Raw).Trim()
$cTarget='E:\SteamLibrary\steamapps\common\Slay the Spire 2\mods\RinArcherCore'
if(Get-Process SlayTheSpire2 -ErrorAction SilentlyContinue | Where-Object Path -EQ 'E:\SteamLibrary\steamapps\common\Slay the Spire 2\SlayTheSpire2.exe'){throw 'Close the original game before restoring B'}
$cFiles=Get-ChildItem -LiteralPath (Join-Path $cBackup 'installed-mod') -File
foreach($file in $cFiles){if($file.Name-notin'RinArcherCore.dll','RinArcherCore.json'){throw 'Unexpected restore payload'};Copy-Item -LiteralPath $file.FullName -Destination $cTarget -Force}
foreach($file in $cFiles){if((Get-FileHash -LiteralPath $file.FullName).Hash-ne(Get-FileHash -LiteralPath (Join-Path $cTarget $file.Name)).Hash){throw 'Restore verification failed'}}
Write-Output 'Milestone B v0.2.1 DLL/JSON restored. User saves and other mods were not written.'
