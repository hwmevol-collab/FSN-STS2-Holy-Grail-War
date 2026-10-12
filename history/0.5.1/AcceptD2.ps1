$ErrorActionPreference='Stop'
$d2Root=Join-Path $PSScriptRoot 'reports\milestone-d2'
$d2Hash=(Get-FileHash (Join-Path $PSScriptRoot 'bin\Release\net9.0\RinArcherCore.dll')).Hash
$d2Pre=Get-Content (Join-Path $d2Root 'precondition.json') -Raw|ConvertFrom-Json
if($d2Pre.status-ne'D2_HARD_PRECONDITION_PASS'){throw 'D2 hard precondition missing'}
$d2Baseline=Join-Path $d2Root 'old-baseline-final'
foreach($d2Name in @('regression-summary.json','graphical-summary.json','Exit-summary.json','Resolution-summary.json','container-1080-summary.json','container-1440-summary.json','c-regression\summary.json','ab-regression\summary.json')){
    $d2Proof=Get-Content (Join-Path $d2Baseline $d2Name) -Raw|ConvertFrom-Json
    if($d2Proof.status-ne'PASS'-or$d2Proof.testedDllSha256-ne$d2Hash){throw "Old baseline missing or stale: $d2Name"}
}
$d2Reg=Get-Content (Join-Path $d2Baseline 'regression-summary.json') -Raw|ConvertFrom-Json
if($d2Reg.total-ne524){throw 'Original invariant coverage changed'}
$d2Tests=Get-Content (Join-Path $d2Root 'd2-test-results.json') -Raw|ConvertFrom-Json
$d2TestManifest=Get-Content (Join-Path $d2Root 'headless-launch.json') -Raw|ConvertFrom-Json
if($d2Tests.status-ne'PASS'-or$d2Tests.passed-ne83-or$d2TestManifest.testedDllSha256-ne$d2Hash){throw 'D2 native headless proofs missing or stale'}
$d2Visual=Get-Content (Join-Path $d2Root 'visual-review.json') -Raw|ConvertFrom-Json
if($d2Visual.status-ne'PASS'-or$d2Visual.testedDllSha256-ne$d2Hash-or$d2Visual.images.Count-ne12){throw 'Native visual review missing or stale'}
foreach($d2Image in $d2Visual.images){if((Get-FileHash (Join-Path $PSScriptRoot $d2Image.path)).Hash-ne$d2Image.sha256){throw 'Reviewed native image changed'}}
foreach($d2Resolution in @('1920x1080','2560x1440')){
    $d2Summary=Get-Content (Join-Path $d2Root "graphical-$d2Resolution\summary.json") -Raw|ConvertFrom-Json
    if($d2Summary.status-ne'PASS'-or$d2Summary.testedDllSha256-ne$d2Hash-or$d2Summary.phases.Count-ne6){throw 'D2 graphical summary missing or stale'}
    foreach($d2Phase in 1..6){
        $d2Dir=Join-Path $d2Root "graphical-$d2Resolution\phase-$d2Phase"
        $d2Result=Get-Content (Join-Path $d2Dir "phase-$d2Phase-results.json") -Raw|ConvertFrom-Json
        $d2Launch=Get-Content (Join-Path $d2Dir 'launch.json') -Raw|ConvertFrom-Json
        if($d2Result.status-ne'PASS'-or$d2Launch.coreDllSha256-ne$d2Hash){throw "D2 phase invalid: $d2Resolution $d2Phase"}
        if(Select-String (Join-Path $d2Dir 'stderr.log') -Pattern '\[ERROR\]|ERROR: System\.|Parent node is busy|Cannot get path|D2_GRAPHICAL_FAIL|TimeoutException' -Quiet){throw 'D2 actionable native runtime error'}
    }
}
$d2Backup=(Get-Content (Join-Path $d2Root 'backup-path.txt') -Raw).Trim()
$d2Source=Get-Content (Join-Path $d2Backup 'source-before.json') -Raw|ConvertFrom-Json
$d2OldTests=@($d2Source|Where-Object {$_.path-like'tests\*'-and$_.path-ne'tests\TestEntry.cs'-and$_.path-notmatch'\\(bin|obj)\\'})
$d2ChangedOldTests=@($d2OldTests|Where-Object {!(Test-Path (Join-Path $PSScriptRoot $_.path))-or(Get-FileHash (Join-Path $PSScriptRoot $_.path)).Hash-ne$_.sha256}|ForEach-Object path)
if($d2ChangedOldTests.Count){throw 'Original test files changed'}
$d2Protected=Get-Content (Join-Path $d2Backup 'protected-before.json') -Raw|ConvertFrom-Json
$d2ChangedProtected=@($d2Protected|Where-Object {!(Test-Path -LiteralPath $_.path)-or(Get-FileHash -LiteralPath $_.path).Hash-ne$_.sha256}|ForEach-Object path)
if($d2ChangedProtected.Count){throw 'Protected state changed'}
$d2Gate=@{status='RIN_ARCHER_RUN_ECONOMY_D2_PASS';version='0.5.0';testedDllSha256=$d2Hash;D1_BASELINE_PASS=$true;NATIVE_CAMPFIRE_PASS=$true;FOCUSED_REST_PASS=$true;SMITH_DUAL_SELECTOR_PASS=$true;NATIVE_MERCHANT_PASS=$true;SHOP_2_PLUS_2_PASS=$true;SHARED_GOLD_PASS=$true;REMOVE_SERVICE_PASS=$true;GLOBAL_REMOVAL_PRICE_PASS=$true;SAVE_RELOAD_CAMPFIRE_PASS=$true;SAVE_RELOAD_MERCHANT_PASS=$true;VANILLA_REGRESSION_PASS=$true;REAL_GRAPHICAL_D2_RUN_PASS=$true;DESIGN_DEVIATIONS=0;DESIGN_CONTRACT_CONFLICT=0;IMPLEMENTATION_BLOCKERS=0;oldInvariantChecks=524;d2Checks=83;oldTestFilesUnchanged=$d2OldTests.Count;protectedFiles=$d2Protected.Count;protectedMismatches=$d2ChangedProtected;humanQA='PENDING';physicalController='PHYSICAL_CONTROLLER_QA_DEFERRED_TO_WORKSHOP_RC';nextMilestone='STOP_BEFORE_E';acceptedAt=(Get-Date).ToString('o')}
$d2Gate|ConvertTo-Json -Depth 5|Set-Content (Join-Path $d2Root 'acceptance.json') -Encoding utf8
$d2Gate|ConvertTo-Json -Depth 5
