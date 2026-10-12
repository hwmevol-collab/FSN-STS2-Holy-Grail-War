namespace RinArcherCore;
public static class GenericSavedRunSignature
{
    public static string? MigrationNotice{get;private set;}
    public static string? MigrationDisplayNotice{get;private set;}
    public static string? ConsumeNotice(){var value=MigrationNotice;MigrationNotice=null;return value;}
    public static void Validate(RunManager __instance)=>ValidateState(__instance.DebugOnlyGetState()!);
    public static void ValidateState(RunState run)
    {
        MigrationNotice=null;MigrationDisplayNotice=null;
        foreach(var p in run.Players.Where(p=>p.Character is RinContractCharacter))
        {
            try{ContractSave.ValidateGameplay(p);}catch(InvalidDataException ex)
            {MigrationNotice=ex.Message;MigrationDisplayNotice=ex.Message;throw;}
            var state=ContractSave.Get(p).Compatibility;if(state.MatrixSignature.Length==0)continue;
            // Reviewed additive 03 -> 04 bugfix migration, only in the new private
            // candidate. No deck/map/RNG/HP transaction is rewritten; unknown saves
            // retain the original fail-closed gate. Original user profile is untouched.
            if(GenericCompatibility.Registry.IsValid&&OS.GetUserDataDir().Contains("RinArcherE2BBugfix-20261009")
                &&FullActRoomSpine.Enabled(p)&&state.MatrixRevision=="E1_MATRIX_AMENDMENT_03"
                &&state.MatrixSignature=="660F7A7934D38643C80795F772CC1662627E9BDB01B1CF2E75A14696BF5828AD"
                &&CompatibilityMatrixFingerprint.Revision=="E1_MATRIX_AMENDMENT_04")
            {
                state.MatrixRevision=CompatibilityMatrixFingerprint.Revision;state.MatrixSignature=CompatibilityMatrixFingerprint.Signature;
                ContractSave.Log(p,"E2B_REVIEWED_ADDITIVE_MATRIX_MIGRATION",new{from="E1_MATRIX_AMENDMENT_03",to=state.MatrixRevision,onlyCompatibilityHeaderChanged=true});
            }
            if(!GenericCompatibility.Registry.IsValid||state.MatrixSignature!=CompatibilityMatrixFingerprint.Signature||state.MatrixRevision!=CompatibilityMatrixFingerprint.Revision)
            {
                MigrationNotice=FsnLoc.Text("UI_51E1EC5B0A2E")+state.MatrixRevision+" / "+state.MatrixSignature+"\nRequired: "+CompatibilityMatrixFingerprint.Revision+" / "+CompatibilityMatrixFingerprint.Signature+"\n"+GenericCompatibility.Registry.FailureReason+FsnLoc.Text("UI_4C395B24163E");
                static string Short(string signature)=>signature[..Math.Min(12,signature.Length)];
                MigrationDisplayNotice=FsnLoc.Text("UI_BB4DE92E9686")+Short(state.MatrixSignature)+FsnLoc.Text("UI_40B842EA6BC2")+Short(CompatibilityMatrixFingerprint.Signature)+FsnLoc.Text("UI_4534E6012B60");
                throw new InvalidDataException(MigrationNotice);
            }
            if(ContractSave.Get(p).RunFlags.GetValueOrDefault(ProductionCompatibility.Flag))ProductionCompatibility.Enable(p);
            else GenericCompatibility.EnableIsolated(p,GenericCompatibility.Registry.Entries.Where(e=>e.Classification is "NATIVE_SAFE" or "GENERIC_ADAPTER").Select(e=>e.ContentId));
        }
    }
}
[HarmonyPatch(typeof(MegaCrit.Sts2.Core.Saves.SaveManager),nameof(MegaCrit.Sts2.Core.Saves.SaveManager.SaveRun))]
public static class GameplayBeforeAutomaticSave
{
    [HarmonyPriority(Priority.First)]
    static void Prefix(){if(RunManager.Instance.DebugOnlyGetState() is {} run)foreach(var p in run.Players.Where(p=>p.Character is RinContractCharacter))ContractSave.ValidateGameplay(p);}
}
[HarmonyPatch(typeof(RunManager),nameof(RunManager.SetUpSavedSingleplayer))]
public static class GenericSaveSignatureBeforeNativeWrite
{
    [HarmonyPriority(Priority.First)]
    static void Prefix(RunState state)=>GenericSavedRunSignature.ValidateState(state);
}
