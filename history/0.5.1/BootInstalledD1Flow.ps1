$ErrorActionPreference='Stop'
$fixGame='E:\SteamLibrary\steamapps\common\Slay the Spire 2'
$fixReport=Join-Path $PSScriptRoot 'reports\d1-native-container-flow'
if(Get-Process SlayTheSpire2 -ErrorAction SilentlyContinue | Where-Object Path -EQ (Join-Path $fixGame 'SlayTheSpire2.exe')){throw 'The user game is running; boot verification postponed'}
$fixInstall=Get-Content -LiteralPath (Join-Path $fixReport 'install-verification.json') -Raw | ConvertFrom-Json
if($fixInstall.payloadMismatches.Count -or $fixInstall.protectedMismatches.Count -or $fixInstall.testDriverInstalled){throw 'Installed payload is not verified'}
$fixAppData=Join-Path $PSScriptRoot 'd1-flow-installed-boot-profile'
$fixSettings=Join-Path $fixAppData 'SlayTheSpire2\default\1'
New-Item -ItemType Directory -Path $fixSettings -Force | Out-Null
'{"schema_version":5,"seen_ea_disclaimer":true,"skip_intro_logo":true,"language":"eng","mod_settings":{"mods_enabled":true,"mod_list":[]}}' | Set-Content -LiteralPath (Join-Path $fixSettings 'settings.save') -Encoding utf8
$fixProcess=Start-Process -FilePath (Join-Path $fixGame 'SlayTheSpire2.exe') -WorkingDirectory $fixGame -ArgumentList '--headless','--force-steam=off','--quit-after','2500','--rin-archer-boot' -Environment @{APPDATA=$fixAppData;STS2_DEV_SKIP='1';SteamAppId='2868840';SteamGameId='2868840'} -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $fixReport 'installed-boot.stdout.log') -RedirectStandardError (Join-Path $fixReport 'installed-boot.stderr.log')
$fixProcess.Id | Set-Content -LiteralPath (Join-Path $fixReport 'installed-boot-pid.txt')
Write-Output "Installed v0.4.2 original-executable boot, isolated APPDATA, PID $($fixProcess.Id)"
