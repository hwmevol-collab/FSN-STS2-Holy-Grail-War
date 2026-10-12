param([string]$MediaAssetId,[string]$ShotId,[double]$Seconds=0,[double]$QaDuration=0,[switch]$Mute,[switch]$ShowClock,[switch]$ResolveOnly)
$env:TEMP='E:\FSN_MASTER_ASSET_WORK\tmp\animation-reference'
$env:TMP=$env:TEMP
$env:PYTHONPYCACHEPREFIX='E:\FSN_MASTER_ASSET_WORK\tmp\pycache'
$taskArgs=@('E:\FSN_MASTER_ASSET_WORK\scripts\animation_play.py')
if($MediaAssetId){$taskArgs+=@('--media',$MediaAssetId)}
if($ShotId){$taskArgs+=@('--shot',$ShotId)}
if(-not $ShotId){$taskArgs+=@('--seconds',$Seconds.ToString([Globalization.CultureInfo]::InvariantCulture))}
if($QaDuration -gt 0){$taskArgs+=@('--duration',$QaDuration.ToString([Globalization.CultureInfo]::InvariantCulture))}
if($Mute){$taskArgs+='--mute'}
if($ShowClock){$taskArgs+='--clock'}
if($ResolveOnly){$taskArgs+='--resolve'}
& 'E:\FSN_MASTER_ASSET_WORK\tools\python\Scripts\python.exe' @taskArgs
if($LASTEXITCODE -ne 0){throw 'Animation playback helper failed.'}
