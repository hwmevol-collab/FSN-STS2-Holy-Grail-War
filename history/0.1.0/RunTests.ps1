param([switch]$NativeQa)
$ErrorActionPreference='Stop'
$sliceRoot=$PSScriptRoot
& 'E:\BaiduNetdiskDownload\FSN\.tools\dotnet\dotnet.exe' build (Join-Path $sliceRoot 'tests\CoreTests.csproj') -c Release --nologo --no-restore
if($LASTEXITCODE -ne 0){throw 'Build failed'}
& (Join-Path $sliceRoot 'PrepareRuntime.ps1')
$sliceMods=Join-Path $sliceRoot 'native-runtime\mods\RinArcherCoreTests'
New-Item -ItemType Directory -Path $sliceMods -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $sliceRoot 'tests\bin\Release\net9.0\RinArcherCoreTests.dll') -Destination $sliceMods -Force
Copy-Item -LiteralPath (Join-Path $sliceRoot 'tests\RinArcherCoreTests.json') -Destination $sliceMods -Force
$sliceExe=Join-Path $sliceRoot 'native-runtime\SlayTheSpire2.exe'
foreach($sliceName in @('core-tests-error.txt','core-test-results.json','qa-state.json','qa-last-result.json','qa-command.json')){
    $sliceOld=Join-Path $sliceRoot "native-runtime\$sliceName"
    if(Test-Path -LiteralPath $sliceOld){Move-Item -LiteralPath $sliceOld -Destination (Join-Path $sliceRoot "reports\$((Get-Date).ToString('yyyyMMdd-HHmmss-ffff'))-$sliceName")}
}
$env:STS2_DEV_SKIP='1'
$sliceArgs=if($NativeQa){@('--force-steam=off','--rin-archer-qa','--rin-archer-native-qa')}else{@('--headless','--force-steam=off','--rin-archer-tests')}
$sliceLog=if($NativeQa){'native-qa'}else{'tests'}
$sliceProc=Start-Process -FilePath $sliceExe -WorkingDirectory (Split-Path $sliceExe) -ArgumentList $sliceArgs -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $sliceRoot "reports\$sliceLog.stdout.log") -RedirectStandardError (Join-Path $sliceRoot "reports\$sliceLog.stderr.log")
$sliceProc.Id | Set-Content -LiteralPath (Join-Path $sliceRoot 'reports\tests-process-id.txt')
Write-Output "Native invariant suite PID $($sliceProc.Id)"
