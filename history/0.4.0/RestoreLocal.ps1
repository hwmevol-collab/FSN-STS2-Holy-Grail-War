param([string]$Baseline)
$ErrorActionPreference='Stop'
$sliceMods='E:\SteamLibrary\steamapps\common\Slay the Spire 2\mods'
if(!$Baseline){$Baseline=(Get-Content -LiteralPath (Join-Path $PSScriptRoot 'reports\install-backup-path.txt') -Raw).Trim()}
if(Get-Process SlayTheSpire2 -ErrorAction SilentlyContinue | Where-Object Path -EQ 'E:\SteamLibrary\steamapps\common\Slay the Spire 2\SlayTheSpire2.exe'){throw 'Close the original game before restoring mods'}
$slicePayload=Get-Content -LiteralPath (Join-Path $Baseline 'payload-installed.json') -Raw | ConvertFrom-Json
foreach($sliceFile in $slicePayload){if(!(Test-Path -LiteralPath $sliceFile.path) -or (Get-FileHash -LiteralPath $sliceFile.path).Hash -ne $sliceFile.sha256){throw "Installed payload has changed; preserve and review: $($sliceFile.path)"}}
$sliceResolvedMods=[IO.Path]::GetFullPath($sliceMods).TrimEnd('\')+'\'
$sliceTargets=@(foreach($sliceName in @('BaseLib','STS2-RitsuLib','RinArcherCore')){
    $sliceTarget=(Resolve-Path -LiteralPath (Join-Path $sliceMods $sliceName)).Path
    if(!$sliceTarget.StartsWith($sliceResolvedMods,[StringComparison]::OrdinalIgnoreCase)){throw 'Restore target escaped the exact mods directory'}
    if((Get-Item -LiteralPath $sliceTarget).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Restore target is a reparse point'}
    $sliceExpected=@($slicePayload | Where-Object {$_.path.StartsWith($sliceTarget+'\',[StringComparison]::OrdinalIgnoreCase)})
    if(@(Get-ChildItem -LiteralPath $sliceTarget -File -Recurse).Count -ne $sliceExpected.Count){throw "Extra files in $sliceTarget; review before restoring"}
    $sliceTarget
})
$sliceArchive=Join-Path $Baseline "restored-payload-$((Get-Date).ToString('yyyyMMdd-HHmmss'))"
New-Item -ItemType Directory -Path $sliceArchive | Out-Null
foreach($sliceTarget in $sliceTargets){Move-Item -LiteralPath $sliceTarget -Destination $sliceArchive}
# Original mods were empty at installation. Real saves were never changed and are not overwritten.
Write-Output "Removed only the three verified new mod directories by moving them to $sliceArchive"
