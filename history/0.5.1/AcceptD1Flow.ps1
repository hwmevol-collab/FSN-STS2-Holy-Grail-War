$ErrorActionPreference='Stop'
$flowRoot=$PSScriptRoot
$flowReport=Join-Path $flowRoot 'reports\d1-native-container-flow'
$flowBackup=(Get-Content -LiteralPath (Join-Path $flowReport 'backup-path.txt') -Raw).Trim()
$flowHash=(Get-FileHash -LiteralPath (Join-Path $flowRoot 'bin\Release\net9.0\RinArcherCore.dll')).Hash
$expected=@{'regression-summary.json'=524;'graphical-summary.json'=97;'Exit-summary.json'=17;'Resolution-summary.json'=42;'c-regression\summary.json'=20}
foreach($name in $expected.Keys){
    $result=Get-Content -LiteralPath (Join-Path $flowReport $name) -Raw|ConvertFrom-Json
    $count=if($name-eq'regression-summary.json'){$result.total}else{$result.passed}
    if($result.status-ne'PASS'-or$result.testedDllSha256-ne$flowHash-or$count-ne$expected[$name]){throw "Acceptance mismatch: $name"}
}
$ab=Get-Content -LiteralPath (Join-Path $flowReport 'ab-regression\summary.json') -Raw|ConvertFrom-Json
if($ab.status-ne'PASS'-or$ab.testedDllSha256-ne$flowHash-or$ab.highlightChecks-ne22-or$ab.bChecks-lt20){throw 'Native A/B regression is incomplete'}
$containerChecks=@();$containerSummaries=@()
foreach($resolution in @('1080','1440')){
    $result=Get-Content -LiteralPath (Join-Path $flowReport "container-$resolution-summary.json") -Raw|ConvertFrom-Json
    if($result.status-ne'PASS'-or$result.testedDllSha256-ne$flowHash-or$result.phases.Count-ne3-or$result.passed-lt70){throw "Container $resolution incomplete or stale"}
    $containerSummaries+=$result
    foreach($phase in 1..3){$containerChecks+=@((Get-Content -LiteralPath (Join-Path $flowReport "container-$($result.requestedResolution)\phase-$phase\phase-$phase-results.json") -Raw|ConvertFrom-Json).checks)}
}
foreach($id in @('VICTORY_NATIVE_LOOT_CONTAINER_NO_AUTO_CARD_SELECTION','UNOPENED_CONTAINER_RESUMES_WITHOUT_AUTO_SELECTION','GENERATED_CONTAINER_NATIVE_CONTINUE_SAME_ROOM_MASTER_OFFER','CONTAINER_RELOAD_NO_RARITY_REROLL','NATIVE_GOLD_ITEM_CLAIMED_EXACTLY_ONCE','CLICK_CARD_ITEM_MASTER_PICK_THEN_SERVANT_PENDING','NATIVE_CONTINUE_RESUMES_EXACT_SAVED_SERVANT_OFFER','CLAIMED_GOLD_NOT_REOFFERED_AFTER_SERVANT_RESUME','DUAL_COMPLETION_RETURNS_SAME_NATIVE_CONTAINER','NATIVE_CARD_ITEM_RESOLVED_AFTER_BOTH_STAGES','COMPLETED_CARD_GOLD_POTION_NOT_REOPENED_AFTER_CONTINUE','SERVANT_ACQUISITION_RESTORED_ONCE','PUBLIC_COMBAT_DEFAULT_MINIMAL_HUD_NO_QA_CONTROLS','PUBLIC_REWARD_HAS_NO_QA_SAVE_EXIT_BUTTON','F8_DEBUG_INFO_WITHOUT_PUBLIC_QA_CONTROLS')){if(@($containerChecks|Where-Object {$_-eq$id}).Count-lt2){throw "Required container check missing at one resolution: $id"}}
$preserved=@()
foreach($name in @('core','alpha','highlight','reward','d1')){
    $old=Get-Content -LiteralPath (Join-Path $flowBackup "previous-evidence\$name-test-results.json") -Raw|ConvertFrom-Json
    $new=Get-Content -LiteralPath (Join-Path $flowReport "$name-test-results.json") -Raw|ConvertFrom-Json
    $missing=@($old.checks|Where-Object {$_-notin$new.checks});if($missing.Count){throw "Old invariant checks missing: $name"}
    $preserved+=@{suite=$name;old=$old.passed;new=$new.passed;missing=$missing}
}
$oldGraph=@();$newGraph=@()
foreach($phase in 1..5){
    $oldGraph+=@((Get-Content -LiteralPath (Join-Path $flowBackup "previous-evidence\resolution-1920x1080\graphical\phase-$phase\phase-$phase-results.json") -Raw|ConvertFrom-Json).checks)
    $newGraph+=@((Get-Content -LiteralPath (Join-Path $flowReport "graphical\phase-$phase\phase-$phase-results.json") -Raw|ConvertFrom-Json).checks)
}
if(@($oldGraph|Where-Object {$_-notin$newGraph}).Count){throw 'Old D1 graphical checks missing'}
@{suites=$preserved;oldD1Graphical=$oldGraph.Count;newD1Graphical=$newGraph.Count;missingD1Graphical=@()}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $flowReport 'old-tests-preservation.json') -Encoding utf8
$contentDiff=@();foreach($directory in @('Content','Runtime')){foreach($file in Get-ChildItem -LiteralPath (Join-Path $flowBackup "source\$directory") -File -Recurse){$relative=[IO.Path]::GetRelativePath((Join-Path $flowBackup 'source'),$file.FullName);if((Get-FileHash -LiteralPath $file.FullName).Hash-ne(Get-FileHash -LiteralPath (Join-Path $flowRoot $relative)).Hash){$contentDiff+=$relative}}}
if($contentDiff.Count){throw 'Gameplay content or reward/persistence rules changed'}
function MapClass([string]$path){$text=[IO.File]::ReadAllText($path);$text.Substring($text.IndexOf('public sealed class D1ActMap'),$text.IndexOf('public static class D1Run')-$text.IndexOf('public sealed class D1ActMap'))}
if((MapClass (Join-Path $flowBackup 'source\QA\D1Run.cs'))-cne(MapClass (Join-Path $flowRoot 'QA\D1Run.cs'))){throw 'D1 topology/spacing was changed'}
@{gameplayContentDifferences=$contentDiff.Count;rewardRuleDifferences=0;hpDeckPersistenceSourceUnchanged=$true;encounterResetSourceUnchanged=$true;mapClassUnchanged=$true;D1_QA_MAP_SPARSITY='EXPECTED_NON_BLOCKING'}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $flowReport 'source-scope-verification.json') -Encoding utf8
$dimensions=@();foreach($resolution in @('1920x1080','2560x1440')){
    $size=$resolution.Split('x');foreach($file in Get-ChildItem -LiteralPath (Join-Path $flowReport "container-$resolution") -Filter '*.png' -File -Recurse){
        $bytes=[IO.File]::ReadAllBytes($file.FullName);$width=[uint32]$bytes[16]*16777216+[uint32]$bytes[17]*65536+[uint32]$bytes[18]*256+$bytes[19];$height=[uint32]$bytes[20]*16777216+[uint32]$bytes[21]*65536+[uint32]$bytes[22]*256+$bytes[23]
        if($width-ne[int]$size[0]-or$height-ne[int]$size[1]){throw "PNG dimensions mismatch: $($file.FullName)"}
        $dimensions+=@{path=$file.FullName;width=$width;height=$height;sha256=(Get-FileHash -LiteralPath $file.FullName).Hash}
    }
}
if($dimensions.Count-lt20){throw 'Native container graphical evidence is incomplete'}
$dimensions|ConvertTo-Json -Depth 4|Set-Content -LiteralPath (Join-Path $flowReport 'container-image-dimensions.json') -Encoding utf8
$acceptance=@{status='D1_NATIVE_CONTAINER_FLOW_PASS';version='0.4.2';testedDllSha256=$flowHash;completedAt=(Get-Date).ToString('o');automatedTotal=524;d1Graphical=97;saveExitAndLegacy=17;existingUserResolution=42;cGraphical=20;bNative=$ab.bChecks;highlightNative=22;nativeACompleteBattle=$true;container1080=$containerSummaries[0].passed;container1440=$containerSummaries[1].passed;containerImages=$dimensions.Count;allOldChecksPreserved=$true;gameplayContentDifferences=0;rewardRuleDifferences=0;D1_QA_MAP_SPARSITY='EXPECTED_NON_BLOCKING';PUBLIC_UI_MODE=$true;NATIVE_UI_FIRST_FOR_PUBLIC_PATH=$true;editorRequired=$false;softwareInstalled=$false;humanQA='PENDING';physicalControllerQA='PENDING';D2='NOT_STARTED';PublicVerticalSlice='NOT_RELEASED';knownRuntimeDiagnostics='RID/shader/resource cleanup at process exit remains unaddressed'}
$acceptance|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $flowReport 'acceptance.json') -Encoding utf8
$acceptance|ConvertTo-Json -Depth 5
