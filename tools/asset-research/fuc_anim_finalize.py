"""Finalize evidence-gated animation report, sidecars and a small review package."""
from fuc_anim_common import *
import urllib.parse
OUTPUT=pathlib.Path('C:/Users/Murasame/Documents/Codex/2026-10-06/files-pasted-by-the-user-fate-2/outputs')

def main():
    b=frozen();st=readjson(AMD/'FUC_ANIMATION_STABILITY.json');pose=readjson(AW/'Runtime/POSE_COMPARISON_SUMMARY.json');natural=readjson(AW/'Runtime/Natural/NATURAL_COMPONENT_COMPARISON.json');exports=readjson(AW/'GLB_EXPORTS.json');validated=readrows(AMD/'FUC_VALIDATED_ANIMATIONS.csv');ui=readjson(AW/'Playback/GALLERY_UI_REGRESSION.json');validator=readjson(AW/'GLTF_VALIDATOR_REPORT.json')
    viewers=[readjson(AW/f'Playback/{pathlib.Path(r["animated_glb"]).stem}_viewer-validation.json') for r in exports]
    assert st['status']=='PASS' and pose['failed']==0 and len(exports)==len(validated)==len(viewers)==len(validator)==9
    assert all(r['status']=='PASS' for r in viewers) and all(r['result']['issues']['numErrors']==r['result']['issues']['numWarnings']==0 for r in validator)
    assert all(sha(r['animated_glb'])==r['sha256'] for r in exports)
    # UI records are DOM observations saved by the actual browser interaction tool.
    for r in ui:
        if r['type']=='image':assert all(i['complete'] and i['width']>0 for i in r['images'])
        elif 'playback' in r['type']:assert all(m['ready']==4 and m['time']>0 and m['error'] is None for m in r['media'])
        for link in r.get('links',[]):
            rel=urllib.parse.unquote(urllib.parse.urlparse(link['url']).path).lstrip('/');assert (L/rel).exists(),rel
    ui_summary=dict(browser='Codex In-app Browser; no Chrome claim',samples=len(ui),images=4,audios=4,old_inline_videos=3,validated_previews=3,original_mpeg_avi='existing link-only behavior preserved; not inline playback PASS',theora_preview='FSN042476 actual MP4 preview readyState=4, 1280x720, time advanced; all original 16 mappings unchanged',static_model='existing GMO/GLB/metadata links preserved',unvalidated_mot='explicit decoded / binding and playback unverified',catalog_count=268504,status='PASS_NO_REGRESSION_WITH_BASELINE_LIMITATIONS',observations_path=str(AW/'Playback/GALLERY_UI_REGRESSION.json'))
    jsonwrite(AMD/'FUC_GALLERY_REGRESSION.json',ui_summary)
    functions=[('0x088869d8','resource loader','0x11 GMO priority, 0x10 MOT; does not load both'),('0x088833b4','GMO constructor','source hierarchy and runtime wrapper'),('0x08881f90..0x08882558','source name -> semantic bone ID remap builder','static 0x089cd120 table, 63 records stride 34; dynamic remap readback'),('0x0888255c','bone ID lookup','model+0x48 int16 remap -> model+0x5c + ordinal*0x140'),('0x08883f10..0x08883fa4','MOT preprocessing','translation * float32(0.1), retain upper16 bits'),('0x0888546c','pose channel binding','bone ID optional remaps; T node+0x20, S+0x30, R+0x50'),('0x08884a30','0x0202 curve evaluation','four components LINEAR, endpoints clamped; 180 primitive tests exact'),('0x0887772c','direction / twist conversion','normalized X direction, X-roll degrees, 16384-entry sine LUT'),('0x08877378','delta and local matrix application','alignment @ Rx, scale columns, XYZ translation; bind_local @ delta under flag0x100'),('0x0893f7dc','SDK world matrix propagation','parent ordinal at SDK+0x3c low12 bits; local+0xb0, world+0xf0'),('0x088866b0','motion player allocation','dt at +0xc initialized to 1/60'),('0x08884b28','motion time update','time += dt, end/loop player-controlled'),('0x08885d24','clip selection / transition','header+8 copied into transition/blend duration at player+0x10'),('0x088842f0','transition evaluator','player flag0x80; excluded from raw single-clip export'),('0x08998cd4','animation VM dispatch','jump table0x089b8fe0, load/select/bind/update/attach operations'),('0x08958018;0x08957ae0;0x08957b18','FPK resource load/ready/finalize','existing read-only resources; no whole-game extraction')]
    csvwrite(AMD/'FUC_RUNTIME_FUNCTIONS.csv',[dict(address=a,role=r,evidence=n,status='confirmed_for_scoped_path') for a,r,n in functions])
    time_rules=dict(time_unit='seconds',update='time += player.dt',default_dt_float32=0.01666666753590107,nominal_pose_rate=60,header_offset8_legacy_name='play_speed',header_offset8_runtime_role='transition/blend duration; not clock multiplier',frame_script_conversion='integer frame count / 60 at 0x089990b0..c4 and 0x08999164..70',source_interpolation='four stored components LINEAR; rotation converted afterwards',export='sample source evaluator every1/60 plus exact end; GLB STEP hold between samples',loop='external player flag0x8; wrap/rebind with 1/60 boundary; no source MOT loop flag assigned',blend='external player flag0x80; header+8 duration/override f12; exports exclude blended pose',root_motion='only source local bone translation exported; full gameplay position/mirror composition not yet exhaustively traced')
    jsonwrite(AMD/'FUC_TIME_AND_PLAYBACK_RULES.json',time_rules)
    jsonwrite(AMD/'FUC_ANIMATED_GLB_MANIFEST.json',exports)
    summary=dict(status='FUC_ANIMATION_RUNTIME_VALIDATION_PASS',scope='validated subset: sir/rin/lan 0000 GMO, bank0 0000 MOT, clip indexes0/1/2; not all3676 clips',validated_models=3,source_transform_nodes=169,validated_animations=9,remaining_decoded_clips_unvalidated=3667,new_asset_ids=0,asset_total=268504,max_asset_id='FSN268504',controlled_runtime=dict(models=3,clips=9,pose_frames=45,node_comparisons=2535,max_translation_error=0.0,max_rotation_angular_error_degrees=0.0,max_scale_error=0.0,max_local_world_matrix_error=0.0),natural_bank_fingerprint=dict(unique_banks=3,offset_slots=720,channels=8403,key_values=480764,max_error=0.0),natural_battle=dict(frames=10,node_components=600,max_translation_xyz_error=natural['max_translation_xyz_error'],max_rotation_storage_error=natural['max_rotation_storage_error'],max_scale_error=natural['max_scale_error'],homogeneous_w_differences=len(natural['homogeneous_w_differences']),full_world_matrix_comparison='not captured in this natural-only probe; controlled matrix comparison is separate'),gltf=dict(files=9,errors=0,warnings=0,validator_version='2.0.0-dev.3.10',max_quaternion_norm_error=max(r['max_quaternion_norm_error'] for r in exports)),playback=dict(viewer='Three.js0.180.0 GLTFLoader + AnimationMixer',files=9,frames=sum(r['frames'] for r in viewers),node_comparisons=sum(r['samples'] for r in viewers),max_matrix_error=max(r['max_matrix_error'] for r in viewers),recorded_rows='per-clip summaries + first12 raw viewer comparisons persisted; all-frame max computed by viewer',source_reference='independently runtime-validated offline evaluator; all286 baked frames expected matrices provided in reference JSON'),previews=3,stability=st,gallery=ui_summary,unknowns=['full-library scale channel numeric validation','track0x40 consumer semantics','negative-X / zero-direction singularity and other matrix flags','optional mirror/bone-remap modes and blends beyond raw single clip','gameplay position integration and separate weapon/equipment attachment','runtime palette/material changes','semantic move/command table','other model/MOT banks and 3667 clips'],recommended_next_step='FAN/AMO/VFX runtime mapping',criteria={str(i):'PASS in validated subset' for i in range(1,12)})
    jsonwrite(AMD/'FUC_ANIMATION_VALIDATION_SUMMARY.json',summary)
    closure=dict(owned_ppsspp_pid=16692,process='closed',debug_breakpoints=readjson(AMD/'RUNTIME_FINAL_DEBUG_STATE.json')['breakpoints']['breakpoints'],evidence_receiver_8998='closed',existing_gallery_server_8986='preserved',original_user_ppsspp_configs_saves='not accessed',diagnostic_patches='RAM-only early scratch calls; restored and game reset before natural evidence; original ISO/ELF hashes unchanged',timestamp=now());jsonwrite(AMD/'SESSION_CLOSURE.json',closure)
    vp=EU/'Converted/AnimatedModels/viewer/index.html';html=vp.read_text('utf-8');html=html.replace("await saveEvidence(select.value.split('/').pop().replace('.glb','.webm'),blob,'video/webm');status.textContent+='\\nWebM 预览已保存';", "const persisted=await saveEvidence(select.value.split('/').pop().replace('.glb','.webm'),blob,'video/webm');status.textContent+=persisted?'\\nWebM 预览已保存':'\\nWebM 预览录制完成，可保存';");vp.write_text(html,encoding='utf-8')
    table='\n'.join('| '+ ' | '.join([r['character'],r['animation_asset_id'],str(r['clip_index']),str(round(float(next(e['duration'] for e in exports if e['animation_asset_id']==r['animation_asset_id'])),6)),str(r['viewer_frames_compared']),r['viewer_max_matrix_error']])+' |' for r in validated)
    report=f'''# FUC Animation Runtime Validation

**FUC_ANIMATION_RUNTIME_VALIDATION_PASS — 仅限明确验证的 3 个模型 / 9 条原始单片段。**

本轮首次完成 Europe 原始 GMO → 游戏骨骼 ID remap → MOT → 离线姿态 → 原始游戏运行时数值 → 标准 Animated GLB → 独立播放器的闭环。其余 3,667 条已解码片段仍未获得同等验收，禁止据此全库批处理。本次没有新增逻辑资产、重新解包或覆盖静态 GLB。

## A. Baseline

冻结时及结束时均为 **268,504** 条资产，FUC Europe **21,899** 条，旧资产 **246,605** 条，最大 ID **FSN268504**。冻结报告：`E:\\FSN_MASTER_ASSET_LIBRARY\\Reports\\FUC_ANIMATION_PRE_BASELINE.json`。关键 Metadata/Gallery 共 446 文件已作 SHA-256 基线和轻量备份（{sum(r['size'] for r in b['files']):,} 字节），备份在 `{AB}`，未复制整个 RawExtracted。

沿用已有 341 静态 GLB、4,059 源 transform nodes、2,642 weighted joints，以及 54 MOT / 3,676 解码片段 / 198,831 通道 / 2,044,587 个关键帧值。未重跑原提取、转换和 ID 分配流程。

## B. Runtime investigation

真实欧版：NPEH00007、版本 1.01。EBOOT ELF 2,000,320 字节，SHA-256 `33e8240519a232be40be503f17a23c2dfd5a361177ffb925de444df95dbe6ba7`。ISO SHA-256 `bdf13beffbad519fd51f1ab075d165d3c7bfa075feef1a5b1fd7775bac0f830d`。两者结束时仍一致。

仅调查动画加载、remap、curve、TRS、矩阵、时间更新和 VM。具体地址/作用见 `FUC_RUNTIME_FUNCTIONS.csv`，静态 ELF 反汇编和 PPSSPP 准确 VFPU 反汇编保存在 `{AW / 'Static'}`。ELF 地址映射为 `file_offset = VA - 0x08804000 + 0x54`。

使用独立 portable PPSSPP 1.20.4、独立 config/memstick，未访问用户配置和存档。经授权显示窗口，实际进入 Shiro/Rin 与 Lancer/Rin 两场战斗，保存了角色 UI、battle PNG、资源指针和内存 dump。早期受暂停启动和无存档确认画面影响出现黑屏；后续通过真实 UI 排除，成功渲染。GPU debugger screenshot 下载接口仍不可靠，最终使用原生窗口截图。早期诊断仅改 WORK/模拟器 RAM，诊断 scratch 已恢复并 reset，未修改 ISO / Preservation EBOOT。

## C. MOT → Model

真实 battle player：`+0x34 → model wrapper`，wrapper `+0x34 → resource record`，record `+0x10 → GMO 路径`；player `+0x2c → bank 指针数组`、`+0x30 → bank 数量`。player `+4` 是按 ID 的中间状态缓冲，不能当作模型指针。

直接读到 `chr/sir/0000.gmo`、`chr/rin/0000.gmo`、`chr/lan/0000.gmo`，分别关联 bank0 中 `chr/<code>/0000.mot`。三份 bank 的全部 720 offset slots、8,403 channels、480,764 key values 经 endian/pointer relocation/translation preprocessing 后与原始源一致，错误 0。Rin 采集两次，统计按唯一 bank 去重。bank1 另外匹配 common MOT，未将 common bank 动画推广为 validated。

路径身份和 bank 全量指纹构成配对证据，不能用“同目录”代替。三份同名 MOT 在多个 costume FPK 中存在完全相同 payload；指纹证明 payload 与资源路径关系，不能唯一判定重复副本的历史容器来源。本次关联到现有 0000 逻辑条目，保留所有其他来源条目与 ID，不声称排他性。

9 个 clip 级 confirmed 关系见 `FUC_MOTION_MODEL_BINDINGS.csv`。人物身份取自实际游戏 UI 与加载路径：Shiro、Rin、Lancer；其余代码未依 Fate 常识批量命名。

## D. Bone mapping

MOT 的 bone 值是引擎 bone ID，**不是 GMO ordinal，也不是 GLB joint index**。`0x08881f90..0x08882558` 从原 GMO node 名构建 remap：静态表 `0x089cd120` 有 63 个 34 字节记录（32 字节名 + int16 ID）。Y/X/Z=0/1/2，hip=3，waist=4，breast=5，neck=6，head=7，L_harm=9、R_harm=13、左右上腿16/19等；动态前缀规则也已保留在证据中。`0x0888255c` 读 model+0x48 int16 remap，再定位 model+0x5c + ordinal×0x140。

例如 sir 的 bone ID0/Y → GMO ordinal13 → GLB node24；ID9/L_harm → ordinal23 → GLB node34。同 ID0 在 rin/lan 的 ordinal分别为10/1。RootNode ordinal0不能冒充 ID0。完整实测 remap 在每个 `SKELETON_EVALUATOR_INPUT.json` 和 `bone_remap.bin`；clip 通道关系表共 **342** 行，GLB joint 明确记录为 `skin_index:joint_index`，可有多个 skin 引用同一 node。

三模型全部 169 源 nodes 的名称、parent 和 GLB adapter 均核对。最大 bind TRS 重建误差 sir 1.19209e-6、rin 2.86102e-6、lan 3.81470e-6；parent 错误0。初始 2e-6 试验阈值使 rin/lan 超限，原试验记录保留；正式采用明确的 float32 TRS 重建容差 2e-5，未隐去失败历史。此误差属于静态 Noesis TRS roundtrip；后续导出动态矩阵误差更低。原 78 个 bN 命名模型仍为 provisional，没有赋予人体语义。

## E. Translation

0x21 经 binder 写入 node+0x20；XYZ 为局部变换的位移分量。loader `0x08883f10..0x08883fa4` 对四个存储分量做 **float32×0.1，再截去低16 bits**，不能替换为最近值 bfloat rounding。原文件 big-endian，运行时数据 little-endian。单位只证明该缩放关系，没有推断真实世界米/厘米。

delta 写入 XYZ 平移，node flag0x100 时 `local = bind_local @ delta`，其他已测试核心节点直接使用 delta。不是将 MOT 当 world position，也不是把 gameplay 位移烘进动画。

真实 battle 10 帧/600 nodes 的 XYZ 位移误差均0。另有10处 T.w差异：rin ordinal18、lan ordinal9 各5帧，源节点 flag0xf04，实际W=1而基线默认W=0。原四分量对比保留590 PASS/10 DIFFERENT_RUNTIME_STATE；W作为辅助存储分量单独记录，不当作第四位置坐标，不声称这10处原四分量完全相同。

## F. Rotation

0x28 是 **归一化后的 X 方向向量 XYZ + 绕 X 的 roll/twist 角度（度）**，不是 quaternion/Euler/axis-angle。`0x0887772c` 先对方向归一化，建立将 X 轴指向该方向的 alignment，再乘 Rx(twist)。若 `k=(1-x)/(y²+z²)`，alignment 三列为 `[x,y,z]`、`[-y,x+z²k,-zyk]`、`[-z,-zyk,x+y²k]`。

twist 使用原始 16,384-entry sine LUT，索引为 `((trunc(float32(angle×182.04444885253906))+2)>>2)&16383`，cos取相差4096项。该量化不能替换成连续数学 sin/cos。LUT从真实 runtime global pointer0x08b1d1d4读取并保存。

按 source matrix 的列向量和乘法顺序计算；离线与原游戏 float32/VFPU路径实测一致。输出 GLB 时才把最终 local rotation 分解为归一化 XYZW quaternion。原 MOT 本身不能直接装进 glTF rotation VEC4。零方向、负X奇点和其他矩阵模式尚未建立通用规则，导出工具拒绝不支持模式。

## G. Scale

0x22 的 binder 写 node+0x30，矩阵路径对三列分别乘 XYZ scale。所选9片段没有0x22 scale通道，三模型169节点的默认 XYZ=1 在运行时/离线对比中得到验证。bind_local 仍保留，不伪造全局缩放。全库327个scale通道尚未完成独立动态采样，**只有本批“缺席/默认”行为升级 confirmed**。

## H. Time

`0x088866b0` 初始化 player+0xc dt=1/60；`0x08884b28` 做 `time += dt`。frame整数在 VM 地址0x089990b0..c4、0x08999164..70除以60转为时间，natural连续捕获也读到0.0166666675增量。key time/end_time使用秒；60Hz是虚拟动画时钟，不能把软件渲染器的实际 wall-clock 渲染速度当作游戏FPS。

旧解码字段 `play_speed`（clip header+8）在真实 select路径0x08885d24进入 player+0x10 的 transition/blend window，不参与默认 time += dt 乘法。为保持旧字段值，未改旧 Catalog/解码JSON；新 `FUC_TIME_AND_PLAYBACK_RULES.json` 记录真实解释。

MOT没有在本轮证明内含 loop flag；player flag0x8控制wrap/rebind，边界包含1/60处理。GLB不伪造 source loop。预览重复播放是 viewer 显式选项。

## I. Interpolation

所选通道格式 flags0x0202，`0x08884a30` 对四个存储分量做 LINEAR，端点clamp、精确key命中及segment选择均由原游戏函数确认。180个独立原函数采样误差0。rotation先插值方向/twist存储，再归一化并转量化矩阵，不能把所有源 rotation 强行 SLERP。

GLB采用 **每1/60秒烘焙 + 精确end sample + STEP保持**，确保每个源时钟帧的姿态一致；STEP是导出帧保持规则，不是源 MOT 插值语义。两个采样帧之间的连续轨迹不宣称精确恢复。

## J. Runtime validation

控制实验调用原始 loader/player/matrix函数，清除transition混合，仅评价原始单clip；模型配对另有natural battle证据。sir49、rin60、lan60节点，每模型clip0/1/2，分别在0%、25%、50%、75%、100%采样：**45姿态帧、2,535节点比较**。

translation四分量、rotation存储四分量、scale四分量、delta/local/world16分量的最大绝对误差均 **0**；world Frobenius误差 **0**；delta rotation去列缩放后的角误差 **0度**。容差2e-5，失败0。完整双矩阵/时间/节点逐行保存 `FUC_RUNTIME_POSE_COMPARISON.csv`。

另用只读conditional breakpoint在真实战斗矩阵函数返回后捕获rin/lan各5帧，共600节点，XYZ/rotation storage/scale误差0；10个W差异如E节。此natural probe没有保存SDK full-world对照，不能与前述controlled full-matrix数值混写。natural原数据、差异表及修正分量统计全部保留。

clip0有自然battle中播放证据；clip1/2具有明显不同的肢体姿态，但没有move/command表确认，仍叫clip_0001/clip_0002。未冒称某个招式或攻击名。`SCALE_AND_MOVEMENT_PROBE_SELECTION.json` 明确保存“不从数值振幅推断idle/move名”。

离线工具长期保存在 `{W / 'scripts/fuc_motion_evaluator.py'}`。支持原始MOT+clip_index、已解码MOT clip JSON、captured skeleton metadata、LUT、time → per-node T/Rstorage/S/delta/local/world JSON。原始sir MOT clip0、t=0.25的CLI复现与游戏49节点world matrix再比较，误差0，见 `EVALUATOR_REPRODUCTION.json`。

## K. GLB export

正式 working copy 共 **9 GLB**，在 `{EU / 'Converted/AnimatedModels'}`，与341静态GLB完全分开。每份包含原mesh/material/texture/skin/IBM/node hierarchy和1条动画，原geometry/skin binary保留，animated local matrices转换为TRS。time SCALAR，T/S VEC3，R normalized quaternion VEC4。

最大导出local矩阵误差 {max(r['max_local_matrix_error'] for r in exports):.9g}，world矩阵误差 {max(r['max_world_matrix_error'] for r in exports):.9g}，quaternion norm误差 {summary['gltf']['max_quaternion_norm_error']:.9g}。GLB容器、buffer/accessor边界及quaternion已检查；[Khronos glTF Validator](https://github.com/KhronosGroup/glTF-Validator) 9/9 **0 errors / 0 warnings**，有保留的 informational unused tangent等提示。[glTF 2.0动画规范](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html#animations) 为格式依据，不是 FUC runtime语义依据。

| UI人物 | 已有clip资产ID | clip | 秒 | 播放器逐帧数 | 播放器最大矩阵误差 |
|---|---|---:|---:|---:|---:|
{table}

## L. Playback validation

实际使用独立于Python导出的 [Three.js GLTFLoader](https://threejs.org/docs/#examples/en/loaders/GLTFLoader) + AnimationMixer，加载9文件、渲染每个烘焙帧，验证skin和body动作。共 **286帧、16,357个node world矩阵比较**，最大误差 **{summary['playback']['max_matrix_error']:.9g}**，无missing nodes；容差2e-4。另有连续播放、三段真实viewer录制WebM及页面截图。没有把Khronos Validator当作第二播放器，Blender/Noesis动态播放本轮未做。

每条浏览器证据JSON保存全样本计数/最大误差和前12条原始行；完整286帧expected matrices保存在viewer reference JSON，controlled runtime CSV保留全部2,535行。未声称16357条viewer原始行全部落盘。

本批是body原始单clip。分离武器/装备绑定、游戏palette/material替换、gameplay position、镜像、blend尚未完整恢复；Lancer的枪不在0000 body模型内，viewer颜色与runtime调色也可能不同。这些不纳入本批body骨骼动画正确性的外观验收，不宣称完整战斗演出已恢复。原始根节点/源局部translation被保留，未加入猜测的移动轨迹。

## M. FAN / AMO

未新增语义结论；1,271 FAN、154 AMO原始数据及旧索引保持。没有在MOT链未完成前转移优先级，也没有借用Fate招式常识命名。

## N. VFX

2,056 eft资源仍保留原始来源。本轮没有证明motion→effect trigger，未批量语义化。

## O. Gallery

原Gallery renderer和268504条catalog.js保持，仅在index.html末尾追加新sidecar map/overlay脚本。9已验证MOT卡片显示“动画已验证”，可打开AnimatedGLB和独立播放器；3个clip0含480p/60fps CFR WebM预览（约3秒，重复由viewer明确控制）。其余MOT明确显示“运动通道已解码 · 骨骼绑定 / 播放未验证”。

真实in-app browser回归：Original/Remastered/FHA/FUC四来源各1图片加载成功、各1音频实际播放且时间前进；Remastered旧Theora MP4预览、FHA MPG→MP4、FUC PMF→MP4实际播放readyState4且无error；静态模型/metadata链接仍有效，未验证MOT状态正确，3个新动画预览均能播放。旧16条Theora preview map SHA不变。

Original MPG/AVI卡片在冻结基线就是“打开工作版/原始文件”链接，没有内嵌播放器：本轮核对入口/文件保持，**不能声称Original视频浏览器内播放PASS**，也没有额外重转Original。浏览器是Codex in-app browser，不冒称Chrome验收。完整UI观测见 `FUC_GALLERY_REGRESSION.json` 和 `Playback/GALLERY_UI_REGRESSION.json`。

日常viewer在既有Gallery server8986上可用，无须8998证据接收器。已保留播放器标签页；独立PPSSPP及本轮8998 server已关闭，debug breakpoints为空。

## P. Stability

asset total=268504，FUC=21899，max ID=FSN268504，new IDs=0，changed old rows=0。Catalog CSV/JSONL/SQLite三份SHA均与冻结基线一致，证明旧ID和字段原值全部保持。446冻结文件中445字节完全不变，唯一授权变化为Gallery/index.html追加overlay，原主逻辑未替换。

624,836条Raw/Working/Thumbnail等冻结路径逐条检查：missing=0、size/mtime变化=0；未对全部raw再做昂贵全量hash，不把stat检查冒称所有raw payload的重新SHA校验。关键Metadata已逐份SHA，原ISO/ELF SHA不变。SQLite `integrity_check=ok`。详细结果 `FUC_ANIMATION_STABILITY.json`、`FUC_BASELINE_FILE_COMPARISON.csv`。

## Q. Failures / Unknown

保留早期GPU screenshot失败、暂停启动/缺存档prompt、临时诊断调用失败日志，以及2e-6 adapter试验超限记录。后续有效结果有独立证据覆盖；不删除失败历史。本轮巨大诊断日志仍在WORK，未混入素材Preservation或复制到轻量交付包。

未确认：其他骨骼/模型、可选mirror/remap、runtime节点附加flag、rotation奇点、全库scale通道数值、0x40消费者、blend全细节、gameplay root运动来源、分离装备/VFX/材质调色、招式/命令语义表。既有32,269结构候选未整体升confirmed，剩余3667片段不导出。GLB的60Hz STEP是帧姿态恢复范围，非连续curve精确承诺。日版Recovery未改动、未并入正式来源。

全部11条PASS门槛在明确的3骨骼/9片段范围成立；本轮成功指标是可复現链，不是全库动画完成率。

## R. Recommended next step

**FAN/AMO/VFX runtime mapping**。先围绕已验证的sir/rin/lan bank和body恢复动画组、装备/效果触发、blend/loop调用语境；再扩展带scale通道/其他flags的第二批验证。保持move语义unknown，尚不进入全库招式命名。

## Deliverables / reproduction

专门索引：`{AMD}` 下的六份要求文件：FUC_MOTION_MODEL_BINDINGS.csv、FUC_MOTION_BONE_BINDINGS.csv、FUC_MOTION_TRACK_SEMANTICS.csv、FUC_RUNTIME_POSE_COMPARISON.csv、FUC_VALIDATED_ANIMATIONS.csv、FUC_ANIMATION_VALIDATION_SUMMARY.json。

可运行复现示例（PowerShell）：

```powershell
& 'E:\\FSN_MASTER_ASSET_WORK\\tools\\python\\Scripts\\python.exe' 'E:\\FSN_MASTER_ASSET_WORK\\scripts\\fuc_motion_evaluator.py' --mot 'E:\\FSN_MASTER_ASSET_LIBRARY\\FateUnlimitedCodesPortable_Europe\\RawExtracted\\Containers\\PSP_GAME\\USRDIR\\data\\fpack\\chr\\sir\\0000.fpk\\chr\\sir\\0000.mot' --clip-index 0 --code sir --time 0.25 --output 'E:\\FSN_MASTER_ASSET_WORK\\fuc\\AnimationValidation\\Runtime\\pose_sir_0_025.json'
```

输出含每node local/world matrix；与 `Runtime/Motion/sir/clip_0000_fraction_050.json` 的runtime world核对。也可用`--skeleton-metadata`及`--sine-lut`显式输入，无需运行模拟器。评估器本身不授予批量export许可；最终gate以validated表为准。

正式报告原路径：`E:\\FSN_MASTER_ASSET_LIBRARY\\Reports\\FUC_ANIMATION_VALIDATION_REPORT.md`。outputs中另有可查看报告、9 GLB+3预览+关键索引/证据的小包；全源、完整debug journal、natural dump仍保存在WORK。包不包含整ISO、EBOOT或整个RawExtracted。
'''
    (L/'Reports/FUC_ANIMATION_VALIDATION_REPORT.md').write_text(report,encoding='utf-8');OUTPUT.mkdir(parents=True,exist_ok=True);(OUTPUT/'FUC_ANIMATION_VALIDATION_REPORT.md').write_text(report,encoding='utf-8')
    for p in [AMD/'FUC_ANIMATION_VALIDATION_SUMMARY.json',AMD/'FUC_VALIDATED_ANIMATIONS.csv']:
        shutil.copy2(p,OUTPUT/p.name)
    for aid in ['FSN259846','FSN258855','FSN258247']:shutil.copy2(L/f'Gallery/animation_previews/{aid}.webm',OUTPUT/(aid+'.webm'))
    package=OUTPUT/'FUC_VALIDATED_ANIMATIONS.zip';manifest=[]
    with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        def add(p,name):
            p=pathlib.Path(p);z.write(p,name);manifest.append(dict(path=name,size=p.stat().st_size,sha256=sha(p)))
        add(OUTPUT/'FUC_ANIMATION_VALIDATION_REPORT.md','FUC_ANIMATION_VALIDATION_REPORT.md')
        for p in AMD.iterdir():
            if p.suffix in ['.csv','.json']:add(p,'Metadata/'+p.name)
        for r in exports:add(r['animated_glb'],'AnimatedModels/'+pathlib.Path(r['animated_glb']).name)
        for aid in ['FSN259846','FSN258855','FSN258247']:add(OUTPUT/(aid+'.webm'),'Previews/'+aid+'.webm')
        for p in (AW/'Playback').glob('*_viewer-validation.json'):add(p,'Evidence/Playback/'+p.name)
        for name in ['POSE_COMPARISON_SUMMARY.json','CHANNEL_COMPARISON_SUMMARY.json','GLB_ADAPTER_VALIDATION.json']:add(AW/'Runtime'/name,'Evidence/'+name)
        for name in ['NATURAL_BANK_SOURCE_VERIFICATION.json','NATURAL_COMPONENT_COMPARISON.json','NATURAL_MOTION_STATE_SUMMARY.json','NATURAL_MOTION_STATE_COMPARISON.csv']:add(AW/'Runtime/Natural'/name,'Evidence/Natural/'+name)
        add(AW/'Playback/GALLERY_UI_REGRESSION.json','Evidence/GALLERY_UI_REGRESSION.json');add(AW/'GLTF_VALIDATOR_REPORT.json','Evidence/GLTF_VALIDATOR_REPORT.json')
        for p in [AW/'Runtime/Natural/SHIRO_RIN_BATTLE.png',AW/'Runtime/Natural/Round2/LANCER_RIN_BATTLE.png']:add(p,'Evidence/'+p.name)
        for p in OUTPUT.glob('FUC_*VALIDATED.jpg'):add(p,'Evidence/'+p.name)
        for name in ['common.py','fuc_common.py','fuc_anim_common.py','fuc_motion_channels.py','fuc_motion_evaluator.py']:add(W/'scripts'/name,'Evaluator/'+name)
        for code in ['sir','rin','lan']:
            add(AW/f'Runtime/Motion/{code}/SKELETON_EVALUATOR_INPUT.json',f'Evaluator/Inputs/{code}/skeleton.json');add(AW/f'Runtime/Motion/{code}/rotation_sine_lut.bin',f'Evaluator/Inputs/{code}/sine_lut.bin')
            mot=EU/f'RawExtracted/Containers/PSP_GAME/USRDIR/data/fpack/chr/{code}/0000.fpk/chr/{code}/0000.mot';add(mot,f'Evaluator/Inputs/{code}/0000.mot')
        z.writestr('Evaluator/README.md','Dependencies: Python 3 + numpy. From Evaluator directory:\n\npython fuc_motion_evaluator.py --mot Inputs/sir/0000.mot --clip-index 0 --skeleton-metadata Inputs/sir/skeleton.json --sine-lut Inputs/sir/sine_lut.bin --time 0.25 --output pose.json\n\nOnly validated subset approved; no automatic export eligibility. Runtime vectors use source direction/twist storage; matrices are column-major. Original library default paths remain supported.\n')
        z.writestr('MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
    with zipfile.ZipFile(package) as z:assert z.testzip() is None
    jsonwrite(OUTPUT/'FUC_DELIVERABLES.json',dict(status=summary['status'],package=str(package),package_bytes=package.stat().st_size,package_sha256=sha(package),entries=len(manifest),report=str(OUTPUT/'FUC_ANIMATION_VALIDATION_REPORT.md')));log('FINAL',summary['status'],package.stat().st_size,len(manifest))
if __name__=='__main__':main()
