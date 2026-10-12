param([switch]$VerifyOnly)
$ErrorActionPreference='Stop'
$bRoot=$PSScriptRoot
$bBackup=(Get-Content -LiteralPath (Join-Path $bRoot 'reports\milestone-b\backup-path.txt') -Raw).Trim()
$bTarget='E:\SteamLibrary\steamapps\common\Slay the Spire 2\mods\RinArcherCore'
$bPayload=@((Join-Path $bRoot 'bin\Release\net9.0\RinArcherCore.dll'),(Join-Path $bRoot 'RinArcherCore.json'))
if(!$VerifyOnly){
    if(Get-Process SlayTheSpire2 -ErrorAction SilentlyContinue | Where-Object Path -EQ 'E:\SteamLibrary\steamapps\common\Slay the Spire 2\SlayTheSpire2.exe'){throw 'Original game running; update postponed'}
    foreach($bFile in Get-ChildItem -LiteralPath (Join-Path $bBackup 'installed-mod') -File){
        $bLive=Join-Path $bTarget $bFile.Name
        if((Get-FileHash -LiteralPath $bFile.FullName).Hash -ne (Get-FileHash -LiteralPath $bLive).Hash){throw "Installed A changed since baseline: $bLive"}
    }
    foreach($bFile in $bPayload){Copy-Item -LiteralPath $bFile -Destination $bTarget -Force}
}
$bBefore=@(Get-Content -LiteralPath (Join-Path $bBackup 'protected-before.json') -Raw | ConvertFrom-Json)
$bMismatch=@(foreach($bEntry in $bBefore){if(!(Test-Path -LiteralPath $bEntry.path) -or (Get-FileHash -LiteralPath $bEntry.path).Hash -ne $bEntry.sha256){$bEntry.path}})
$bPayloadMismatch=@(foreach($bFile in $bPayload){$bLive=Join-Path $bTarget (Split-Path $bFile -Leaf);if((Get-FileHash -LiteralPath $bFile).Hash -ne (Get-FileHash -LiteralPath $bLive).Hash){$bLive}})
$bResult=@{backup=$bBackup;protectedFiles=$bBefore.Count;protectedMismatches=$bMismatch;payloadMismatches=$bPayloadMismatch;dllSha256=(Get-FileHash -LiteralPath (Join-Path $bTarget 'RinArcherCore.dll')).Hash;manifestSha256=(Get-FileHash -LiteralPath (Join-Path $bTarget 'RinArcherCore.json')).Hash;onlyTargetModUpdated=$true}
$bResult | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $bRoot 'reports\milestone-b\install-verification.json') -Encoding utf8
if($bMismatch.Count -or $bPayloadMismatch.Count){throw 'B install hash mismatch; inspect install-verification.json'}
$bResult | ConvertTo-Json -Depth 4
