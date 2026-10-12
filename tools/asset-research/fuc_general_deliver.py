"""Package only additive evidence/index/report outputs; preserve all older deliverables."""
from fuc_general_common import *
import zipfile,shutil
OUT=pathlib.Path(r'C:\Users\Murasame\Documents\Codex\2026-10-06\files-pasted-by-the-user-fate-2\outputs')

def main():
    s=readjson(BMD/'FUC_BATTLE_GENERALIZATION_SUMMARY.json');assert s['status']=='FUC_BATTLE_RUNTIME_GENERALIZATION_PASS' and all(s['pass_gates'].values())
    OUT.mkdir(parents=True,exist_ok=True)
    report=L/'Reports/FUC_BATTLE_RUNTIME_GENERALIZATION_REPORT.md';shutil.copy2(report,OUT/report.name)
    shutil.copy2(BMD/'FUC_BATTLE_GENERALIZATION_SUMMARY.json',OUT/'FUC_BATTLE_GENERALIZATION_SUMMARY.json')
    shutil.copy2(BMD/'FUC_BATTLE_PREVIEW_READINESS.json',OUT/'FUC_BATTLE_PREVIEW_READINESS.json')
    archive=OUT/'FUC_BATTLE_GENERALIZATION_INDEXES.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(BMD.glob('*')):
            if p.is_file():z.write(p,p.name)
    doc='''# FUC 战斗运行时第二轮交付

系统验收结果：FUC_BATTLE_RUNTIME_GENERALIZATION_PASS。
完整同步 Body+Weapon+Effect+Audio 预览：未完成。没有新增 asset_id 或 animation GLB。

双击 Open-FUC-Battle-Generalization.cmd 打开证据页。它使用原 E: 素材库，优先复用已有本地素材浏览服务；必要时建立只读本地浏览服务。声音和原有身体+枪预览独立显示，不会被手工拼成同步演出。

新增索引在 INDEXES.zip。运行时快照、失败探针、最终回归、清理记录与新工具在 REPRODUCIBILITY.zip。详细结论及 A–S 报告在同目录 Markdown。

本轮新增证据：Shiro/Rin 22 个 FAN/BPO 数值样本，Lancer 2 个完整出生矩阵和22次快照更新，sound ID0x232D 到 FSN260985 的一条真实上游因果链。三模型九条 Golden动画、枪的附着和268504条主库均通过回归。

完整预览缺口见 FUC_BATTLE_PREVIEW_READINESS.json。Shiro/Rin有效装备、第二角色ownereffect、AMO插值、完整clip145姿态与特效/音频重放尚未验证。不依据画面猜招式或资源归属。
'''
    (OUT/'FUC_BATTLE_GENERALIZATION_README.md').write_text(doc,encoding='utf-8')
    reproduction='''# Reproduction and scope

Use the preserved E:/FSN_MASTER_ASSET_WORK and E:/FSN_MASTER_ASSET_LIBRARY. Source Europe ISO and Raw remain read-only. The original fuc_motion_evaluator.py and all fuc_battle_* files are byte-frozen. New programs use fuc_general_* and write only BattleGeneralization paths.

Offline audits, in dependency order:
1. fuc_general_effect_pose.py: F32 source world@local-offset full matrix and point comparison.
2. fuc_general_evidence_audit.py: returned sound request object, bank/program, resolved payload, voice/SAS argument and return checks; Rin texture cache; executable section scope.
3. fuc_general_golden_gate.py: 45 frozen game poses/2535nodes, exact evaluator regression.
4. fuc_general_stability.py: inherited527 critical file hashes,341model hashes/size/mtime,624836path references,readonly SQLite integrity/IDs. NEW_GOLDEN_FREEZE_CHECK.json additionally checks the72 current baseline entries.
5. Fresh standard Three.js validation and Play controls for all9 clips, and6 Golden equipment matrices. Evidence receiver must target a NEW empty folder; never overwrite original acceptance artifacts. GoldenFinalPlayback is this final run.
6. fuc_general_indices.py, fuc_general_report.py, fuc_general_deliver.py: publish additive indexes/report/delivery only after the above evidence.

To re-acquire runtime, use isolated PPSSPP/config/memstick. Confirm the Europe ELF hash in EXECUTABLE_ADDRESS_SCOPE.json first. Rediscover character pointers through natural08832A68 loads. Historical heap addresses in the archive MUST NOT be reused in a new match. Bank entries are loaded MOT data bases; equipment records use strideC8. Apply a single precision write watch at a time, or bounded execution breakpoint. Sound-chain script follows the actual returned queue and asserts bank/program/payload identities; it does not invoke sound functions artificially.

An independent natural episode cannot be synchronized to another by matching host timestamps. Sound request /SAS keyon and effect activation keep their separate episode and clock-domain records. FullBattlePreview is false; readiness JSON is not a completed preview manifest. Re-running diagnostic helpers does not grant clip145 export eligibility.

Cleanup every diagnostic CPU/memory breakpoint and release inputs, then close only the owned PPSSPP PID. No hooks, RAMpatches, scratch writes, patched EBOOT or ISO writes were used in this run. The process was closed; it is not a live continuation target.

DISCARDED_INTERPRETATIONS.json explains early failed helper assumptions and failed sound probes. Their bytes remain included for audit, but accepted indexes use FullVerified and LanSoundCausality5 only. Failed captures must never silently be promoted.
'''
    (OUT/'FUC_BATTLE_GENERALIZATION_REPRODUCTION.md').write_text(reproduction,encoding='utf-8')
    ps='''param([switch]$NoLaunch)
$ErrorActionPreference = 'Stop'
$libraryRoot = 'E:\\FSN_MASTER_ASSET_LIBRARY'
$pythonPath = 'E:\\FSN_MASTER_ASSET_WORK\\tools\\python\\Scripts\\python.exe'
if (!(Test-Path -LiteralPath "$libraryRoot\\Gallery\\FUC_BATTLE_RUNTIME_V2.html")) { throw 'FUC evidence page was not found in the library.' }
$port = 8986
try { $null = Invoke-WebRequest "http://127.0.0.1:$port/Gallery/FUC_BATTLE_RUNTIME_V2.html" -UseBasicParsing -TimeoutSec 3 }
catch {
  $port = 8990
  try { $null = Invoke-WebRequest "http://127.0.0.1:$port/Gallery/FUC_BATTLE_RUNTIME_V2.html" -UseBasicParsing -TimeoutSec 3 }
  catch {
    Start-Process -FilePath $pythonPath -ArgumentList @('-m','http.server',"$port",'--bind','127.0.0.1','--directory',$libraryRoot) -WindowStyle Hidden
    Start-Sleep -Milliseconds 700
    $null = Invoke-WebRequest "http://127.0.0.1:$port/Gallery/FUC_BATTLE_RUNTIME_V2.html" -UseBasicParsing -TimeoutSec 5
  }
}
$url = "http://127.0.0.1:$port/Gallery/FUC_BATTLE_RUNTIME_V2.html"
if (!$NoLaunch) { Start-Process $url }
Write-Output $url
'''
    (OUT/'Open-FUC-Battle-Generalization.ps1').write_text(ps,encoding='utf-8-sig')
    (OUT/'Open-FUC-Battle-Generalization.cmd').write_text('@echo off\r\npowershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Open-FUC-Battle-Generalization.ps1"\r\nif errorlevel 1 pause\r\n',encoding='ascii')
    arc=OUT/'FUC_BATTLE_GENERALIZATION_REPRODUCIBILITY.zip'
    with zipfile.ZipFile(arc,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(BR.rglob('*')):
            if p.is_file():z.write(p,'BattleGeneralization/'+p.relative_to(BR).as_posix())
        for p in sorted((W/'scripts').glob('fuc_general_*')):
            if p.is_file():z.write(p,'scripts/'+p.name)
        z.write(W/'backups/fuc-battle-generalization-pre/BASELINE.json','baseline/FUC_BATTLE_GENERALIZATION_PRE_BASELINE.json')
        z.write(OUT/'FUC_BATTLE_GENERALIZATION_REPRODUCTION.md','REPRODUCTION.md')
        z.write(report,report.name)
    for path in [archive,arc]:
        with zipfile.ZipFile(path) as z:assert z.testzip() is None
    names=[report.name,'FUC_BATTLE_GENERALIZATION_SUMMARY.json','FUC_BATTLE_PREVIEW_READINESS.json','FUC_BATTLE_GENERALIZATION_INDEXES.zip','FUC_BATTLE_GENERALIZATION_REPRODUCIBILITY.zip','FUC_BATTLE_GENERALIZATION_README.md','FUC_BATTLE_GENERALIZATION_REPRODUCTION.md','Open-FUC-Battle-Generalization.ps1','Open-FUC-Battle-Generalization.cmd']
    if (OUT/'FUC_BATTLE_GENERALIZATION_OVERVIEW.png').exists():names.append('FUC_BATTLE_GENERALIZATION_OVERVIEW.png')
    manifest=dict(status=s['status'],complete_battle_preview=False,files=[dict(name=n,path=str(OUT/n),bytes=(OUT/n).stat().st_size,sha256=sha(OUT/n)) for n in names],catalog_modified=False,new_asset_ids=0)
    jsonwrite(OUT/'FUC_BATTLE_GENERALIZATION_DELIVERABLES.json',manifest);print([(r['name'],r['bytes']) for r in manifest['files']])
if __name__=='__main__':main()
