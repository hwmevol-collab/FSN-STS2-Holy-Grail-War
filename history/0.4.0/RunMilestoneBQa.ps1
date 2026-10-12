param([ValidateSet('Arsenal','Reinforcement','Field')][string]$Phase='Arsenal')
$ErrorActionPreference='Stop'
$bQa=Join-Path $PSScriptRoot 'native-runtime'
$bEvidence=Join-Path $PSScriptRoot 'reports\milestone-b'
function State {Get-Content -LiteralPath (Join-Path $bQa 'qa-state.json') -Raw | ConvertFrom-Json}
function WaitState([scriptblock]$condition){
    $until=(Get-Date).AddSeconds(45)
    do{$s=State;if(&$condition $s){return $s};Start-Sleep -Milliseconds 150}while((Get-Date)-lt $until)
    throw 'QA state wait timeout'
}
function Q([hashtable]$command){
    $result=Join-Path $bQa 'qa-last-result.json';$before=if(Test-Path $result){(Get-Item $result).LastWriteTimeUtc}else{[datetime]::MinValue}
    if(Test-Path (Join-Path $bQa 'qa-command.json')){throw 'Pending command'}
    $command | ConvertTo-Json -Compress | Set-Content -LiteralPath (Join-Path $bQa 'qa-command.json') -Encoding utf8
    $until=(Get-Date).AddSeconds(45)
    do{Start-Sleep -Milliseconds 150;if((Test-Path $result)-and(Get-Item $result).LastWriteTimeUtc-gt $before){$r=Get-Content $result -Raw | ConvertFrom-Json;if(!$r.ok){throw $r.error};return}}while((Get-Date)-lt $until)
    throw ('QA command timeout: '+($command|ConvertTo-Json -Compress))
}
function Capture([string]$name){Q @{op='screenshot';name=$name};Copy-Item -LiteralPath (Join-Path $bQa "$name.png") -Destination $bEvidence -Force;Copy-Item -LiteralPath (Join-Path $bQa 'qa-state.json') -Destination (Join-Path $bEvidence "$name.json") -Force;Write-Output "CAPTURE $name"}
function Assert([bool]$ok,[string]$name){if(!$ok){throw "NATIVE_QA_FAIL: $name"};Write-Output "PASS $name"}
function PlayId([string]$id,[hashtable]$extra=@{}){
    $s=State;$hand=if($s.active-eq'CHAR_RIN'){@($s.rin.hand)}else{@($s.archer.hand)};$index=-1
    for($i=0;$i-lt$hand.Count;$i++){if($hand[$i].SourceCardId-eq$id){$index=$i;break}}
    if($index-lt0){throw "Card missing: $id"};$cmd=@{op='play';index=$index};foreach($key in $extra.Keys){$cmd[$key]=$extra[$key]};Q $cmd
}
function AddTrace([bool]$upgrade=$false){Q @{op='fixture';card='TRACE';upgraded=$upgrade}}
function TraceArm([string]$arm,[bool]$upgrade=$false){AddTrace $upgrade;PlayId 'ARC_S_TRACE' @{arm=$arm;capture='trace-choice'};Copy-Item -LiteralPath (Join-Path $bQa 'trace-choice.png') -Destination (Join-Path $bEvidence 'trace-choice.png') -Force}
function EndTurn { $t=(State).Turn;Q @{op='end'};WaitState {param($s)$s.Turn-eq($t+1)-and$s.phase-eq'Play'-and!$s.busy} | Out-Null }
function StartQaState([string]$owner='CHAR_ARCHER'){WaitState {param($s)$s.startingChoice} | Out-Null;Q @{op='start';owner=$owner};WaitState {param($s)$s.Turn-eq1-and$s.phase-eq'Play'-and!$s.busy} | Out-Null}
function Restart([bool]$field=$false,[string]$owner='CHAR_ARCHER'){Q @{op='restart';field=$field};StartQaState $owner}
if($Phase-eq'Arsenal'){
    StartQaState
    AddTrace;$before=State;PlayId 'ARC_S_TRACE';$after=State
    Assert ($before.Energy-eq$after.Energy-and$before.archer.hand.Count-eq$after.archer.hand.Count) 'Trace cancel preserves card and energy'
    TraceArm 'ARM_KANSHOU_BAKUYA';PlayId 'ARM_KANSHOU_BAKUYA';Assert ((State).enemy.servantHp-eq42) 'normal K&B 6 damage';Capture 'B-normal-kb'
    TraceArm 'ARM_RHO_AIAS';PlayId 'ARM_RHO_AIAS';Assert ((State).archer.block-eq8-and(State).rin.block-eq0) 'normal Rho independent Archer 8';Capture 'C-normal-rho'
    EndTurn
    TraceArm 'ARM_HRUNTING';$before=State;PlayId 'ARM_HRUNTING';$after=State;Assert ($before.Energy-eq$after.Energy-and$before.Mana-eq$after.Mana-and$after.IndependentActionAvailable) 'Hrunting cancel preserves resources and IA'
    PlayId 'ARM_HRUNTING' @{target='MASTER';capture='hrunting-choice'};Copy-Item (Join-Path $bQa 'hrunting-choice.png') $bEvidence -Force
    Assert ((State).enemy.masterHp-eq25) 'Hrunting targets reserve Master';Capture 'D-hrunting-reserve-master'
    EndTurn
    TraceArm 'ARM_HRUNTING';PlayId 'ARM_HRUNTING' @{target='SERVANT'};Assert ((State).enemy.servantHp-eq33) 'Hrunting targets Servant';Capture 'D-hrunting-servant'
    EndTurn
    TraceArm 'ARM_HRUNTING' $true;$arm=@((State).archer.hand | Where-Object {$_.SourceCardId -eq 'ARM_HRUNTING'})[0];$instance=$arm.InstanceId
    Q @{op='switch'};Capture 'E-banked-hrunting';EndTurn
    Q @{op='switch'};$arm=@((State).archer.hand|Where-Object {$_.SourceCardId -eq 'ARM_HRUNTING'})[0]
    Assert ($arm.InstanceId-eq$instance-and$arm.arm.temporaryManaDiscount-eq0) 'Banking same instance and Trace+ expires';Capture 'E-restored-hrunting'
    Capture 'K-target-tag-front'
}
if($Phase-eq'Reinforcement'){
    if((State).startingChoice){StartQaState 'CHAR_RIN'}else{Restart $false 'CHAR_RIN'}
    Q @{op='fixture';card='REINFORCE'};PlayId 'RIN_S_REINFORCE_PROJECTION' @{boost=$true;capture='reinforce-jewel-choice'};Copy-Item (Join-Path $bQa 'reinforce-jewel-choice.png') $bEvidence -Force
    Assert ((State).Jewel-eq0-and(State).PendingReinforcement.Active) 'explicit Jewel consumed once, Pending set'
    Q @{op='switch'};TraceArm 'ARM_KANSHOU_BAKUYA';Capture 'G-reinforced-jewel-kb';PlayId 'ARM_KANSHOU_BAKUYA'
    Assert ((State).enemy.servantHp-eq36-and(State).IndependentActionAvailable) 'reinforced 6x2, instance discount 0M, IA unused';Capture 'B-reinforced-two-hits'
    EndTurn
    TraceArm 'ARM_KANSHOU_BAKUYA';$arm=@((State).archer.hand|Where-Object {$_.SourceCardId -eq 'ARM_KANSHOU_BAKUYA'})[0];Assert (!$arm.arm.reinforced) 'second projection is ordinary';PlayId 'ARM_KANSHOU_BAKUYA'
    Assert (!(State).IndependentActionAvailable) 'ordinary 1M weapon consumes IA';Capture 'H-normal-ia'
    Restart $false 'CHAR_RIN'
    Q @{op='fixture';card='REINFORCE';upgraded=$true};PlayId 'RIN_S_REINFORCE_PROJECTION' @{boost=$false};Q @{op='switch'};TraceArm 'ARM_RHO_AIAS';PlayId 'ARM_RHO_AIAS'
    Assert ((State).archer.block-eq8-and(State).rin.block-eq8) 'reinforced Rho protects reserve Rin independently';Capture 'C-reinforced-reserve-rin'
    Restart $false 'CHAR_RIN'
    Q @{op='fixture';card='REINFORCE';upgraded=$true};PlayId 'RIN_S_REINFORCE_PROJECTION' @{boost=$false};Q @{op='switch'};EndTurn
    Assert ((State).PendingReinforcement.Active) 'Pending survives shared turn and switch'
    TraceArm 'ARM_HRUNTING';PlayId 'ARM_HRUNTING' @{target='MASTER'};Assert ((State).enemy.masterHp-eq20) 'reinforced Hrunting 14';Capture 'F-reinforced-hrunting'
    Q @{op='guard'};$before=State;Q @{op='nonattack'};Assert ((State).rin.hp-eq($before.rin.hp-3)-and(State).GuardCharges-eq1) 'Guard ignores nonattack'
    EndTurn
    Q @{op='guard'};$before=State;EndTurn
    Assert ((State).rin.hp-eq$before.rin.hp-and(State).archer.hp-eq($before.archer.hp-12)-and(State).GuardCharges-eq0) 'Guard redirects MASTER before damage';Capture 'I-guard-master'
    Capture 'K-target-tag-both'
}
if($Phase-eq'Field'){
    if((State).startingChoice){StartQaState 'CHAR_ARCHER'}else{Restart $true 'CHAR_ARCHER'};Assert ((State).enemy.masterHp-eq42-and(State).enemy.servantHp-eq56) 'QA field exact HP';Capture 'J-field-front-12'
    $before=State;EndTurn;Assert ((State).archer.hp-eq($before.archer.hp-12)) 'FIELD 9+3 FRONT 12';Capture 'K-field-both-8'
    $before=State;EndTurn;Assert ((State).rin.hp-eq($before.rin.hp-8)-and(State).archer.hp-eq($before.archer.hp-8)) 'FIELD 5+3 BOTH 8';Capture 'K-field-master-14'
    Q @{op='suppress'};$before=State;Capture 'J-field-suppressed';EndTurn
    Assert ((State).rin.hp-eq($before.rin.hp-11)-and!(State).FieldStatuses[0].Suppressed) 'suppressed MASTER base11, FIELD recovers next player start';Capture 'J-field-recovered'
    EndTurn;Assert ((State).enemy.masterBlock-eq10-and(State).enemy.ActiveId-eq'QA_PAIR_BASIC_SERVANT') 'step4 Master block10 switches Servant'
    $before=State;EndTurn;Assert ((State).archer.hp-eq($before.archer.hp-12)) 'FIELD recovered attack12 repeats cycle';Capture 'J-field-next-cycle'
}
Write-Output "NATIVE_MILESTONE_B_$($Phase.ToUpperInvariant())_PASS"
