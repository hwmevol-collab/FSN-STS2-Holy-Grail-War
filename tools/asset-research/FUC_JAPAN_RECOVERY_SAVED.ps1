param(
    [ValidateSet('Inventory','ExtractISO','Diagnose','ExtractContainers','ConvertTextures','ParseModels','ParseAnimations','ExtractAudio','Compare','Verify','Report','RecoverAvailable','All')]
    [string]$Phase='Inventory'
)
$ErrorActionPreference='Stop'
$env:PYTHONIOENCODING='utf-8'
$fucPython='E:\FSN_MASTER_ASSET_WORK\tools\python\Scripts\python.exe'
$fucScripts='E:\FSN_MASTER_ASSET_WORK\scripts'
function Invoke-FucScript([string]$Name) {
    & $fucPython (Join-Path $fucScripts $Name)
    if ($LASTEXITCODE -ne 0) { throw "FUC phase failed: $Name" }
}
if ($Phase -in @('Inventory','All','RecoverAvailable')) { Invoke-FucScript 'fuc_prepare.py' }
if ($Phase -in @('All','ExtractISO')) {
    $fucBaseline=Get-Content -LiteralPath 'E:\FSN_MASTER_ASSET_WORK\fuc\SOURCE_ZIP_BASELINE.json' -Raw | ConvertFrom-Json
    if (-not $fucBaseline.complete_zip) { throw 'Source ZIP is truncated. Full extraction/integration is blocked. Supply a complete source before rebaselining. WORK-only recovery is available with -Phase RecoverAvailable.' }
    Invoke-FucScript 'fuc_iso.py'
    if ($Phase -eq 'All') { throw 'The complete-source integration pipeline still requires a reviewed continuation. This diagnostic script does not fabricate an integration PASS.' }
}
if ($Phase -in @('Diagnose','RecoverAvailable')) { Invoke-FucScript 'fuc_salvage.py' }
if ($Phase -in @('ExtractContainers','RecoverAvailable')) {
    Invoke-FucScript 'fuc_fpk_probe.py'
    Invoke-FucScript 'fuc_fpk_extract.py'
}
if ($Phase -in @('ParseModels','RecoverAvailable')) { Invoke-FucScript 'fuc_models_stage.py' }
if ($Phase -in @('ConvertTextures','RecoverAvailable')) { Invoke-FucScript 'fuc_textures_stage.py' }
if ($Phase -in @('ParseAnimations','RecoverAvailable')) { Invoke-FucScript 'fuc_motion_data_stage.py' }
if ($Phase -in @('ExtractAudio','RecoverAvailable')) { Invoke-FucScript 'fuc_audio_stage.py' }
if ($Phase -in @('Compare','RecoverAvailable')) { Invoke-FucScript 'fuc_compare_stage.py' }
if ($Phase -in @('Verify','RecoverAvailable')) { Invoke-FucScript 'fuc_verify_preserved.py' }
if ($Phase -in @('Report','RecoverAvailable')) { Invoke-FucScript 'fuc_blocked_report.py' }
Write-Output 'FUC work stage finished. No master IDs are allocated from this incomplete source.'
