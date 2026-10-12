$ErrorActionPreference='Stop'
$focusRoot=Join-Path $PSScriptRoot 'reports\d2-rest-focus-highlight'
$focusBackup=(Get-Content (Join-Path $focusRoot 'backup-path.txt') -Raw).Trim()
$focusReceipt=Get-Content (Join-Path $focusRoot 'install-verification.json') -Raw|ConvertFrom-Json
if(Get-CimInstance Win32_Process -Filter "Name='SlayTheSpire2.exe'"){throw 'Game is open; preserve session'}
$focusTargets=@(@{backup='installed-mod';target='E:\SteamLibrary\steamapps\common\Slay the Spire 2\mods\RinArcherCore'},@{backup='manual-mod';target=(Join-Path $PSScriptRoot 'd2-human-runtime\mods\RinArcherCore')})
foreach($dir in $focusTargets){
    if((Get-FileHash (Join-Path $dir.target 'RinArcherCore.dll')).Hash-ne$focusReceipt.installedDllSha256){throw 'Installed payload changed; restore aborted'}
    if((Get-FileHash (Join-Path $dir.target 'RinArcherCore.json')).Hash-ne$focusReceipt.installedManifestSha256){throw 'Installed manifest changed; restore aborted'}
}
foreach($dir in $focusTargets){
    foreach($name in @('RinArcherCore.dll','RinArcherCore.json')){Copy-Item -LiteralPath (Join-Path $focusBackup "$($dir.backup)\$name") -Destination (Join-Path $dir.target $name) -Force;if((Get-FileHash (Join-Path $dir.target $name)).Hash-ne(Get-FileHash (Join-Path $focusBackup "$($dir.backup)\$name")).Hash){throw 'Restore readback mismatch'}}
}
Write-Output 'D2 v0.5.0 payload restored in installed and manual runtime; all profiles preserved.'
