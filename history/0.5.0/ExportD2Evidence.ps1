$ErrorActionPreference='Stop'
$d2Root=Join-Path $PSScriptRoot 'reports\milestone-d2'
$d2Lines=[Collections.Generic.List[string]]::new()
$d2EventCounts=@{}
$d2Kinds=@('CAMPFIRE_ENTERED','REST_PREVIEW','REST_COMMITTED','SMITH_SELECTOR_OPENED','SMITH_OPENED','SMITH_COMMITTED','MERCHANT_GENERATED','MERCHANT_CARD_PURCHASED','CARD_REMOVE_OPENED','CARD_REMOVED','QA_GOLD_INJECTION','GRAPHICAL_QA_HP_FIXTURE')
foreach($d2Resolution in @('1920x1080','2560x1440')){
    foreach($d2Phase in 1..6){
        $d2Log=Join-Path $d2Root "graphical-$d2Resolution\phase-$d2Phase\stdout.log"
        foreach($d2Match in Select-String -LiteralPath $d2Log -SimpleMatch '[RIN_ARCHER_RUN] {'){
            $d2Json=$d2Match.Line.Substring($d2Match.Line.IndexOf('{'))
            $d2Event=$d2Json|ConvertFrom-Json
            if($d2Event.ev-notin$d2Kinds){continue}
            $d2Lines.Add((@{resolution=$d2Resolution;phase=$d2Phase;evidenceLine=$d2Match.LineNumber;event=$d2Event}|ConvertTo-Json -Depth 12 -Compress))
            $d2EventCounts[$d2Event.ev]=1+$d2EventCounts[$d2Event.ev]
        }
    }
}
[IO.File]::WriteAllLines((Join-Path $d2Root 'd2-telemetry-evidence.jsonl'),$d2Lines,[Text.UTF8Encoding]::new($false))
$d2Route=@{}
foreach($d2Resolution in @('1920x1080','2560x1440')){$d2Save=Get-Content (Join-Path $d2Root "graphical-$d2Resolution\phase-5\second-merchant-reload.json") -Raw|ConvertFrom-Json;$d2Route[$d2Resolution]=@{seed=$d2Save.RunSeed;gold=$d2Save.Gold;rinHp=$d2Save.Master.CurrentHp;archerHp=$d2Save.ArcherHp;metrics=$d2Save.Economy;campfires=$d2Save.Campfires;shops=$d2Save.Shops}}
@{eventCounts=$d2EventCounts;records=$d2Lines.Count;continuousRoute=$d2Route;balance='RUN_ECONOMY_BALANCE_OBSERVATION_ONLY';publicBalance='NOT_PUBLIC_BALANCE';extraGold=500}|ConvertTo-Json -Depth 12|Set-Content (Join-Path $d2Root 'economy-observations.json') -Encoding utf8
$d2Backup=(Get-Content (Join-Path $d2Root 'backup-path.txt') -Raw).Trim()
$d2Source=Get-Content (Join-Path $d2Backup 'source-before.json') -Raw|ConvertFrom-Json
$d2Modified=@(foreach($d2File in $d2Source|Where-Object {$_.path-notmatch'\\(bin|obj)\\'}){$d2Path=Join-Path $PSScriptRoot $d2File.path;if((Test-Path -LiteralPath $d2Path)-and(Get-FileHash -LiteralPath $d2Path).Hash-ne$d2File.sha256){@{path=$d2File.path;before=$d2File.sha256;after=(Get-FileHash -LiteralPath $d2Path).Hash}}})
$d2Files=@(Get-ChildItem -LiteralPath $PSScriptRoot -File|Where-Object Extension -In '.cs','.csproj','.json','.md','.ps1','.cmd')
foreach($d2Dir in @('Content','Runtime','Compatibility','UI','QA','tests')){$d2Files+=Get-ChildItem (Join-Path $PSScriptRoot $d2Dir) -File -Recurse|Where-Object {$_.FullName-notmatch'\\(bin|obj)\\'-and$_.Extension-in'.cs','.json','.csproj'}}
$d2New=@(foreach($d2File in $d2Files){$d2Relative=[IO.Path]::GetRelativePath($PSScriptRoot,$d2File.FullName);if($d2Relative-notin$d2Source.path){@{path=$d2Relative;sha256=(Get-FileHash $d2File.FullName).Hash}}})
@{modified=$d2Modified;added=$d2New;originalTests='UNCHANGED_EXCEPT_TESTENTRY_DISPATCH';noGitRepository=$true}|ConvertTo-Json -Depth 5|Set-Content (Join-Path $d2Root 'source-changes.json') -Encoding utf8
Write-Output "D2 evidence export: $($d2Lines.Count) telemetry records, $($d2Modified.Count) modified and $($d2New.Count) added source/delivery files"
