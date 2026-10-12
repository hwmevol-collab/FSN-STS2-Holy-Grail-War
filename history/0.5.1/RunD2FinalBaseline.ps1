$ErrorActionPreference='Stop'
$d2Start=Get-Date
$d2Hash=(Get-FileHash (Join-Path $PSScriptRoot 'bin\Release\net9.0\RinArcherCore.dll')).Hash
& (Join-Path $PSScriptRoot 'RunFlowRegressions.ps1')
& (Join-Path $PSScriptRoot 'RunAllNativeContainerQa.ps1')
& (Join-Path $PSScriptRoot 'RunAllNativeContainerQa.ps1') -UserResolution
$d2Root=Join-Path $PSScriptRoot 'reports\milestone-d2'
$d2Destination=Join-Path $d2Root 'old-baseline-final'
if(Test-Path $d2Destination){throw 'Final baseline already exists; archive it before replacing'}
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'reports\d1-native-container-flow') -Destination $d2Destination -Recurse
$d2Results=Join-Path $PSScriptRoot 'native-runtime\d2-test-results.json'
if((Get-Item $d2Results).LastWriteTime-lt$d2Start){throw 'D2 headless results are stale'}
$d2Tests=Get-Content $d2Results -Raw|ConvertFrom-Json
if($d2Tests.status-ne'PASS'-or$d2Tests.passed-ne83){throw 'D2 native command checks failed'}
Copy-Item -LiteralPath $d2Results -Destination $d2Root -Force
@{status='PASS';testedDllSha256=$d2Hash;startedAt=$d2Start.ToString('o');completedAt=(Get-Date).ToString('o');checks=83;originalChecks=524;testsDriverNotInstalled=$true}|ConvertTo-Json|Set-Content (Join-Path $d2Root 'headless-launch.json') -Encoding utf8
if((Get-FileHash (Join-Path $PSScriptRoot 'bin\Release\net9.0\RinArcherCore.dll')).Hash-ne$d2Hash){throw 'Core changed during final baseline'}
Write-Output 'FINAL OLD BASELINE + D2 NATIVE HEADLESS PASS'
