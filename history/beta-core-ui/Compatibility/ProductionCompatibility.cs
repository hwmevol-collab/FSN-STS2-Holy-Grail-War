using System.Collections.Frozen;
using MegaCrit.Sts2.Core.Map;
using MegaCrit.Sts2.Core.Rooms;
using MegaCrit.Sts2.Core.Nodes.Screens.Map;
using MegaCrit.Sts2.Core.TestSupport;
namespace RinArcherCore;

public static class ProductionCompatibility
{
    public const string Flag="E2A_GENERIC_COMPATIBILITY";
    static readonly FrozenSet<string> Families=new[]{"ContractEffectResolver","ActiveCharacterEffectResolver","CardOwnerEffectResolver","DamageTargetEffectResolver","MemberTargetResolver","DualDeckCardSelector","DualRewardModifierResolver","RelicEligibilityResolver","PotionEligibilityResolver","EventEligibilityResolver"}.ToFrozenSet(StringComparer.Ordinal);
    static readonly FrozenSet<string> Scopes=new[]{"CONTRACT","ENEMY","ACTIVE_AT_TRIGGER","ACTIVE_HAND","CARD_OWNER","DAMAGE_TARGET","CHOOSE_MEMBER","CHOOSE_DECK","DUAL_DECK_SELECTOR","RANDOM_PERMANENT_CARD_UNION"}.ToFrozenSet(StringComparer.Ordinal);
    public static IReadOnlySet<string> ReadyIds=>GenericCompatibility.Registry.Entries.Where(IsReady).Select(e=>e.ContentId).ToFrozenSet(StringComparer.Ordinal);
    public static bool IsReady(CompatibilityContent e)=>GenericCompatibility.Registry.IsValid&&e.Recommendation==VanillaCompatibilityRegistry.GenericRecommendation
        &&e.Classification is "NATIVE_SAFE" or "GENERIC_ADAPTER"&&e.AdapterFamilies.All(Families.Contains)
        &&e.Effects.All(r=>Scopes.Contains(r.Scope)&&(r.AdapterFamily==null||Families.Contains(r.AdapterFamily)));
    public static void Enable(Player p)
    {
        ContractEffectResolver.RequireContract(p);var state=ContractSave.Get(p);
        // Keep the capability gate even on version drift; eligibility then fails closed.
        state.RunFlags[Flag]=true;
        if(!GenericCompatibility.Registry.IsValid)throw new InvalidDataException("VANILLA_COMPATIBILITY_VERSION_MISMATCH: "+GenericCompatibility.Registry.FailureReason);
        if(state.Compatibility.MatrixSignature.Length>0&&(state.Compatibility.MatrixSignature!=CompatibilityMatrixFingerprint.Signature||state.Compatibility.MatrixRevision!=CompatibilityMatrixFingerprint.Revision))
            throw new InvalidDataException("COMPATIBILITY_SAVE_MIGRATION_REQUIRED: save preserved; reviewed matrix migration is required.");
        state.Compatibility.MatrixSignature=CompatibilityMatrixFingerprint.Signature;state.Compatibility.MatrixRevision=CompatibilityMatrixFingerprint.Revision;
        GenericCompatibility.ClearIsolated(p);
    }
    public static bool IsPublic(RunState? run)=>run?.Players.Any(p=>p.Character is RinContractCharacter&&ContractSave.Get(p).RunFlags.GetValueOrDefault(Flag))==true;
}
[HarmonyPatch(typeof(RunManager),"InitializeNewRun")]
public static class GenericPublicRunInitialization
{
    [HarmonyPriority(Priority.Last)]
    static void Postfix(RunManager __instance)
    {
        if(TestMode.IsOn||D1Run.Creating||D2Run.Creating||E2ARun.Creating||PublicUiMode.CreatingDebugRun||FullActIndependentRunInitialization.Requested())return;
        foreach(var p in __instance.DebugOnlyGetState()!.Players.Where(p=>p.Character is RinContractCharacter))
        {ProductionCompatibility.Enable(p);((RunState)p.RunState).ExtraFields.StartedWithNeow=false;ContractSave.Get(p).RunFlags[PublicUiMode.Flag]=true;ContractSave.Sync(p);}
    }
}
[HarmonyPatch(typeof(RunManager),nameof(RunManager.GenerateMap))]
public static class GenericPublicBoundedMap
{
    static void Postfix(RunManager __instance,ref Task __result){if(ProductionCompatibility.IsPublic(__instance.DebugOnlyGetState())&&!FullActRoomSpine.Enabled(__instance.DebugOnlyGetState()))__result=After(__result,__instance);}
    static async Task After(Task original,RunManager manager)
    {
        await original;var run=manager.DebugOnlyGetState()!;
        // The vertical slice stays bounded; no Boss/Elite/Unknown/Act transition.
        if(run.Map is not SavedActMap)run.Map=new E2AActMap(run.Map!.GetRowCount(),optionalServices:true);
        NMapScreen.Instance?.SetMap(run.Map,run.Rng.Seed,true);NMapScreen.Instance?.SetTravelEnabled(true);
    }
}
