param([switch]$Stop,[switch]$NoBrowser)
$ErrorActionPreference='Stop'
$taskLaunchMutex=[System.Threading.Mutex]::new($false,'Local\FSNUnifiedSemanticCatalogLauncher')
if(-not $taskLaunchMutex.WaitOne(15000)){throw 'Another semantic catalog launch is still in progress.'}
try {
$taskStatePath='E:\FSN_MASTER_ASSET_WORK\unified-semantic\SERVER.json'
if(Test-Path -LiteralPath $taskStatePath){
    $taskState=Get-Content -LiteralPath $taskStatePath -Raw | ConvertFrom-Json
    try{
        $taskConfig=Invoke-RestMethod -Uri "http://127.0.0.1:$($taskState.port)/api/config" -TimeoutSec 3
        if($taskConfig.service -eq 'FSN_UNIFIED' -and $taskConfig.token -eq $taskState.token){
            if($Stop){Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:$($taskState.port)/api/shutdown" -Headers @{'X-Semantic-Token'=$taskState.token} -ContentType 'application/json' -Body '{}' | Out-Null;return}
            if(-not $NoBrowser){Start-Process $taskState.url};return
        }
    }catch{}
}
if($Stop){Write-Host 'Semantic catalog server is already stopped.';return}
if(-not (Test-Path -LiteralPath 'E:\FSN_MASTER_ASSET_LIBRARY\SemanticCatalog\Database\FSN_SEMANTIC.sqlite')){throw 'The semantic database is not ready. Run the authorized catalog pipeline first.'}
$env:PYTHONPYCACHEPREFIX='E:\FSN_MASTER_ASSET_WORK\pycache\unified'
$env:PYTHONIOENCODING='utf-8'
$taskLog='E:\FSN_MASTER_ASSET_WORK\unified-semantic\server.log'
$taskErrorLog='E:\FSN_MASTER_ASSET_WORK\unified-semantic\server-error.log'
$taskServerArguments=@('E:\FSN_MASTER_ASSET_WORK\scripts\unified_server.py')
if(-not $NoBrowser){$taskServerArguments+='--open-browser'}
Start-Process -FilePath 'D:\Python\python.exe' -ArgumentList $taskServerArguments -WindowStyle Hidden -RedirectStandardOutput $taskLog -RedirectStandardError $taskErrorLog | Out-Null
for($taskAttempt=0;$taskAttempt -lt 20;$taskAttempt++){
    Start-Sleep -Milliseconds 250
    try {
        $taskNewState=Get-Content -LiteralPath $taskStatePath -Raw | ConvertFrom-Json
        $taskNewConfig=Invoke-RestMethod -Uri "http://127.0.0.1:$($taskNewState.port)/api/config" -TimeoutSec 2
        if($taskNewConfig.service -eq 'FSN_UNIFIED' -and $taskNewConfig.token -eq $taskNewState.token){return}
    } catch {}
}
throw 'The local service did not start. See the semantic service log in the work directory.'
} finally {
    $taskLaunchMutex.ReleaseMutex()
    $taskLaunchMutex.Dispose()
}
