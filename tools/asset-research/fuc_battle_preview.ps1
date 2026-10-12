$ErrorActionPreference = 'Stop'
$battlePython = 'E:\FSN_MASTER_ASSET_WORK\tools\python\Scripts\python.exe'
$battleLibrary = 'E:\FSN_MASTER_ASSET_LIBRARY'
$battlePort = 8986
try { $battleProbe = Invoke-WebRequest -Uri "http://127.0.0.1:$battlePort/Gallery/FUC_BATTLE_RUNTIME.html" -TimeoutSec 3; if ($battleProbe.Content -notlike '*FUC*') { throw 'Unexpected local server content' } }
catch { $battlePort = 8997; $battlePreviewServer = Start-Process -FilePath $battlePython -ArgumentList @('-m','http.server',[string]$battlePort,'--bind','127.0.0.1','--directory',$battleLibrary) -WindowStyle Hidden -PassThru; Start-Sleep -Milliseconds 500 }
Start-Process "http://127.0.0.1:$battlePort/Gallery/FUC_BATTLE_RUNTIME.html"
