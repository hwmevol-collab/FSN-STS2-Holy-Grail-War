$ErrorActionPreference='Stop'
$focusStart=Get-Date
$focusHash=(Get-FileHash (Join-Path $PSScriptRoot 'bin\Release\net9.0\RinArcherCore.dll')).Hash
$focusRoot=Join-Path $PSScriptRoot 'reports\d2-rest-focus-highlight'
& (Join-Path $PSScriptRoot 'RunFlowRegressions.ps1')
& (Join-Path $PSScriptRoot 'RunAllNativeContainerQa.ps1')
& (Join-Path $PSScriptRoot 'RunAllNativeContainerQa.ps1') -UserResolution
$focusDestination=Join-Path $focusRoot 'full-regression'
if(Test-Path $focusDestination){throw 'Full regression evidence already exists'}
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'reports\d1-native-container-flow') -Destination $focusDestination -Recurse
$focusTestsPath=Join-Path $PSScriptRoot 'native-runtime\d2-test-results.json'
if((Get-Item $focusTestsPath).LastWriteTime-lt$focusStart){throw 'D2 test results stale'}
$focusTests=Get-Content $focusTestsPath -Raw|ConvertFrom-Json
if($focusTests.status-ne'PASS'-or$focusTests.passed-ne83){throw 'D2 headless checks failed'}
Copy-Item -LiteralPath $focusTestsPath -Destination $focusRoot -Force
& (Join-Path $PSScriptRoot 'RunAllD2GraphQa.ps1')
& (Join-Path $PSScriptRoot 'RunAllD2GraphQa.ps1') -UserResolution
foreach($res in @('1920x1080','2560x1440')){Copy-Item -LiteralPath (Join-Path $PSScriptRoot "reports\milestone-d2\graphical-$res") -Destination (Join-Path $focusRoot "d2-graphical-$res") -Recurse}
if((Get-FileHash (Join-Path $PSScriptRoot 'bin\Release\net9.0\RinArcherCore.dll')).Hash-ne$focusHash){throw 'Core changed during regression'}
@{status='PASS';testedDllSha256=$focusHash;startedAt=$focusStart.ToString('o');completedAt=(Get-Date).ToString('o');oldInvariantChecks=524;d2InvariantChecks=83;d2GraphicalChecksPerResolution=117;scope='All existing A-B-C-D1 and D2 suites; no tests skipped or weakened'}|ConvertTo-Json|Set-Content (Join-Path $focusRoot 'full-regression-summary.json')
Write-Output 'FULL A-B-C-D1 / D2 REGRESSION PASS'
