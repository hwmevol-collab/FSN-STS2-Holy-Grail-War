$ErrorActionPreference='Stop'
$bRoot=$PSScriptRoot
$bTarget='E:\SteamLibrary\steamapps\common\Slay the Spire 2\mods\RinArcherCore'
$bBackup=(Get-Content -LiteralPath (Join-Path $bRoot 'reports\milestone-b\backup-path.txt') -Raw).Trim()
if(Get-Process SlayTheSpire2 -ErrorAction SilentlyContinue | Where-Object Path -EQ 'E:\SteamLibrary\steamapps\common\Slay the Spire 2\SlayTheSpire2.exe'){throw 'Original game running'}
$bInstalled=Get-Content -LiteralPath (Join-Path $bRoot 'reports\milestone-b\install-verification.json') -Raw | ConvertFrom-Json
if((Get-FileHash -LiteralPath (Join-Path $bTarget 'RinArcherCore.dll')).Hash -ne $bInstalled.dllSha256){throw 'Installed DLL changed after B; cannot overwrite'}
if((Get-FileHash -LiteralPath (Join-Path $bTarget 'RinArcherCore.json')).Hash -ne $bInstalled.manifestSha256){throw 'Installed manifest changed after B; cannot overwrite'}
$bRestore=Join-Path $bBackup 'installed-mod'
if(@(Get-ChildItem -LiteralPath $bTarget -File).Count -ne @(Get-ChildItem -LiteralPath $bRestore -File).Count){throw 'Unexpected extra installed files'}
$bHold=Join-Path $bBackup ('b-payload-before-restore-'+(Get-Date -Format 'yyyyMMdd-HHmmss'))
Copy-Item -LiteralPath $bTarget -Destination $bHold -Recurse
Get-ChildItem -LiteralPath $bRestore -File | Copy-Item -Destination $bTarget -Force
foreach($bFile in Get-ChildItem -LiteralPath $bRestore -File){if((Get-FileHash -LiteralPath $bFile.FullName).Hash -ne (Get-FileHash -LiteralPath (Join-Path $bTarget $bFile.Name)).Hash){throw 'A restore mismatch'}}
'MILESTONE_A_PAYLOAD_RESTORED; source stays at B, real saves untouched'
