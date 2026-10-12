param([switch]$LaunchBoot)
$ErrorActionPreference='Stop'
$sliceRoot=$PSScriptRoot
$sliceGame='E:\SteamLibrary\steamapps\common\Slay the Spire 2'
$sliceRuntime=Join-Path $sliceRoot 'native-runtime'
New-Item -ItemType Directory -Path $sliceRuntime -Force | Out-Null
foreach($sliceFile in Get-ChildItem -LiteralPath $sliceGame -File | Where-Object {$_.Extension -in '.exe','.dll','.pck','.json'}) {
    $sliceDest=Join-Path $sliceRuntime $sliceFile.Name
    if(!(Test-Path -LiteralPath $sliceDest)){New-Item -ItemType HardLink -Path $sliceDest -Target $sliceFile.FullName | Out-Null}
}
$sliceData=Join-Path $sliceRuntime 'data_sts2_windows_x86_64'
New-Item -ItemType Directory -Path $sliceData -Force | Out-Null
foreach($sliceFile in Get-ChildItem -LiteralPath (Join-Path $sliceGame 'data_sts2_windows_x86_64') -File){
    $sliceDest=Join-Path $sliceData $sliceFile.Name
    if(!(Test-Path -LiteralPath $sliceDest)){New-Item -ItemType HardLink -Path $sliceDest -Target $sliceFile.FullName | Out-Null}
}
@'
[application]
config/use_custom_user_dir=true
config/custom_user_dir_name="RinArcherCoreQA-20261007"
[display]
window/size/viewport_width=1280
window/size/viewport_height=720
window/size/mode=0
'@ | Set-Content -LiteralPath (Join-Path $sliceRuntime 'override.cfg') -Encoding utf8
foreach($sliceMod in @('BaseLib','STS2-RitsuLib','RinArcherCore')){New-Item -ItemType Directory -Path (Join-Path $sliceRuntime "mods\$sliceMod") -Force | Out-Null}
Copy-Item -Path 'E:\SteamLibrary\steamapps\workshop\content\2868840\3737335127\BaseLib\*' -Destination (Join-Path $sliceRuntime 'mods\BaseLib') -Recurse -Force
Copy-Item -Path (Join-Path $sliceRoot 'dependencies\*') -Destination (Join-Path $sliceRuntime 'mods\STS2-RitsuLib') -Recurse -Force
Copy-Item -LiteralPath (Join-Path $sliceRoot 'RinArcherCore.json') -Destination (Join-Path $sliceRuntime 'mods\RinArcherCore') -Force
Copy-Item -LiteralPath (Join-Path $sliceRoot 'bin\Release\net9.0\RinArcherCore.dll') -Destination (Join-Path $sliceRuntime 'mods\RinArcherCore') -Force
if($LaunchBoot){
    $sliceUser=Join-Path $env:APPDATA 'RinArcherCoreQA-20261007\default\1'
    New-Item -ItemType Directory -Path $sliceUser -Force | Out-Null
    '{"schema_version":5,"seen_ea_disclaimer":true,"skip_intro_logo":true,"language":"eng","mod_settings":{"mods_enabled":true,"mod_list":[]}}' | Set-Content -LiteralPath (Join-Path $sliceUser 'settings.save') -Encoding utf8
    $env:SteamAppId='2868840'; $env:SteamGameId='2868840'
    $sliceProc=Start-Process -FilePath (Join-Path $sliceRuntime 'SlayTheSpire2.exe') -WorkingDirectory $sliceRuntime -ArgumentList '--headless','--quit-after','800','--force-steam=off','--rin-archer-boot' -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $sliceRoot 'reports\boot.stdout.log') -RedirectStandardError (Join-Path $sliceRoot 'reports\boot.stderr.log')
    $sliceProc.Id | Set-Content -LiteralPath (Join-Path $sliceRoot 'reports\boot-process-id.txt')
    Write-Output "Launched isolated native game PID $($sliceProc.Id)"
}
