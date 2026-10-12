param([switch]$UserResolution,[ValidateRange(1,3)][int]$StartPhase=1)
$ErrorActionPreference='Stop'
$flowReport=Join-Path $PSScriptRoot 'reports\d1-native-container-flow'
$flowResults=@()
$flowHash=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'bin\Release\net9.0\RinArcherCore.dll')).Hash
$flowResolution=if($UserResolution){'2560x1440'}else{'1920x1080'}
if($StartPhase-gt1){
    foreach($previous in 1..($StartPhase-1)){
        $priorRoot=Join-Path $flowReport "container-$flowResolution\phase-$previous"
        $prior=Get-Content -LiteralPath (Join-Path $priorRoot "phase-$previous-results.json") -Raw|ConvertFrom-Json
        $priorLaunch=Get-Content -LiteralPath (Join-Path $priorRoot "container-$previous-launch.json") -Raw|ConvertFrom-Json
        if($prior.status-ne'PASS'-or$priorLaunch.coreDllSha256-ne$flowHash){throw 'Prior container phase is not accepted for this core DLL'}
        $flowResults+=@{phase=$previous;passed=$prior.passed;status=$prior.status;testedDllSha256=$flowHash}
    }
    $priorRoot=Join-Path $flowReport "container-$flowResolution\phase-$($StartPhase-1)"
    $checkpoint=if($StartPhase-eq2){'generated-container'}else{'servant-pending'}
    Copy-Item -LiteralPath (Join-Path $priorRoot "checkpoint-$checkpoint.save") -Destination (Join-Path $env:APPDATA 'RinArcherCoreQA-20261007\default\1\modded\profile1\saves\current_run.save') -Force
    Copy-Item -LiteralPath (Join-Path $priorRoot 'witness.json') -Destination (Join-Path $PSScriptRoot 'native-runtime\flow-qa\witness.json') -Force
}
foreach($phase in $StartPhase..3){
    & (Join-Path $PSScriptRoot 'RunNativeContainerQa.ps1') -Phase $phase -UserResolution:$UserResolution
    $flowPid=[int](Get-Content -LiteralPath (Join-Path $flowReport "container-$phase-pid.txt"))
    $flowProcess=Get-Process -Id $flowPid -ErrorAction Stop
    if(!$flowProcess.WaitForExit(210000)){throw "Container phase $phase timed out; isolated process preserved"}
    $flowResult=Get-Content -LiteralPath (Join-Path $PSScriptRoot "native-runtime\flow-qa\phase-$phase-results.json") -Raw|ConvertFrom-Json
    $flowLaunch=Get-Content -LiteralPath (Join-Path $flowReport "container-$phase-launch.json") -Raw|ConvertFrom-Json
    $flowHash=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'bin\Release\net9.0\RinArcherCore.dll')).Hash
    if($flowResult.status-ne'PASS'-or$flowLaunch.coreDllSha256-ne$flowHash){throw "Container phase $phase failed or stale DLL"}
    $flowErrors=@(Select-String -LiteralPath (Join-Path $flowReport "container-$phase.stderr.log") -Pattern '\[ERROR\]|ERROR: System\.|Parent node is busy|Cannot get path|CONTAINER_GRAPHICAL_FAIL|TimeoutException')
    if($flowErrors.Count){throw "Container phase $phase emitted runtime errors"}
    $flowEvidence=Join-Path $flowReport "container-$($flowLaunch.requestedResolution)\phase-$phase"
    New-Item -ItemType Directory -Path $flowEvidence -Force|Out-Null
    Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'native-runtime\flow-qa') -File|Where-Object LastWriteTime -GE ([datetime]$flowLaunch.startedAt)|Copy-Item -Destination $flowEvidence -Force
    foreach($suffix in @('stdout.log','stderr.log')){Copy-Item -LiteralPath (Join-Path $flowReport "container-$phase.$suffix") -Destination $flowEvidence -Force}
    Copy-Item -LiteralPath (Join-Path $flowReport "container-$phase-launch.json") -Destination $flowEvidence -Force
    $flowResults+=@{phase=$phase;passed=$flowResult.passed;status=$flowResult.status;testedDllSha256=$flowHash}
    Write-Output "CONTAINER PHASE $phase PASS ($($flowResult.passed) checks)"
}
@{status='PASS';requestedResolution=$(if($UserResolution){'2560x1440'}else{'1920x1080'});phases=$flowResults;passed=($flowResults|Measure-Object -Property passed -Sum).Sum;testedDllSha256=$flowHash;humanQA='PENDING'}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $flowReport $(if($UserResolution){'container-1440-summary.json'}else{'container-1080-summary.json'})) -Encoding utf8
