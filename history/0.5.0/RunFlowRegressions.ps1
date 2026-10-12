param([ValidateSet('Invariant','D1','Exit','Resolution','C','AB')][string]$StartAt='Invariant',[switch]$HighlightOnly)
$ErrorActionPreference='Stop'
$flowRoot=$PSScriptRoot
$flowReport=Join-Path $flowRoot 'reports\d1-native-container-flow'
$flowRuntime=Join-Path $flowRoot 'native-runtime'
$flowHash=(Get-FileHash -LiteralPath (Join-Path $flowRoot 'bin\Release\net9.0\RinArcherCore.dll')).Hash
$flowStages=@('Invariant','D1','Exit','Resolution','C','AB')
function Wait-FlowProcess([int]$processId,[int]$seconds=180){$process=Get-Process -Id $processId -ErrorAction Stop;if(!$process.WaitForExit($seconds*1000)){throw "Isolated process $processId timed out; preserved for inspection"};if($process.ExitCode){throw "Isolated process $processId exited $($process.ExitCode)"}}
function Ensure-FlowHash {if((Get-FileHash -LiteralPath (Join-Path $flowRoot 'bin\Release\net9.0\RinArcherCore.dll')).Hash-ne$flowHash){throw 'Core payload changed during regression'}}
function Check-FlowLog([string]$path){if(@(Select-String -LiteralPath $path -Pattern '\[ERROR\]|ERROR: System\.|Parent node is busy|Cannot get path|TimeoutException').Count){throw "Managed runtime error: $path"}}
foreach($stage in $flowStages[$flowStages.IndexOf($StartAt)..($flowStages.Count-1)]){
    Ensure-FlowHash
    if($stage-eq'Invariant'){
        & (Join-Path $flowRoot 'RunTests.ps1')
        Wait-FlowProcess ([int](Get-Content (Join-Path $flowRoot 'reports\tests-process-id.txt')))
        $suites=@();foreach($name in @('core','alpha','highlight','reward','d1')){
            $result=Get-Content (Join-Path $flowRuntime "$name-test-results.json") -Raw|ConvertFrom-Json
            if($result.status-ne'PASS'){throw "Invariant $name failed"}
            Copy-Item -LiteralPath (Join-Path $flowRuntime "$name-test-results.json") -Destination $flowReport -Force
            $suites+=@{suite=$name;passed=$result.passed;status=$result.status}
        }
        foreach($suffix in @('stdout.log','stderr.log')){Copy-Item -LiteralPath (Join-Path $flowRoot "reports\tests.$suffix") -Destination (Join-Path $flowReport "regression.$suffix") -Force}
        Check-FlowLog (Join-Path $flowReport 'regression.stderr.log')
        @{status='PASS';total=($suites|Measure-Object passed -Sum).Sum;suites=$suites;testedDllSha256=$flowHash}|ConvertTo-Json -Depth 5|Set-Content (Join-Path $flowReport 'regression-summary.json') -Encoding utf8
    }
    if($stage-eq'D1'){& (Join-Path $flowRoot 'RunAllD1GraphQa.ps1')}
    if($stage-eq'Exit'){& (Join-Path $flowRoot 'RunFixPublicPathQa.ps1') -Suite Exit}
    if($stage-eq'Resolution'){& (Join-Path $flowRoot 'RunFixPublicPathQa.ps1') -Suite Resolution}
    if($stage-eq'C'){
        & (Join-Path $flowRoot 'PrepareRuntime.ps1')
        $evidence=Join-Path $flowReport 'c-regression';New-Item -ItemType Directory -Path $evidence -Force|Out-Null
        $started=Get-Date
        $process=Start-Process -FilePath (Join-Path $flowRuntime 'SlayTheSpire2.exe') -WorkingDirectory $flowRuntime -ArgumentList '--force-steam=off','--rin-archer-c-qa' -Environment @{SteamAppId='2868840';SteamGameId='2868840';STS2_DEV_SKIP='1'} -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $evidence 'stdout.log') -RedirectStandardError (Join-Path $evidence 'stderr.log')
        Wait-FlowProcess $process.Id 360
        $result=Get-Content (Join-Path $flowRuntime 'c-qa\results.json') -Raw|ConvertFrom-Json
        if($result.status-ne'PASS'){throw 'C native regression failed'}
        Get-ChildItem (Join-Path $flowRuntime 'c-qa') -File|Where-Object LastWriteTime -GE $started|Copy-Item -Destination $evidence -Force
        Check-FlowLog (Join-Path $evidence 'stderr.log')
        @{status='PASS';passed=$result.passed;testedDllSha256=$flowHash;startedAt=$started.ToString('o');pid=$process.Id}|ConvertTo-Json|Set-Content (Join-Path $evidence 'summary.json') -Encoding utf8
    }
    if($stage-eq'AB'){
        & (Join-Path $flowRoot 'RunTests.ps1') -NativeQa
        $bridgeId=[int](Get-Content (Join-Path $flowRoot 'reports\tests-process-id.txt'))
        $deadline=(Get-Date).AddSeconds(60)
        while(!(Test-Path (Join-Path $flowRuntime 'qa-state.json'))-or!(Get-Content (Join-Path $flowRuntime 'qa-state.json') -Raw|ConvertFrom-Json).startingChoice){if((Get-Date)-gt$deadline){throw 'Native A/B start timeout'};Start-Sleep -Milliseconds 200}
        $evidence=Join-Path $flowReport 'ab-regression';New-Item -ItemType Directory -Path $evidence -Force|Out-Null
        if(!$HighlightOnly){
        & (Join-Path $flowRoot 'QaCommand.ps1') -Operation start -Owner CHAR_ARCHER
        & (Join-Path $flowRoot 'RunBattleQa.ps1') -EvidenceDirectory $evidence | Tee-Object -FilePath (Join-Path $evidence 'a-battle.log')
        & (Join-Path $flowRoot 'QaCommand.ps1') -Operation restart
        & (Join-Path $flowRoot 'RunMilestoneBQa.ps1') -Phase Arsenal -EvidenceDirectory $evidence | Tee-Object -FilePath (Join-Path $evidence 'b-arsenal.log')
        & (Join-Path $flowRoot 'RunMilestoneBQa.ps1') -Phase Reinforcement -EvidenceDirectory $evidence | Tee-Object -FilePath (Join-Path $evidence 'b-reinforcement.log')
        & (Join-Path $flowRoot 'RunMilestoneBQa.ps1') -Phase Field -EvidenceDirectory $evidence | Tee-Object -FilePath (Join-Path $evidence 'b-field.log')
        & (Join-Path $flowRoot 'QaCommand.ps1') -Operation restart
        }else{foreach($proof in @(@('a-battle.log','NATIVE_QA_BATTLE_COMPLETE'),@('b-arsenal.log','NATIVE_MILESTONE_B_ARSENAL_PASS'),@('b-reinforcement.log','NATIVE_MILESTONE_B_REINFORCEMENT_PASS'),@('b-field.log','NATIVE_MILESTONE_B_FIELD_PASS'))){if(!(Select-String -LiteralPath (Join-Path $evidence $proof[0]) -Pattern $proof[1] -Quiet)){throw 'Prior native A/B proofs are incomplete'}}}
        & (Join-Path $flowRoot 'RunHighlightQa.ps1') -EvidenceDirectory $evidence | Tee-Object -FilePath (Join-Path $evidence 'highlight.log')
        & (Join-Path $flowRoot 'QaCommand.ps1') -Operation quit
        Wait-FlowProcess $bridgeId
        foreach($suffix in @('stdout.log','stderr.log')){Copy-Item -LiteralPath (Join-Path $flowRoot "reports\native-qa.$suffix") -Destination (Join-Path $evidence $suffix) -Force}
        Check-FlowLog (Join-Path $evidence 'stderr.log')
        $bChecks=@(Get-ChildItem $evidence -Filter 'b-*.log'|Select-String -Pattern '^PASS ').Count
        $highlightChecks=@(Select-String -LiteralPath (Join-Path $evidence 'highlight.log') -Pattern '^PASS ').Count
        if($highlightChecks-ne22){throw 'Highlight regression did not cover all 22 scenarios'}
        @{status='PASS';aBattle='NATIVE_QA_BATTLE_COMPLETE';bChecks=$bChecks;highlightChecks=$highlightChecks;testedDllSha256=$flowHash;pid=$bridgeId}|ConvertTo-Json|Set-Content (Join-Path $evidence 'summary.json') -Encoding utf8
    }
    Ensure-FlowHash;Write-Output "FLOW REGRESSION $stage PASS"
}
