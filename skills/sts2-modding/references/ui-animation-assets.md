# UI, animation, VFX, and audio

来源：Visuals 全部；BaseLib 14；Ritsu Basic 02/10/14/17、Gameplay 01/03/05/06/07/12、Utilities 07；[索引](sources.md)。日期 2026-10-12。教程机制 TUTORIAL；本轮无游戏显示/音频复测。

## Scenes and UI

角色/怪物视觉 root 配齐 unique names：Visuals、Bounds、IntentPos、CenterPos，Ritsu 教程另要求 TalkPos；以目标版本 factory 的访问路径为准。Visuals 层用 Sprite2D/AnimatedSprite2D/Spine，AnimationPlayer 是动画控制节点，不假定它继承 Node2D。3D 放透明 SubViewport，检查投影与尺寸。
ScriptManagerBridge.LookupScriptsInAssembly 或 Ritsu EnsureGodotScriptsRegistered 与 scene conversion 是不同用途；自动转换不说明任意 node 结构可用。自定义 NCreatureVisuals 实例应符合 factory 所需 root 类型/构造函数。
能量计数器和选人背景有固定子节点与 unique-name 访问；修改美术时先看原 scene，不改名打断绑定。导出时文本资源转换、.import、path/case 按当前 package 的已工作设置核对，不照教程一概 toggle。
UI 优先复用原生选牌/目标/奖励交互。自建顶栏按钮、toast、右键 action 只在需求需要时加；mouse/controller、焦点、关闭/重开和 canceled choice 共同验证。开发面板不代替公共 UI。
Toast 在 GameReady 后可用。TopBarHandler 的 IsVisible/IsOpen/GetCount 与 OnClick 各自轻量；右键 handler 有 priority/consume，model绑定 IDisposable 需释放。HealthBarForecast/额外 badges 是显示层，不能改变伤害事实；触发 invalidation 才刷新非 DisplayAmount 相关数据。
Config 可 fluent/reflection/schema，控件 binding 与 ModDataStore 生命周期匹配；Write 后 Save 才磁盘持久化。不要为一个简单参数引入全套配置 schema。

## Character animation

Spine 教程指定 4.2.43 与 Godot extension；实际版本匹配需验证，不保证所有旧骨骼文件可直接导入。原生动画名常见 idle_loop/attack/cast/hurt/die；状态 trigger Idle/Attack/Cast/Hit/Dead 不等同素材动画名，明确映射。
Ritsu VisualCueSet 可 static image/sequence，Build 一次；保持 VisualsPath 和 TryCreateCreatureVisuals。StandardCue/ModAnimStateMachineBuilder 提供 non-Spine 状态/回到 idle；custom SetupCustomCreatureAnimator 使用当前库 signature。death 保留终态，不机械把所有 clip 后继设 idle；连续受击/施法中断与 node 释放须实测。
本机 SOURCE_VERIFIED：CharacterModel.GenerateAnimator(MegaSprite)；新版 Creature 参数/AnimationStates 不适用当前 API。FSN 已有二维 runtime，不以本 Skill 重新创建另一动画系统。
商店 relaxed_loop、休息点 act-specific loops/world procedural cues 与战斗模型独立；反向/多人镜像需检查 parent scale/ControlRoot。Tween 绑定 node、结束 Kill/free，scene退出后不继续回写旧对象。

## VFX and materials

Frame 动画用透明 PNG/SpriteFrames，atlas 用正确 rows/columns/region，减分辨率与可见范围后再看性能。one-shot Finished/timer 销毁；loop/persistent 在作用域结束显式清理。
VfxCmd/AttackCommand.WithHitFx 的 path 解析与缓存依赖当前版本；教程 independent PackedScene cache 是可选方案，不因教程一句“缓存会清掉”重写现有 preloader。只缓存资源，活节点每次实例化；预加载时机不能早于 Godot 资源系统 ready。
用 NCombatRoom CombatVfxContainer 前层 / BackCombatVfxContainer 后层；world/global position 转到正确容器坐标，处理朝向与 ZIndex。重复渲染多个实例时先 Duplicate Material，再设置 shader 参数，否则共享 material 改色影响所有实例。
Particles 的量/寿命/one_shot/emitting/explosiveness 与实际效果长度协调；简单 node scale 不保证粒子模拟范围/参数同步缩放。
Godot canvas_item shader 可 UV/TIME/alpha/noise/rim/outline；screen-reading distortion 需实际 renderer 验证。昂贵采样/blur 控制成本，保留原 transparency。WorldEnvironment 影响整场，修改前保存实际环境参数并在退出恢复，多个效果并发不互相覆盖。
组合原生 VFX 优先读取已存在路径/命令；VfxCmd 通常不返回节点，确需修改实例再用 factory，不 patch 全局返回行为。

## Audio and visual style

FMOD 教程 2.03.06：自建命名空间 bank，保持 Master bank 原样，导出 bank+GUIDs，SFX/music bus routing 决定原生音量控制。Godot export 包含非resource .bank/GUIDs；loose audio 给 FMOD 必须未经 Godot 转码。
Ritsu deferred bank/GUID registration、VirtualFmodEventRegistry 支持事件路径；direct file playback 不自动跟原生音量，virtual event 在开始时采样 bus volume，播放中即时调音需验证。别以“发出 Play 调用”断言用户听到声音。
风格参考用真实游戏构图/比例、轮廓、大色块与动画拆分需求；它不是擅自改用户确认美术方向的许可。卡图 250×190/先古 250×351 是教程参考尺寸，最终检查实际 UI 裁切/可读性。
