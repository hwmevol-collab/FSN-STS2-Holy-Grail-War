$ErrorActionPreference='Stop'
$d1Root=$PSScriptRoot
$d1Report=Join-Path $d1Root 'reports\milestone-d1'
$d1Version=(Get-Content -LiteralPath (Join-Path $d1Root 'RinArcherCore.json') -Raw | ConvertFrom-Json).version
$d1Gate=Get-Content -LiteralPath (Join-Path $d1Report 'acceptance.json') -Raw | ConvertFrom-Json
if($d1Version-ne'0.4.0'-or$d1Gate.status-ne'RIN_ARCHER_RUN_CORE_D1_PASS'){throw 'D1 package gate failed'}
& (Join-Path $d1Root 'UpdateLocalD1.ps1') -VerifyOnly | Out-Null
$d1Dist=Join-Path $d1Root 'dist'
$d1Stamp=(Get-Date).ToString('yyyyMMdd-HHmmss')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,8)
$d1Stage=Join-Path $d1Dist "stage-d1-$d1Stamp"
$d1Extract=Join-Path $d1Dist "verified-d1-$d1Stamp"
New-Item -ItemType Directory -Path $d1Stage,$d1Extract -Force | Out-Null
$d1Local=Join-Path $d1Stage 'local'
New-Item -ItemType Directory -Path (Join-Path $d1Local 'mods') -Force | Out-Null
foreach($name in @('BaseLib','STS2-RitsuLib','RinArcherCore')){Copy-Item -LiteralPath (Join-Path 'E:\SteamLibrary\steamapps\common\Slay the Spire 2\mods' $name) -Destination (Join-Path $d1Local 'mods') -Recurse}
Copy-Item -LiteralPath (Join-Path $d1Root 'README.md'),(Join-Path $d1Root 'LaunchMilestoneD1Playtest.ps1'),(Join-Path $d1Root 'PlayMilestoneD1.cmd') -Destination $d1Local
$d1Source=Join-Path $d1Stage 'source'
New-Item -ItemType Directory -Path $d1Source -Force | Out-Null
$d1Sources=@(Get-ChildItem -LiteralPath $d1Root -File | Where-Object Extension -In '.cs','.csproj','.json','.ps1','.cmd','.md')
foreach($dir in @('Content','Runtime','Compatibility','UI','QA','tests')){$d1Sources+=Get-ChildItem -LiteralPath (Join-Path $d1Root $dir) -File -Recurse | Where-Object {$_.Extension-in'.cs','.csproj','.json'-and$_.FullName-notmatch'\\(bin|obj)\\'}}
foreach($file in $d1Sources){$relative=[IO.Path]::GetRelativePath($d1Root,$file.FullName);$dest=Join-Path $d1Source $relative;New-Item -ItemType Directory -Path (Split-Path $dest) -Force | Out-Null;Copy-Item -LiteralPath $file.FullName -Destination $dest}
Copy-Item -LiteralPath (Join-Path $d1Root 'dependencies') -Destination $d1Source -Recurse
$d1Evidence=Join-Path $d1Stage 'evidence\reports'
New-Item -ItemType Directory -Path $d1Evidence -Force | Out-Null
Copy-Item -LiteralPath $d1Report -Destination $d1Evidence -Recurse
$d1OldReceipt=Join-Path $d1Evidence 'milestone-d1\package-verification.json'
if(Test-Path -LiteralPath $d1OldReceipt){Remove-Item -LiteralPath $d1OldReceipt}
foreach($name in @('MILESTONE_D1_REPORT.md','MILESTONE_C_REPORT.md','MILESTONE_B_REPORT.md','SELF_TARGET_HIGHLIGHT_ROUTING_REPORT.md')){Copy-Item -LiteralPath (Join-Path $d1Root "reports\$name") -Destination $d1Evidence}
$d1Results=@()
foreach($kind in @('local','source','evidence')){
    $stage=Join-Path $d1Stage $kind
    $files=@(Get-ChildItem -LiteralPath $stage -File -Recurse)
    if($kind-eq'local'-and@($files | Where-Object Name -Match '^RinArcherCoreTests').Count){throw 'Test driver leaked into the local package'}
    $zip=Join-Path $d1Dist "RinArcherCore-$d1Version-$kind.zip"
    if(Test-Path -LiteralPath $zip){Move-Item -LiteralPath $zip -Destination (Join-Path $d1Dist "$d1Stamp-previous-d1-$kind.zip")}
    Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zip -CompressionLevel Optimal
    $read=[IO.Compression.ZipFile]::OpenRead($zip)
    try{$entries=@($read.Entries | Where-Object {$_.Name.Length-gt0});if($entries.Count-ne$files.Count){throw "Archive count mismatch: $kind"};foreach($entry in $entries){$stream=$entry.Open();try{$stream.CopyTo([IO.Stream]::Null)}finally{$stream.Dispose()}}}finally{$read.Dispose()}
    $extracted=Join-Path $d1Extract $kind
    [IO.Compression.ZipFile]::ExtractToDirectory($zip,$extracted)
    $extractedFiles=@(Get-ChildItem -LiteralPath $extracted -File -Recurse)
    if($extractedFiles.Count-ne$files.Count){throw "Extracted count mismatch: $kind"}
    foreach($file in $files){$dest=Join-Path $extracted ([IO.Path]::GetRelativePath($stage,$file.FullName));if(!(Test-Path -LiteralPath $dest)-or(Get-FileHash -LiteralPath $dest).Hash-ne(Get-FileHash -LiteralPath $file.FullName).Hash){throw "Extracted hash mismatch: $kind"}}
    if($kind-eq'local'-and(Get-FileHash -LiteralPath (Join-Path $extracted 'mods\RinArcherCore\RinArcherCore.dll')).Hash-ne$d1Gate.testedDllSha256){throw 'Packaged DLL differs from tested DLL'}
    $d1Results+=@{kind=$kind;path=$zip;bytes=(Get-Item -LiteralPath $zip).Length;sha256=(Get-FileHash -LiteralPath $zip).Hash;files=$files.Count;allEntriesRead=$true;allExtractedHashesMatch=$true;extractedDirectory=$extracted}
    Write-Output "$kind package: $($files.Count) files fully read, extracted and hash-verified"
}
@{status='PASS';version=$d1Version;testedDllSha256=$d1Gate.testedDllSha256;localTestDriverAbsent=$true;packages=$d1Results;receiptIsExternalToArchives=$true} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $d1Report 'package-verification.json') -Encoding utf8
