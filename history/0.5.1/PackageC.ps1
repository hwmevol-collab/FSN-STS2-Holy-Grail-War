$ErrorActionPreference='Stop'
$cRoot=$PSScriptRoot
$cVersion=(Get-Content -LiteralPath (Join-Path $cRoot 'RinArcherCore.json') -Raw | ConvertFrom-Json).version
if($cVersion-ne'0.3.0'){throw 'PackageC only packages the frozen Milestone C payload'}
$cReport=Join-Path $cRoot 'reports\milestone-c'
$cGate=Get-Content -LiteralPath (Join-Path $cReport 'acceptance.json') -Raw | ConvertFrom-Json
if($cGate.status-ne'RIN_ARCHER_ALPHA_CARD_POOL_PASS'){throw 'Milestone C acceptance has not passed'}
$cDist=Join-Path $cRoot 'dist'
$cStamp=(Get-Date).ToString('yyyyMMdd-HHmmss')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,8)
$cStage=Join-Path $cDist "stage-c-$cStamp"
$cExtract=Join-Path $cDist "verified-c-$cStamp"
New-Item -ItemType Directory -Path $cStage,$cExtract -Force | Out-Null
$cLiveMods='E:\SteamLibrary\steamapps\common\Slay the Spire 2\mods'
$cLocal=Join-Path $cStage 'local'
New-Item -ItemType Directory -Path (Join-Path $cLocal 'mods') -Force | Out-Null
foreach($name in @('BaseLib','STS2-RitsuLib','RinArcherCore')){
    Copy-Item -LiteralPath (Join-Path $cLiveMods $name) -Destination (Join-Path $cLocal 'mods') -Recurse
}
Copy-Item -LiteralPath (Join-Path $cRoot 'README.md'),(Join-Path $cRoot 'LaunchMilestoneCPlaytest.ps1') -Destination $cLocal
$cSource=Join-Path $cStage 'source'
New-Item -ItemType Directory -Path $cSource -Force | Out-Null
$cSources=@(Get-ChildItem -LiteralPath $cRoot -File | Where-Object Extension -In '.cs','.csproj','.json','.ps1','.md')
foreach($dir in @('Content','Runtime','Compatibility','UI','QA','tests')){
    $cSources+=Get-ChildItem -LiteralPath (Join-Path $cRoot $dir) -File -Recurse | Where-Object {$_.Extension-in'.cs','.csproj','.json'-and$_.FullName-notmatch'\\(bin|obj)\\'}
}
foreach($file in $cSources){
    $relative=[IO.Path]::GetRelativePath($cRoot,$file.FullName)
    $dest=Join-Path $cSource $relative
    New-Item -ItemType Directory -Path (Split-Path $dest) -Force | Out-Null
    Copy-Item -LiteralPath $file.FullName -Destination $dest
}
Copy-Item -LiteralPath (Join-Path $cRoot 'dependencies') -Destination $cSource -Recurse
$cEvidence=Join-Path $cStage 'evidence\reports'
New-Item -ItemType Directory -Path $cEvidence -Force | Out-Null
Copy-Item -LiteralPath $cReport -Destination $cEvidence -Recurse
# The external receipt records archive hashes, so it cannot be enclosed in its own archive.
$cStaleReceipt=Join-Path $cEvidence 'milestone-c\package-verification.json'
if(Test-Path -LiteralPath $cStaleReceipt){Remove-Item -LiteralPath $cStaleReceipt}
foreach($name in @('MILESTONE_C_REPORT.md','MILESTONE_B_REPORT.md','MILESTONE_B_HUMAN_QA_CLOSEOUT.json','MILESTONE_A_HUMAN_QA_CLOSEOUT.json','SELF_TARGET_HIGHLIGHT_ROUTING_REPORT.md')){
    Copy-Item -LiteralPath (Join-Path $cRoot "reports\$name") -Destination $cEvidence
}
foreach($name in @('milestone-b-closeout','human-qa-closeout','self-target-highlight')){
    Copy-Item -LiteralPath (Join-Path $cRoot "reports\$name") -Destination $cEvidence -Recurse
}
$cExpectedDll=(Get-FileHash -LiteralPath (Join-Path $cRoot 'bin\Release\net9.0\RinArcherCore.dll')).Hash
$cResults=@()
foreach($kind in @('local','source','evidence')){
    $stage=Join-Path $cStage $kind
    $files=@(Get-ChildItem -LiteralPath $stage -File -Recurse)
    if($kind-eq'local'-and@($files | Where-Object Name -Match '^RinArcherCoreTests').Count){throw 'Test driver leaked into the local package'}
    $zip=Join-Path $cDist "RinArcherCore-$cVersion-$kind.zip"
    if(Test-Path -LiteralPath $zip){Move-Item -LiteralPath $zip -Destination (Join-Path $cDist "$cStamp-previous-c-$kind.zip")}
    Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zip -CompressionLevel Optimal
    $read=[IO.Compression.ZipFile]::OpenRead($zip)
    try{
        $fileEntries=@($read.Entries | Where-Object {$_.Name.Length-gt0})
        if($fileEntries.Count-ne$files.Count){throw "Archive file count mismatch: $kind"}
        foreach($entry in $fileEntries){
            $stream=$entry.Open()
            try{$stream.CopyTo([IO.Stream]::Null)}finally{$stream.Dispose()}
        }
    }finally{$read.Dispose()}
    $extracted=Join-Path $cExtract $kind
    [IO.Compression.ZipFile]::ExtractToDirectory($zip,$extracted)
    $extractedFiles=@(Get-ChildItem -LiteralPath $extracted -File -Recurse)
    if($extractedFiles.Count-ne$files.Count){throw "Extracted file count mismatch: $kind"}
    foreach($file in $files){
        $relative=[IO.Path]::GetRelativePath($stage,$file.FullName)
        $dest=Join-Path $extracted $relative
        if(!(Test-Path -LiteralPath $dest)-or(Get-FileHash -LiteralPath $dest).Hash-ne(Get-FileHash -LiteralPath $file.FullName).Hash){throw "Extracted hash mismatch: $kind/$relative"}
    }
    if($kind-eq'local'){
        $actualDll=(Get-FileHash -LiteralPath (Join-Path $extracted 'mods\RinArcherCore\RinArcherCore.dll')).Hash
        if($actualDll-ne$cExpectedDll){throw 'Packaged DLL does not match the frozen tested DLL'}
    }
    $cResults+=@{kind=$kind;path=$zip;bytes=(Get-Item -LiteralPath $zip).Length;sha256=(Get-FileHash -LiteralPath $zip).Hash;files=$files.Count;allEntriesRead=$true;extractedFiles=$extractedFiles.Count;allExtractedHashesMatch=$true;extractedDirectory=$extracted}
    Write-Output "$kind package: $($files.Count) files fully read, extracted and hash-verified"
}
@{status='PASS';version=$cVersion;testedDllSha256=$cExpectedDll;localTestDriverAbsent=$true;stage=$cStage;packages=$cResults;receiptIsExternalToArchives=$true} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $cReport 'package-verification.json') -Encoding utf8
Write-Output 'All three Milestone C packages verified'
