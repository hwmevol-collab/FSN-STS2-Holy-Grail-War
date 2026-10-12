[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$semanticWork='E:\FSN_MASTER_ASSET_WORK\fuc\SemanticMapping'
$semanticRuntime='E:\FSN_MASTER_ASSET_WORK\tools\ppsspp-isolated\runtime'
$semanticExe=Join-Path $semanticRuntime 'PPSSPPWindows64.exe'
if(-not(Test-Path -LiteralPath 'E:\FSN_MASTER_ASSET_WORK\backups\fuc-semantic-mapping-pre\BASELINE.json')){throw 'Semantic baseline required'}
if(Get-NetTCPConnection -LocalPort 8991 -State Listen -ErrorAction SilentlyContinue){throw 'Debugger occupied'}
$semanticIni=Join-Path $semanticWork 'semantic_debug.ini'
@'
[General]
RemoteDebuggerOnStartup = True
RemoteDebuggerLocal = True
RemoteISOPort = 8991
RemoteShareOnStartup = False
PauseOnLostFocus = False
PauseWhenMinimized = False
DumpFileTypes = 0
FileLogging = True
CheckForNewVersion = False
EnableCheats = False
EnablePlugins = False
[CPU]
CPUCore = 1
FastMemoryAccess = False
[Graphics]
GraphicsBackend = 2
SoftwareRenderer = False
ReplaceTextures = False
[Sound]
Enable = True
'@ | Set-Content -LiteralPath $semanticIni -Encoding ascii
$semanticIso='E:\BaiduNetdiskDownload\FSN\素材\Fate-Unlimited Codes (Europe) (PSP) (PSN)\Fate-Unlimited Codes (Europe) (PSP) (PSN).iso'
$semanticLog=Join-Path $semanticWork ('ppsspp_'+[DateTime]::UtcNow.ToString('yyyyMMdd_HHmmss')+'.log')
$semanticArgs=@('--windowed',"--log=`"$semanticLog`"",'--loglevel=3',"--appendconfig=`"$semanticIni`"",'--cpu=jit',"`"$semanticIso`"")
$semanticProcess=Start-Process -FilePath $semanticExe -WorkingDirectory $semanticRuntime -ArgumentList $semanticArgs -WindowStyle Normal -PassThru
[ordered]@{process_id=$semanticProcess.Id;exe=$semanticExe;source_iso=$semanticIso;config=$semanticIni;memstick=(Join-Path $semanticRuntime 'memstick');purpose='Command List and bounded semantic anchors only';started_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $semanticWork 'RUNTIME_PROCESS.json') -Encoding utf8
Write-Output "Isolated semantic session started: $($semanticProcess.Id)"
