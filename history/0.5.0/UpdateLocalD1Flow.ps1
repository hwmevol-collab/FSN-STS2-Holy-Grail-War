param([switch]$VerifyOnly)
$ErrorActionPreference='Stop'
$fixRoot=$PSScriptRoot
$fixReport=Join-Path $fixRoot 'reports\d1-native-container-flow'
$fixBackup=(Get-Content -LiteralPath (Join-Path $fixReport 'backup-path.txt') -Raw).Trim()
$fixTarget='E:\SteamLibrary\steamapps\common\Slay the Spire 2\mods\RinArcherCore'
$fixBefore=@(Get-Content -LiteralPath (Join-Path $fixBackup 'protected-before.json') -Raw | ConvertFrom-Json)
function Get-FixMismatches { @($fixBefore | Where-Object {!(Test-Path -LiteralPath $_.path) -or (Get-FileHash -LiteralPath $_.path).Hash -ne $_.sha256} | ForEach-Object path) }
if(!$VerifyOnly){
    if(Get-CimInstance Win32_Process -Filter "Name='SlayTheSpire2.exe'" | Where-Object {$_.ExecutablePath -eq 'E:\SteamLibrary\steamapps\common\Slay the Spire 2\SlayTheSpire2.exe' -or $_.ExecutablePath -eq (Join-Path $fixRoot 'd1-human-runtime\SlayTheSpire2.exe')}){throw 'The user game/playtest is open; payload update is postponed'}
    if((Get-FixMismatches).Count){throw 'Protected files changed; inspect before updating'}
    foreach($file in Get-ChildItem -LiteralPath (Join-Path $fixBackup 'installed-mod') -File){if((Get-FileHash -LiteralPath $file.FullName).Hash -ne (Get-FileHash -LiteralPath (Join-Path $fixTarget $file.Name)).Hash){throw 'Installed payload changed since backup'}}
    $fixGate=Get-Content -LiteralPath (Join-Path $fixReport 'acceptance.json') -Raw | ConvertFrom-Json
    $fixHash=(Get-FileHash -LiteralPath (Join-Path $fixRoot 'bin\Release\net9.0\RinArcherCore.dll')).Hash
    if($fixGate.status -ne 'D1_NATIVE_CONTAINER_FLOW_PASS' -or $fixGate.testedDllSha256 -ne $fixHash){throw 'The built DLL is not the accepted test payload'}
    Copy-Item -LiteralPath (Join-Path $fixRoot 'bin\Release\net9.0\RinArcherCore.dll'),(Join-Path $fixRoot 'RinArcherCore.json') -Destination $fixTarget -Force
    $fixHuman=Join-Path $fixRoot 'd1-human-runtime\mods\RinArcherCore'
    if(Test-Path -LiteralPath $fixHuman){Copy-Item -LiteralPath (Join-Path $fixTarget 'RinArcherCore.dll'),(Join-Path $fixTarget 'RinArcherCore.json') -Destination $fixHuman -Force}
}
$fixMismatch=@(Get-FixMismatches)
$fixPayloadMismatch=@(foreach($name in @('RinArcherCore.dll','RinArcherCore.json')){
    $built=if($name.EndsWith('.dll')){Join-Path $fixRoot "bin\Release\net9.0\$name"}else{Join-Path $fixRoot $name}
    if((Get-FileHash -LiteralPath $built).Hash -ne (Get-FileHash -LiteralPath (Join-Path $fixTarget $name)).Hash){$name}
})
$fixHuman=Join-Path $fixRoot 'd1-human-runtime\mods\RinArcherCore'
$fixHumanMismatch=@(foreach($name in @('RinArcherCore.dll','RinArcherCore.json')){if(!(Test-Path -LiteralPath (Join-Path $fixHuman $name)) -or (Get-FileHash -LiteralPath (Join-Path $fixHuman $name)).Hash -ne (Get-FileHash -LiteralPath (Join-Path $fixTarget $name)).Hash){$name}})
$fixTestInstalled=@(Get-ChildItem -LiteralPath $fixTarget,(Join-Path $fixRoot 'd1-human-runtime\mods') -File -Recurse | Where-Object Name -Match '^RinArcherCoreTests').Count -gt 0
$fixResult=@{version='0.4.2';backup=$fixBackup;protectedFiles=$fixBefore.Count;protectedMismatches=$fixMismatch;payloadMismatches=$fixPayloadMismatch;humanPayloadMismatches=$fixHumanMismatch;installedDllSha256=(Get-FileHash -LiteralPath (Join-Path $fixTarget 'RinArcherCore.dll')).Hash;humanDllSha256=(Get-FileHash -LiteralPath (Join-Path $fixHuman 'RinArcherCore.dll')).Hash;testDriverInstalled=$fixTestInstalled;updatedPayload=@('RinArcherCore.dll','RinArcherCore.json');humanRetest='PENDING'}
$fixResult | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $fixReport 'install-verification.json') -Encoding utf8
if($fixMismatch.Count -or $fixPayloadMismatch.Count -or $fixHumanMismatch.Count -or $fixResult.testDriverInstalled){throw 'D1 fix installation verification failed'}
$fixResult | ConvertTo-Json -Depth 5
