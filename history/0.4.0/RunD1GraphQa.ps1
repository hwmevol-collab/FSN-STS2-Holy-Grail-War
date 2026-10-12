param([ValidateRange(1,5)][int]$Phase=1)
$ErrorActionPreference='Stop'
$d1Root=$PSScriptRoot
$d1Runtime=Join-Path $d1Root 'native-runtime'
$d1Report=Join-Path $d1Root 'reports\milestone-d1'
if(Get-CimInstance Win32_Process -Filter "Name='SlayTheSpire2.exe'" | Where-Object {$_.ExecutablePath -eq (Join-Path $d1Runtime 'SlayTheSpire2.exe')}){throw 'The isolated native runtime is already in use'}
& 'E:\BaiduNetdiskDownload\FSN\.tools\dotnet\dotnet.exe' build (Join-Path $d1Root 'tests\CoreTests.csproj') -c Release --no-restore --nologo
if($LASTEXITCODE-ne0){throw 'D1 graphical driver build failed'}
& (Join-Path $d1Root 'PrepareRuntime.ps1')
$d1Mods=Join-Path $d1Runtime 'mods\RinArcherCoreTests'
Copy-Item -LiteralPath (Join-Path $d1Root 'tests\bin\Release\net9.0\RinArcherCoreTests.dll'),(Join-Path $d1Root 'tests\RinArcherCoreTests.json') -Destination $d1Mods -Force
$env:SteamAppId='2868840';$env:SteamGameId='2868840';$env:STS2_DEV_SKIP='1'
$d1Process=Start-Process -FilePath (Join-Path $d1Runtime 'SlayTheSpire2.exe') -WorkingDirectory $d1Runtime -ArgumentList '--force-steam=off',"--rin-archer-d1-qa-$Phase" -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $d1Report "graphical-$Phase.stdout.log") -RedirectStandardError (Join-Path $d1Report "graphical-$Phase.stderr.log")
$d1Process.Id|Set-Content -LiteralPath (Join-Path $d1Report "graphical-$Phase-pid.txt")
@{phase=$Phase;pid=$d1Process.Id;graphical=$true;testDllSha256=(Get-FileHash -LiteralPath (Join-Path $d1Mods 'RinArcherCoreTests.dll')).Hash;coreDllSha256=(Get-FileHash -LiteralPath (Join-Path $d1Runtime 'mods\RinArcherCore\RinArcherCore.dll')).Hash;startedAt=(Get-Date).ToString('o');isolatedProfile='RinArcherCoreQA-20261007'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $d1Report "graphical-$Phase-launch.json") -Encoding utf8
Write-Output "D1 native graphical phase $Phase PID $($d1Process.Id)"
