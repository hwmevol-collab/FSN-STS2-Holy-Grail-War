param([switch]$PrepareOnly)
$ErrorActionPreference='Stop'
$d2Root=$PSScriptRoot
$d2Game='E:\SteamLibrary\steamapps\common\Slay the Spire 2'
$d2Manual=Join-Path $d2Root 'd2-human-runtime'
if(Get-Process SlayTheSpire2 -ErrorAction SilentlyContinue | Where-Object Path -EQ (Join-Path $d2Manual 'SlayTheSpire2.exe')){throw 'The isolated D2 playtest is already open'}
New-Item -ItemType Directory -Path $d2Manual,(Join-Path $d2Manual 'data_sts2_windows_x86_64'),(Join-Path $d2Manual 'mods') -Force | Out-Null
foreach($file in Get-ChildItem -LiteralPath $d2Game -File | Where-Object Extension -In '.exe','.dll','.pck','.json'){$dest=Join-Path $d2Manual $file.Name;if(!(Test-Path -LiteralPath $dest)){New-Item -ItemType HardLink -Path $dest -Target $file.FullName | Out-Null}}
foreach($file in Get-ChildItem -LiteralPath (Join-Path $d2Game 'data_sts2_windows_x86_64') -File){$dest=Join-Path $d2Manual "data_sts2_windows_x86_64\$($file.Name)";if(!(Test-Path -LiteralPath $dest)){New-Item -ItemType HardLink -Path $dest -Target $file.FullName | Out-Null}}
foreach($name in @('BaseLib','STS2-RitsuLib','RinArcherCore')){New-Item -ItemType Directory -Path (Join-Path $d2Manual "mods\$name") -Force | Out-Null;Copy-Item -Path (Join-Path $d2Game "mods\$name\*") -Destination (Join-Path $d2Manual "mods\$name") -Recurse -Force}
@'
[application]
config/use_custom_user_dir=true
config/custom_user_dir_name="RinArcherCore-MilestoneD2-Manual"
'@ | Set-Content -LiteralPath (Join-Path $d2Manual 'override.cfg') -Encoding utf8
$d2Profile=Join-Path $env:APPDATA 'RinArcherCore-MilestoneD2-Manual\default\1'
New-Item -ItemType Directory -Path $d2Profile -Force | Out-Null
$d2Settings=Join-Path $d2Profile 'settings.save'
if(!(Test-Path -LiteralPath $d2Settings)){'{"schema_version":5,"seen_ea_disclaimer":true,"skip_intro_logo":true,"language":"eng","mod_settings":{"mods_enabled":true,"mod_list":[]}}' | Set-Content -LiteralPath $d2Settings -Encoding utf8}
if(@(Get-ChildItem -LiteralPath (Join-Path $d2Manual 'mods') -File -Recurse | Where-Object Name -Match '^RinArcherCoreTests').Count){throw 'Test driver must not be in the human playtest runtime'}
if(!$PrepareOnly){Start-Process -FilePath (Join-Path $d2Manual 'SlayTheSpire2.exe') -WorkingDirectory $d2Manual -ArgumentList '--force-steam=off' -Environment @{SteamAppId='2868840';SteamGameId='2868840';STS2_DEV_SKIP='1'} -WindowStyle Normal}
Write-Output 'D2 isolated manual QA ready. Choose Rin / Archer · D2 Campfire / Merchant. QA_D2_RUN includes 500 fixture gold. Human QA remains pending.'

