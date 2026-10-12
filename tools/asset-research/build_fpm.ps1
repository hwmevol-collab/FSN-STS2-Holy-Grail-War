$ErrorActionPreference='Stop'
$taskWork='E:\FSN_MASTER_ASSET_WORK'
$env:TEMP=Join-Path $taskWork 'tmp';$env:TMP=$env:TEMP
$env:DOTNET_CLI_HOME=Join-Path $taskWork 'tmp\dotnet-home'
$env:NUGET_PACKAGES=Join-Path $taskWork 'tmp\nuget'
$project=Join-Path $taskWork 'repos\FatePackageManager\FatePackageManager.csproj'
$source=Get-Content -LiteralPath $project -Raw
$source.Replace('<TargetFramework>net8.0</TargetFramework>','<TargetFramework>net9.0</TargetFramework>') | Set-Content -LiteralPath $project -Encoding utf8
& 'E:\BaiduNetdiskDownload\FSN\.tools\dotnet\dotnet.exe' publish $project -c Release -o (Join-Path $taskWork 'tools\fpm')
if($LASTEXITCODE -ne 0) { throw 'FatePackageManager build failed; retained source and cache are on E:' }
