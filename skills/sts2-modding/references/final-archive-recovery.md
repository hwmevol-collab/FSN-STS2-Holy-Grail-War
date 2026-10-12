# Final FSN archive recovery (2026-10-13)

This Skill does not require an E: FSN workspace to function. Generic version/Harmony/lifecycle/ownership/UI/save guidance is in this Skill's own references. baseline.json preserves exact reviewed assembly identities. Historical project paths in fsn-practice.md identify evidence, not executable dependencies.

FSN code/document archive: https://github.com/hwmevol-collab/FSN-STS2-Holy-Grail-War
Workshop: https://steamcommunity.com/sharedfiles/filedetails/?id=3818087982
Final source: src/ + loader/ from 0.9.4-game-compat.1-visual-loader-fix-01-dual. Read its root FINAL_HANDOFF.md before rebuilding. .NET SDK 9; BaseLib 3.4.7; complete multi-version RitsuLib 0.6.7. Only exact Windows v0.107.1 / 59260271 and v0.111.0 / 41cef1ea were reviewed. Full hashes/MVIDs are retained in the repository verified-games.json and this Skill's baseline records.

Cache lesson: native UpdateVisuals→UpdatePortrait can overwrite banner/border Texture/Material without changing model identity. Restore those resource properties before cached return; retain texture objects and layout state. The final Windows checks covered repeat refresh, native hand hover, native upgrade preview and Switch.

Path lesson: content code cannot repair a Loader that fails before loading it. A present absolute Assembly.Location wins; otherwise use validated absolute AppPaths.DataDir/.godot/mono/publish/arm64/sts2.dll. Never trust relative cwd files. Check assembly name + runtime/file MVID, full version/commit/SHA tuple, then content DLL SHA. Windows fixture checks are not Android device acceptance.

Maintenance is on hiatus. Android startup errors remained, support was discontinued, and no Android fixes are planned. Scoped checks do not prove all vanilla content, a complete natural Run or human acceptance. Retrieve detailed evidence from repository docs/project/reports/ or the private ARCHIVE_INDEX.md; do not fabricate unavailable evidence or rely on deleted absolute paths.
