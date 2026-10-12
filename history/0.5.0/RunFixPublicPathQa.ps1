param([ValidateSet('Exit','Resolution')][string]$Suite='Exit')
$ErrorActionPreference='Stop'
$fixReport=Join-Path $PSScriptRoot 'reports\d1-native-container-flow'
$fixNative=Join-Path $PSScriptRoot 'native-runtime\d1-qa'
$fixHash=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'bin\Release\net9.0\RinArcherCore.dll')).Hash
$fixSummary=@()
foreach($step in 1..2){
    $fixStarted=Get-Date
    if($Suite -eq 'Exit'){
        & (Join-Path $PSScriptRoot 'RunD1ExitUiQa.ps1') -Legacy:($step -eq 2)
        $fixStem='exit-ui';$fixResultFile=Join-Path $fixNative 'exit-ui-results.json'
        $fixEvidence=Join-Path $fixReport $(if($step -eq 1){'exit-ui'}else{'legacy-ui'})
    }else{
        & (Join-Path $PSScriptRoot 'RunD1GraphQa.ps1') -Phase $step -UserResolution
        $fixStem="graphical-$step";$fixResultFile=Join-Path $fixNative "phase-$step-results.json"
        $fixEvidence=Join-Path $fixReport "resolution-2560x1440\phase-$step"
    }
    $fixPid=[int](Get-Content -LiteralPath (Join-Path $fixReport "$fixStem-pid.txt"))
    $fixProcess=Get-Process -Id $fixPid -ErrorAction Stop
    if(!$fixProcess.WaitForExit(190000)){throw "$Suite step $step timed out; isolated process preserved"}
    $fixResult=Get-Content -LiteralPath $fixResultFile -Raw | ConvertFrom-Json
    $fixLaunch=Get-Content -LiteralPath (Join-Path $fixReport "$fixStem-launch.json") -Raw | ConvertFrom-Json
    if($fixResult.status -ne 'PASS' -or $fixLaunch.coreDllSha256 -ne $fixHash){throw "$Suite step $step failed or used a different core DLL"}
    $fixErrors=@(Select-String -LiteralPath (Join-Path $fixReport "$fixStem.stderr.log") -Pattern '\[ERROR\]|ERROR: System\.|Parent node is busy|Cannot get path|D1_.*FAILED|D1 GRAPHICAL FAIL|TimeoutException')
    if($fixErrors.Count){throw "$Suite step $step emitted a runtime exception"}
    New-Item -ItemType Directory -Path $fixEvidence -Force | Out-Null
    Get-ChildItem -LiteralPath $fixNative -File | Where-Object LastWriteTime -GE $fixStarted | Copy-Item -Destination $fixEvidence -Force
    foreach($suffix in @('stdout.log','stderr.log')){Copy-Item -LiteralPath (Join-Path $fixReport "$fixStem.$suffix") -Destination $fixEvidence -Force}
    Copy-Item -LiteralPath (Join-Path $fixReport "$fixStem-launch.json") -Destination $fixEvidence -Force
    $fixSummary+=@{step=$step;status=$fixResult.status;passed=$fixResult.passed;testedDllSha256=$fixHash;path=$fixEvidence}
    Write-Output "$Suite step $step PASS ($($fixResult.passed) checks)"
}
@{status='PASS';suite=$Suite;testedDllSha256=$fixHash;passed=($fixSummary|Measure-Object -Property passed -Sum).Sum;steps=$fixSummary} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $fixReport "$Suite-summary.json") -Encoding utf8
