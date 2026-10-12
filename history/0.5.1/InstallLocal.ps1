param([switch]$VerifyOnly,[string]$Baseline)
$ErrorActionPreference='Stop'
$sliceRoot=$PSScriptRoot
$sliceGame='E:\SteamLibrary\steamapps\common\Slay the Spire 2'
$sliceMods=Join-Path $sliceGame 'mods'
$sliceSaves=Join-Path $env:APPDATA 'SlayTheSpire2'
$sliceWorkshop='E:\SteamLibrary\steamapps\workshop\content\2868840'
function Get-ProtectedManifest {
    $sliceFiles=@()
    if(Test-Path -LiteralPath $sliceSaves){$sliceFiles+=Get-ChildItem -LiteralPath $sliceSaves -File -Recurse -Force}
    $sliceFiles+=Get-ChildItem -LiteralPath (Join-Path $sliceGame 'data_sts2_windows_x86_64') -File
    $sliceFiles+=Get-ChildItem -LiteralPath $sliceGame -File | Where-Object Extension -In '.exe','.dll','.pck','.json'
    $sliceFiles+=Get-ChildItem -LiteralPath $sliceWorkshop -File -Recurse | Where-Object FullName -Match '\\(3737335127|3737336234)\\'
    foreach($slicePart in @('src','scripts','tests')){
        $sliceOld=Join-Path 'E:\BaiduNetdiskDownload\FSN' $slicePart
        if(Test-Path -LiteralPath $sliceOld){$sliceFiles+=Get-ChildItem -LiteralPath $sliceOld -File -Recurse | Where-Object {$_.Extension -in '.cs','.csproj','.ps1','.json' -and $_.FullName -notmatch '\\(bin|obj)\\'}}
    }
    $sliceFiles | Sort-Object FullName -Unique | ForEach-Object {@{path=$_.FullName;sha256=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash}}
}
if(!$VerifyOnly){
    if(Get-Process SlayTheSpire2 -ErrorAction SilentlyContinue | Where-Object Path -EQ (Join-Path $sliceGame 'SlayTheSpire2.exe')){throw 'Original game is running; local installation cannot replace loaded DLLs'}
    $sliceBackup=Join-Path $sliceRoot "backups\$((Get-Date).ToString('yyyyMMdd-HHmmss'))"
    New-Item -ItemType Directory -Path $sliceBackup -Force | Out-Null
    foreach($sliceSource in @($sliceMods,$sliceSaves)){
        if(Test-Path -LiteralPath $sliceSource){
            if(Get-ChildItem -LiteralPath $sliceSource -Recurse -Force | Where-Object {$_.Attributes -band [IO.FileAttributes]::ReparsePoint}){throw "Reparse point in backup source: $sliceSource"}
            Copy-Item -LiteralPath $sliceSource -Destination (Join-Path $sliceBackup (Split-Path $sliceSource -Leaf)) -Recurse -Force
        }
    }
    $sliceProtected=@(Get-ProtectedManifest)
    $sliceProtected | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $sliceBackup 'protected-before.json') -Encoding utf8
    $sliceOldMods=@(Get-ChildItem -LiteralPath $sliceMods -File -Recurse -Force | ForEach-Object {@{path=$_.FullName;sha256=(Get-FileHash -LiteralPath $_.FullName).Hash}})
    ConvertTo-Json -InputObject $sliceOldMods -Depth 4 | Set-Content -LiteralPath (Join-Path $sliceBackup 'mods-before.json') -Encoding utf8
    foreach($sliceName in @('BaseLib','STS2-RitsuLib','RinArcherCore')){
        $sliceTarget=Join-Path $sliceMods $sliceName
        if(Test-Path -LiteralPath $sliceTarget){throw "Target already exists; review backed-up target before replacement: $sliceTarget"}
    }
    foreach($sliceName in @('BaseLib','STS2-RitsuLib','RinArcherCore')){
        $sliceTarget=Join-Path $sliceMods $sliceName
        New-Item -ItemType Directory -Path $sliceTarget -Force | Out-Null
    }
    Copy-Item -Path (Join-Path $sliceWorkshop '3737335127\BaseLib\*') -Destination (Join-Path $sliceMods 'BaseLib') -Recurse
    Copy-Item -Path (Join-Path $sliceRoot 'dependencies\*') -Destination (Join-Path $sliceMods 'STS2-RitsuLib') -Recurse
    Copy-Item -LiteralPath (Join-Path $sliceRoot 'RinArcherCore.json'),(Join-Path $sliceRoot 'bin\Release\net9.0\RinArcherCore.dll') -Destination (Join-Path $sliceMods 'RinArcherCore')
    $slicePayload=@(Get-ChildItem -LiteralPath $sliceMods -File -Recurse | ForEach-Object {@{path=$_.FullName;sha256=(Get-FileHash -LiteralPath $_.FullName).Hash}})
    $slicePayload | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $sliceBackup 'payload-installed.json') -Encoding utf8
    $Baseline=$sliceBackup
    $Baseline | Set-Content -LiteralPath (Join-Path $sliceRoot 'reports\install-backup-path.txt')
}
if(!$Baseline){$Baseline=(Get-Content -LiteralPath (Join-Path $sliceRoot 'reports\install-backup-path.txt') -Raw).Trim()}
$sliceBefore=Get-Content -LiteralPath (Join-Path $Baseline 'protected-before.json') -Raw | ConvertFrom-Json
$sliceMismatch=@(foreach($sliceEntry in $sliceBefore){if(!(Test-Path -LiteralPath $sliceEntry.path) -or (Get-FileHash -LiteralPath $sliceEntry.path).Hash -ne $sliceEntry.sha256){$sliceEntry.path}})
$sliceSources=@(@{source=(Join-Path $sliceRoot 'dependencies');target=(Join-Path $sliceMods 'STS2-RitsuLib')},@{source=(Join-Path $sliceWorkshop '3737335127\BaseLib');target=(Join-Path $sliceMods 'BaseLib')})
$slicePayloadMismatch=@(foreach($slicePair in $sliceSources){foreach($sliceFile in Get-ChildItem -LiteralPath $slicePair.source -File -Recurse){$sliceRelative=[IO.Path]::GetRelativePath($slicePair.source,$sliceFile.FullName);$sliceInstalled=Join-Path $slicePair.target $sliceRelative;if((Get-FileHash -LiteralPath $sliceFile.FullName).Hash -ne (Get-FileHash -LiteralPath $sliceInstalled).Hash){$sliceInstalled}}};foreach($sliceFile in @((Join-Path $sliceRoot 'RinArcherCore.json'),(Join-Path $sliceRoot 'bin\Release\net9.0\RinArcherCore.dll'))){$sliceInstalled=Join-Path $sliceMods "RinArcherCore\$(Split-Path $sliceFile -Leaf)";if((Get-FileHash -LiteralPath $sliceFile).Hash -ne (Get-FileHash -LiteralPath $sliceInstalled).Hash){$sliceInstalled}})
$sliceReport=@{baseline=$Baseline;protectedFiles=$sliceBefore.Count;mismatches=$sliceMismatch;payloadMismatches=$slicePayloadMismatch;installedDllSha256=(Get-FileHash -LiteralPath (Join-Path $sliceMods 'RinArcherCore\RinArcherCore.dll')).Hash}
$sliceReport | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $sliceRoot 'reports\protected-install-verification.json') -Encoding utf8
if($sliceMismatch.Count -gt 0 -or $slicePayloadMismatch.Count -gt 0){throw 'Hash verification failed; inspect verification report'}
$sliceReport | ConvertTo-Json -Depth 4
