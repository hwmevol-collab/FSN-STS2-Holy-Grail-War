$ErrorActionPreference='Stop'
$d2Game='E:\SteamLibrary\steamapps\common\Slay the Spire 2'
$d2Report=Join-Path $PSScriptRoot 'reports\milestone-d2'
if(Get-Process SlayTheSpire2 -ErrorAction SilentlyContinue | Where-Object Path -EQ (Join-Path $d2Game 'SlayTheSpire2.exe')){throw 'The user game is running; boot verification postponed'}
$d2Install=Get-Content -LiteralPath (Join-Path $d2Report 'install-verification.json') -Raw | ConvertFrom-Json
if($d2Install.payloadMismatches.Count -or $d2Install.protectedMismatches.Count -or $d2Install.testDriverInstalled){throw 'Installed payload is not verified'}
$d2AppData=Join-Path $PSScriptRoot 'd2-installed-boot-profile'
$d2Settings=Join-Path $d2AppData 'SlayTheSpire2\default\1'
New-Item -ItemType Directory -Path $d2Settings -Force | Out-Null
'{"schema_version":5,"seen_ea_disclaimer":true,"skip_intro_logo":true,"language":"eng","mod_settings":{"mods_enabled":true,"mod_list":[]}}' | Set-Content -LiteralPath (Join-Path $d2Settings 'settings.save') -Encoding utf8
$d2Process=Start-Process -FilePath (Join-Path $d2Game 'SlayTheSpire2.exe') -WorkingDirectory $d2Game -ArgumentList '--force-steam=off','--quit-after','2500','--rin-archer-boot' -Environment @{APPDATA=$d2AppData;STS2_DEV_SKIP='1';SteamAppId='2868840';SteamGameId='2868840'} -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $d2Report 'installed-boot.stdout.log') -RedirectStandardError (Join-Path $d2Report 'installed-boot.stderr.log')
$d2Process.Id | Set-Content -LiteralPath (Join-Path $d2Report 'installed-boot-pid.txt')
Write-Output "Installed v0.5.0 original-executable boot, isolated APPDATA, PID $($d2Process.Id)"


