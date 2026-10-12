"""Package additive battle evidence and tools without copying source archives or RawExtracted."""
from fuc_battle_common import *
OUT=pathlib.Path(r'C:/Users/Murasame/Documents/Codex/2026-10-06/files-pasted-by-the-user-fate-2/outputs')
def main():
 overview=L/'Gallery/FUC_BATTLE_RUNTIME.html';shutil.copy2(overview,W/'scripts/fuc_battle_gallery_overview.html')
 readme='''# FUC Battle Runtime 已验证样本与复现

本轮结果为 FUC_BATTLE_RUNTIME_MAPPING_PASS，范围是用户规定的最小 A-F闭环，完整效果和声音战斗预览尚未恢复。

## 打开结果

双击 outputs 中的“打开战斗验证预览.cmd”，或在现有 Gallery 服务打开 /Gallery/FUC_BATTLE_RUNTIME.html。预览只包含已有 Lancer 三条身体动画和已确认枪附着，不包含猜测的效果或声音。新入口没有更改原 Gallery 主页面。

报告同时保存到 E:/FSN_MASTER_ASSET_LIBRARY/Reports/FUC_BATTLE_RUNTIME_MAPPING_REPORT.md。13个CSV及总结位于 FateUnlimitedCodesPortable_Europe/Metadata/BattleRuntimeMapping。runtime captures 位于 E:/FSN_MASTER_ASSET_WORK/fuc/BattleRuntimeMapping。

## 已确认结果

- FAN 原 loader、角色对象、实际消费者及非零 BPO 输出。
- Lancer body bone153→GMO32→GLB42→weapon bone0/GMO1/GLB2；自然矩阵复制2次误差0。
- 1002.gmo经1000.seq原VM激活、world矩阵消费、9次callback到结束以及池复用cleanup。
- MOTbank0 clip145 (FSN258272) 的一条实际效果激活发生在body t=.05／frame3；不是MOT内事件表的声明。
- 三次自然SAS key-on的完整ADPCM数据匹配已有声音库；上游soundID/动作因果和共享payload bank歧义没有消除。
- 原Golden3模型9clip新回归：45pose/2535节点误差0；Three.js286帧/16357节点最大误差1.0312226656431639e-6。
- 268504旧ID、Catalog逐值、341静态GLB和冻结路径保持；新assetID0。

## 离线复核

使用工作区既有Python：

```powershell
& 'E:\\FSN_MASTER_ASSET_WORK\\tools\\python\\Scripts\\python.exe' 'E:\\FSN_MASTER_ASSET_WORK\\scripts\\fuc_battle_indices.py'
& 'E:\\FSN_MASTER_ASSET_WORK\\tools\\python\\Scripts\\python.exe' 'E:\\FSN_MASTER_ASSET_WORK\\scripts\\fuc_battle_golden_gate.py'
& 'E:\\FSN_MASTER_ASSET_WORK\\tools\\python\\Scripts\\python.exe' 'E:\\FSN_MASTER_ASSET_WORK\\scripts\\fuc_battle_stability.py'
```

indices仅重建新增BattleRuntimeMapping关系表，不修改旧Catalog；golden_gate把新计算写入本轮GoldenRegression，对照旧冻结runtime采样。需要现有主库、旧fuc_motion_evaluator等依赖，包内未重复复制整库。

Three.js的逐帧验收是查看器“逐帧数值验收”按钮；证据server fuc_battle_evidence_server.py --folder <新目录> 仅绑定127.0.0.1:8998，服务根为主库、收到JSON/WebM只写BattleRuntimeMapping所选目录，不覆盖现有证据。一般播放不需要证据server。

## 原游戏动态重采样

继续用工作区 isolated PPSSPP和独立battle_debug.ini，绝不访问原用户配置、存档或改ISO。前一次会话已关闭，不能直接对旧heap指针运行新probe。

固定Europe ELF代码地址可复用，heap对象需要每次发现：

1. loader_trace在088869D8捕获FAN1000/AMO4000原路径、返回resource和payload。
2. function_probe在088326F4 --character 捕获原FAN消费者；a0是当次character，从+3C发现body，+40发现MOTplayer。
3. character+5DC发现当前attachment记录；08837964和089449AC捕获原记录/parent矩阵复制。模型地址由实际参数得出。
4. 自然进入Lancer/已验证sir/rin的Practice上下文；在4354捕获实际效果激活 --effect，使用该ctx的新地址在088D3A80连续采样 --until-end。不要把已加载模型存在当成spawn。
5. 从实际modeldescriptor捕获modelwrapper，再在08877378条件a0==当次wrapper，用model_apply_probe保存input和SDKoutput。不要硬编码本报告的09530C10跨会话使用。
6. audio_trace在0894A1AC捕获原key-on及voice-record+20/+24 payload。游戏代码与全局voice表地址来自此Europe ELF；character地址在当前helper里是本会话09C09700，重采样前应按当次FAN/character参数更新。
7. effect clock与body clock分别记录。释放按键后让游戏自然推进至少一帧，再按下，避免paused时false/true未被游戏观测到而错过新press。
8. 所有probe只暂停/读取并跟随原调用返回，不主动调用游戏函数、不注入RAM、不patchEBOOT。最终cleanup再关闭独立实例。

fuc_battle_effect_watch.py保留了大量memory-write watch的失败调查，仅作失败证据；不要再次大量并发watch。最终方法使用少量function conditional breakpoints。

## 包内容与限制

FUC_BATTLE_RUNTIME_INDEXES.zip：13个关系/格式/矩阵/更新索引及机器摘要。
FUC_BATTLE_RUNTIME_REPRODUCIBILITY.zip：新工具、精选原runtime entry/return及矩阵数据、局部ELF反汇编、Golden新回归和路径完整性证据。

没有重新提取ISO/FPK、复制RawExtracted、重新生成341静态GLB、增加ID、批量导出3676clip或命名招式。Chrome not validated。AMO实际消费、特效bone来源的锁定/偏移公式、soundID上游、完整声音同步预览依旧unknown。
'''
 (OUT/'FUC_BATTLE_RUNTIME_README.md').write_text(readme,encoding='utf-8');(W/'scripts/fuc_battle_reproduction.md').write_text(readme,encoding='utf-8')
 with zipfile.ZipFile(OUT/'FUC_BATTLE_RUNTIME_INDEXES.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in sorted(BMD.iterdir()):
   if p.is_file():z.write(p,p.name)
 evidence_folders=['FANConsumerDirect','FANFrameNatural','LoaderTrace','WeaponAttachmentNatural','WeaponParentMatrixCopy','EffectTimelineHeld','EffectHeldUpdates','EffectNearUpdates','EffectNearCleanup','EffectMatrixApplyReleased','AudioKeyOnPayload','Static','GoldenRegression','PlaybackFinal','PlaybackAcceptance']
 manifest=[]
 with zipfile.ZipFile(OUT/'FUC_BATTLE_RUNTIME_REPRODUCIBILITY.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p in sorted((W/'scripts').glob('fuc_battle_*')):
   if p.is_file():z.write(p,'scripts/'+p.name);manifest.append(dict(source=str(p),archive='scripts/'+p.name,sha256=sha(p),size=p.stat().st_size))
  for folder in evidence_folders:
   for p in sorted((BR/folder).rglob('*')):
    if p.is_file():a='evidence/'+str(p.relative_to(BR)).replace('\\','/');z.write(p,a);manifest.append(dict(source=str(p),archive=a,sha256=sha(p),size=p.stat().st_size))
  for p in [BR/'FAN_RUNTIME_PROOF.json',BR/'EQUIPMENT_RUNTIME_PROOF.json',BR/'EFFECT_SEQ_SOURCE_PROOF.json',BR/'BATTLE_EVIDENCE_SUMMARY.json',BR/'STABILITY_FINAL.json',BR/'DEBUGGER_CLEANUP.json',BR/'GALLERY_BROWSER_REGRESSION.json',BR/'GALLERY_MEDIA_CHECKS.json',BR/'FROZEN_FILE_FINAL_COMPARISON.json',BB/'BASELINE.json']:
   a='evidence/'+p.name;z.write(p,a);manifest.append(dict(source=str(p),archive=a,sha256=sha(p),size=p.stat().st_size))
  for p in BMD.iterdir():
   if p.is_file():z.write(p,'indices/'+p.name)
  z.writestr('EVIDENCE_MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
 for p in [OUT/'FUC_BATTLE_RUNTIME_INDEXES.zip',OUT/'FUC_BATTLE_RUNTIME_REPRODUCIBILITY.zip']:
  with zipfile.ZipFile(p) as z:assert z.testzip() is None
 deliverables=[p for p in OUT.iterdir() if p.is_file() and p.name!='FUC_BATTLE_DELIVERABLES.json' and (p.name.startswith('FUC_BATTLE_') or p.name.startswith('打开战斗') or p.name=='Open-FUC-Battle-Preview.ps1' or p.name=='lancer_attachment_preview.png')]
 jsonwrite(OUT/'FUC_BATTLE_DELIVERABLES.json',dict(timestamp=now(),files=[dict(name=p.name,size=p.stat().st_size,sha256=sha(p)) for p in sorted(deliverables)]));print([(p.name,p.stat().st_size) for p in deliverables])
if __name__=='__main__':main()
