param([ValidateRange(1,3)][int]$Phase=1,[switch]$UserResolution)
$ErrorActionPreference='Stop'
$flowRuntime=Join-Path $PSScriptRoot 'native-runtime'
$flowReport=Join-Path $PSScriptRoot 'reports\d1-native-container-flow'
if(Get-CimInstance Win32_Process -Filter "Name='SlayTheSpire2.exe'"|Where-Object ExecutablePath -EQ (Join-Path $flowRuntime 'SlayTheSpire2.exe')){throw 'Isolated runtime is in use'}
& 'E:\BaiduNetdiskDownload\FSN\.tools\dotnet\dotnet.exe' build (Join-Path $PSScriptRoot 'tests\CoreTests.csproj') -c Release --no-restore --nologo
if($LASTEXITCODE-ne0){throw 'Container driver build failed'}
& (Join-Path $PSScriptRoot 'PrepareRuntime.ps1')
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'tests\bin\Release\net9.0\RinArcherCoreTests.dll'),(Join-Path $PSScriptRoot 'tests\RinArcherCoreTests.json') -Destination (Join-Path $flowRuntime 'mods\RinArcherCoreTests') -Force
$env:SteamAppId='2868840';$env:SteamGameId='2868840';$env:STS2_DEV_SKIP='1'
$flowArgs=@('--force-steam=off',"--rin-archer-container-qa-$Phase");if($UserResolution){$flowArgs+='--rin-archer-public-path-1440'}
$flowProcess=Start-Process -FilePath (Join-Path $flowRuntime 'SlayTheSpire2.exe') -WorkingDirectory $flowRuntime -ArgumentList $flowArgs -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $flowReport "container-$Phase.stdout.log") -RedirectStandardError (Join-Path $flowReport "container-$Phase.stderr.log")
$flowProcess.Id|Set-Content -LiteralPath (Join-Path $flowReport "container-$Phase-pid.txt")
@{phase=$Phase;pid=$flowProcess.Id;startedAt=(Get-Date).ToString('o');coreDllSha256=(Get-FileHash -LiteralPath (Join-Path $flowRuntime 'mods\RinArcherCore\RinArcherCore.dll')).Hash;testDllSha256=(Get-FileHash -LiteralPath (Join-Path $flowRuntime 'mods\RinArcherCoreTests\RinArcherCoreTests.dll')).Hash;isolatedProfile='RinArcherCoreQA-20261007';requestedResolution=$(if($UserResolution){'2560x1440'}else{'1920x1080'})}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $flowReport "container-$Phase-launch.json") -Encoding utf8
Write-Output "Native reward-container phase $Phase PID $($flowProcess.Id)"
