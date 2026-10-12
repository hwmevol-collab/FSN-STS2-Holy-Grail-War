param([string]$EvidenceDirectory='')
$ErrorActionPreference='Stop'
$qaRoot=Join-Path $PSScriptRoot 'native-runtime'
$qaEvidence=if($EvidenceDirectory){$EvidenceDirectory}else{Join-Path $PSScriptRoot 'reports'}
New-Item -ItemType Directory -Path $qaEvidence -Force | Out-Null
function Read-QaState { & (Join-Path $PSScriptRoot 'ReadNativeQaJson.ps1') -Path (Join-Path $qaRoot 'qa-state.json') }
function Wait-QaTurn([int]$turn){
    $qaUntil=(Get-Date).AddSeconds(35)
    do{$qaState=Read-QaState;if($qaState.Turn -eq $turn -and $qaState.phase -eq 'Play' -and !$qaState.busy){return $qaState};Start-Sleep -Milliseconds 150}while((Get-Date)-lt $qaUntil)
    throw "Turn $turn did not enter Play; inspect logs"
}
function Qa([string]$op,[int]$index=0,[bool]$boost=$false,[string]$name='qa-capture'){& (Join-Path $PSScriptRoot 'QaCommand.ps1') -Operation $op -Index $index -Boost $boost -Name $name}
function Save-QaState([string]$name){Copy-Item -LiteralPath (Join-Path $qaRoot 'qa-state.json') -Destination (Join-Path $qaEvidence "$name.json") -Force;Qa screenshot -name $name;Copy-Item -LiteralPath (Join-Path $qaRoot "$name.png") -Destination $qaEvidence -Force}
$qaInitial=Wait-QaTurn 1
if($qaInitial.active -ne 'CHAR_ARCHER' -or $qaInitial.Energy -ne 3 -or $qaInitial.Mana -ne 3){throw 'Expected explicitly selected Archer opening'}
Save-QaState 'qa-02-opening-archer'
Qa cancel 0
Qa play 1
Save-QaState 'qa-03-cover-reserve-rin'
Qa switch
if((Read-QaState).Energy -ne 2){throw 'Switch refreshed shared energy'}
Save-QaState 'qa-04-bank-archer'
Qa play 0 $true
Qa play 1
Qa end
$qaTwo=Wait-QaTurn 2
if($qaTwo.archer.hand.Count -ne 4 -or $qaTwo.Mana -ne 4){throw 'Reserve freeze / Rin supply failure'}
Save-QaState 'qa-05-frozen-through-turn'
Qa switch
Qa play 0
Qa play 0
Qa play 0
Qa end
$qaThree=Wait-QaTurn 3
Qa play 1
Qa play 1
Qa play 1
Qa end
$qaFour=Wait-QaTurn 4
if($qaFour.rin.hp -ne 46 -or $qaFour.archer.hp -ne 70){throw 'MASTER did not hit reserve Rin independently'}
Save-QaState 'qa-06-master-reserve-hit'
Qa switch
Qa play 2
Qa play 2
Qa play 2
Qa end
$qaFive=Wait-QaTurn 5
if($qaFive.rin.hp -ne 44 -or $qaFive.archer.hp -ne 63){throw 'BOTH did not use independent Block'}
Save-QaState 'qa-07-both-independent'
for($qaTurn=5;$qaTurn -le 10;$qaTurn++){
    $qaNow=Wait-QaTurn $qaTurn
    while($qaNow.Energy -gt 0 -and !$qaNow.Finished){
        $qaHand=if($qaNow.active -eq 'CHAR_RIN'){@($qaNow.rin.hand)}else{@($qaNow.archer.hand)}
        $qaPick=-1
        for($qaIndex=0;$qaIndex -lt $qaHand.Count;$qaIndex++){if($qaHand[$qaIndex].SourceCardId -match 'GANDR|JEWEL_RELEASE|BOW_SHOT|CLOSE_COMBAT'){$qaPick=$qaIndex;break}}
        if($qaPick -lt 0){for($qaIndex=0;$qaIndex -lt $qaHand.Count;$qaIndex++){if($qaHand[$qaIndex].SourceCardId -eq 'RIN_S_JEWEL_PREPARATION'){$qaPick=$qaIndex;break}}}
        if($qaPick -lt 0 -and $qaNow.FreeSwitchAvailable){Qa switch;$qaNow=Read-QaState;continue}
        if($qaPick -lt 0){break}
        Qa play $qaPick ($qaNow.Jewel -gt 0)
        $qaNow=Read-QaState
    }
    $qaNow=Read-QaState
    if($qaNow.Finished){Save-QaState 'qa-08-contract-victory';Write-Output 'NATIVE_QA_BATTLE_COMPLETE';return}
    Qa end
}
throw 'Native QA battle did not finish within 10 turns'
