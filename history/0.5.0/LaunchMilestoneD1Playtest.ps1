param([switch]$PrepareOnly)
$ErrorActionPreference='Stop'
$d1Root=$PSScriptRoot
$d1Game='E:\SteamLibrary\steamapps\common\Slay the Spire 2'
$d1Manual=Join-Path $d1Root 'd1-human-runtime'
if(Get-Process SlayTheSpire2 -ErrorAction SilentlyContinue | Where-Object Path -EQ (Join-Path $d1Manual 'SlayTheSpire2.exe')){throw 'The isolated D1 playtest is already open'}
New-Item -ItemType Directory -Path $d1Manual,(Join-Path $d1Manual 'data_sts2_windows_x86_64'),(Join-Path $d1Manual 'mods') -Force | Out-Null
foreach($file in Get-ChildItem -LiteralPath $d1Game -File | Where-Object Extension -In '.exe','.dll','.pck','.json'){$dest=Join-Path $d1Manual $file.Name;if(!(Test-Path -LiteralPath $dest)){New-Item -ItemType HardLink -Path $dest -Target $file.FullName | Out-Null}}
foreach($file in Get-ChildItem -LiteralPath (Join-Path $d1Game 'data_sts2_windows_x86_64') -File){$dest=Join-Path $d1Manual "data_sts2_windows_x86_64\$($file.Name)";if(!(Test-Path -LiteralPath $dest)){New-Item -ItemType HardLink -Path $dest -Target $file.FullName | Out-Null}}
foreach($name in @('BaseLib','STS2-RitsuLib','RinArcherCore')){New-Item -ItemType Directory -Path (Join-Path $d1Manual "mods\$name") -Force | Out-Null;Copy-Item -Path (Join-Path $d1Game "mods\$name\*") -Destination (Join-Path $d1Manual "mods\$name") -Recurse -Force}
@'
[application]
config/use_custom_user_dir=true
config/custom_user_dir_name="RinArcherCore-MilestoneD1-Manual"
'@ | Set-Content -LiteralPath (Join-Path $d1Manual 'override.cfg') -Encoding utf8
$d1Profile=Join-Path $env:APPDATA 'RinArcherCore-MilestoneD1-Manual\default\1'
New-Item -ItemType Directory -Path $d1Profile -Force | Out-Null
$d1Settings=Join-Path $d1Profile 'settings.save'
if(!(Test-Path -LiteralPath $d1Settings)){'{"schema_version":5,"seen_ea_disclaimer":true,"skip_intro_logo":true,"language":"eng","mod_settings":{"mods_enabled":true,"mod_list":[]}}' | Set-Content -LiteralPath $d1Settings -Encoding utf8}
if(@(Get-ChildItem -LiteralPath (Join-Path $d1Manual 'mods') -File -Recurse | Where-Object Name -Match '^RinArcherCoreTests').Count){throw 'Test driver must not be in the human playtest runtime'}
if(!$PrepareOnly){Start-Process -FilePath (Join-Path $d1Manual 'SlayTheSpire2.exe') -WorkingDirectory $d1Manual -ArgumentList '--force-steam=off' -Environment @{SteamAppId='2868840';SteamGameId='2868840';STS2_DEV_SKIP='1'} -WindowStyle Normal}
Write-Output 'D1 isolated manual QA ready. Choose Rin / Archer · D1 Run Integration. Resume with native Continue after Save/Exit. Human QA remains pending.'
