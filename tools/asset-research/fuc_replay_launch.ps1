[CmdletBinding()]
param([switch]$Visible,[switch]$Interpreter,[switch]$Software)
$ErrorActionPreference='Stop'
$battleWork='E:\FSN_MASTER_ASSET_WORK\fuc\BattleReplay'
$battleRuntime='E:\FSN_MASTER_ASSET_WORK\tools\ppsspp-isolated\runtime'
$battleExe=Join-Path $battleRuntime 'PPSSPPWindows64.exe'
if(-not(Test-Path -LiteralPath 'E:\FSN_MASTER_ASSET_WORK\backups\fuc-battle-replay-pre\BASELINE.json')){throw 'Battle golden baseline required'}
if(Get-NetTCPConnection -LocalPort 8991 -State Listen -ErrorAction SilentlyContinue){throw 'Debugger port already occupied; do not replace another process'}
$battleIni=Join-Path $battleWork 'replay_debug.ini'
$battleText=@'
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
'@
if($Interpreter){$battleText=$battleText.Replace('CPUCore = 1','CPUCore = 0')}
if($Software){$battleText=$battleText.Replace('GraphicsBackend = 2','GraphicsBackend = 0').Replace('SoftwareRenderer = False','SoftwareRenderer = True')}
$battleText | Set-Content -LiteralPath $battleIni -Encoding ascii
$battleIso='E:\BaiduNetdiskDownload\FSN\素材\Fate-Unlimited Codes (Europe) (PSP) (PSN)\Fate-Unlimited Codes (Europe) (PSP) (PSN).iso'
$battleLog=Join-Path $battleWork ('ppsspp_'+[DateTime]::UtcNow.ToString('yyyyMMdd_HHmmss')+'.log')
$battleArgs=@('--windowed',"--log=`"$battleLog`"",'--loglevel=3',"--appendconfig=`"$battleIni`"")
if($Interpreter){$battleArgs+='--cpu=interpreter'}else{$battleArgs+='--cpu=jit'}
if($Software){$battleArgs+='--graphics=software'}
$battleArgs+="`"$battleIso`""
$battleStyle=if($Visible){'Normal'}else{'Hidden'}
$battleProcess=Start-Process -FilePath $battleExe -WorkingDirectory $battleRuntime -ArgumentList $battleArgs -WindowStyle $battleStyle -PassThru
[ordered]@{process_id=$battleProcess.Id;exe=$battleExe;source_iso=$battleIso;config=$battleIni;debugger='ws://127.0.0.1:8991/debugger';memstick=(Join-Path $battleRuntime 'memstick');purpose='diagnostic_only same-episode battle replay';started_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $battleWork 'RUNTIME_PROCESS.json') -Encoding utf8
Write-Output "Isolated battle debugger started: $($battleProcess.Id)"
