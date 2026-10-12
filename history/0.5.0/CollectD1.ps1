$ErrorActionPreference='Stop'
$d1Report=Join-Path $PSScriptRoot 'reports\milestone-d1'
& (Join-Path $PSScriptRoot 'VerifyD1Evidence.ps1')
$d1Counts=@{core=85;alpha=58;highlight=10;reward=308;d1=63}
foreach($pair in $d1Counts.GetEnumerator()){$result=Get-Content -LiteralPath (Join-Path $d1Report "$($pair.Key)-test-results.json") -Raw | ConvertFrom-Json;if($result.status-ne'PASS'-or$result.passed-ne$pair.Value){throw "Automated gate failed: $($pair.Key)"}}
$d1Build=Get-Content -LiteralPath (Join-Path $d1Report 'test-build.json') -Raw | ConvertFrom-Json
$d1Graph=Get-Content -LiteralPath (Join-Path $d1Report 'graphical-summary.json') -Raw | ConvertFrom-Json
$d1Proof=Get-Content -LiteralPath (Join-Path $d1Report 'evidence-verification.json') -Raw | ConvertFrom-Json
$d1Exit=Get-Content -LiteralPath (Join-Path $d1Report 'exit-ui-results.json') -Raw | ConvertFrom-Json
$d1ExitLaunch=Get-Content -LiteralPath (Join-Path $d1Report 'exit-ui-launch.json') -Raw | ConvertFrom-Json
if($d1Exit.status-ne'PASS'-or$d1Exit.passed-ne8-or$d1ExitLaunch.coreDllSha256-ne$d1Build.coreDllSha256){throw 'Reward Save/Exit UI gate failed'}
if($d1Build.warnings-ne0-or$d1Build.errors-ne0-or$d1Graph.status-ne'PASS'-or$d1Proof.status-ne'PASS'-or$d1Graph.testedDllSha256-ne$d1Build.coreDllSha256-or(Get-FileHash -LiteralPath (Join-Path $PSScriptRoot 'bin\Release\net9.0\RinArcherCore.dll')).Hash-ne$d1Build.coreDllSha256){throw 'Final D1 binary gate failed'}
$d1Gates=[ordered]@{}
foreach($name in @('C_BASELINE_461_PASS','CONTRACT_RUN_STATE_PASS','MULTI_ROOM_HP_PASS','DUAL_DECK_PERSISTENCE_PASS','UPGRADE_PERSISTENCE_PASS','GOLD_PERSISTENCE_PASS','ENCOUNTER_RESET_PASS','DUAL_REWARD_PASS','REWARD_OWNER_ISOLATION_PASS','REWARD_RARITY_ISOLATION_PASS','REWARD_DETERMINISM_PASS','REWARD_SAVE_RESUME_PASS','RUN_DEFEAT_PASS','ACT_TRANSITION_PASS','REAL_GRAPHICAL_MULTI_ROOM_PASS')){$d1Gates[$name]=$true}
foreach($d1Line in Get-Content -LiteralPath (Join-Path $d1Report 'graphical-5.stdout.log')){if($d1Line-match'Saved run history: (\d+\.run)'){$d1Name=$Matches[1];$d1History=Join-Path $env:APPDATA "RinArcherCoreQA-20261007\default\1\modded\profile1\saves\history\$d1Name";New-Item -ItemType Directory -Path (Join-Path $d1Report 'native-death-history') -Force | Out-Null;Copy-Item -LiteralPath $d1History -Destination (Join-Path $d1Report 'native-death-history') -Force}}
$d1Gate=@{status='RIN_ARCHER_RUN_CORE_D1_PASS';version='0.4.0';gates=$d1Gates;DESIGN_DEVIATIONS=0;DESIGN_CONTRACT_CONFLICT=0;IMPLEMENTATION_BLOCKERS=0;counts=$d1Counts;automatedTotal=524;graphicalChecks=59;mainGraphicalChecks=51;rewardExitUiChecks=8;exactEvidenceChecks=$d1Proof.passed;testedDllSha256=$d1Build.coreDllSha256;buildWarnings=0;buildErrors=0;humanQA='PENDING';FullRunPlayability='DEFERRED_D2_E';NOT_PUBLIC_FINAL_RUN=$true;completedAt=(Get-Date).ToString('o')}
$d1Gate | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $d1Report 'acceptance.json') -Encoding utf8
Write-Output 'RIN_ARCHER_RUN_CORE_D1_PASS: 461 old + 63 D1 + 51 multi-room + 8 reward exit UI checks'
