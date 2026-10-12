param([switch]$PrepareOnly)
$ErrorActionPreference='Stop'
$cRoot=$PSScriptRoot
$cGame='E:\SteamLibrary\steamapps\common\Slay the Spire 2'
$cManual=Join-Path $cRoot 'human-runtime'
if(Get-Process SlayTheSpire2 -ErrorAction SilentlyContinue | Where-Object Path -EQ (Join-Path $cManual 'SlayTheSpire2.exe')){throw 'The isolated playtest is already open'}
New-Item -ItemType Directory -Path $cManual,(Join-Path $cManual 'data_sts2_windows_x86_64'),(Join-Path $cManual 'mods') -Force | Out-Null
foreach($file in Get-ChildItem -LiteralPath $cGame -File | Where-Object Extension -In '.exe','.dll','.pck','.json'){$dest=Join-Path $cManual $file.Name;if(!(Test-Path -LiteralPath $dest)){New-Item -ItemType HardLink -Path $dest -Target $file.FullName | Out-Null}}
foreach($file in Get-ChildItem -LiteralPath (Join-Path $cGame 'data_sts2_windows_x86_64') -File){$dest=Join-Path $cManual "data_sts2_windows_x86_64\$($file.Name)";if(!(Test-Path -LiteralPath $dest)){New-Item -ItemType HardLink -Path $dest -Target $file.FullName | Out-Null}}
foreach($name in @('BaseLib','STS2-RitsuLib','RinArcherCore')){New-Item -ItemType Directory -Path (Join-Path $cManual "mods\$name") -Force | Out-Null;Copy-Item -Path (Join-Path $cGame "mods\$name\*") -Destination (Join-Path $cManual "mods\$name") -Recurse -Force}
@'
[application]
config/use_custom_user_dir=true
config/custom_user_dir_name="RinArcherCore-MilestoneC-Manual"
'@ | Set-Content -LiteralPath (Join-Path $cManual 'override.cfg') -Encoding utf8
$cProfile=Join-Path $env:APPDATA 'RinArcherCore-MilestoneC-Manual\default\1'
New-Item -ItemType Directory -Path $cProfile -Force | Out-Null
$cSettings=Join-Path $cProfile 'settings.save'
if(!(Test-Path -LiteralPath $cSettings)){'{"schema_version":5,"seen_ea_disclaimer":true,"skip_intro_logo":true,"language":"eng","mod_settings":{"mods_enabled":true,"mod_list":[]}}' | Set-Content -LiteralPath $cSettings -Encoding utf8}
if(!$PrepareOnly){Start-Process -FilePath (Join-Path $cManual 'SlayTheSpire2.exe') -WorkingDirectory $cManual -ArgumentList '--force-steam=off' -Environment @{SteamAppId='2868840';SteamGameId='2868840';STS2_DEV_SKIP='1'} -WindowStyle Normal}
Write-Output 'Isolated manual QA is ready. Choose QA_ALPHA_DRAFT_LAB or QA_ALPHA_ARCHETYPE from the main menu. No test driver is included.'
