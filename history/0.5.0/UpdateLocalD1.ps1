param([switch]$VerifyOnly)
$ErrorActionPreference='Stop'
$d1Root=$PSScriptRoot
$d1Report=Join-Path $d1Root 'reports\milestone-d1'
$d1Backup=(Get-Content -LiteralPath (Join-Path $d1Report 'backup-path.txt') -Raw).Trim()
$d1Target='E:\SteamLibrary\steamapps\common\Slay the Spire 2\mods\RinArcherCore'
$d1Before=@(Get-Content -LiteralPath (Join-Path $d1Backup 'protected-before.json') -Raw | ConvertFrom-Json)
function Get-D1Mismatches {@(foreach($entry in $d1Before){if(!(Test-Path -LiteralPath $entry.path)-or(Get-FileHash -LiteralPath $entry.path).Hash-ne$entry.sha256){$entry.path}})}
if(!$VerifyOnly){
    if(Get-Process SlayTheSpire2 -ErrorAction SilentlyContinue | Where-Object Path -EQ 'E:\SteamLibrary\steamapps\common\Slay the Spire 2\SlayTheSpire2.exe'){throw 'User game is running; target update postponed'}
    if((Get-D1Mismatches).Count){throw 'Protected files drifted; inspect without overwriting user data'}
    foreach($file in Get-ChildItem -LiteralPath (Join-Path $d1Backup 'installed-mod') -File){if((Get-FileHash -LiteralPath $file.FullName).Hash-ne(Get-FileHash -LiteralPath (Join-Path $d1Target $file.Name)).Hash){throw 'Installed C payload changed since preflight'}}
    $d1Gate=Get-Content -LiteralPath (Join-Path $d1Report 'acceptance.json') -Raw | ConvertFrom-Json
    if($d1Gate.status-ne'RIN_ARCHER_RUN_CORE_D1_PASS'){throw 'D1 engineering acceptance gate failed'}
    if((Get-FileHash -LiteralPath (Join-Path $d1Root 'bin\Release\net9.0\RinArcherCore.dll')).Hash-ne$d1Gate.testedDllSha256){throw 'DLL differs from accepted native test payload'}
    $d1Paths=@(Get-ChildItem -LiteralPath 'E:\SteamLibrary\steamapps\common\Slay the Spire 2\mods' -File -Recurse | Where-Object {$_.FullName-notlike "$d1Target\*"} | Select-Object -ExpandProperty FullName)
    $d1Profile=Join-Path $env:APPDATA 'SlayTheSpire2'
    if(Test-Path -LiteralPath $d1Profile){$d1Paths+=Get-ChildItem -LiteralPath $d1Profile -File -Recurse | Select-Object -ExpandProperty FullName}
    $d1Seen=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase);foreach($entry in $d1Before){[void]$d1Seen.Add($entry.path)}
    foreach($path in $d1Paths){if($d1Seen.Add($path)){$d1Before+=@{path=$path;sha256=(Get-FileHash -LiteralPath $path).Hash}}}
    $d1Before | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $d1Backup 'protected-before.json') -Encoding utf8
    Copy-Item -LiteralPath (Join-Path $d1Root 'bin\Release\net9.0\RinArcherCore.dll'),(Join-Path $d1Root 'RinArcherCore.json') -Destination $d1Target -Force
}
$d1ProtectedMismatch=@(Get-D1Mismatches)
$d1PayloadMismatch=@(foreach($file in @((Join-Path $d1Root 'bin\Release\net9.0\RinArcherCore.dll'),(Join-Path $d1Root 'RinArcherCore.json'))){if((Get-FileHash -LiteralPath $file).Hash-ne(Get-FileHash -LiteralPath (Join-Path $d1Target (Split-Path $file -Leaf))).Hash){$file}})
$d1Result=@{version='0.4.0';backup=$d1Backup;protectedFiles=$d1Before.Count;protectedMismatches=$d1ProtectedMismatch;payloadMismatches=$d1PayloadMismatch;installedDllSha256=(Get-FileHash -LiteralPath (Join-Path $d1Target 'RinArcherCore.dll')).Hash;onlyTargetDllAndJsonUpdated=$true;testDriverInstalled=@(Get-ChildItem -LiteralPath $d1Target -File -Recurse | Where-Object Name -Match '^RinArcherCoreTests').Count -gt 0}
$d1Result | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $d1Report 'install-verification.json') -Encoding utf8
if($d1ProtectedMismatch.Count-or$d1PayloadMismatch.Count-or$d1Result.testDriverInstalled){throw 'D1 installation verification failed'}
$d1Result | ConvertTo-Json -Depth 4
