param([switch]$VerifyOnly)
$ErrorActionPreference='Stop'
$highlightRoot=$PSScriptRoot
$highlightReport=Join-Path $highlightRoot 'reports\self-target-highlight'
$highlightBackup=(Get-Content -LiteralPath (Join-Path $highlightReport 'backup-path.txt') -Raw).Trim()
$highlightTarget='E:\SteamLibrary\steamapps\common\Slay the Spire 2\mods\RinArcherCore'
$highlightPayload=@((Join-Path $highlightRoot 'bin\Release\net9.0\RinArcherCore.dll'),(Join-Path $highlightRoot 'RinArcherCore.json'))
$highlightBefore=@(Get-Content -LiteralPath (Join-Path $highlightBackup 'protected-before.json') -Raw | ConvertFrom-Json)
function ProtectedMismatch {@(foreach($entry in $highlightBefore){if(!(Test-Path -LiteralPath $entry.path)-or(Get-FileHash -LiteralPath $entry.path).Hash-ne$entry.sha256){$entry.path}})}
if(!$VerifyOnly){
    if(Get-Process SlayTheSpire2 -ErrorAction SilentlyContinue | Where-Object Path -EQ 'E:\SteamLibrary\steamapps\common\Slay the Spire 2\SlayTheSpire2.exe'){throw 'Original game running; update postponed'}
    if((ProtectedMismatch).Count){throw 'Protected files changed since baseline; inspect before installing'}
    foreach($file in Get-ChildItem -LiteralPath (Join-Path $highlightBackup 'installed-mod') -File){
        if((Get-FileHash -LiteralPath $file.FullName).Hash-ne(Get-FileHash -LiteralPath (Join-Path $highlightTarget $file.Name)).Hash){throw 'Installed mod changed since bugfix backup'}
    }
    foreach($file in $highlightPayload){Copy-Item -LiteralPath $file -Destination $highlightTarget -Force}
}
$highlightMismatch=@(ProtectedMismatch)
$highlightPayloadMismatch=@(foreach($file in $highlightPayload){if((Get-FileHash -LiteralPath $file).Hash-ne(Get-FileHash -LiteralPath (Join-Path $highlightTarget (Split-Path $file -Leaf))).Hash){$file}})
$highlightResult=@{backup=$highlightBackup;version='0.2.1';protectedFiles=$highlightBefore.Count;protectedMismatches=$highlightMismatch;payloadMismatches=$highlightPayloadMismatch;dllSha256=(Get-FileHash -LiteralPath (Join-Path $highlightTarget 'RinArcherCore.dll')).Hash;onlyTargetModUpdated=$true}
$highlightResult | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $highlightReport 'install-verification.json') -Encoding utf8
if($highlightMismatch.Count-or$highlightPayloadMismatch.Count){throw 'Highlight fix install verification failed'}
$highlightResult | ConvertTo-Json -Depth 4
