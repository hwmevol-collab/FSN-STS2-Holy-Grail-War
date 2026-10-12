param([switch]$Baseline,[switch]$UserResolution)
$ErrorActionPreference='Stop'
$focusRuntime=Join-Path $PSScriptRoot 'native-runtime'
$focusResolution=if($UserResolution){'2560x1440'}else{'1920x1080'}
$focusMode=if($Baseline){'baseline'}else{'fixed'}
$focusReport=Join-Path $PSScriptRoot "reports\d2-rest-focus-highlight\$focusMode-$focusResolution"
if(Get-CimInstance Win32_Process -Filter "Name='SlayTheSpire2.exe'"|Where-Object ExecutablePath -EQ (Join-Path $focusRuntime 'SlayTheSpire2.exe')){throw 'QA runtime is in use'}
if(Test-Path (Join-Path $focusReport 'launch.json')){Copy-Item -LiteralPath $focusReport -Destination ($focusReport+'-attempt-'+(Get-Date).ToString('yyyyMMdd-HHmmss')) -Recurse}
New-Item -ItemType Directory -Path $focusReport -Force|Out-Null
& 'E:\BaiduNetdiskDownload\FSN\.tools\dotnet\dotnet.exe' build (Join-Path $PSScriptRoot 'tests\CoreTests.csproj') -c Release --no-restore --nologo
if($LASTEXITCODE-ne0){throw 'QA build failed'}
& (Join-Path $PSScriptRoot 'PrepareRuntime.ps1')
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'tests\bin\Release\net9.0\RinArcherCoreTests.dll'),(Join-Path $PSScriptRoot 'tests\RinArcherCoreTests.json') -Destination (Join-Path $focusRuntime 'mods\RinArcherCoreTests') -Force
$focusArgs=@('--force-steam=off',"--rin-archer-rest-focus-$([string]$(if($Baseline){'baseline'}else{'qa'}))");if($UserResolution){$focusArgs+='--rin-archer-public-path-1440'}
$focusStart=Get-Date
$focusProcess=Start-Process -FilePath (Join-Path $focusRuntime 'SlayTheSpire2.exe') -WorkingDirectory $focusRuntime -ArgumentList $focusArgs -Environment @{SteamAppId='2868840';SteamGameId='2868840';STS2_DEV_SKIP='1'} -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $focusReport 'stdout.log') -RedirectStandardError (Join-Path $focusReport 'stderr.log')
@{startedAt=$focusStart.ToString('o');pid=$focusProcess.Id;coreDllSha256=(Get-FileHash (Join-Path $focusRuntime 'mods\RinArcherCore\RinArcherCore.dll')).Hash;baseline=[bool]$Baseline;requestedResolution=$focusResolution;physicalController=$false;input='Native mouse/key events and software controller actions through native NInputManager'}|ConvertTo-Json|Set-Content (Join-Path $focusReport 'launch.json')
if(!$focusProcess.WaitForExit(180000)){throw 'Focus QA timed out; process preserved'}
Get-ChildItem (Join-Path $focusRuntime 'rest-focus-qa') -File|Where-Object LastWriteTime -GE $focusStart|Copy-Item -Destination $focusReport -Force
$focusResult=Get-Content (Join-Path $focusReport 'results.json') -Raw|ConvertFrom-Json
if($focusResult.status-ne'PASS'){throw $focusResult.error}
if(Select-String -LiteralPath (Join-Path $focusReport 'stderr.log') -Pattern '\[ERROR\]|ERROR: System\.|Parent node is busy|Cannot get path|TimeoutException' -Quiet){throw 'Focus QA runtime error'}
Write-Output "REST FOCUS $focusMode $focusResolution PASS ($($focusResult.passed) checks)"
