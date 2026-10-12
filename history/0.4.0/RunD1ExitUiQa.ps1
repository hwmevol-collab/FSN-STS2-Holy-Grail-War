$ErrorActionPreference='Stop'
$d1Root=$PSScriptRoot
$d1Report=Join-Path $d1Root 'reports\milestone-d1'
$d1Runtime=Join-Path $d1Root 'native-runtime'
if(Get-CimInstance Win32_Process -Filter "Name='SlayTheSpire2.exe'" | Where-Object {$_.ExecutablePath -eq (Join-Path $d1Runtime 'SlayTheSpire2.exe')}){throw 'The isolated runtime is already in use'}
$d1Profile=Join-Path $env:APPDATA 'RinArcherCoreQA-20261007\default\1\modded\profile1\saves'
$d1Target=Join-Path $d1Profile 'current_run.save'
if(!$d1Target.StartsWith((Join-Path $env:APPDATA 'RinArcherCoreQA-20261007')+'\')){throw 'Save fixture target escaped isolated profile'}
if(Test-Path -LiteralPath $d1Target){Copy-Item -LiteralPath $d1Target -Destination (Join-Path $d1Report 'graphical\C-duplicate-complete.save') -Force}
Copy-Item -LiteralPath (Join-Path $d1Report 'graphical\checkpoint-master-pending.save') -Destination $d1Target -Force
& 'E:\BaiduNetdiskDownload\FSN\.tools\dotnet\dotnet.exe' build (Join-Path $d1Root 'tests\CoreTests.csproj') -c Release --no-restore --nologo
if($LASTEXITCODE-ne0){throw 'UI exit driver build failed'}
& (Join-Path $d1Root 'PrepareRuntime.ps1')
Copy-Item -LiteralPath (Join-Path $d1Root 'tests\bin\Release\net9.0\RinArcherCoreTests.dll') -Destination (Join-Path $d1Runtime 'mods\RinArcherCoreTests') -Force
$env:SteamAppId='2868840';$env:SteamGameId='2868840';$env:STS2_DEV_SKIP='1'
$d1Process=Start-Process -FilePath (Join-Path $d1Runtime 'SlayTheSpire2.exe') -WorkingDirectory $d1Runtime -ArgumentList '--force-steam=off','--rin-archer-d1-ui-exit' -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $d1Report 'exit-ui.stdout.log') -RedirectStandardError (Join-Path $d1Report 'exit-ui.stderr.log')
$d1Process.Id | Set-Content -LiteralPath (Join-Path $d1Report 'exit-ui-pid.txt')
@{pid=$d1Process.Id;coreDllSha256=(Get-FileHash -LiteralPath (Join-Path $d1Runtime 'mods\RinArcherCore\RinArcherCore.dll')).Hash;testDllSha256=(Get-FileHash -LiteralPath (Join-Path $d1Runtime 'mods\RinArcherCoreTests\RinArcherCoreTests.dll')).Hash;graphical=$true} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $d1Report 'exit-ui-launch.json') -Encoding utf8
