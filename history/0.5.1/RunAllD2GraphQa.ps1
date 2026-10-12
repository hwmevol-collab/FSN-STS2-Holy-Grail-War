param([switch]$UserResolution)
$ErrorActionPreference='Stop'
& 'E:\BaiduNetdiskDownload\FSN\.tools\dotnet\dotnet.exe' build (Join-Path $PSScriptRoot 'tests\CoreTests.csproj') -c Release --no-restore --nologo
if($LASTEXITCODE){throw 'D2 build failed'}
$d2Hash=(Get-FileHash (Join-Path $PSScriptRoot 'bin\Release\net9.0\RinArcherCore.dll')).Hash
$d2Resolution=if($UserResolution){'2560x1440'}else{'1920x1080'}
$d2Results=@()
foreach($d2Phase in 1..6){
    & (Join-Path $PSScriptRoot 'RunNativeD2Qa.ps1') -Phase $d2Phase -UserResolution:$UserResolution
    $d2Dir=Join-Path $PSScriptRoot "reports\milestone-d2\graphical-$d2Resolution\phase-$d2Phase"
    $d2Result=Get-Content (Join-Path $d2Dir "phase-$d2Phase-results.json") -Raw|ConvertFrom-Json
    $d2Launch=Get-Content (Join-Path $d2Dir 'launch.json') -Raw|ConvertFrom-Json
    if($d2Result.status-ne'PASS'-or$d2Launch.coreDllSha256-ne$d2Hash){throw 'D2 graphical acceptance payload changed'}
    $d2Results+=@{phase=$d2Phase;passed=$d2Result.passed;status=$d2Result.status;testedDllSha256=$d2Hash}
}
@{status='PASS';resolution=$d2Resolution;phases=$d2Results;passed=($d2Results|Measure-Object passed -Sum).Sum;testedDllSha256=$d2Hash;nativeSoftwareController='PASS';physicalController='PHYSICAL_CONTROLLER_QA_DEFERRED_TO_WORKSHOP_RC';humanQA='PENDING'}|ConvertTo-Json -Depth 6|Set-Content (Join-Path $PSScriptRoot "reports\milestone-d2\graphical-$d2Resolution\summary.json") -Encoding utf8
