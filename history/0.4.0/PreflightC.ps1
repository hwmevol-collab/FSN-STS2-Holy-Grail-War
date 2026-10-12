$ErrorActionPreference='Stop'
$cRoot=$PSScriptRoot
$cReport=Join-Path $cRoot 'reports\milestone-c'
New-Item -ItemType Directory -Path $cReport -Force | Out-Null
$cCloseout=Get-Content -LiteralPath (Join-Path $cRoot 'reports\MILESTONE_B_HUMAN_QA_CLOSEOUT.json') -Raw | ConvertFrom-Json
if($cCloseout.closeoutStatus-ne'PASS'-or$cCloseout.HUMAN_SELF_TARGET_HIGHLIGHT_CONFIRMATION_PENDING-ne0-or$cCloseout.DESIGN_DEVIATIONS-ne0-or$cCloseout.IMPLEMENTATION_BLOCKERS-ne0){throw 'Milestone B hard precondition failed'}
foreach($entry in @(@('core-test-results.json',85),@('alpha-test-results.json',58),@('highlight-test-results.json',10))){
    $cResult=Get-Content -LiteralPath (Join-Path $cRoot "native-runtime\$($entry[0])") -Raw | ConvertFrom-Json
    if($cResult.status-ne'PASS'-or$cResult.passed-ne$entry[1]-or$cResult.total-ne$entry[1]){throw 'Live regression failed'}
    Copy-Item -LiteralPath (Join-Path $cRoot "native-runtime\$($entry[0])") -Destination $cReport
}
$cTarget='E:\SteamLibrary\steamapps\common\Slay the Spire 2\mods\RinArcherCore'
if((Get-FileHash -LiteralPath (Join-Path $cTarget 'RinArcherCore.dll')).Hash-ne$cCloseout.verification.installedDllSha256){throw 'Installed B payload changed'}
$cBackup=Join-Path $cRoot ('backups\'+(Get-Date).ToString('yyyyMMdd-HHmmss')+'-milestone-c')
New-Item -ItemType Directory -Path (Join-Path $cBackup 'source'),(Join-Path $cBackup 'installed-mod') -Force | Out-Null
foreach($dir in @('Content','Runtime','Compatibility','UI','QA','tests')){
    New-Item -ItemType Directory -Path (Join-Path $cBackup "source\$dir") -Force | Out-Null
    Get-ChildItem -LiteralPath (Join-Path $cRoot $dir) -File | Copy-Item -Destination (Join-Path $cBackup "source\$dir")
}
Get-ChildItem -LiteralPath $cRoot -File | Copy-Item -Destination (Join-Path $cBackup 'source')
Get-ChildItem -LiteralPath $cTarget -File | Copy-Item -Destination (Join-Path $cBackup 'installed-mod')
$cSource=@(Get-ChildItem -LiteralPath (Join-Path $cBackup 'source') -File -Recurse | ForEach-Object {@{path=$_.FullName.Substring((Join-Path $cBackup 'source').Length+1);sha256=(Get-FileHash -LiteralPath $_.FullName).Hash}})
$cSource | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $cBackup 'source-before.json') -Encoding utf8
$cOldBackup=(Get-Content -LiteralPath (Join-Path $cRoot 'reports\self-target-highlight\backup-path.txt') -Raw).Trim()
$cProtected=@(Get-Content -LiteralPath (Join-Path $cOldBackup 'protected-before.json') -Raw | ConvertFrom-Json | ForEach-Object {
    if(Test-Path -LiteralPath $_.path){@{path=$_.path;sha256=(Get-FileHash -LiteralPath $_.path).Hash}}
})
$cProtected | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $cBackup 'protected-before.json') -Encoding utf8
$cBackup | Set-Content -LiteralPath (Join-Path $cReport 'backup-path.txt')
@{status='PASS';milestoneA=85;milestoneB=58;highlight=10;BHumanCloseout='PASS';installedVersion='0.2.1';sourceMatchesInstalled=$true;protectedFiles=$cProtected.Count;backup=$cBackup;DESIGN_DEVIATIONS=0;IMPLEMENTATION_BLOCKERS=0} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $cReport 'precondition.json') -Encoding utf8
Copy-Item -LiteralPath 'C:\Users\Murasame\.codex\attachments\779652ad-08ee-4872-bcdc-556a6edf1d95\已粘贴的文本.txt' -Destination (Join-Path $cReport 'MILESTONE_C_IMPLEMENTATION_CONTRACT.txt')
Get-Content -LiteralPath (Join-Path $cReport 'precondition.json') -Raw
