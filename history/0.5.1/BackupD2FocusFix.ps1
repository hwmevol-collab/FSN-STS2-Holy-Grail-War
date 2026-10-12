$ErrorActionPreference='Stop'
$fixReport=Join-Path $PSScriptRoot 'reports\d2-rest-focus-highlight'
New-Item -ItemType Directory -Path $fixReport -Force|Out-Null
if(Test-Path (Join-Path $fixReport 'backup-path.txt')){throw 'Backup already exists'}
if(Get-CimInstance Win32_Process -Filter "Name='SlayTheSpire2.exe'"){throw 'Game is open; preserve session'}
$fixBackup=Join-Path $PSScriptRoot "backups\$((Get-Date).ToString('yyyyMMdd-HHmmss'))-d2-focus-fix"
New-Item -ItemType Directory -Path $fixBackup,(Join-Path $fixBackup 'source'),(Join-Path $fixBackup 'profiles') -Force|Out-Null
Get-ChildItem $PSScriptRoot -File|Copy-Item -Destination (Join-Path $fixBackup 'source')
foreach($dir in @('UI','Runtime','Content','Compatibility','QA','tests')){Copy-Item -LiteralPath (Join-Path $PSScriptRoot $dir) -Destination (Join-Path $fixBackup 'source') -Recurse}
$fixGame='E:\SteamLibrary\steamapps\common\Slay the Spire 2'
Copy-Item -LiteralPath (Join-Path $fixGame 'mods\RinArcherCore') -Destination (Join-Path $fixBackup 'installed-mod') -Recurse
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'd2-human-runtime\mods\RinArcherCore') -Destination (Join-Path $fixBackup 'manual-mod') -Recurse
foreach($profile in @('SlayTheSpire2','RinArcherCore-MilestoneD1-Manual','RinArcherCore-MilestoneD2-Manual')){if(Test-Path (Join-Path $env:APPDATA $profile)){Copy-Item -LiteralPath (Join-Path $env:APPDATA $profile) -Destination (Join-Path $fixBackup 'profiles') -Recurse}}
$fixProtectedRoots=@(Get-ChildItem (Join-Path $fixGame 'mods') -Directory|Where-Object Name -NE 'RinArcherCore'|ForEach-Object FullName)
$fixProtectedRoots+=@('SlayTheSpire2','RinArcherCore-MilestoneD1-Manual','RinArcherCore-MilestoneD2-Manual')|ForEach-Object {Join-Path $env:APPDATA $_}
$fixProtectedRoots+=Join-Path $PSScriptRoot 'd1-human-runtime\mods'
$fixProtected=@(foreach($dir in $fixProtectedRoots){if(Test-Path $dir){Get-ChildItem -LiteralPath $dir -File -Recurse|ForEach-Object {@{path=$_.FullName;sha256=(Get-FileHash $_.FullName).Hash}}}})
$fixProtected|ConvertTo-Json -Depth 4|Set-Content (Join-Path $fixBackup 'protected-before.json') -Encoding utf8
$fixSource=@(foreach($dir in @('UI','Runtime','Content','Compatibility','QA','tests')){Get-ChildItem (Join-Path $PSScriptRoot $dir) -File -Recurse|Where-Object FullName -NotMatch '\\(bin|obj)\\'|ForEach-Object {@{path=$_.FullName;sha256=(Get-FileHash $_.FullName).Hash}}})
$fixSource|ConvertTo-Json -Depth 4|Set-Content (Join-Path $fixBackup 'source-before.json') -Encoding utf8
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'reports\milestone-d2') -Destination (Join-Path $fixBackup 'accepted-d2-evidence') -Recurse
$fixBackup|Set-Content (Join-Path $fixReport 'backup-path.txt')
@{status='PASS';priorVersion='0.5.0';priorInstalledDllSha256=(Get-FileHash (Join-Path $fixBackup 'installed-mod\RinArcherCore.dll')).Hash;protectedFiles=$fixProtected.Count;manualD2ProfileBackedUp=$true;humanD2GameplayFeedback='No new gameplay issues; focus UI bug awaiting fix and recheck';createdAt=(Get-Date).ToString('o')}|ConvertTo-Json|Set-Content (Join-Path $fixReport 'precondition.json')
Write-Output "Protected backup complete: $fixBackup ($($fixProtected.Count) files)"
