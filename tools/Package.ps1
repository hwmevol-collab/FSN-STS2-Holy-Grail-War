param([Parameter(Mandatory=$true)][string]$ResourcesZip)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem
$taskRoot=Split-Path $PSScriptRoot
$taskRevision='0.9.4-game-compat.1-visual-loader-fix-01-dual'
$taskOutput=Join-Path $taskRoot ('artifacts/package-'+[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds())
New-Item -ItemType Directory -Path $taskOutput | Out-Null
[System.IO.Compression.ZipFile]::ExtractToDirectory((Resolve-Path -LiteralPath $ResourcesZip).Path,$taskOutput)
$taskMod=Join-Path $taskOutput 'mods/RinArcherCore'
if(!(Test-Path -LiteralPath (Join-Path $taskMod 'FSNArtReboot.pck'))){throw 'Final shared MOD resources missing'}
$taskManifest=Get-Content -Raw -LiteralPath (Join-Path $taskRoot 'verified-games.json') | ConvertFrom-Json
foreach($taskVariant in $taskManifest.Variants){
 $taskVersion=$taskVariant.Game.GameVersion.TrimStart('v')
 $taskPayload=Join-Path $taskRoot ('artifacts/'+$taskVersion+'/RinArcherCore.dll')
 Copy-Item -LiteralPath $taskPayload -Destination (Join-Path $taskMod ($taskVariant.Directory+'/RinArcherCore.dll'))
 $taskVariant.PayloadSha256=(Get-FileHash -LiteralPath $taskPayload).Hash
}
Copy-Item -LiteralPath (Join-Path $taskRoot 'artifacts/loader/RinArcherCore.Loader.dll') -Destination (Join-Path $taskMod 'RinArcherCore.dll')
$taskJson=$taskManifest | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText((Join-Path $taskMod 'mod-variants.manifest'),$taskJson,[System.Text.UTF8Encoding]::new($false))
# A resource-seed candidate record refers to the old bytes; replace it with actual rebuild identities.
$taskRecord=@{ revision=$taskRevision; status='REBUILT_NOT_RUNTIME_ACCEPTED'; loaderSha256=(Get-FileHash -LiteralPath (Join-Path $taskMod 'RinArcherCore.dll')).Hash; variants=$taskManifest.Variants }
[System.IO.File]::WriteAllText((Join-Path $taskOutput 'CANDIDATE.json'),($taskRecord|ConvertTo-Json -Depth 10),[System.Text.UTF8Encoding]::new($false))
$taskZip=$taskOutput+'.zip'
[System.IO.Compression.ZipFile]::CreateFromDirectory($taskOutput,$taskZip)
Get-FileHash -LiteralPath $taskZip
Write-Output 'Independent rebuilt package; test before publishing. No Workshop update or game/save installation performed.'
