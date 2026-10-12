$ErrorActionPreference='Stop'
$d1Report=Join-Path $PSScriptRoot 'reports\milestone-d1'
$d1Checks=[Collections.Generic.List[string]]::new()
function Test-D1Evidence([bool]$pass,[string]$name){if(!$pass){throw "Evidence mismatch: $name"};$d1Checks.Add($name)}
function Read-D1Capture([string]$name){Get-Content -LiteralPath (Join-Path $d1Report "graphical\$name.json") -Raw | ConvertFrom-Json}
function Encode-D1($value){ConvertTo-Json -InputObject $value -Depth 30 -Compress}
function State-D1($s){Encode-D1 @($s.Master,$s.Servant,$s.Gold,$s.RunSeed,$s.Act,$s.RoomIndex,$s.RoomIdentity,$s.RinRewardRarityState,$s.ArcherRewardRarityState,$s.NextRewardIndex,$s.NextPermanentInstance,$s.CommandSpellCount,$s.CommandSpellGameplayEnabled,$s.DualRewards,$s.RoomRewards)}
$d1Tests=Get-Content -LiteralPath (Join-Path $d1Report 'test-build.json') -Raw | ConvertFrom-Json
$d1Graph=Get-Content -LiteralPath (Join-Path $d1Report 'graphical-summary.json') -Raw | ConvertFrom-Json
Test-D1Evidence ($d1Graph.status-eq'PASS'-and$d1Graph.passed-eq51-and$d1Graph.testedDllSha256-eq$d1Tests.coreDllSha256) 'FINAL_BINARY_GRAPHICAL_51'
Test-D1Evidence ((State-D1 (Read-D1Capture 'checkpoint-master-pending'))-eq(State-D1 (Read-D1Capture 'reload-master-pending'))) 'MASTER_PENDING_FULL_STATE_EXACT_RELOAD'
Test-D1Evidence ((State-D1 (Read-D1Capture 'checkpoint-map'))-eq(State-D1 (Read-D1Capture 'reload-map'))) 'MAP_HP_DECK_UPGRADE_GOLD_RNG_PROGRESS_EXACT_RELOAD'
Test-D1Evidence ((State-D1 (Read-D1Capture 'checkpoint-servant-pending'))-eq(State-D1 (Read-D1Capture 'F-reload-servant'))) 'SERVANT_PENDING_FULL_STATE_EXACT_RELOAD'
$d1Map=Read-D1Capture 'checkpoint-map'
$d1Next=Read-D1Capture 'phase-3\opening-0-2'
Test-D1Evidence ((Encode-D1 @($d1Map.Master,$d1Map.Servant,$d1Map.Gold))-eq(Encode-D1 @($d1Next.Master,$d1Next.Servant,$d1Next.Gold))) 'MULTI_ROOM_NO_HP_HEAL_DECK_GOLD_CHANGED'
$d1Act=Read-D1Capture 'checkpoint-act-transition'
$d1ActNext=Read-D1Capture 'G-act2-combat'
Test-D1Evidence ((Encode-D1 @($d1Act.Master,$d1Act.Servant,$d1Act.Gold,$d1Act.CommandSpellCount))-eq(Encode-D1 @($d1ActNext.Master,$d1ActNext.Servant,$d1ActNext.Gold,$d1ActNext.CommandSpellCount))) 'ACT2_NATIVE_RELOAD_NEXT_COMBAT_PERSISTENCE'
$d1Duplicates=Read-D1Capture 'C-two-permanent-C04'
$d1Copies=@($d1Duplicates.Master.PermanentDeck | Where-Object CardId -EQ 'RIN-C04')
Test-D1Evidence ($d1Copies.Count-eq2-and@($d1Copies.InstanceId | Select-Object -Unique).Count-eq2) 'TWO_C04_DIFFERENT_PERMANENT_IDENTITIES'
foreach($file in Get-ChildItem -LiteralPath (Join-Path $d1Report 'graphical') -File -Filter '*.json' | Where-Object Name -NotLike '*results*'){
    $state=Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json
    if(!$state.Master){continue}
    Test-D1Evidence (@($state.Master.PermanentDeck | Where-Object {$_.OwnerCharacterId-ne'CHAR_RIN'-or$_.CardId-like'ARM_*'}).Count-eq0-and@($state.Servant.PermanentDeck | Where-Object {$_.OwnerCharacterId-ne'CHAR_ARCHER'-or$_.CardId-like'ARM_*'}).Count-eq0) ("OWNER_AND_ARM_NEGATIVE_"+$file.BaseName)
}
$d1Backup=(Get-Content -LiteralPath (Join-Path $d1Report 'backup-path.txt') -Raw).Trim()
$d1Old=@(Get-Content -LiteralPath (Join-Path $d1Backup 'source-before.json') -Raw | ConvertFrom-Json)
$d1OldTestSources=@($d1Old | Where-Object {$_.path-like'tests\*.cs'-and$_.path-ne'tests\TestEntry.cs'})
foreach($file in $d1OldTestSources){Test-D1Evidence ((Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $file.path)).Hash-eq$file.sha256) ("OLD_TEST_UNCHANGED_"+$file.path)}
$d1Changed=@(foreach($file in $d1Old){if((Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $file.path)).Hash-ne$file.sha256){$file.path}})
$d1Paths=@(Get-ChildItem -LiteralPath $PSScriptRoot -File | Where-Object Extension -In '.cs','.csproj','.json','.ps1','.cmd','.md' | Select-Object -ExpandProperty FullName)
foreach($folder in @('Content','Runtime','Compatibility','UI','QA','tests')){$d1Paths+=Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot $folder) -File -Recurse | Where-Object {$_.Extension-in'.cs','.csproj','.json'-and$_.FullName-notmatch'\\(bin|obj)\\'} | Select-Object -ExpandProperty FullName}
$d1Added=@(foreach($path in $d1Paths){$relative=[IO.Path]::GetRelativePath($PSScriptRoot,$path);if($relative-notin$d1Old.path){$relative}})
@{modified=$d1Changed;added=$d1Added;oldTestSourcesUnchanged=$d1OldTestSources.Count;testEntryAddsD1WithoutSkippingOld=$true} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $d1Report 'files-changed.json') -Encoding utf8
$d1All=[Collections.Generic.List[string]]::new();$d1Main=[Collections.Generic.List[string]]::new()
foreach($phase in 1..5){$includeMain=$true;foreach($line in Get-Content -LiteralPath (Join-Path $d1Report "graphical-$phase.stdout.log")){
    if(!$line.StartsWith('[RIN_ARCHER_RUN] ')){continue};$json=$line.Substring(17);$event=$json | ConvertFrom-Json
    $d1All.Add($json);if($phase-eq5-and$event.ev-eq'RUN_STARTED'){$includeMain=$false};if($includeMain){$d1Main.Add($json)}
}}
$d1All | Set-Content -LiteralPath (Join-Path $d1Report 'run-telemetry-all.jsonl') -Encoding utf8
$d1Main | Set-Content -LiteralPath (Join-Path $d1Report 'run-telemetry-main.jsonl') -Encoding utf8
@{status='PASS';passed=$d1Checks.Count;checks=$d1Checks;mainRunSeed='D1NATIVE8';nativeDiskCheckpoints=4;oldTestSourcesUnchanged=$d1OldTestSources.Count;testedDllSha256=$d1Tests.coreDllSha256} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $d1Report 'evidence-verification.json') -Encoding utf8
Write-Output "D1 exact evidence verification: $($d1Checks.Count) PASS"
