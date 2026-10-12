# Lightweight continual learning

适用：每次 STS2 开发、诊断、评审或迁移任务收尾。用户已授权持续维护本 Skill references；只编辑本 Skill 知识，不写全局 Codex memories，不改历史验收或扩大任务权限。用户明确只读/禁止写入时尊重该限制，在交付中给出待提炼内容。

## A brief check

从刚完成的工作判断是否获得可复用的新 API 用法、patch 技巧、版本差异、调试方法或已验证错误教训。无需另跑研究或测试来凑经验。没有新事实、只有本次数值/文案/状态变化时跳过写入。

有知识时：搜索相关参考的 API/症状/版本 → 合并已有段落或添加短条目 → 写回 UTF-8 → 独立读回修改段落。证据提升更新原条目，不每次追加重复任务日志。已有运行证据不能被新静态检查降级或自动扩展。

可直接编辑 Markdown，短格式：

```text
### Stable topic key / API or symptom
结论与做法：具体可执行修正，包括必要反例。
适用：游戏版本/commit或DLL身份；库版本/compat；工程范围。
状态：API_VERIFIED | SOURCE_VERIFIED | RUNTIME_VERIFIED | TUTORIAL | UNVERIFIED。
依据：教程固定commit链接；或源码path:line+方法；运行结论另附报告/日志路径及构建身份。
验证日期：YYYY-MM-DD；限制：未验证版本、UI或联机场景。
```

API_VERIFIED：实际程序集存在且签名/元数据核对。SOURCE_VERIFIED：对应实际程序集的方法体或项目源码核对。RUNTIME_VERIFIED：对应版本与行为执行证据。TUTORIAL：研究上游但未本机证实。UNVERIFIED：假设/待验证。人类 QA 另写 USER_CONFIRMED 及范围，绝不从自动化推导。一般不留无依据猜测；重要未决问题只留一个短 UNVERIFIED 条目与验证方向。

## Bound the knowledge

- 每个主题一个维护位置；相同 API/版本结论去重，补证据用链接代替长文。
- 只读写本次所属文件，不扫全库。先读当前文件保留并发新增，写后再读；冲突合并，不覆盖另一任务知识。
- 留最小示例、适用条件、一个代表性失败及依据。完整日志、DLL、图片、教程/反编译源码在项目报告或研究缓存，Skill 只链接。
- 每主题尽量不超过 200 行，references 总量目标不超过 120 KiB。超长条目合并成规则与链接，淘汰重复/低价值描述；版本对照保留。此为维护软目标，不能因此停止交付或添加审核流程。
- 实证差异才改结论；弃用内容归并版本对照，不无限追加 changelog。新主题只有能改变未来决策才新建文件并链接入口。

## Persistence

常规收尾读回变更段落即可。仅更改入口 frontmatter/路由/openai.yaml 时用 Codex skill-creator 的 scripts/quick_validate.py。新上下文从同一用户级目录发现 Skill 并读磁盘内容，不能用上一会话总结代替已更新文件。
