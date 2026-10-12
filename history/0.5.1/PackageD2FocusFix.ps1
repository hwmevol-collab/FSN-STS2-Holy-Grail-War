$ErrorActionPreference='Stop'
$d2Root=$PSScriptRoot
$d2Report=Join-Path $d2Root 'reports\d2-rest-focus-highlight'
$d2Version=(Get-Content -LiteralPath (Join-Path $d2Root 'RinArcherCore.json') -Raw | ConvertFrom-Json).version
$d2Gate=Get-Content -LiteralPath (Join-Path $d2Report 'acceptance.json') -Raw | ConvertFrom-Json
if($d2Version-ne'0.5.1'-or$d2Gate.status-ne'D2_REST_FOCUS_HIGHLIGHT_ARBITRATION_PASS'){throw 'D2 package gate failed'}
& (Join-Path $d2Root 'UpdateLocalD2FocusFix.ps1') -VerifyOnly | Out-Null
$d2Dist=Join-Path $d2Root 'dist'
$d2Stamp=(Get-Date).ToString('yyyyMMdd-HHmmss')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,8)
$d2Stage=Join-Path $d2Dist "stage-d2-$d2Stamp"
$d2Extract=Join-Path $d2Dist "verified-d2-$d2Stamp"
New-Item -ItemType Directory -Path $d2Stage,$d2Extract -Force | Out-Null
$d2Local=Join-Path $d2Stage 'local'
New-Item -ItemType Directory -Path (Join-Path $d2Local 'mods') -Force | Out-Null
foreach($name in @('BaseLib','STS2-RitsuLib','RinArcherCore')){Copy-Item -LiteralPath (Join-Path 'E:\SteamLibrary\steamapps\common\Slay the Spire 2\mods' $name) -Destination (Join-Path $d2Local 'mods') -Recurse}
Copy-Item -LiteralPath (Join-Path $d2Root 'README.md'),(Join-Path $d2Root 'LaunchMilestoneD2Playtest.ps1'),(Join-Path $d2Root 'PlayMilestoneD2.cmd') -Destination $d2Local
New-Item -ItemType Directory -Path (Join-Path $d2Local 'reports\d2-rest-focus-highlight') -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $d2Root 'reports\D2_REST_FOCUS_HIGHLIGHT_REPORT.md') -Destination (Join-Path $d2Local 'reports')
Copy-Item -LiteralPath (Join-Path $d2Report 'HUMAN_FOCUS_RECHECK.md') -Destination (Join-Path $d2Local 'reports\d2-rest-focus-highlight')
$d2Source=Join-Path $d2Stage 'source'
New-Item -ItemType Directory -Path $d2Source -Force | Out-Null
$d2Sources=@(Get-ChildItem -LiteralPath $d2Root -File | Where-Object Extension -In '.cs','.csproj','.json','.ps1','.cmd','.md')
foreach($dir in @('Content','Runtime','Compatibility','UI','QA','tests')){$d2Sources+=Get-ChildItem -LiteralPath (Join-Path $d2Root $dir) -File -Recurse | Where-Object {$_.Extension-in'.cs','.csproj','.json'-and$_.FullName-notmatch'\\(bin|obj)\\'}}
foreach($file in $d2Sources){$relative=[IO.Path]::GetRelativePath($d2Root,$file.FullName);$dest=Join-Path $d2Source $relative;New-Item -ItemType Directory -Path (Split-Path $dest) -Force | Out-Null;Copy-Item -LiteralPath $file.FullName -Destination $dest}
Copy-Item -LiteralPath (Join-Path $d2Root 'dependencies') -Destination $d2Source -Recurse
$d2Evidence=Join-Path $d2Stage 'evidence\reports'
New-Item -ItemType Directory -Path $d2Evidence -Force | Out-Null
Copy-Item -LiteralPath $d2Report -Destination $d2Evidence -Recurse
$d2OldReceipt=Join-Path $d2Evidence 'd2-rest-focus-highlight\package-verification.json'
if(Test-Path -LiteralPath $d2OldReceipt){Remove-Item -LiteralPath $d2OldReceipt}
foreach($name in @('D2_REST_FOCUS_HIGHLIGHT_REPORT.md')){Copy-Item -LiteralPath (Join-Path $d2Root "reports\$name") -Destination $d2Evidence}
$d2Results=@()
foreach($kind in @('local','source','evidence')){
    $stage=Join-Path $d2Stage $kind
    $files=@(Get-ChildItem -LiteralPath $stage -File -Recurse)
    if($kind-eq'local'-and@($files | Where-Object Name -Match '^RinArcherCoreTests').Count){throw 'Test driver leaked into the local package'}
    $zip=Join-Path $d2Dist "RinArcherCore-$d2Version-$kind.zip"
    if(Test-Path -LiteralPath $zip){Move-Item -LiteralPath $zip -Destination (Join-Path $d2Dist "$d2Stamp-previous-d2-$kind.zip")}
    Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zip -CompressionLevel Optimal
    $read=[IO.Compression.ZipFile]::OpenRead($zip)
    try{$entries=@($read.Entries | Where-Object {$_.Name.Length-gt0});if($entries.Count-ne$files.Count){throw "Archive count mismatch: $kind"};foreach($entry in $entries){$stream=$entry.Open();try{$stream.CopyTo([IO.Stream]::Null)}finally{$stream.Dispose()}}}finally{$read.Dispose()}
    $extracted=Join-Path $d2Extract $kind
    [IO.Compression.ZipFile]::ExtractToDirectory($zip,$extracted)
    $extractedFiles=@(Get-ChildItem -LiteralPath $extracted -File -Recurse)
    if($extractedFiles.Count-ne$files.Count){throw "Extracted count mismatch: $kind"}
    foreach($file in $files){$dest=Join-Path $extracted ([IO.Path]::GetRelativePath($stage,$file.FullName));if(!(Test-Path -LiteralPath $dest)-or(Get-FileHash -LiteralPath $dest).Hash-ne(Get-FileHash -LiteralPath $file.FullName).Hash){throw "Extracted hash mismatch: $kind"}}
    if($kind-eq'local'-and(Get-FileHash -LiteralPath (Join-Path $extracted 'mods\RinArcherCore\RinArcherCore.dll')).Hash-ne$d2Gate.testedDllSha256){throw 'Packaged DLL differs from tested DLL'}
    $d2Results+=@{kind=$kind;path=$zip;bytes=(Get-Item -LiteralPath $zip).Length;sha256=(Get-FileHash -LiteralPath $zip).Hash;files=$files.Count;allEntriesRead=$true;allExtractedHashesMatch=$true;extractedDirectory=$extracted}
    Write-Output "$kind package: $($files.Count) files fully read, extracted and hash-verified"
}
@{status='PASS';version=$d2Version;testedDllSha256=$d2Gate.testedDllSha256;localTestDriverAbsent=$true;packages=$d2Results;receiptIsExternalToArchives=$true} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $d2Report 'package-verification.json') -Encoding utf8



