$ErrorActionPreference='Stop'
$d1Report=Join-Path $PSScriptRoot 'reports\milestone-d1'
$d1Backup=(Get-Content -LiteralPath (Join-Path $d1Report 'backup-path.txt') -Raw).Trim()
$d1Target='E:\SteamLibrary\steamapps\common\Slay the Spire 2\mods\RinArcherCore'
if(Get-Process SlayTheSpire2 -ErrorAction SilentlyContinue | Where-Object Path -EQ 'E:\SteamLibrary\steamapps\common\Slay the Spire 2\SlayTheSpire2.exe'){throw 'Close the user game before restoring its mod'}
$d1Receipt=Get-Content -LiteralPath (Join-Path $d1Report 'install-verification.json') -Raw | ConvertFrom-Json
if((Get-FileHash -LiteralPath (Join-Path $d1Target 'RinArcherCore.dll')).Hash-ne$d1Receipt.installedDllSha256){throw 'Installed payload changed since D1; inspect before restoring'}
foreach($file in Get-ChildItem -LiteralPath (Join-Path $d1Backup 'installed-mod') -File){Copy-Item -LiteralPath $file.FullName -Destination $d1Target -Force;if((Get-FileHash -LiteralPath (Join-Path $d1Target $file.Name)).Hash-ne(Get-FileHash -LiteralPath $file.FullName).Hash){throw 'Restore hash mismatch'}}
Write-Output 'Restored accepted v0.3.0 DLL/JSON. Other mods and all save directories were preserved.'
