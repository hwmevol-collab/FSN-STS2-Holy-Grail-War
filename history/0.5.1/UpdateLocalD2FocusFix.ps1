param([switch]$VerifyOnly)
$ErrorActionPreference='Stop'
$focusRoot=Join-Path $PSScriptRoot 'reports\d2-rest-focus-highlight'
$focusBackup=(Get-Content (Join-Path $focusRoot 'backup-path.txt') -Raw).Trim()
$focusGate=Get-Content (Join-Path $focusRoot 'acceptance.json') -Raw|ConvertFrom-Json
$focusTarget='E:\SteamLibrary\steamapps\common\Slay the Spire 2\mods\RinArcherCore'
$focusManual=Join-Path $PSScriptRoot 'd2-human-runtime\mods\RinArcherCore'
$focusHash=(Get-FileHash (Join-Path $PSScriptRoot 'bin\Release\net9.0\RinArcherCore.dll')).Hash
if($focusGate.status-ne'D2_REST_FOCUS_HIGHLIGHT_ARBITRATION_PASS'-or$focusGate.testedDllSha256-ne$focusHash){throw 'Focus fix engineering gate mismatch'}
$focusProtected=@(Get-Content (Join-Path $focusBackup 'protected-before.json') -Raw|ConvertFrom-Json)
function Get-FocusProtectedMismatches {@($focusProtected|Where-Object {!(Test-Path -LiteralPath $_.path)-or(Get-FileHash $_.path).Hash-ne$_.sha256}|ForEach-Object path)}
if(!$VerifyOnly){
    if(Get-CimInstance Win32_Process -Filter "Name='SlayTheSpire2.exe'"){throw 'Game is open; preserve session'}
    if((Get-FocusProtectedMismatches).Count){throw 'Protected state changed'}
    foreach($dir in @(@{backup='installed-mod';target=$focusTarget},@{backup='manual-mod';target=$focusManual})){foreach($file in Get-ChildItem (Join-Path $focusBackup $dir.backup) -File -Recurse){$relative=[IO.Path]::GetRelativePath((Join-Path $focusBackup $dir.backup),$file.FullName);if((Get-FileHash $file.FullName).Hash-ne(Get-FileHash (Join-Path $dir.target $relative)).Hash){throw 'Target mod changed since backup'}}}
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'bin\Release\net9.0\RinArcherCore.dll'),(Join-Path $PSScriptRoot 'RinArcherCore.json') -Destination $focusTarget -Force
    & (Join-Path $PSScriptRoot 'LaunchMilestoneD2Playtest.ps1') -PrepareOnly
}
$focusPayloadMismatches=@(foreach($name in @('RinArcherCore.dll','RinArcherCore.json')){$built=if($name.EndsWith('.dll')){Join-Path $PSScriptRoot "bin\Release\net9.0\$name"}else{Join-Path $PSScriptRoot $name};foreach($target in @($focusTarget,$focusManual)){if((Get-FileHash $built).Hash-ne(Get-FileHash (Join-Path $target $name)).Hash){Join-Path $target $name}}})
$focusProtectedMismatches=@(Get-FocusProtectedMismatches)
$focusTests=@(Get-ChildItem -LiteralPath $focusTarget,(Join-Path $PSScriptRoot 'd2-human-runtime\mods') -Recurse -File|Where-Object Name -Match '^RinArcherCoreTests').Count-gt0
@{status=if($focusPayloadMismatches.Count-or$focusProtectedMismatches.Count-or$focusTests){'FAIL'}else{'PASS'};version='0.5.1';backup=$focusBackup;installedDllSha256=(Get-FileHash (Join-Path $focusTarget 'RinArcherCore.dll')).Hash;installedManifestSha256=(Get-FileHash (Join-Path $focusTarget 'RinArcherCore.json')).Hash;manualDllSha256=(Get-FileHash (Join-Path $focusManual 'RinArcherCore.dll')).Hash;payloadMismatches=$focusPayloadMismatches;protectedFiles=$focusProtected.Count;protectedMismatches=$focusProtectedMismatches;testDriverInstalled=$focusTests;D1AndD2ManualProfiles='PRESERVED';humanFocusRecheck='PENDING';updatedPayload=@('RinArcherCore.dll','RinArcherCore.json')}|ConvertTo-Json -Depth 5|Set-Content (Join-Path $focusRoot 'install-verification.json')
if($focusPayloadMismatches.Count-or$focusProtectedMismatches.Count-or$focusTests){throw 'Installation verification failed'}
Get-Content (Join-Path $focusRoot 'install-verification.json')
