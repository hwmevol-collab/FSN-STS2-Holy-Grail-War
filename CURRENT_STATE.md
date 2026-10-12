# Final project state / 最终状态

2026-10-13. Development and maintenance are on hiatus with no planned update schedule.
开发与维护暂停，暂无恢复计划或时间表。

Final candidate: `0.9.4-game-compat.1-visual-loader-fix-01-dual`; content informational version remains `0.9.4-game-compat.1`.
Windows: exact STS2 v0.107.1 / 59260271 and v0.111.0 / 41cef1ea only (complete SHA/MVID tuples in verified-games.json).
BaseLib 3.4.7; complete multi-version RitsuLib 0.6.7. Android is unsupported; actual startup faults persisted and no further fixes are planned.

The final visual/loader fix had 191 scoped graphical assertions and 21 negative checks per Windows version. These include repeated visuals, hand hover, native deck upgrade preview, Switch, path simulation and identity/payload rejection. They do not prove all vanilla content or a complete natural Run. Human acceptance remains PENDING. Prior event/relic/Wither/Bronze Scales/save checks belong to their specific earlier reports, not a new full regression claim.

The current C# is in src/ and loader/. docs/project/ preserves historical project documents and their original dates/statuses. Root documents supersede old navigation for new developers; old historical acceptances are retained, not promoted.
