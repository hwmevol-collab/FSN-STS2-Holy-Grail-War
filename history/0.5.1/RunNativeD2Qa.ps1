param([ValidateRange(1,8)][int]$Phase=1,[switch]$UserResolution)
$ErrorActionPreference='Stop'
$d2Runtime=Join-Path $PSScriptRoot 'native-runtime'
$d2Resolution=if($UserResolution){'2560x1440'}else{'1920x1080'}
$d2Report=Join-Path $PSScriptRoot "reports\milestone-d2\graphical-$d2Resolution\phase-$Phase"
if(Get-CimInstance Win32_Process -Filter "Name='SlayTheSpire2.exe'"|Where-Object ExecutablePath -EQ (Join-Path $d2Runtime 'SlayTheSpire2.exe')){throw 'Isolated runtime is in use'}
if(Test-Path (Join-Path $d2Report 'launch.json')){$d2Attempt=Join-Path $PSScriptRoot "reports\milestone-d2\attempts\$((Get-Date).ToString('yyyyMMdd-HHmmss'))-$d2Resolution-phase-$Phase";New-Item -ItemType Directory -Path (Split-Path $d2Attempt) -Force|Out-Null;Copy-Item -LiteralPath $d2Report -Destination $d2Attempt -Recurse}
New-Item -ItemType Directory -Path $d2Report -Force|Out-Null
& 'E:\BaiduNetdiskDownload\FSN\.tools\dotnet\dotnet.exe' build (Join-Path $PSScriptRoot 'tests\CoreTests.csproj') -c Release --no-restore --nologo
if($LASTEXITCODE-ne0){throw 'D2 driver build failed'}
& (Join-Path $PSScriptRoot 'PrepareRuntime.ps1')
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'tests\bin\Release\net9.0\RinArcherCoreTests.dll'),(Join-Path $PSScriptRoot 'tests\RinArcherCoreTests.json') -Destination (Join-Path $d2Runtime 'mods\RinArcherCoreTests') -Force
$d2Args=@('--force-steam=off',"--rin-archer-d2-qa-$Phase");if($UserResolution){$d2Args+='--rin-archer-public-path-1440'}
$d2Started=Get-Date
$d2Process=Start-Process -FilePath (Join-Path $d2Runtime 'SlayTheSpire2.exe') -WorkingDirectory $d2Runtime -ArgumentList $d2Args -Environment @{SteamAppId='2868840';SteamGameId='2868840';STS2_DEV_SKIP='1'} -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $d2Report 'stdout.log') -RedirectStandardError (Join-Path $d2Report 'stderr.log')
$d2Launch=@{phase=$Phase;pid=$d2Process.Id;startedAt=$d2Started.ToString('o');coreDllSha256=(Get-FileHash (Join-Path $d2Runtime 'mods\RinArcherCore\RinArcherCore.dll')).Hash;testDllSha256=(Get-FileHash (Join-Path $d2Runtime 'mods\RinArcherCoreTests\RinArcherCoreTests.dll')).Hash;isolatedProfile='RinArcherCoreQA-20261007';requestedResolution=$d2Resolution}
$d2Launch|ConvertTo-Json|Set-Content (Join-Path $d2Report 'launch.json') -Encoding utf8
Write-Output "D2 graphical phase $Phase PID $($d2Process.Id) $d2Resolution"
if(!$d2Process.WaitForExit(600000)){throw 'D2 phase timed out; isolated process preserved'}
Get-ChildItem (Join-Path $d2Runtime 'd2-qa') -File|Where-Object LastWriteTime -GE $d2Started|Copy-Item -Destination $d2Report -Force
$d2Result=Get-Content (Join-Path $d2Report "phase-$Phase-results.json") -Raw|ConvertFrom-Json
if($d2Result.status-ne'PASS'){throw "D2 phase $Phase failed: $($d2Result.error)"}
if(Select-String -LiteralPath (Join-Path $d2Report 'stderr.log') -Pattern '\[ERROR\]|ERROR: System\.|Parent node is busy|Cannot get path|D2_GRAPHICAL_FAIL|TimeoutException' -Quiet){throw 'D2 runtime emitted actionable errors'}
Write-Output "D2 PHASE $Phase PASS ($($d2Result.passed) checks)"


