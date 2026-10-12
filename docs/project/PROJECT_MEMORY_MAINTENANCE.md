# Project Memory Maintenance

2026-10-09 / V1。入口 [AGENTS](AGENTS.md)。项目事实在工程文件/原验收；Project Memory 是有来源的
导航与状态投影，不是第二个自动判定玩法 PASS 的数据库。

## Ownership / commands

手工稳定：PROJECT_CONTEXT、DESIGN_BIBLE、AGENTS、maintenance；人工审核的数据：PROJECT_STATE、
[milestones](project-memory/milestones.json)、[capabilities](project-memory/capabilities.json)、
[decisions](project-memory/decisions.json)、[debts](project-memory/debts.json)、USER_CONFIRMED input。
自动生成：CURRENT_STATE、MILESTONE_INDEX、ACCEPTANCE_INDEX、COMPATIBILITY_STATE、DECISIONS、
KNOWN_DEBTS、CONTENT_BASELINE、HANDOFF_LATEST。不要直接编辑生成文件；编辑对应权威输入再生成。

在工程根 PowerShell 执行：

```powershell
./Update-ProjectMemory.ps1
./Update-ContentBaseline.ps1
./Validate-ProjectMemory.ps1 -WriteReport -ReportDirectory reports/milestone-e2a-human-qa-closeout/project-memory
python -B project-memory/test_memory.py --report-dir reports/milestone-e2a-human-qa-closeout/project-memory
```

上述报告目录是 E2A Closeout 的本轮示例；未来任务替换为新的独立目录，勿覆盖本轮或 V1 已验收输出。

已有 `python`（本机 D:/Python/python.exe）与 PowerShell，不新增软件。Windows PowerShell 5.1 /
PowerShell 7 wrappers 均调用相同 Python 标准库工具。直接入口：
[memory.py](project-memory/memory.py) 的 `generate/content/validate`。默认 validate read-only；
`-WriteReport -ReportDirectory <task-evidence-dir>` 写当前任务 validation/onboarding evidence；
negative QA 使用同一 `--report-dir`。参数未指定时保留 V1 默认路径以兼容旧命令，但未来任务必须指定
新的目录，禁止覆盖已验收历史输出。不启动游戏、不编译、
不导入 production modules、不联网、不安装 MOD、不访问账号凭据。

生成确定性：JSON sorted keys、UTF-8 LF；日期来自 reviewed lastVerified，不用当前时钟改写旧结论。
生成器保留人工状态，不把 retest、engineer、formal closeout 互相升级。源码抽取支持当前明确 grammar，
不执行 C#；Starter/Arms 动态 effect 保留原表达式与 definition reference。形状/accepted distribution
变化时 fail closed，需扩展 parser 并审新验收，不能猜默认数值。

## Update triggers

Engineering milestone 完成：新 immutable report/acceptance 先落盘，再审其 scope，更新 PROJECT_STATE、
milestones、capabilities、debts；生成 CURRENT_STATE / indices / HANDOFF。旧 PASS 不能回退或被新计划掩盖。
Design change：用户明确授权后更新 DESIGN_BIBLE 与 decisions，新 ADR 写 supersedes 和依据，保留旧合同。
Matrix change：用户批准并通过对应 matrix validation 后更新 COMPATIBILITY_STATE 输入/state 与
milestones supersession；保留原版 history。单一 ACTIVE Matrix；readiness 与 native pool 分开。
Human QA：记 USER_CONFIRMED、candidate/SHA、原话/上下文、receivedOn、确知的实际 retest 时间；不知道
则 UNKNOWN。Engineering PASS / retest CONFIRMED_PASS / formal closeout PASS 三栏分开；旧报告 PENDING
不改。正式 closeout 需要新用户任务、新 immutable closeout 文件和验收，V1 不自动执行。
2026-10-09 的新用户任务已授权并完成 E2A Closeout；当前验收见
[MILESTONE_E2A_HUMAN_QA_CLOSEOUT](reports/MILESTONE_E2A_HUMAN_QA_CLOSEOUT.json)。原 USER_CONFIRMED
输入及 UX/manual 历史 PENDING 保持原字节；formal 状态由新 closeout 和 PROJECT_STATE 表达。
真实 regression：新增 BUG debt + 复现/报告链接，生成 HANDOFF；当前 milestone 不得掩盖旧 PASS→FAIL。

