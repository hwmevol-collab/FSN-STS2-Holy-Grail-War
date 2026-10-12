param([ValidateRange(1,5)][int]$StartPhase=1)
$ErrorActionPreference='Stop'
$d1Report=Join-Path $PSScriptRoot 'reports\d1-native-container-flow'
& 'E:\BaiduNetdiskDownload\FSN\.tools\dotnet\dotnet.exe' build (Join-Path $PSScriptRoot 'tests\CoreTests.csproj') -c Release --no-restore --nologo
if($LASTEXITCODE-ne0){throw 'D1 driver build failed'}
$d1ExpectedHash=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'bin\Release\net9.0\RinArcherCore.dll')).Hash
$d1Results=@()
if($StartPhase -gt 1){foreach($phase in 1..($StartPhase-1)){
    $d1Prior=Get-Content -LiteralPath (Join-Path $d1Report "graphical\phase-$phase\phase-$phase-results.json") -Raw|ConvertFrom-Json
    $d1PriorLaunch=Get-Content -LiteralPath (Join-Path $d1Report "graphical-$phase-launch.json") -Raw|ConvertFrom-Json
    if($d1Prior.status-ne'PASS'-or$d1PriorLaunch.coreDllSha256-ne$d1ExpectedHash){throw 'Prior phase does not match tested DLL'}
    $d1Results+=@{phase=$phase;passed=$d1Prior.passed;status=$d1Prior.status;coreDllSha256=$d1PriorLaunch.coreDllSha256}
}}
if($StartPhase -gt 1){
    $d1Checkpoint=@('checkpoint-master-pending','checkpoint-map','checkpoint-servant-pending','checkpoint-act-transition')[$StartPhase-2]
    $d1Fixture=Join-Path $d1Report "graphical\phase-$($StartPhase-1)\$d1Checkpoint.save"
    $d1Profile=Join-Path $env:APPDATA 'RinArcherCoreQA-20261007\default\1\modded\profile1\saves\current_run.save'
    Copy-Item -LiteralPath $d1Fixture -Destination $d1Profile -Force
}
foreach($phase in $StartPhase..5){
    & (Join-Path $PSScriptRoot 'RunD1GraphQa.ps1') -Phase $phase
    $d1Pid=[int](Get-Content -LiteralPath (Join-Path $d1Report "graphical-$phase-pid.txt"))
    $d1Process=Get-Process -Id $d1Pid -ErrorAction Stop
    if(!$d1Process.WaitForExit(190000)){throw "Phase $phase timed out; the isolated process is preserved for inspection"}
    $d1Result=Get-Content -LiteralPath (Join-Path $PSScriptRoot "native-runtime\d1-qa\phase-$phase-results.json") -Raw | ConvertFrom-Json
    $d1Launch=Get-Content -LiteralPath (Join-Path $d1Report "graphical-$phase-launch.json") -Raw | ConvertFrom-Json
    if($d1Result.status-ne'PASS'-or$d1Launch.coreDllSha256-ne$d1ExpectedHash){throw "Phase $phase failed or used a different DLL"}
    $d1Errors=@(Select-String -LiteralPath (Join-Path $d1Report "graphical-$phase.stderr.log") -Pattern '\[ERROR\]|ERROR: System\.|Parent node is busy|Cannot get path|D1_.*FAILED|D1 GRAPHICAL FAIL|TimeoutException')
    if($d1Errors.Count){throw "Phase $phase emitted a runtime exception"}
    $d1Results+=@{phase=$phase;passed=$d1Result.passed;status=$d1Result.status;coreDllSha256=$d1Launch.coreDllSha256}
    $d1PhaseEvidence=Join-Path $d1Report "graphical\phase-$phase"
    New-Item -ItemType Directory -Path $d1PhaseEvidence -Force | Out-Null
    Copy-Item -Path (Join-Path $PSScriptRoot 'native-runtime\d1-qa\*') -Destination $d1PhaseEvidence -Force
    Write-Output "FINAL PHASE $phase PASS ($($d1Result.passed) checks)"
}
$d1Graph=Join-Path $d1Report 'graphical'
New-Item -ItemType Directory -Path $d1Graph -Force | Out-Null
Copy-Item -Path (Join-Path $PSScriptRoot 'native-runtime\d1-qa\*') -Destination $d1Graph -Force
@{status='PASS';graphical=$true;crossProcessReload=$true;testedDllSha256=$d1ExpectedHash;phases=$d1Results;passed=($d1Results | Measure-Object -Property passed -Sum).Sum;scenarios=@('A','B','C','D','E','F','G','H');humanQA='PENDING'} | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $d1Report 'graphical-summary.json') -Encoding utf8

