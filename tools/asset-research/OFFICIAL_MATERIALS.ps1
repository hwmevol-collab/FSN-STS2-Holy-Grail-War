param([ValidateSet('Inventory','Extract','Pages','OCR','TOC','Index','Tags','Integrate','Gallery','Similarity','Verify','QA','Report','All')][string]$Mode='All')
$ErrorActionPreference='Stop'
$taskPython='E:\FSN_MASTER_ASSET_WORK\tools\python\Scripts\python.exe'
$taskScripts='E:\FSN_MASTER_ASSET_WORK\scripts'
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONPYCACHEPREFIX='E:\FSN_MASTER_ASSET_WORK\tmp\official-material\pycache'
function Run-Stage([string]$Script,[string[]]$Arguments=@()) {
    & $taskPython (Join-Path $taskScripts $Script) @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Official Material stage failed: $Script $Arguments" }
}
switch ($Mode) {
    'Inventory' { Run-Stage 'official_materials.py' @('Inventory') }
    'Extract' { Run-Stage 'official_materials.py' @('Extract') }
    'Pages' { Run-Stage 'official_materials.py' @('Pages') }
    'OCR' { Run-Stage 'official_materials_tools.py'; Run-Stage 'official_materials.py' @('OCR'); Run-Stage 'official_materials_vertical.py' }
    'TOC' { Run-Stage 'official_materials_toc_probe.py'; Run-Stage 'official_materials_semantics.py' }
    'Tags' { Run-Stage 'official_materials_semantics.py' }
    'Index' { Run-Stage 'official_materials_index.py' @('Index') }
    'Similarity' { Run-Stage 'official_materials_index.py' @('Similarity') }
    'Integrate' { Run-Stage 'official_materials_index.py' @('Integrate') }
    'Gallery' { Run-Stage 'official_materials_gallery.py' }
    'Verify' { Run-Stage 'official_materials_verify.py' }
    'QA' { Run-Stage 'official_materials_extra_review.py'; Run-Stage 'official_materials_finish.py' @('QA') }
    'Report' { Run-Stage 'official_materials_finish.py' @('Report'); Run-Stage 'official_materials_report_zh.py' }
    'All' {
        Run-Stage 'official_materials.py' @('Inventory'); Run-Stage 'official_materials.py' @('Extract'); Run-Stage 'official_materials.py' @('Pages')
        Run-Stage 'official_materials_tools.py'; Run-Stage 'official_materials.py' @('OCR'); Run-Stage 'official_materials_vertical.py'
        Run-Stage 'official_materials_toc_probe.py'; Run-Stage 'official_materials_semantics.py'; Run-Stage 'official_materials_index.py' @('Index')
        Run-Stage 'official_materials_extra_review.py'; Run-Stage 'official_materials_finish.py' @('QA'); Run-Stage 'official_materials_index.py' @('Similarity'); Run-Stage 'official_materials_gallery.py'; Run-Stage 'official_materials_index.py' @('Integrate'); Run-Stage 'official_materials_verify.py'; Run-Stage 'official_materials_finish.py' @('Report'); Run-Stage 'official_materials_report_zh.py'
    }
}
