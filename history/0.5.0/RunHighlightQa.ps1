param([string]$EvidenceDirectory='')
$ErrorActionPreference='Stop'
$highlightRuntime=Join-Path $PSScriptRoot 'native-runtime'
$highlightEvidence=if($EvidenceDirectory){$EvidenceDirectory}else{Join-Path $PSScriptRoot 'reports\self-target-highlight'}
New-Item -ItemType Directory -Path $highlightEvidence -Force | Out-Null
function State {& (Join-Path $PSScriptRoot 'ReadNativeQaJson.ps1') -Path (Join-Path $highlightRuntime 'qa-state.json')}
function WaitState([scriptblock]$condition){
    $until=(Get-Date).AddSeconds(45)
    do{if(Test-Path (Join-Path $highlightRuntime 'qa-state.json')){$s=State;if(&$condition $s){return}};Start-Sleep -Milliseconds 150}while((Get-Date)-lt$until)
    throw 'Highlight QA state timeout'
}
function Q([hashtable]$command){
    $result=Join-Path $highlightRuntime 'qa-last-result.json'
    $before=if(Test-Path $result){(Get-Item $result).LastWriteTimeUtc}else{[datetime]::MinValue}
    if(Test-Path (Join-Path $highlightRuntime 'qa-command.json')){throw 'Pending QA command'}
    $command | ConvertTo-Json -Compress | Set-Content -LiteralPath (Join-Path $highlightRuntime 'qa-command.json') -Encoding utf8
    $until=(Get-Date).AddSeconds(45)
    do{Start-Sleep -Milliseconds 150;if((Test-Path $result)-and(Get-Item $result).LastWriteTimeUtc-gt$before){$r=& (Join-Path $PSScriptRoot 'ReadNativeQaJson.ps1') -Path $result;if(!$r.ok){throw $r.error};return}}while((Get-Date)-lt$until)
    throw ('QA command timeout: '+($command|ConvertTo-Json -Compress))
}
function StartQa([string]$owner){WaitState {param($s)$s.startingChoice};Q @{op='start';owner=$owner};WaitState {param($s)$s.Turn-eq1-and$s.phase-eq'Play'-and!$s.busy};Start-Sleep -Seconds 3}
function Restart([string]$owner){Q @{op='restart'};StartQa $owner}
function Highlight([string]$scenario,[string]$mode,[string]$suffix=''){
    Q @{op='highlight';scenario=$scenario;mode=$mode}
    foreach($ext in @('png','json')){Copy-Item -LiteralPath (Join-Path $highlightRuntime "$mode-$scenario.$ext") -Destination (Join-Path $highlightEvidence "$mode-$scenario$suffix.$ext") -Force}
    Write-Output "PASS $mode $scenario$suffix"
}
function EndTurn{$t=(State).Turn;Q @{op='end'};WaitState {param($s)$s.Turn-eq($t+1)-and$s.phase-eq'Play'-and!$s.busy}}
StartQa 'CHAR_RIN'
Highlight 'rin-self' 'mouse';Highlight 'rin-self' 'controller'
foreach($mode in @('mouse','controller')){
    Restart 'CHAR_ARCHER'
    foreach($scenario in @('archer-self','cover','front','front-reserve','projected-front','hrunting','rho','reinforced-rho')){Highlight $scenario $mode}
    EndTurn;EndTurn
    Highlight 'front' $mode '-enemy-master-active'
    Highlight 'projected-front' $mode '-enemy-master-active'
}
Write-Output 'NATIVE_HIGHLIGHT_QA_22_PASS'
