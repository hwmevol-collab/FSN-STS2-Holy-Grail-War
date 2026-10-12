$ErrorActionPreference='Stop'
$fixReport=Join-Path $PSScriptRoot 'reports\d1-map-native-ui-fix'
$fixHash=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'bin\Release\net9.0\RinArcherCore.dll')).Hash
$fixExpected=@{'regression-summary.json'=524;'graphical-summary.json'=97;'Exit-summary.json'=17;'Resolution-summary.json'=42;'c-regression\summary.json'=20}
foreach($name in $fixExpected.Keys){
    $fixResult=Get-Content -LiteralPath (Join-Path $fixReport $name) -Raw|ConvertFrom-Json
    $fixCount=if($name -eq 'regression-summary.json'){$fixResult.total}else{$fixResult.passed}
    if($fixResult.status-ne'PASS'-or$fixResult.testedDllSha256-ne$fixHash-or$fixCount-ne$fixExpected[$name]){throw "Acceptance mismatch: $name"}
}
$fixPreserved=@()
foreach($name in @('core','alpha','highlight','reward','d1')){
    $a=Get-Content -LiteralPath (Join-Path $PSScriptRoot "reports\milestone-d1\$name-test-results.json") -Raw|ConvertFrom-Json
    $b=Get-Content -LiteralPath (Join-Path $fixReport "$name-test-results.json") -Raw|ConvertFrom-Json
    $missing=@($a.checks|Where-Object {$_-notin$b.checks})
    if($missing.Count){throw "Old checks missing: $name"}
    $fixPreserved+=@{suite=$name;old=$a.passed;new=$b.passed;missing=$missing}
}
$oldGraph=@();$newGraph=@()
foreach($n in 1..5){
    $oldGraph+=@((Get-Content -LiteralPath (Join-Path $PSScriptRoot "reports\milestone-d1\graphical\phase-$n-results.json") -Raw|ConvertFrom-Json).checks)
    $newGraph+=@((Get-Content -LiteralPath (Join-Path $fixReport "resolution-1920x1080\graphical\phase-$n\phase-$n-results.json") -Raw|ConvertFrom-Json).checks)
}
$oldExit=(Get-Content -LiteralPath (Join-Path $PSScriptRoot 'reports\milestone-d1\exit-ui-results.json') -Raw|ConvertFrom-Json).checks
$newExit=(Get-Content -LiteralPath (Join-Path $fixReport 'exit-ui\exit-ui-results.json') -Raw|ConvertFrom-Json).checks
$missingGraph=@($oldGraph|Where-Object {$_-notin$newGraph});$missingExit=@($oldExit|Where-Object {$_-notin$newExit})
if($missingGraph.Count-or$missingExit.Count){throw 'Old graphical checks missing'}
@{suites=$fixPreserved;d1GraphicalOld=$oldGraph.Count;d1GraphicalNew=$newGraph.Count;d1GraphicalMissing=$missingGraph;exitUiMissing=$missingExit}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $fixReport 'old-tests-preservation.json') -Encoding utf8
$fixScope=Get-Content -LiteralPath (Join-Path $fixReport 'source-scope-verification.json') -Raw|ConvertFrom-Json
if($fixScope.gameplayContentDifferences-or$fixScope.rewardRuleDifferences){throw 'Gameplay or reward rules changed'}
$fixImages=@(Get-Content -LiteralPath (Join-Path $fixReport 'resolution-image-dimensions.json') -Raw|ConvertFrom-Json)
if(!$fixImages.Count-or@($fixImages|Where-Object {$_.width-ne2560-or$_.height-ne1440}).Count){throw 'Actual-user-resolution image dimensions failed'}
$fixAcceptance=@{status='D1_MAP_NATIVE_UI_FIX_PASS';version='0.4.1';testedDllSha256=$fixHash;completedAt=(Get-Date).ToString('o');automatedTotal=524;d1Graphical1920=97;saveExitAndLegacy=17;actualResolutionGraphical=42;cGraphical=20;renderResolutions=@('1920x1080','2560x1440');actualResolutionImages=$fixImages.Count;allOldChecksPreserved=$true;gameplayContentDifferences=0;rewardRuleDifferences=0;nativeScrollBoundsUnchanged=$true;NATIVE_UI_FIRST_FOR_PUBLIC_PATH=$true;editorRequired=$false;softwareInstalled=$false;humanQA='PENDING';physicalControllerQA='PENDING';D2='NOT_STARTED';PublicVerticalSlice='NOT_RELEASED';knownRuntimeDiagnostics='RID/shader/resource cleanup at process exit remains unaddressed'}
$fixAcceptance|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $fixReport 'acceptance.json') -Encoding utf8
$fixAcceptance|ConvertTo-Json -Depth 5
