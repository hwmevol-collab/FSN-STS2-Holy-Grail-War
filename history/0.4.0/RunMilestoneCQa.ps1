$ErrorActionPreference='Stop'
$cRoot=$PSScriptRoot
& 'E:\BaiduNetdiskDownload\FSN\.tools\dotnet\dotnet.exe' build (Join-Path $cRoot 'tests\CoreTests.csproj') -c Release --no-restore --nologo
if($LASTEXITCODE-ne0){throw 'C graphical driver build failed'}
& (Join-Path $cRoot 'PrepareRuntime.ps1')
$cTests=Join-Path $cRoot 'native-runtime\mods\RinArcherCoreTests'
New-Item -ItemType Directory -Path $cTests -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $cRoot 'tests\bin\Release\net9.0\RinArcherCoreTests.dll'),(Join-Path $cRoot 'tests\RinArcherCoreTests.json') -Destination $cTests -Force
$cEvidence=Join-Path $cRoot 'native-runtime\c-qa'
if(Test-Path -LiteralPath $cEvidence){$cArchive=Join-Path $cRoot ('reports\milestone-c\graphical-attempt-'+(Get-Date).ToString('yyyyMMdd-HHmmss'));Move-Item -LiteralPath $cEvidence -Destination $cArchive;foreach($name in @('graphical.stdout.log','graphical.stderr.log')){if(Test-Path -LiteralPath (Join-Path $cRoot "reports\milestone-c\$name")){Copy-Item -LiteralPath (Join-Path $cRoot "reports\milestone-c\$name") -Destination $cArchive}}}
$env:SteamAppId='2868840';$env:SteamGameId='2868840';$env:STS2_DEV_SKIP='1'
$cProc=Start-Process -FilePath (Join-Path $cRoot 'native-runtime\SlayTheSpire2.exe') -WorkingDirectory (Join-Path $cRoot 'native-runtime') -ArgumentList '--force-steam=off','--rin-archer-c-qa' -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $cRoot 'reports\milestone-c\graphical.stdout.log') -RedirectStandardError (Join-Path $cRoot 'reports\milestone-c\graphical.stderr.log')
$cProc.Id | Set-Content -LiteralPath (Join-Path $cRoot 'reports\milestone-c\graphical-pid.txt')
Write-Output "C graphical QA PID $($cProc.Id)"
