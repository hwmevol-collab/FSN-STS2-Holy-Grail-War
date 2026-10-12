param(
 [Parameter(Mandatory=$true)][string]$Game107,
 [Parameter(Mandatory=$true)][string]$Game111,
 [Parameter(Mandatory=$true)][string]$BaseLibDll,
 [Parameter(Mandatory=$true)][string]$RitsuRoot,
 [string]$Dotnet='dotnet'
)
$ErrorActionPreference='Stop'
$taskRoot=Split-Path $PSScriptRoot
$taskManifest=Get-Content -Raw -LiteralPath (Join-Path $taskRoot 'verified-games.json') | ConvertFrom-Json
foreach($taskVersion in @('0.107.1','0.111.0')){
 $taskGame=if($taskVersion -eq '0.107.1'){$Game107}else{$Game111}
 $taskExpected=@($taskManifest.Variants | Where-Object {$_.Game.GameVersion -eq ('v'+$taskVersion)})[0].Game
 $taskRelease=Get-Content -Raw -LiteralPath (Join-Path $taskGame 'release_info.json') | ConvertFrom-Json
 $taskGameDll=Join-Path $taskGame 'data_sts2_windows_x86_64/sts2.dll'
 if($taskRelease.version -ne $taskExpected.GameVersion -or $taskRelease.commit -ne $taskExpected.Commit -or (Get-FileHash -LiteralPath $taskGameDll).Hash -ne $taskExpected.AssemblySha256){throw 'Game identity differs from reviewed build'}
 $taskOutput=Join-Path $taskRoot ('artifacts/'+$taskVersion)
 & $Dotnet build (Join-Path $taskRoot 'src/RinArcherCore.csproj') -c Release "-p:GameDir=$taskGame" "-p:BaseLibDll=$BaseLibDll" "-p:RitsuLibReferenceTarget=$taskVersion" "-p:RitsuLibReferenceRoot=$RitsuRoot/" -o $taskOutput
 if($LASTEXITCODE -ne 0){throw "Content build failed: $taskVersion"}
}
& $Dotnet build (Join-Path $taskRoot 'loader/RinArcherCore.Loader.csproj') -c Release "-p:GameDir=$Game107" -o (Join-Path $taskRoot 'artifacts/loader')
if($LASTEXITCODE -ne 0){throw 'Loader build failed'}
Write-Output 'Compiled both content variants and oldest-API Loader. Rebuilt bytes require new payload hashes; no gameplay acceptance is inferred.'
