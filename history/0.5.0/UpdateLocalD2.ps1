param([switch]$VerifyOnly)
$ErrorActionPreference='Stop'
$d2Report=Join-Path $PSScriptRoot 'reports\milestone-d2'
$d2Backup=(Get-Content (Join-Path $d2Report 'backup-path.txt') -Raw).Trim()
$d2Target='E:\SteamLibrary\steamapps\common\Slay the Spire 2\mods\RinArcherCore'
$d2Protected=@(Get-Content (Join-Path $d2Backup 'protected-before.json') -Raw|ConvertFrom-Json)
$d2Gate=Get-Content (Join-Path $d2Report 'acceptance.json') -Raw|ConvertFrom-Json
$d2Hash=(Get-FileHash (Join-Path $PSScriptRoot 'bin\Release\net9.0\RinArcherCore.dll')).Hash
if($d2Gate.status-ne'RIN_ARCHER_RUN_ECONOMY_D2_PASS'-or$d2Gate.testedDllSha256-ne$d2Hash){throw 'D2 engineering gate or DLL hash mismatch'}
function Get-D2ProtectedMismatches {@($d2Protected|Where-Object {!(Test-Path -LiteralPath $_.path)-or(Get-FileHash -LiteralPath $_.path).Hash-ne$_.sha256}|ForEach-Object path)}
if(!$VerifyOnly){
    if(Get-CimInstance Win32_Process -Filter "Name='SlayTheSpire2.exe'"|Where-Object {$_.ExecutablePath-eq'E:\SteamLibrary\steamapps\common\Slay the Spire 2\SlayTheSpire2.exe'-or$_.ExecutablePath-eq(Join-Path $PSScriptRoot 'd2-human-runtime\SlayTheSpire2.exe')}){throw 'User game or D2 manual game is open; payload preserved'}
    if((Get-D2ProtectedMismatches).Count){throw 'Protected files changed; inspect before installing'}
    foreach($d2File in Get-ChildItem (Join-Path $d2Backup 'installed-mod') -File){if((Get-FileHash $d2File.FullName).Hash-ne(Get-FileHash (Join-Path $d2Target $d2File.Name)).Hash){throw 'Installed mod changed since D2 backup'}}
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'bin\Release\net9.0\RinArcherCore.dll'),(Join-Path $PSScriptRoot 'RinArcherCore.json') -Destination $d2Target -Force
    & (Join-Path $PSScriptRoot 'LaunchMilestoneD2Playtest.ps1') -PrepareOnly
}
$d2Mismatches=@(Get-D2ProtectedMismatches)
$d2Payload=@(foreach($d2Name in @('RinArcherCore.dll','RinArcherCore.json')){$d2Built=if($d2Name.EndsWith('.dll')){Join-Path $PSScriptRoot "bin\Release\net9.0\$d2Name"}else{Join-Path $PSScriptRoot $d2Name};if((Get-FileHash $d2Built).Hash-ne(Get-FileHash (Join-Path $d2Target $d2Name)).Hash){$d2Name}})
$d2Human=Join-Path $PSScriptRoot 'd2-human-runtime\mods\RinArcherCore'
$d2HumanMismatches=@(foreach($d2Name in @('RinArcherCore.dll','RinArcherCore.json')){if(!(Test-Path (Join-Path $d2Human $d2Name))-or(Get-FileHash (Join-Path $d2Human $d2Name)).Hash-ne(Get-FileHash (Join-Path $d2Target $d2Name)).Hash){$d2Name}})
$d2Tests=@(Get-ChildItem -LiteralPath $d2Target,(Join-Path $PSScriptRoot 'd2-human-runtime\mods') -File -Recurse|Where-Object Name -Match '^RinArcherCoreTests').Count-gt0
$d2Result=@{version='0.5.0';backup=$d2Backup;protectedFiles=$d2Protected.Count;protectedMismatches=$d2Mismatches;payloadMismatches=$d2Payload;humanPayloadMismatches=$d2HumanMismatches;installedDllSha256=(Get-FileHash (Join-Path $d2Target 'RinArcherCore.dll')).Hash;installedManifestSha256=(Get-FileHash (Join-Path $d2Target 'RinArcherCore.json')).Hash;humanDllSha256=(Get-FileHash (Join-Path $d2Human 'RinArcherCore.dll')).Hash;testDriverInstalled=$d2Tests;updatedPayload=@('RinArcherCore.dll','RinArcherCore.json');humanQA='PENDING';D1ManualProfile='PRESERVED'}
$d2Result|ConvertTo-Json -Depth 5|Set-Content (Join-Path $d2Report 'install-verification.json') -Encoding utf8
if($d2Mismatches.Count-or$d2Payload.Count-or$d2HumanMismatches.Count-or$d2Tests){throw 'D2 installation verification failed'}
$d2Result|ConvertTo-Json -Depth 5

