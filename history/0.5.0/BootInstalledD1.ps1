$ErrorActionPreference='Stop'
$d1Game='E:\SteamLibrary\steamapps\common\Slay the Spire 2'
if(Get-Process SlayTheSpire2 -ErrorAction SilentlyContinue | Where-Object Path -EQ (Join-Path $d1Game 'SlayTheSpire2.exe')){throw 'The user game is running; boot verification postponed'}
$d1AppData=Join-Path $PSScriptRoot 'd1-installed-boot-profile'
$d1Settings=Join-Path $d1AppData 'SlayTheSpire2\default\1'
New-Item -ItemType Directory -Path $d1Settings -Force | Out-Null
'{"schema_version":5,"seen_ea_disclaimer":true,"skip_intro_logo":true,"language":"eng","mod_settings":{"mods_enabled":true,"mod_list":[]}}' | Set-Content -LiteralPath (Join-Path $d1Settings 'settings.save') -Encoding utf8
$d1Report=Join-Path $PSScriptRoot 'reports\milestone-d1'
$d1Process=Start-Process -FilePath (Join-Path $d1Game 'SlayTheSpire2.exe') -WorkingDirectory $d1Game -ArgumentList '--headless','--force-steam=off','--quit-after','2500','--rin-archer-boot' -Environment @{APPDATA=$d1AppData;STS2_DEV_SKIP='1';SteamAppId='2868840';SteamGameId='2868840'} -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $d1Report 'installed-boot.stdout.log') -RedirectStandardError (Join-Path $d1Report 'installed-boot.stderr.log')
$d1Process.Id | Set-Content -LiteralPath (Join-Path $d1Report 'installed-boot-pid.txt')
Write-Output "Installed v0.4.0 original-executable boot, isolated APPDATA, PID $($d1Process.Id)"
