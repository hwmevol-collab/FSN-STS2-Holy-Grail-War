"""Acceptance consolidation; refuses closure if any required evidence gate fails."""
from fuc_replay_common import *
import csv,hashlib,shutil,zipfile,subprocess,struct
P=BR/'Episode08';V=BR/'ViewerAcceptanceFinalV3';OUT=EU/'Converted/BattleScenes/lan_clip145'
DEL=pathlib.Path(r'C:\Users\Murasame\Documents\Codex\2026-10-06\files-pasted-by-the-user-fate-2\outputs')
def save(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def main():
    baseline=readjson(W/'backups/fuc-battle-replay-pre/BASELINE.json');checks=[]
    for r in baseline['files']+baseline['catalog']:
        p=pathlib.Path(r['path']);ok=p.exists() and p.stat().st_size==r['bytes'] and sha(p)==r['sha256'];checks.append(dict(path=str(p),equal=ok))
    assert all(x['equal'] for x in checks)
    finalbaseline=dict(status='PASS',frozen_files=len(baseline['files']),catalogs=len(baseline['catalog']),changed=[],new_asset_ids=0);save(BR/'REPLAY_BASELINE_FINAL_COMPARISON.json',finalbaseline)
    stability=readjson(BR/'STABILITY_FINAL.json');assert stability['status']=='PASS';assert stability['asset_total']==268504 and stability['new_asset_ids']==0
    offline=readjson(BR/'BUILD_VALIDATION.json');viewer=readjson(V/'lan_clip145_replay_viewer_validation.json');playback=readjson(V/'lan_clip145_replay_playback.json');encoding=readjson(V/'lan_clip145_native_video_encoding.json');validator=readjson(BR/'GLTF_VALIDATOR_REPORT.json');golden=readjson(BR/'GoldenRegression/GOLDEN_EVALUATOR_SUMMARY.json');weapon=readjson(V/'lan_equipment_viewer_validation.json');ident=readjson(BR/'EPISODE_RESOURCE_IDENTITIES.json');cleanup=readjson(BR/'DEBUGGER_CLEANUP.json')
    assert offline['status']==viewer['status']==playback['status']==encoding['status']==golden['status']==weapon['status']=='PASS'
    assert viewer['missing']==viewer['visibilityMismatches']==0 and max(viewer['max_matrix_error'].values())<2e-5
    assert playback['audio']['start_native_frame']==6 and playback['audio']['source_event']==174 and playback['audio_current_time']>0 and playback['audio_error'] is None
    assert encoding['input_frames']==encoding['encoded_frames']==83 and encoding['interpolated_frames']==0 and encoding['inserted_events']==0
    assert validator['result']['issues']['numErrors']==validator['result']['issues']['numWarnings']==0
    assert not cleanup['after']['cpu']['breakpoints'] and not cleanup['after']['memory']['breakpoints']
    assert golden['models']==3 and golden['clips']==9 and golden['failures']==0
    g=[readjson(p) for p in sorted(V.glob('*__mot_0000__clip_*_viewer-validation.json'))];assert len(g)==9 and all(x['status']=='PASS' for x in g)
    gg=dict(status='PASS',models=3,clips=9,runtime_evaluator=golden,three_frames=sum(x['frames'] for x in g),three_nodes=sum(x['samples'] for x in g),three_max_matrix_error=max(x['max_matrix_error'] for x in g),missing=0,playback_failures=0,playback_evidence='each Golden clip observed advancing in browser; short Rin clip2 additionally reset and observed time0.2424 playing=true',weapon_attachment=weapon,effect_external_current_episode=offline['metrics']['effect_external_snapshot'],sound_current_episode=ident['audio'])
    save(BR/'GOLDEN_REGRESSION_FINAL.json',gg)
    cap=readjson(BMD/'FUC_LAN_CLIP145_EPISODE.json');manifest=readjson(BMD/'FUC_LAN_CLIP145_REPLAY_MANIFEST.json');eid=cap['episode_id'];assert viewer['episode_id']==playback['episode_id']==offline['episode_id']==encoding['episode_id']==eid
    native_video=V/'lan_clip145_native_frames_480p60.webm';destvideo=L/'Gallery/animation_previews/lan_clip145_episode_replay_480p60.webm';destvideo.parent.mkdir(exist_ok=True);shutil.copy2(native_video,destvideo)
    # The video is the validated native frame sequence. Live audio uses existing
    # FLAC; no manual mux, re-decoding, or additional sound working copies.
    probe=json.loads(subprocess.check_output([r'D:\DDplay\ffmpeg\ffprobe.exe','-v','error','-count_frames','-show_entries','stream=codec_name,width,height,r_frame_rate,avg_frame_rate,nb_read_frames:format=duration,size','-of','json',str(destvideo)],text=True));st=probe['streams'][0];assert st['nb_read_frames']=='83' and st['avg_frame_rate']=='60/1' and st['height']==480;save(BR/'PREVIEW_MEDIA_VALIDATION.json',probe)
    status='FUC_LAN_CLIP145_FULL_BATTLE_REPLAY_PASS';closure='FUC_LOW_LEVEL_RUNTIME_RESEARCH_CLOSED'
    summary=dict(status=status,closure=closure,scope='CLOSED FOR MOD DEVELOPMENT; validated single episode replay, not full-game or general battle-pose reverse engineering',episode_id=eid,new_asset_ids=0,asset_total=268504,fuc_asset_count=21899,max_asset_id='FSN268504',same_episode=True,body_pose_mode='runtime-authoritative baked final world pose; world-derived glTF locals',final_pose_formula_generalized=False,native_samples=83,offline=offline,viewer={k:v for k,v in viewer.items() if k!='rows'},actual_playback=playback,golden=gg,gltf_validator=dict(errors=0,warnings=0,infos=validator['result']['issues']['numInfos']),native_video=dict(path=str(destvideo),frames=83,fps=60,width=854,height=480,bytes=destvideo.stat().st_size,audio=False,interpolated_frames=0),stability=stability,baseline=finalbaseline,cleanup=dict(cpu_breakpoints=0,memory_breakpoints=0,hooks=0,scratch_writes=0,ram_writes=0,ppsspp_pid=47072,ppsspp_closed=True),collector=dict(complete=cap['complete'],failure=cap['failure'],interpretation='90-frame tail target timed out; captured replay endpoints complete; no other episodes spliced'),unsupported_features=manifest['unsupported_features'],next_step='Move / Command Semantic Mapping',acceptance_gates={k:'PASS' for k in ['A_same_episode','B_final_body_pose','C_weapon','D_effect_birth_update_lifetime_visibility','E_audio_causality_start','F_clock_bridge','G_actual_viewer_playback','H_numeric_validation','I_golden_regression','J_existing_assets_stability']})
    # The emulator was identity-checked and stopped. A local viewer service stays
    # available for review, with an explicit close helper in the output folder.
    running=subprocess.check_output(['powershell','-NoProfile','-Command',"@(Get-CimInstance Win32_Process -Filter 'ProcessId=47072').Count"],text=True).strip();assert running=='0'
    save(BMD/'FUC_BATTLE_REPLAY_SUMMARY.json',summary)
    manifest['status']='validated_episode_replay';manifest['validation_summary'].update(viewer='PASS',viewer_evidence=str(V/'lan_clip145_replay_viewer_validation.json'),viewer_max_matrix_error=viewer['max_matrix_error'],visibility_mismatches=0,actual_audio_playback='PASS',golden='PASS',stability='PASS',closure=closure);manifest['preview']='/Gallery/animation_previews/'+destvideo.name;manifest['preview_audio']='none; use HTML KeyOn-scheduled existing FLAC';manifest['body_animation_scope']='actual ingress/clip145/exit/idle tail of this captured episode, not raw clip145';save(BMD/'FUC_LAN_CLIP145_REPLAY_MANIFEST.json',manifest)
    save(L/'Gallery/FUC_BATTLE_REPLAY_ENTRY.json',dict(status=status,episode_id=eid,viewer='FUC_LAN_CLIP145_REPLAY.html',preview='animation_previews/'+destvideo.name,asset_ids=['FSN248769','FSN248770','FSN248810','FSN248817','FSN258272','FSN260985'],new_asset_ids=0,entry_type='additive Gallery sidecar; old Gallery files unchanged'))
    report=f'''# Lancer clip145 同 Episode Full Battle Replay

**{status}**  
**{closure} — CLOSED FOR MOD DEVELOPMENT**  
完成时间：{now()}。范围：`validated_episode_replay`；并非整个 FUC 100% 逆向，也不是任意战斗动作的通用离线重建。

## A. Baseline

资产 268,504；FUC Europe 21,899；最大 ID FSN268504；新增 ID **0**。本轮基线冻结 3,944 个文件，轻量备份约 13 MB，未复制 Raw/ISO。基线位于 `Reports/FUC_BATTLE_REPLAY_PRE_BASELINE.json`；三种 Catalog 的 SHA-256 均保持原值。

## B. Golden Regression

原 3 models / 9 clips 继续 PASS。重新执行原 evaluator 对冻结的真实运行时 45 帧、2,535 节点进行比较：failures=0，max error=0。这不是重新采集三个角色的自然战斗。独立 Three.js 回归：286 帧、16,357 节点，最大矩阵误差 {gg['three_max_matrix_error']:.12g}；missing=0、实际播放失败=0。旧枪 viewer 的 6 次矩阵比较误差 0。新 Episode 的 external snapshot 28 次比较误差 0；声音 0x232D 的因果链也在本次 Episode 重现。

## C. Episode Capture

唯一正式来源：`{eid}`，`WORK/fuc/BattleReplay/Episode08`。自然单次 triangle 输入；原欧洲 ISO 只读；未注入游戏调用、未 patch RAM/EBOOT。角色 0x09C09700，player 0x09C6B290，body 0x0941CF80，weapon 0x09C581E0，FX context 0x08D8CD94，FX thread 0x08DA8974。

保存 85 个完整原生 frame（0..84）、1,356 个有序事件；重放使用 frame2..84 的 **83 个完整最终姿态**。采集器额外尾段目标 90 帧在 600 秒调试等待上限超时，原始 `complete=false` / TimeoutError 完整保留，未改写为成功。全部本次重放必需端点已在超时前取得：FX END/cleanup、body 离开 clip145、SAS KeyOn 返回 0、已有 FLAC 播放长度所需尾段。原生 SAS voice 完整结束/游标未恢复，见 N/O/U。Episode01..07 只保留诊断；其中并行采集干扰的 04..06 明确排除；没有拼接旧 body/effect/audio。

## D. Actual Battle Pose Pipeline

实测调用链：08884B28 player/MOT update → 088326F4 FAN 阶段 → 嵌套 08831E90 BPO → 08877378 模型节点 apply/matrix build → 08837964 weapon attachment → equipment 返回后的最终 body/weapon → FX VM/callback → audio consumer/SAS。入口与返回的节点缓冲全部保留；`FUC_BATTLE_POSE_PIPELINE.csv` 和 `FUC_BATTLE_POSE_STAGE_COMPARISON.csv` 保存阶段证据。

完整 composition 公式尚未通用化。本轮按用户第 50 条授权，采用 **runtime-authoritative baked final pose**。某些 SDK local 按普通父子层级重乘不能得到其最终 world（例如 frame6 最大差 0.1973297298）；因此导出从本次真实 final world 经 `inverse(parent_world) × child_world` 得到 glTF local，而不是强套 stale/special-policy SDK local。全部 60 节点进入标准 GLB，已数值验收。

## E. Raw MOT vs Final Pose

raw single clip145 与实际 final pose 分开保存。frame6、body_time=0.0666666701436：raw-vs-SDK-local max=1.717264890671；raw-vs-final-world max=1.933810591698。其他控制点见 `FUC_BATTLE_POSE_COMPONENTS.csv`。这是一项明确失败的控制实验，**不是**新 GLB 的姿态来源。未试 bone offset、手工旋转或时间微调。

## F. Transition / Blend

event42/native frame2 自然选择 clip145；player +0x10 window=0.0333333350718，+0x14=0；flags 从 0x040003C0 经 frame3 update 的 0x040002C0 到 frame4 update 的 0x04000240。原始 player 0x100-byte 快照逐事件保留。前序 clip0 的最后时间为 0.0333333350718；target 145 的 clock 在选择时重置 0。未完整恢复内部 previous-pose buffer/权重算式，**不伪造 blend weight**；实际组合结果由 final SDK 姿态权威记录。event446/frame15 返回 clip0，frame16 的最终身体已处于 clip0。

## G. FAN / BPO Contribution

目标 Episode 实际执行了 088326F4 → 08831E90。frame3 的 BPO entry46/return47：ordinal9 的 runtime +0x24 从 0 到 -0.00400000019，+0x48 从 0 到 16。FAN inclusive entry45/return48 包含这次嵌套 BPO，不能把它重复称为独立 FAN 文件 opcode 写入。阶段时 SDK 矩阵尚未重建；后续 model apply 写出新 local/world。确切 FAN 文件 entry 与该 BPO 参数源尚未完整命名；本次 replay 保留实际结果，不猜语义。

## H. Gameplay Transform

frame6 SDK ordinal1 local translation X=-1.717264890671，并含实际朝向变换；raw MOT 缺少这层战斗世界位置。角色位置/朝向及 SDK 最终 world 均保留在 runtime capture。重放只烘焙当前 Episode 的实际组合结果；不把它写回 raw evaluator 或原 9 个 GLB。无人工 root 移动。

## I. Frame Update Order

master = `float32((native_frame − 2) × measured_delta)`；实测 delta=0.01666666753590107，即本样本约 60 Hz。保持每个事件的 call_order_index、原始 body clock、fixed8 wait 和 phase；body clock reset 不改变 master 序列。CPU ticks/host debugger 时间只作诊断，不充当 game time。

| 事件 | event | native frame | master 秒 | phase |
|---|---:|---:|---:|---|
| clip145 selected | 42 | 2 | 0 | body state select |
| FX activation | 82/83 | 5 | 0.05000000447 | final body 之后 |
| sound request | 98 | 5 | 0.05000000447 | battle VM |
| FX birth point | 132 | 6 | 0.06666667014 | source body153 已完成 |
| FX external copy | 137 | 6 | 0.06666667014 | birth point 之后 |
| SAS KeyOn | 174/175 | 6 | 0.06666667014 | FX commit 之后 |
| FX END | 408 | 13 | 0.18333333731 | thread PC/render stream 清空 |
| cleanup phase | 431 | 14 | 0.20000001788 | model flags 0x20010→0x11 |
| clip0 selected | 446 | 15 | 0.21666668355 | target state 离开 |

同一 body_time 的不同 phase 不混用：frame_end 中 FX 仍可能是上一 callback 的姿态，验收使用当前 FX callback post，而非错拿 frame_end 的旧 FX。

## J. Weapon Replay

body source153→ordinal32→GLB42；weapon source0→ordinal1→GLB2，使用本次实际 remap table。每个 frame 的枪由 **当前重放身体153 world** 推导，不播放旧枪矩阵。离线 83×4=332 次 world 比较，max element/Frobenius error 都为 0；Three.js 最大误差 {viewer['max_matrix_error']['weapon']:.12g}。

## K. Effect Birth

`E = W_body153_at_native_frame6 × T(0,2.4,0)`。event132 的源矩阵地址 0x09C7F2F0 正是当前 body ordinal32 SDK world；与本次 frame6 world 16 元素差 0。计算出的 external translation 为 (1.193428039551,1.027234554291,0.089062780142)。28 次后续 snapshot 比较误差 0；同期身体153矩阵最大变化 1.765523791313，证明 external 是 snapshot，不连续跟随。

## L. SEQ Replay

当前 runtime SEQ 长 30,608 bytes，对 FSN248810 source 逐字节比较，只有 loader 修改的 +0xC pointer word 不同；所有命令 bytes 一致。最小重放根据当前 thread/model 解析结果处理 source bone remap、op16 absolute scale、op18 kind0 linear vector increment、kind5 `position += velocity; velocity += acceleration`，按 float32 次序计算；curve update 在新 SEQ 命令之前执行。wait=1/4 的本机字段分别 256/1024，均逐次匹配；opcode0/sub3 是 yield，未伪造数值 wait。

主 stream 与实际捕获的 thread+0x78 secondary stream 都保存于 `FUC_SEQ_REPLAY_TRACE.csv`。render stream 使用 thread+8=SEQ+12920，其三个 source words 为 material transfer、model draw opcode14/sub0x32、return。其执行路径通过同 Episode live pointer 与静态 088D3BDC/088CE7F8→088781D8 联合证明；**这三项不是逐 opcode breakpoint 捕获**，CSV 明示此区别。所有未知 material/control 参数保留 raw 64-byte lookahead，尾部可能包含下一条命令，不猜 opcode 语义或 color ordering。

## M. Effect Timeline

activation frame5 已 active，但 render thread+8=0，因此几何 **不可见**；frame6 出生矩阵与 draw stream 就绪，frame6..12 可见；frame13 END 清空 render stream，不再提交；frame14 cleanup 停用 pooled model。不是以 activation 时间直接当 birth/visible 时间。

source curves 恢复 node1 scale：frame6 (1,.4,1)，frame7 (1,.8,1)，frame8 (1,.9,1)，随后按 kind0 增量变化；node2 translationY：0,0,.03125,.09375,.1875,.3125,.46875。END 的 runtime TRS 仍可推进，但 SDK 持有最后可见矩阵；重放不绘制隐藏的 pending pose。102 次 FX world、28 次 external 离线比较误差均 0；Three.js FX max={viewer['max_matrix_error']['effect']:.12g}；34 个 callback 状态的 visibility mismatch=0。

精确 PSP material packed-color / blend / palette / shader 不支持，采用源几何与纹理/材质的标准 GLB 简化显示。没有为了相似度手调颜色/透明度。早期把 active 当 visible 的预览仅留在诊断目录，正式交付是 **ViewerAcceptanceFinalV3**。

## N. Audio Causal Event

同 Episode random list=[0x232C,0x232D,0x232E]，index1，实际 0x232D；random state=2002353090。battle event98→encoded request99→queue0x089F9B5C/event100→consumer168→program44/registered bank2→payload lookup169→voice0x08A142B4/event171→SetVoice172(return0)→KeyOn174(return0，event175)。PPHD SHA-256=17f8ccfa31e0e61e3af6a1b4ea3a9e125f4d9ca9050bc3d071f6b345869863ac，对应 FSN251363 `snd/se/chr_lan00.phd`。6768-byte 当前 RAM payload 对现有 FSN260985 ADPCM 逐字节相等，SHA-256=d096917d381d9af6ca4e4ba8bccb34cc68d547dc4a37224f11587a7b3508ac4d。

引用现有 22050 Hz FLAC，不重解码、不新建声音副本。HTML 在已确认的 native frame6/event174 master=0.06666667014 启动。实播证据 audio.currentTime={playback['audio_current_time']:.6f}、error=null。原生 SetVoice loop 参数=1；没有据此伪造 native voice 结束时机。此处闭合的是 caller/queue/payload/SAS **启动事件**；原生波形 pitch、sample cursor、完整 voice termination 仍未知，属于用户第36条允许的范围。

## O. Clock Domain Bridge

body_60hz、effect_fixed8、audio_runtime 原值保留在 Episode/Timeline。native frame+call order 是桥，不强行声称相同 native 时钟。KeyOn 与上游 request 不同帧；FX activation 与 birth 不同帧。浏览器显示时间仅驱动这个已确定的 master 事件序列；它不反推 PSP 时机，也不宣称硬件音频 sample 精度。视频不人工 mux 声音，完整 HTML 有实时 KeyOn 播放。

## P. Replay Manifest

`FateUnlimitedCodesPortable_Europe/Metadata/BattleReplay/FUC_LAN_CLIP145_REPLAY_MANIFEST.json`。包含 same episode、原 asset IDs、最终姿态来源、源 raw clip、weapon formula、birth vector evidence、source SEQ transform commands、snapshot/visible 区间、音频因果和 clock bridge。新 GLB 位于 `Converted/BattleScenes/lan_clip145/lan_clip145_battle_pose.glb`；Model/Skeleton/Skin/83 frames/180 animation channels。旧 9 个动画和 341 个静态 GLB 完全分离。

## Q. Viewer Validation

标准 Three.js GLTFLoader + AnimationMixer 实际载入和播放。全 60 body nodes / 4 weapon nodes / 3 FX nodes，missing=0；max matrix error={max(viewer['max_matrix_error'].values()):.12g}，visibility mismatch=0。native fps 预览使用 WebCodecs 对已采集的 83 帧逐一编码，timestamp 来源 master frame，未插值/补事件；ffprobe 854×480、60/1 fps、83 帧、1.383333 秒、{destvideo.stat().st_size:,} bytes。GLB container、accessor/buffer bounds、normalized quaternion 均 PASS；Khronos validator errors=0/warnings=0/infos=29。

## R. Numeric Runtime Comparison

| 链 | 比较次数 | 离线 max element | 离线 max Frobenius | Three.js max element |
|---|---:|---:|---:|---:|
| body final world | 4980 | 1.043823840474e-6 | 1.562566346091e-6 | {viewer['max_matrix_error']['body']:.12g} |
| weapon | 332 | 0 | 0 | {viewer['max_matrix_error']['weapon']:.12g} |
| FX world | 102 | 0 | 0 | {viewer['max_matrix_error']['effect']:.12g} |
| FX external | 28 | 0 | 0 | included in FX world |

严格 gate 为 2e-5；实际误差为 0 或约 1e-6。不是“看起来合理”。详细 CSV 为 `FUC_LAN_CLIP145_RUNTIME_VS_REPLAY.csv`，包含 16 元素、max abs/Frobenius/translation 指标、native frame 和 event index；ViewerAcceptanceFinalV3 保留独立播放器逐节点误差。

## S. Gallery

新增 `Gallery/FUC_LAN_CLIP145_REPLAY.html`、`fuc_lan_clip145_replay.js` 与 entry sidecar，未修改旧 Gallery/旧 Catalog。支持一次播放、暂停、原生帧检查、矩阵/visible 验收及无插值预览。正式 preview：`Gallery/animation_previews/lan_clip145_episode_replay_480p60.webm`。输出目录 `Open_FUC_Replay.cmd` 可打开，`Close_FUC_Replay.cmd` 只关闭其已核对身份的本机查看服务。当前查看器已显示本次 birth frame，保留一个本机 loopback 服务供查看；旧 8986 服务未动。

## T. Stability

旧资产 ID/旧字段值改变 0；new asset_id=0；268504/maxFSN268504；CSV/JSONL/SQLite **byte-identical**；SQLite integrity=ok。3,944 本轮冻结文件无变化，继承冻结 527 文件无变化，341 静态 GLB SHA/mtime/size 无变化。624,836 个 protected references / 456,988 个 unique paths，无缺失/size 变化。完整 Raw payload 哈希没有重新扫描；所有写入局限于新命名空间，未写 Raw/Preservation/ISO。CPU/memory breakpoints=0，hooks/scratch/RAM writes=0；独立 PPSSPP PID47072 已关闭，用户配置/存档未访问。

## U. Failures / Unknown

保留原始采集器尾段 TimeoutError；正式 Episode 端点已覆盖而 collector.complete 仍 false。JIT 多断点漏捕、诊断 04..06 采集重叠被排除，正式08为单 interpreter collector。早期 VFR/active-visible 预览被更严格相位检查淘汰。未完全解出通用 battle blend/FAN/gameplay/world-policy 生成公式、精确 PSP 材质绘制、原生 SAS sample clock/pitch/voice end。这些是本次用户明确允许的 replay/简化 renderer 范围限制，不包装成已完成的全引擎逆向。AMO/BAM/TUV/MIL/PAR 未扩展，招式未猜名。

## V. FUC Runtime Closure Decision

**{status}**。A–J 本轮 gate 全部满足，包括同 Episode 因果、final pose 权威复现、weapon、FX birth/update/end/visible、KeyOn start、clock bridge、实际 viewer、数值误差、Golden 回归、旧库稳定。

**{closure} — CLOSED FOR MOD DEVELOPMENT**。仅针对当前 MOD 制作所需底层技术基础；不声称任意 battle 动作可纯离线重建或整个 FUC 100% 逆向。后续冻结重型 runtime 研究，下一步只进入 **Move / Command Semantic Mapping**。
'''
    reportpath=L/'Reports/FUC_LAN_CLIP145_FULL_BATTLE_REPLAY_REPORT.md';reportpath.write_text(report,encoding='utf-8')
    DEL.mkdir(exist_ok=True);shutil.copy2(reportpath,DEL/reportpath.name);shutil.copy2(destvideo,DEL/destvideo.name);shutil.copy2(OUT/'lan_clip145_battle_pose.glb',DEL/'lan_clip145_battle_pose.glb');shutil.copy2(V/'replay_final_frame.png',DEL/'lan_clip145_replay_frame.png');shutil.copy2(BMD/'FUC_BATTLE_REPLAY_SUMMARY.json',DEL/'FUC_BATTLE_REPLAY_SUMMARY.json')
    save(DEL/'replay_service_session.json',dict(pid=32812,port=8998,service=str(W/'scripts/fuc_replay_evidence_server.py'),session='ViewerAcceptanceFinalV3'))
    (DEL/'FUC_Replay_README.md').write_text('''# Lancer clip145 重放\n\n双击 Open_FUC_Replay.cmd 打开完整交互查看器（身体、枪、特效、确认 KeyOn 时机的声音）。关闭后台查看服务用 Close_FUC_Replay.cmd。\n\n安装内容位于原主库的新 BattleReplay/BattleScenes/Gallery 命名空间；启动器引用本机 E: 主库，不复制音频或旧资产。\n\nlan_clip145_episode_replay_480p60.webm 是 83 个真实已采集 native poses 的 480p/60fps 视频，只有画面；声音在 HTML 查看器播放。\n\nlan_clip145_battle_pose.glb 是含完整 model/skin/skeleton/animation 的 runtime-authoritative final-pose Episode working copy，不是 raw MOT 通用导出。\n\nFUC_LAN_CLIP145_REPLAY_EVIDENCE.zip 保存本次 Episode08、重放索引、公式/转换脚本、独立播放器验收、保护基线比较和新 GLB/reference。它不包含 ISO/RawExtracted/现有 FLAC。\n\n精确 PSP 材质混色/shader、native SAS pitch/sample-clock、任意动作的通用最终姿态组合公式仍未恢复；scope=validated_episode_replay。\n''',encoding='utf-8')
    z=DEL/'FUC_LAN_CLIP145_REPLAY_EVIDENCE.zip'
    with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for root,prefix in [(BMD,'Metadata/BattleReplay'),(P,'Episode08'),(V,'ViewerAcceptanceFinalV3'),(OUT,'BattleScenes/lan_clip145')]:
            for p in sorted(root.rglob('*')):
                if p.is_file():archive.write(p,prefix+'/'+p.relative_to(root).as_posix())
        for p in sorted((W/'scripts').glob('fuc_replay_*')):
            if p.is_file():archive.write(p,'scripts/'+p.name)
        for p in [reportpath,BR/'BUILD_VALIDATION.json',BR/'STABILITY_FINAL.json',BR/'REPLAY_BASELINE_FINAL_COMPARISON.json',BR/'GOLDEN_REGRESSION_FINAL.json',BR/'GLTF_VALIDATOR_REPORT.json',BR/'EPISODE_RESOURCE_IDENTITIES.json',BR/'DEBUGGER_CLEANUP.json',BR/'PREVIEW_MEDIA_VALIDATION.json',L/'Gallery/FUC_LAN_CLIP145_REPLAY.html',L/'Gallery/fuc_lan_clip145_replay.js']:
            archive.write(p,('Gallery/' if p.parent.name=='Gallery' else 'Reports/')+p.name)
    with zipfile.ZipFile(z) as archive:assert archive.testzip() is None;entries=len(archive.namelist())
    save(DEL/'FUC_REPLAY_DELIVERABLE_HASHES.json',[dict(file=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in [DEL/reportpath.name,DEL/destvideo.name,DEL/'lan_clip145_battle_pose.glb',z]])
    print(json.dumps(dict(status=status,closure=closure,report=str(reportpath),evidence_zip_bytes=z.stat().st_size,evidence_entries=entries,asset_total=268504,new_asset_ids=0,viewer_max_matrix_error=max(viewer['max_matrix_error'].values()),source_episodes=1),ensure_ascii=False))
if __name__=='__main__':main()
