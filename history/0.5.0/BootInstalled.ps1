$ErrorActionPreference='Stop'
$sliceQaAppData=Join-Path $PSScriptRoot 'installed-boot-profile'
$sliceSettings=Join-Path $sliceQaAppData 'SlayTheSpire2\default\1'
New-Item -ItemType Directory -Path $sliceSettings -Force | Out-Null
'{"schema_version":5,"seen_ea_disclaimer":true,"skip_intro_logo":true,"language":"eng","mod_settings":{"mods_enabled":true,"mod_list":[]}}' | Set-Content -LiteralPath (Join-Path $sliceSettings 'settings.save') -Encoding utf8
$sliceGame='E:\SteamLibrary\steamapps\common\Slay the Spire 2'
$sliceProc=Start-Process -FilePath (Join-Path $sliceGame 'SlayTheSpire2.exe') -WorkingDirectory $sliceGame -ArgumentList '--headless','--force-steam=off','--quit-after','2500','--rin-archer-boot' -Environment @{APPDATA=$sliceQaAppData;STS2_DEV_SKIP='1';SteamAppId='2868840';SteamGameId='2868840'} -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $PSScriptRoot 'reports\installed-boot.stdout.log') -RedirectStandardError (Join-Path $PSScriptRoot 'reports\installed-boot.stderr.log')
$sliceProc.Id | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'reports\installed-boot-process-id.txt')
Write-Output "Installed mod boot on original executable, isolated APPDATA, PID $($sliceProc.Id)"
