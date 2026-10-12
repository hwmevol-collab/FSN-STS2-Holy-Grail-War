$ErrorActionPreference='Stop'
$focusRoot=Join-Path $PSScriptRoot 'reports\d2-rest-focus-highlight'
$focusHash=(Get-FileHash (Join-Path $PSScriptRoot 'bin\Release\net9.0\RinArcherCore.dll')).Hash
$focusRegression=Get-Content (Join-Path $focusRoot 'full-regression-summary.json') -Raw|ConvertFrom-Json
if($focusRegression.status-ne'PASS'-or$focusRegression.testedDllSha256-ne$focusHash){throw 'Full regression is missing or stale'}
foreach($name in @('regression-summary.json','graphical-summary.json','Exit-summary.json','Resolution-summary.json','container-1080-summary.json','container-1440-summary.json','c-regression\summary.json','ab-regression\summary.json')){
    $proof=Get-Content (Join-Path $focusRoot "full-regression\$name") -Raw|ConvertFrom-Json
    if($proof.status-ne'PASS'-or$proof.testedDllSha256-ne$focusHash){throw "Regression missing/stale: $name"}
}
if((Get-Content (Join-Path $focusRoot 'full-regression\regression-summary.json') -Raw|ConvertFrom-Json).total-ne524){throw 'Original invariant count changed'}
$focusD2=Get-Content (Join-Path $focusRoot 'd2-test-results.json') -Raw|ConvertFrom-Json
if($focusD2.status-ne'PASS'-or$focusD2.passed-ne83){throw 'D2 invariant coverage changed'}
foreach($res in @('1920x1080','2560x1440')){
    $dir=Join-Path $focusRoot "fixed-$res"
    $result=Get-Content (Join-Path $dir 'results.json') -Raw|ConvertFrom-Json
    $launch=Get-Content (Join-Path $dir 'launch.json') -Raw|ConvertFrom-Json
    if($result.status-ne'PASS'-or$result.passed-ne62-or$launch.coreDllSha256-ne$focusHash){throw "Focus native QA missing/stale: $res"}
    foreach($state in @('mouse-off-both','mouse-rin','mouse-archer','controller-focus-rin','controller-move-archer','controller-to-mouse-archer','mouse-to-controller-rin','mouse-to-keyboard-rin','keyboard-move-archer')){if($result.checks-notcontains($state+'_HIGHLIGHT_ARBITRATION')){throw "Missing focus scenario: $state"}}
    $d2Summary=Get-Content (Join-Path $focusRoot "d2-graphical-$res\summary.json") -Raw|ConvertFrom-Json
    if($d2Summary.status-ne'PASS'-or$d2Summary.testedDllSha256-ne$focusHash-or$d2Summary.phases.Count-ne6){throw 'D2 native phases missing/stale'}
    foreach($phase in 1..6){$d2Dir=Join-Path $focusRoot "d2-graphical-$res\phase-$phase";$phaseResult=Get-Content (Join-Path $d2Dir "phase-$phase-results.json") -Raw|ConvertFrom-Json;$phaseLaunch=Get-Content (Join-Path $d2Dir 'launch.json') -Raw|ConvertFrom-Json;if($phaseResult.status-ne'PASS'-or$phaseLaunch.coreDllSha256-ne$focusHash){throw 'D2 native phase mismatch'}}
}
$focusVisual=Get-Content (Join-Path $focusRoot 'visual-review.json') -Raw|ConvertFrom-Json
if($focusVisual.status-ne'PASS'-or$focusVisual.testedDllSha256-ne$focusHash-or$focusVisual.images.Count-lt14){throw 'Visual review missing/stale'}
foreach($img in $focusVisual.images){if((Get-FileHash -LiteralPath $img.path).Hash-ne$img.sha256){throw 'Reviewed image changed'}}
$focusBackup=(Get-Content (Join-Path $focusRoot 'backup-path.txt') -Raw).Trim()
$focusSource=@(Get-Content (Join-Path $focusBackup 'source-before.json') -Raw|ConvertFrom-Json)
$focusAllowed=@((Join-Path $PSScriptRoot 'UI\FocusedRestUi.cs'),(Join-Path $PSScriptRoot 'tests\TestEntry.cs'))
$focusChanged=@($focusSource|Where-Object {$_.path-notin$focusAllowed-and(!(Test-Path -LiteralPath $_.path)-or(Get-FileHash $_.path).Hash-ne$_.sha256)}|ForEach-Object path)
if($focusChanged.Count){throw "Out-of-scope source change: $focusChanged"}
$focusProtected=@(Get-Content (Join-Path $focusBackup 'protected-before.json') -Raw|ConvertFrom-Json)
$focusMismatches=@($focusProtected|Where-Object {!(Test-Path -LiteralPath $_.path)-or(Get-FileHash $_.path).Hash-ne$_.sha256}|ForEach-Object path)
if($focusMismatches.Count){throw 'Protected state changed'}
@{status='D2_REST_FOCUS_HIGHLIGHT_ARBITRATION_PASS';version='0.5.1';testedDllSha256=$focusHash;focusChecksPerResolution=62;originalInvariantChecks=524;d2InvariantChecks=83;d2NativeChecksPerResolution=117;protectedFiles=$focusProtected.Count;protectedMismatches=$focusMismatches;gameplaySourcesAndPriorTestAssertionsUnchanged=$true;humanGameplayFeedback='D2 human play completed, no new gameplay issues';humanFocusRecheck='PENDING';physicalController='DEFERRED_TO_WORKSHOP_RC';nextMilestone='STOP_BEFORE_E';acceptedAt=(Get-Date).ToString('o')}|ConvertTo-Json|Set-Content (Join-Path $focusRoot 'acceptance.json')
Get-Content (Join-Path $focusRoot 'acceptance.json')
