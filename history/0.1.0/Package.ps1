$ErrorActionPreference='Stop'
$sliceRoot=$PSScriptRoot
$sliceDist=Join-Path $sliceRoot 'dist'
$sliceStamp=(Get-Date).ToString('yyyyMMdd-HHmmss')
$sliceStage=Join-Path $sliceDist "stage-$sliceStamp"
New-Item -ItemType Directory -Path $sliceStage -Force | Out-Null
$sliceLocal=Join-Path $sliceStage 'local\mods'
New-Item -ItemType Directory -Path $sliceLocal -Force | Out-Null
foreach($sliceName in @('BaseLib','STS2-RitsuLib','RinArcherCore')){Copy-Item -LiteralPath "E:\SteamLibrary\steamapps\common\Slay the Spire 2\mods\$sliceName" -Destination $sliceLocal -Recurse}
Copy-Item -LiteralPath (Join-Path $sliceRoot 'README.md') -Destination (Join-Path $sliceStage 'local')
$sliceSource=Join-Path $sliceStage 'source'
New-Item -ItemType Directory -Path $sliceSource -Force | Out-Null
$sliceSources=@(Get-ChildItem -LiteralPath $sliceRoot -File | Where-Object Extension -In '.cs','.csproj','.json','.ps1','.md')
foreach($sliceDir in @('Content','Runtime','Compatibility','UI','QA','tests')){$sliceSources+=Get-ChildItem -LiteralPath (Join-Path $sliceRoot $sliceDir) -File -Recurse | Where-Object {$_.Extension -in '.cs','.csproj','.json' -and $_.FullName -notmatch '\\(bin|obj)\\'}}
foreach($sliceFile in $sliceSources){$sliceRelative=[IO.Path]::GetRelativePath($sliceRoot,$sliceFile.FullName);$sliceDest=Join-Path $sliceSource $sliceRelative;New-Item -ItemType Directory -Path (Split-Path $sliceDest) -Force | Out-Null;Copy-Item -LiteralPath $sliceFile.FullName -Destination $sliceDest}
Copy-Item -LiteralPath (Join-Path $sliceRoot 'dependencies') -Destination $sliceSource -Recurse
$sliceEvidence=Join-Path $sliceStage 'evidence'
Copy-Item -LiteralPath (Join-Path $sliceRoot 'reports') -Destination $sliceEvidence -Recurse
$sliceSummary=@()
foreach($sliceKind in @('local','source','evidence')){
    $sliceZip=Join-Path $sliceDist "RinArcherCore-0.1.0-$sliceKind.zip"
    if(Test-Path -LiteralPath $sliceZip){Move-Item -LiteralPath $sliceZip -Destination (Join-Path $sliceDist "$sliceStamp-previous-$sliceKind.zip")}
    Compress-Archive -Path (Join-Path $sliceStage "$sliceKind\*") -DestinationPath $sliceZip -CompressionLevel Optimal
    $sliceRead=[IO.Compression.ZipFile]::OpenRead($sliceZip)
    try{
        if($sliceKind -eq 'local' -and @($sliceRead.Entries | Where-Object FullName -Match 'RinArcherCoreTests').Count){throw 'Test assembly leaked into local install package'}
        foreach($sliceEntry in $sliceRead.Entries){if($sliceEntry.Length -gt 0){$sliceStream=$sliceEntry.Open();try{$sliceStream.CopyTo([IO.Stream]::Null)}finally{$sliceStream.Dispose()}}}
        $sliceSummary+=@{kind=$sliceKind;path=$sliceZip;entries=$sliceRead.Entries.Count;sha256=(Get-FileHash -LiteralPath $sliceZip).Hash;allEntriesRead=$true}
    }finally{$sliceRead.Dispose()}
}
$sliceSummary | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $sliceRoot 'reports\package-verification.json') -Encoding utf8
$sliceSummary | ConvertTo-Json -Depth 4
