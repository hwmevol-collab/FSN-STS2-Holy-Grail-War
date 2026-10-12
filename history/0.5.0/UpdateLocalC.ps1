param([switch]$VerifyOnly)
$ErrorActionPreference='Stop'
$cRoot=$PSScriptRoot
$cReport=Join-Path $cRoot 'reports\milestone-c'
$cBackup=(Get-Content -LiteralPath (Join-Path $cReport 'backup-path.txt') -Raw).Trim()
$cTarget='E:\SteamLibrary\steamapps\common\Slay the Spire 2\mods\RinArcherCore'
$cBefore=@(Get-Content -LiteralPath (Join-Path $cBackup 'protected-before.json') -Raw | ConvertFrom-Json)
function Mismatches {@(foreach($entry in $cBefore){if(!(Test-Path -LiteralPath $entry.path)-or(Get-FileHash -LiteralPath $entry.path).Hash-ne$entry.sha256){$entry.path}})}
if(!$VerifyOnly){
    if(Get-Process SlayTheSpire2 -ErrorAction SilentlyContinue | Where-Object Path -EQ 'E:\SteamLibrary\steamapps\common\Slay the Spire 2\SlayTheSpire2.exe'){throw 'User game is running; target update postponed'}
    if((Mismatches).Count){throw 'Protected files drifted; inspect without overwriting user data'}
    foreach($file in Get-ChildItem -LiteralPath (Join-Path $cBackup 'installed-mod') -File){if((Get-FileHash -LiteralPath $file.FullName).Hash-ne(Get-FileHash -LiteralPath (Join-Path $cTarget $file.Name)).Hash){throw 'Installed B payload changed since preflight'}}
    foreach($resultName in @('core-test-results.json','alpha-test-results.json','highlight-test-results.json','reward-test-results.json')){if((Get-Content -LiteralPath (Join-Path $cReport $resultName) -Raw | ConvertFrom-Json).status-ne'PASS'){throw 'Automated gate failed'}}
    if((Get-Content -LiteralPath (Join-Path $cReport 'graphical\results.json') -Raw | ConvertFrom-Json).status-ne'PASS'){throw 'Graphical gate failed'}
    # Extend protection to every currently present file; retain original hashes for old entries.
    $cPaths=@(Get-ChildItem -LiteralPath 'E:\SteamLibrary\steamapps\common\Slay the Spire 2\mods' -File -Recurse | Where-Object {$_.FullName-notlike "$cTarget\*"} | Select-Object -ExpandProperty FullName)
    $cProfile=Join-Path $env:APPDATA 'SlayTheSpire2'
    if(Test-Path -LiteralPath $cProfile){$cPaths+=Get-ChildItem -LiteralPath $cProfile -File -Recurse | Select-Object -ExpandProperty FullName}
    $cSeen=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase);foreach($entry in $cBefore){[void]$cSeen.Add($entry.path)}
    foreach($path in $cPaths){if($cSeen.Add($path)){$cBefore+=@{path=$path;sha256=(Get-FileHash -LiteralPath $path).Hash}}}
    $cBefore | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $cBackup 'protected-before.json') -Encoding utf8
    Copy-Item -LiteralPath (Join-Path $cRoot 'bin\Release\net9.0\RinArcherCore.dll'),(Join-Path $cRoot 'RinArcherCore.json') -Destination $cTarget -Force
}
$cProtectedMismatch=@(Mismatches)
$cPayloadMismatch=@(foreach($file in @((Join-Path $cRoot 'bin\Release\net9.0\RinArcherCore.dll'),(Join-Path $cRoot 'RinArcherCore.json'))){if((Get-FileHash -LiteralPath $file).Hash-ne(Get-FileHash -LiteralPath (Join-Path $cTarget (Split-Path $file -Leaf))).Hash){$file}})
$cResult=@{version='0.3.0';backup=$cBackup;protectedFiles=$cBefore.Count;protectedMismatches=$cProtectedMismatch;payloadMismatches=$cPayloadMismatch;installedDllSha256=(Get-FileHash -LiteralPath (Join-Path $cTarget 'RinArcherCore.dll')).Hash;onlyTargetDllAndJsonUpdated=$true;testDriverInstalled=$false}
$cResult | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $cReport 'install-verification.json') -Encoding utf8
if($cProtectedMismatch.Count-or$cPayloadMismatch.Count){throw 'C installation verification failed'}
$cResult | ConvertTo-Json -Depth 4
