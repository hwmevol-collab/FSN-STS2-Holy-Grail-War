param([ValidateSet('Inventory','Probe','Tracks','Subtitles','Shots','Thumbnails','Sequences','Terms','Duplicates','Index','Overviews','Validate','Integrate','Gallery','Verify','QA','Report','All')][string]$Mode='Verify',[int]$Port=8776)
$env:TEMP='E:\FSN_MASTER_ASSET_WORK\tmp\animation-reference'
$env:TMP=$env:TEMP
$env:PYTHONPYCACHEPREFIX='E:\FSN_MASTER_ASSET_WORK\tmp\pycache'
$taskPython='E:\FSN_MASTER_ASSET_WORK\tools\python\Scripts\python.exe'
$taskScripts='E:\FSN_MASTER_ASSET_WORK\scripts'
function Invoke-AnimationStage([string]$TaskFile,[string]$TaskMode){
  if($TaskMode){& $taskPython (Join-Path $taskScripts $TaskFile) $TaskMode}else{& $taskPython (Join-Path $taskScripts $TaskFile)}
  if($LASTEXITCODE -ne 0){throw "Animation stage failed: $TaskFile $TaskMode"}
}
switch($Mode){
 'Inventory'{Invoke-AnimationStage 'animation_inventory.py' ''}
 'Probe'{Invoke-AnimationStage 'animation_shots.py' 'Probe'}
 {$_ -in 'Tracks','Subtitles'}{Invoke-AnimationStage 'animation_tracks.py' ''}
 {$_ -in 'Shots','Thumbnails'}{Invoke-AnimationStage 'animation_shots.py' 'Shots'}
 {$_ -in 'Sequences','Terms','Index'}{Invoke-AnimationStage 'animation_index.py' 'Index'}
 'Duplicates'{Invoke-AnimationStage 'animation_index.py' 'Duplicates'}
 'Overviews'{Invoke-AnimationStage 'animation_overviews.py' ''}
 'Validate'{Invoke-AnimationStage 'animation_validation.py' ''}
 'Integrate'{Invoke-AnimationStage 'animation_finalize.py' 'Integrate'}
 'Verify'{Invoke-AnimationStage 'animation_finalize.py' 'Verify'}
 'QA'{Invoke-AnimationStage 'animation_qa.py' ''}
 'Report'{Invoke-AnimationStage 'animation_finalize.py' 'Report'}
 'Gallery'{& $taskPython (Join-Path $taskScripts 'animation_serve.py') --port $Port --open-browser}
 'All'{
   Invoke-AnimationStage 'animation_inventory.py' ''
   Invoke-AnimationStage 'animation_tracks.py' ''
   if(-not(Test-Path -LiteralPath 'E:\FSN_MASTER_ASSET_LIBRARY\AnimationReferences\Metadata\ANIMATION_DETECTOR_PROBE.json')){Invoke-AnimationStage 'animation_shots.py' 'Probe'; throw 'Review the cross-work probe before running the pinned full detector.'}
   Invoke-AnimationStage 'animation_shots.py' 'Shots'
   Invoke-AnimationStage 'animation_index.py' 'Index'
   Invoke-AnimationStage 'animation_overviews.py' ''
   Invoke-AnimationStage 'animation_index.py' 'Duplicates'
   Invoke-AnimationStage 'animation_validation.py' ''
   Invoke-AnimationStage 'animation_qa.py' ''
   Invoke-AnimationStage 'animation_finalize.py' 'Integrate'
   Invoke-AnimationStage 'animation_finalize.py' 'Verify'
   Invoke-AnimationStage 'animation_finalize.py' 'Report'
 }
}
