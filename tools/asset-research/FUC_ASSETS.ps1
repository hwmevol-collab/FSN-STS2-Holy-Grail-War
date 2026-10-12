[CmdletBinding()]
param([ValidateSet('Inventory','ExtractISO','ExtractContainers','ConvertTextures','ParseModels','ParseAnimations','ExtractAudio','ExtractVideo','ParseGameData','Index','Integrate','Gallery','LegacyPreviews','Compare','FullPRSVerify','Verify','Report','All')][string]$Phase='Verify')
$ErrorActionPreference='Stop'
$env:PYTHONIOENCODING='utf-8'
$env:FUC_STAGE_ROOT='E:\FSN_MASTER_ASSET_WORK\fuc\Europe'
$env:FUC_SOURCE_VERSION='FateUnlimitedCodesPortable_Europe'
$fucPython='E:\FSN_MASTER_ASSET_WORK\tools\python\Scripts\python.exe'
$fucScripts='E:\FSN_MASTER_ASSET_WORK\scripts'
$fucMetadata='E:\FSN_MASTER_ASSET_LIBRARY\FateUnlimitedCodesPortable_Europe\Metadata'
function Invoke-FucScript([string]$Name){& $fucPython (Join-Path $fucScripts $Name);if($LASTEXITCODE -ne 0){throw "FUC phase failed: $Name"}}
if(-not(Test-Path -LiteralPath 'E:\FSN_MASTER_ASSET_WORK\backups\fuc-pre-integration\BASELINE.json')){throw 'Frozen pre-integration baseline is required. Never replace it with a new baseline after integration.'}
$fucPhases=if($Phase -eq 'All'){
    if(Test-Path -LiteralPath (Join-Path $fucMetadata 'INTEGRATION_COMMIT.json')){@('Verify','Compare','Report')}else{@('Inventory','ExtractContainers','ParseModels','ConvertTextures','ParseAnimations','ExtractAudio','ExtractVideo','ParseGameData','FullPRSVerify','Index','Integrate','Gallery','LegacyPreviews','Verify','Compare','Report')}
}else{@($Phase)}
foreach($fucPhase in $fucPhases){
    switch($fucPhase){
        {$_ -in 'Inventory','ExtractISO'}{Invoke-FucScript 'fuc_europe_inventory.py';Invoke-FucScript 'fuc_europe_prepare.py'}
        'ExtractContainers'{Invoke-FucScript 'fuc_fpk_probe.py';Invoke-FucScript 'fuc_fpk_extract.py'}
        'ParseModels'{Invoke-FucScript 'fuc_models_stage.py'}
        'ConvertTextures'{Invoke-FucScript 'fuc_textures_stage.py'}
        'ParseAnimations'{Invoke-FucScript 'fuc_motion_channels.py';Invoke-FucScript 'fuc_source_bones.py'}
        'ExtractAudio'{Invoke-FucScript 'fuc_audio_stage.py';Invoke-FucScript 'fuc_soundbanks_stage.py'}
        'ExtractVideo'{Invoke-FucScript 'fuc_video_stage.py'}
        'ParseGameData'{if(-not(Test-Path -LiteralPath 'E:\FSN_MASTER_ASSET_WORK\fuc\Europe\Executable\EBOOT_DECRYPTED.bin')){& (Join-Path $fucScripts 'fuc_europe_decrypt.ps1')};Invoke-FucScript 'fuc_europe_data.py'}
        'FullPRSVerify'{Invoke-FucScript 'fuc_full_fpk_verify.py'}
        'Index'{Invoke-FucScript 'fuc_europe_index.py'}
        'Integrate'{Invoke-FucScript 'fuc_europe_integrate.py'}
        'Gallery'{Invoke-FucScript 'fuc_europe_gallery.py'}
        'LegacyPreviews'{Invoke-FucScript 'fuc_legacy_video_previews.py'}
        'Compare'{Invoke-FucScript 'fuc_europe_supplement.py'}
        'Verify'{Invoke-FucScript 'fuc_europe_verify.py'}
        'Report'{Invoke-FucScript 'fuc_europe_report.py'}
    }
}
Write-Output 'Europe phase completed. Existing integration is never appended again. Japan recovery is separate and receives no master asset IDs. Browser checks are recorded independently; unresolved motion binding/VFX/game tables keep the final status PARTIAL.'
