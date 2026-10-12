$ErrorActionPreference='Stop'
$d2Report=Join-Path $PSScriptRoot 'reports\milestone-d2'
$d2Id=[int](Get-Content (Join-Path $d2Report 'installed-boot-pid.txt'))
$d2Process=Get-Process -Id $d2Id -ErrorAction SilentlyContinue
$d2Code=$null
if($d2Process){if(!$d2Process.WaitForExit(180000)){throw 'Owned installed boot is still running; preserved'};$d2Code=$d2Process.ExitCode}
$d2Log=Join-Path $d2Report 'installed-boot.stdout.log'
if(!(Select-String -LiteralPath $d2Log -Pattern '[RIN_ARCHER] BOOT:' -SimpleMatch -Quiet)-or!(Select-String -LiteralPath $d2Log -Pattern 'main menu loaded (complete)' -SimpleMatch -Quiet)){throw 'Installed graphical boot did not reach main menu'}
if(Select-String -LiteralPath (Join-Path $d2Report 'installed-boot.stderr.log') -Pattern '\[ERROR\]|ERROR: System\.|Parent node is busy|Cannot get path|TimeoutException|Parameter "t" is null' -Quiet){throw 'Installed graphical boot emitted actionable errors'}
if(Select-String -LiteralPath $d2Log -Pattern 'RinArcherCoreTests' -SimpleMatch -Quiet){throw 'Test driver detected in installed game'}
@{status='PASS';version='0.5.0';pid=$d2Id;executable='E:\SteamLibrary\steamapps\common\Slay the Spire 2\SlayTheSpire2.exe';isolatedAPPDATA=(Join-Path $PSScriptRoot 'd2-installed-boot-profile');mode='ACTUAL_INSTALLED_GRAPHICAL_BOOT';mainMenuLoaded=$true;processExited=$true;exitCode=$d2Code;installedDllSha256=(Get-FileHash 'E:\SteamLibrary\steamapps\common\Slay the Spire 2\mods\RinArcherCore\RinArcherCore.dll').Hash;testDriverAbsent=$true;featureCoverage='D2 native graphical gameplay verified separately on identical DLL; human play pending'}|ConvertTo-Json -Depth 5|Set-Content (Join-Path $d2Report 'installed-boot-verification.json') -Encoding utf8
Get-Content (Join-Path $d2Report 'installed-boot-verification.json')
