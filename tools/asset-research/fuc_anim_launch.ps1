[CmdletBinding()]
param([switch]$Visible,[switch]$Software,[switch]$Jit)
$ErrorActionPreference='Stop'
$fucWork='E:\FSN_MASTER_ASSET_WORK\fuc\AnimationValidation'
$fucRuntime='E:\FSN_MASTER_ASSET_WORK\tools\ppsspp-isolated\runtime'
$fucExe=Join-Path $fucRuntime 'PPSSPPWindows64.exe'
if(-not(Test-Path -LiteralPath 'E:\FSN_MASTER_ASSET_WORK\backups\fuc-animation-pre-validation\BASELINE.json')){throw 'Freeze animation baseline first'}
$fucPrevious=Join-Path $fucWork 'RUNTIME_PROCESS.json'
if(Test-Path -LiteralPath $fucPrevious){
    $fucOwned=(Get-Content -LiteralPath $fucPrevious -Raw | ConvertFrom-Json)
    $fucRunning=Get-Process -Id $fucOwned.process_id -ErrorAction SilentlyContinue
    if($fucRunning){if($fucRunning.Path -ne $fucExe){throw 'Recorded process identity differs; do not stop it'};Stop-Process -Id $fucRunning.Id;$fucRunning.WaitForExit()}
}
$fucOldIni=Join-Path $fucRuntime 'memstick\PSP\SYSTEM\ppsspp.ini'
$fucConfigBaseline=Join-Path $fucWork 'ISOLATED_CONFIG_BEFORE.ini'
if(-not(Test-Path -LiteralPath $fucConfigBaseline)){Copy-Item -LiteralPath $fucOldIni -Destination $fucConfigBaseline}
$fucIni=Join-Path $fucWork 'animation_debug.ini'
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
CPUCore = 0
FastMemoryAccess = False
[Graphics]
GraphicsBackend = 2
ReplaceTextures = False
[Sound]
Enable = True
'@ | Set-Content -LiteralPath $fucIni -Encoding ascii
$fucConfigText=Get-Content -LiteralPath $fucIni -Raw
if($Software){$fucConfigText=$fucConfigText.Replace('GraphicsBackend = 2','GraphicsBackend = 0').Replace('ReplaceTextures = False',"ReplaceTextures = False`nSoftwareRenderer = True")}
if($Jit){$fucConfigText=$fucConfigText.Replace('CPUCore = 0','CPUCore = 1')}
$fucConfigText | Set-Content -LiteralPath $fucIni -Encoding ascii
$fucIso='E:\BaiduNetdiskDownload\FSN\素材\Fate-Unlimited Codes (Europe) (PSP) (PSN)\Fate-Unlimited Codes (Europe) (PSP) (PSN).iso'
$fucLog=Join-Path $fucWork 'ppsspp_runtime.log'
if(Test-Path -LiteralPath $fucLog){Move-Item -LiteralPath $fucLog -Destination (Join-Path $fucWork ("ppsspp_runtime_"+[DateTime]::UtcNow.ToString('yyyyMMdd_HHmmss')+'.log'))}
$fucArguments=@('--windowed',"--log=`"$fucLog`"",'--loglevel=4',"--appendconfig=`"$fucIni`"")
if($Software){$fucArguments+='--graphics=software'}
if($Jit){$fucArguments+='--cpu=jit'}
$fucArguments+="`"$fucIso`""
$fucWindowStyle=if($Visible){'Normal'}else{'Hidden'}
$fucProcess=Start-Process -FilePath $fucExe -WorkingDirectory $fucRuntime -ArgumentList $fucArguments -WindowStyle $fucWindowStyle -PassThru
[ordered]@{process_id=$fucProcess.Id;exe=$fucExe;source_iso=$fucIso;config=$fucIni;debugger='ws://127.0.0.1:8991/debugger';memstick=(Join-Path $fucRuntime 'memstick');purpose='diagnostic_only animation runtime';started_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $fucWork 'RUNTIME_PROCESS.json') -Encoding utf8
Write-Output "Isolated animation debugger process started: $($fucProcess.Id)"
