$ErrorActionPreference='Stop'
$cRoot=$PSScriptRoot;$cReport=Join-Path $cRoot 'reports\milestone-c'
foreach($file in @('core-test-results.json','alpha-test-results.json','highlight-test-results.json','reward-test-results.json','alpha-card-registry.json')){Copy-Item -LiteralPath (Join-Path $cRoot "native-runtime\$file") -Destination $cReport -Force}
Copy-Item -LiteralPath (Join-Path $cRoot 'reports\tests.stdout.log'),(Join-Path $cRoot 'reports\tests.stderr.log') -Destination $cReport -Force
if(!(Test-Path -LiteralPath (Join-Path $cReport 'graphical'))){Copy-Item -LiteralPath (Join-Path $cRoot 'native-runtime\c-qa') -Destination (Join-Path $cReport 'graphical') -Recurse}
$cRecords=@(Get-Content -LiteralPath (Join-Path $cReport 'graphical.stdout.log') | Where-Object {$_-like '[[]RIN_ARCHER[]] {*'} | ForEach-Object {($_ -replace '^\[RIN_ARCHER\] ','') | ConvertFrom-Json})
$cRecords | ForEach-Object {$_ | ConvertTo-Json -Depth 20 -Compress} | Set-Content -LiteralPath (Join-Path $cReport 'native-telemetry.jsonl') -Encoding utf8
$cRecords | Group-Object ev | ForEach-Object {@{event=$_.Name;count=$_.Count}} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $cReport 'telemetry-summary.json') -Encoding utf8
$cRecords | Where-Object ev -In 'REWARD_OFFER','REWARD_PICK','REWARD_SKIP','FREE_JEWEL_BOOST_TRIGGERED','ZERO_MANA_ATTACK_BONUS','ZERO_MANA_BLOCK_BONUS','RIN_END_TURN_MANA','PROJECTED_EXHAUST_ENGINE','ARM_RESOLVED_ADDED','COMBAT_SUMMARY' | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $cReport 'telemetry-samples.json') -Encoding utf8
$cBackup=(Get-Content -LiteralPath (Join-Path $cReport 'backup-path.txt') -Raw).Trim()
$cFiles=@(Get-ChildItem -LiteralPath $cRoot -File | Where-Object Extension -In '.cs','.csproj','.json','.ps1','.md')
foreach($dir in @('Content','Runtime','Compatibility','UI','QA','tests')){$cFiles+=Get-ChildItem -LiteralPath (Join-Path $cRoot $dir) -File | Where-Object Extension -In '.cs','.csproj','.json'}
$cChanged=@(foreach($file in $cFiles){$relative=[IO.Path]::GetRelativePath($cRoot,$file.FullName);$old=Join-Path $cBackup "source\$relative";if(!(Test-Path -LiteralPath $old)-or(Get-FileHash -LiteralPath $old).Hash-ne(Get-FileHash -LiteralPath $file.FullName).Hash){$relative}})
if('PreflightC.ps1'-notin$cChanged){$cChanged+='PreflightC.ps1'}
$cChanged | Sort-Object | Set-Content -LiteralPath (Join-Path $cReport 'files-changed.txt') -Encoding utf8
$cEmpty=Join-Path $cReport 'empty.txt';[IO.File]::WriteAllText($cEmpty,'')
$cCheck=@(foreach($relative in $cChanged){$old=Join-Path $cBackup "source\$relative";if(!(Test-Path -LiteralPath $old)){$old=$cEmpty};$messages=@(& git -c core.autocrlf=false diff --no-index --check -- $old (Join-Path $cRoot $relative) 2>&1 | ForEach-Object {"$_"});if($messages.Count){@{file=$relative;messages=$messages}}})
@{status=if($cCheck.Count){'FAIL'}else{'PASS'};checkedFiles=$cChanged.Count;diagnostics=$cCheck} | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $cReport 'whitespace-check.json') -Encoding utf8
if($cCheck.Count){throw 'Whitespace check has diagnostics'}
Write-Output "Collected $($cRecords.Count) native events; $($cChanged.Count) source/script/document changes"
