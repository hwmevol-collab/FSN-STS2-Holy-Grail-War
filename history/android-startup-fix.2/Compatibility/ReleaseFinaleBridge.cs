using MegaCrit.Sts2.Core.Models.Events;
using MegaCrit.Sts2.Core.Entities.Ancients;
namespace RinArcherCore;

// The native ending has no dialogue for custom characters. Supply one line while
// retaining its score animation, ActChangeSynchronizer, WinRun and game-over flow.
public static class ReleaseFinaleBridge
{
    public const string Id="EVENT.THE_ARCHITECT";
    public static bool Ready(Player p)=>FullActRoomSpine.Enabled(p)&&GenericCompatibility.Registry.IsValid
        &&p.RunState.CurrentActIndex==p.RunState.Acts.Count-1;
    public static IReadOnlySet<string> ReadyIds(Player p)=>Ready(p)?new HashSet<string>([Id],StringComparer.Ordinal):new HashSet<string>();
}
[HarmonyPatch(typeof(TheArchitect),"LoadDialogue")]
public static class ReleaseContractFinalDialogue
{
    static bool Prefix(TheArchitect __instance)
    {
        if(__instance.Owner?.Character is not RinContractCharacter)return true;
        if(!ReleaseFinaleBridge.Ready(__instance.Owner))throw new InvalidOperationException("Contract finale requires the native final Act.");
        var dialogue=new AncientDialogue(""){EndAttackers=ArchitectAttackers.Both};
        dialogue.Lines[0].Speaker=AncientDialogueSpeaker.Character;
        dialogue.Lines[0].LineText=EconomyNativeUi.Text(FsnLoc.Text("RELEASE_FINALE_LINE"));
        // Retain the native single-choice dialogue RNG call.
        AccessTools.Property(typeof(TheArchitect),"Dialogue").SetValue(__instance,__instance.Rng.NextItem(new[]{dialogue}));
        ContractSave.Log(__instance.Owner,"RC_NATIVE_FINALE_DIALOGUE",new{nativeScore=true,nativeWinRun=true,contract=ContractRuntime.ContractId});
        return false;
    }
}
