$ErrorActionPreference='Stop'
$d1Report=Join-Path $PSScriptRoot 'reports\milestone-d1'
$d1ExpectedHash=(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'bin\Release\net9.0\RinArcherCore.dll')).Hash
$d1Results=@()
foreach($phase in 1..5){
    & (Join-Path $PSScriptRoot 'RunD1GraphQa.ps1') -Phase $phase
    $d1Pid=[int](Get-Content -LiteralPath (Join-Path $d1Report "graphical-$phase-pid.txt"))
    $d1Process=Get-Process -Id $d1Pid -ErrorAction Stop
    if(!$d1Process.WaitForExit(190000)){throw "Phase $phase timed out; the isolated process is preserved for inspection"}
    $d1Result=Get-Content -LiteralPath (Join-Path $PSScriptRoot "native-runtime\d1-qa\phase-$phase-results.json") -Raw | ConvertFrom-Json
    $d1Launch=Get-Content -LiteralPath (Join-Path $d1Report "graphical-$phase-launch.json") -Raw | ConvertFrom-Json
    if($d1Result.status-ne'PASS'-or$d1Launch.coreDllSha256-ne$d1ExpectedHash){throw "Phase $phase failed or used a different DLL"}
    $d1Errors=@(Select-String -LiteralPath (Join-Path $d1Report "graphical-$phase.stderr.log") -Pattern '\[ERROR\]|D1_.*FAILED|D1 GRAPHICAL FAIL|TimeoutException')
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