关键 source fingerprints 在 [source-fingerprints](project-memory/source-fingerprints.json) 绑定已审文件。
普通 generate 不重新 pin。只有新任务确已产生 accepted source/report 变化，人工核对差异后才更新对应
fingerprint 行与 lastVerified（未变化行保留），同步 capability/latestAcceptance 与来源。首次 `pin-sources`
只允许文件不存在时调用；不得删除 pin 文件来让失败 gate 假通过。游戏 SHA/MVID/version 漂移必须先
重新做兼容验收，不得仅改 fingerprint。paths 缺失、同名 conflicting state、陈旧文档都应失败并记录
MEMORY_SOURCE_CONFLICT。locations 是集中机器配置，其他引用以工程相对路径或 root-key/path 表示。

E2B 本轮以 PARTIAL milestone 交付；已通过的组件和旧合同回归单独见
[component acceptance](reports/milestone-e2b/component-acceptance.json)。仅本轮三项修改模块的
current source fingerprints 更新，并在 source-transition 保留原 SHA 与新依据；原验收和 Candidate
不重写。Validator 以当前 milestone 作用域解释三项 Human 字段，并独立验证 E2A 历史 Closeout，
禁止新 milestone PENDING 回退旧 PASS，也禁止用组件 PASS 升级 E2B 完整 Act。

## Validation / evidence / protection

[state.schema](project-memory/state.schema.json) 是 JSON Schema 2020-12；标准库 validator 完整实现此 schema
使用的 type/required/properties/additionalProperties/const/enum/pattern/minimum/minLength/minItems/
uniqueItems/minProperties/items 子集。未支持的新增 keyword 报错，不静默忽略。新字段需同步 schema。
QA 包含 required files、真实 links/references、deterministic generated output、unique IDs、milestone/
Matrix supersession、actual signed bytes/SHA/MVID/install/candidate、Human QA scope、source freshness 和
从 AGENTS reachable chain 解析 onboarding answers；负向 fixtures 在内存构造，不写原报告/Matrix。

V1 新会话预期答案在 [onboarding-check](project-memory/onboarding-check.json)，未来状态变化应依据新
原验收同步更新；不是通过修改 expected 掩盖缺链。QA 输出只证明记忆一致性，不能代替人类或 gameplay QA。
本轮全部既有工程、payload、证据、正式 mods 与当前 profiles 哈希记录在
[protected-before](reports/project-memory-v1/protected-before.json)；结束独立再哈希与新增/删除集合比较。
保护器 [protection.py](project-memory/protection.py) 的 `before` 拒绝覆盖历史基线；未来任务需新的 dated
baseline，勿复用旧人工试玩前快照。可变用户 profile 自然变化需要单独列出，不回滚存档。
每个 memory patch 完成执行 generate→validate→negative QA；必要时取新保护快照；报告不冒充玩法重测。

## Stop / review

本轮交付报告 [FSN_PROJECT_MEMORY_V1_ACCEPTANCE](reports/FSN_PROJECT_MEMORY_V1_ACCEPTANCE.md)。
未来建议和 current roadmap 不是授权。V1 的原始停止范围仅描述其历史任务。E2A Closeout 完成即
停止，等待新的 E2B 开发指令；不得自动启动 E2B/E2C/Command Spell/Presentation/Workshop。

E2B Blocker Resolution：当前 Matrix 使用完整 Original→01→02 supersession 链，E2A 历史证据验证其自身 Amendment01；新 source pin 只由新 scoped acceptance/source-transition 更新。旧 telemetry incident FAIL 保留，新 dated protection 独立验证。组件/图形自动/实际完整路线/真人结论必须分别维护。

Event Exhaustion Final：Matrix03 历史链 Original→01→02→03；E2A 历史绑定01不迁移。原始失效/败北/QA 中途非法存档证据保留。当前二进制上的 3042 适用旧断言与新增测试分列，126 个旧 Candidate 断言只算历史。每条新 regression 必须指向实际 runtimeBinding，并由 Validator 校验实际 DLL。
