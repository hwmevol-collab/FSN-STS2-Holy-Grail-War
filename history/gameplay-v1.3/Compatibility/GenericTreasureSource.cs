using System.Reflection;
using System.Runtime.CompilerServices;
using MegaCrit.Sts2.Core.Rooms;
using MegaCrit.Sts2.Core.Multiplayer.Game;
using MegaCrit.Sts2.Core.Nodes.Rooms;
using MegaCrit.Sts2.Core.Nodes.CommonUi;
using MegaCrit.Sts2.Core.Nodes.GodotExtensions;
using MegaCrit.Sts2.Core.Helpers;
using MegaCrit.Sts2.Core.Context;
namespace RinArcherCore;
public sealed class CompatibleTreasureState
{
    public string RoomIdentity{get;set;}="";
    public List<string> RolledRelics{get;set;}=[];
    public bool GoldProcessed{get;set;}
    public bool Complete{get;set;}
    public bool Skipped{get;set;}
}
public static class GenericTreasureSource
{
    static readonly ConditionalWeakTable<Player,HashSet<string>> Preselected=new();
    public static CompatibleTreasureState State(Player p)
    {
        // Native noncombat restore can append a history entry. A treasure's
        // identity is the act/map coordinate, never a changing history count.
        var states=ContractSave.Get(p).CompatibleTreasures;string room=$"{p.RunState.CurrentActIndex}:{p.RunState.CurrentMapCoord}";
        var state=states.SingleOrDefault(s=>s.RoomIdentity==room);if(state!=null)return state;
        state=new(){RoomIdentity=room};states.Add(state);return state;
    }
    public static bool ConsumePreselection(Player p,string id)=>Preselected.TryGetValue(p,out var ids)&&ids.Remove(id);
    public static void RememberPreselection(Player p,string id)=>Preselected.GetOrCreateValue(p).Add(id);
    public static void ValidateBudget(Player p)
    {
        if(p.RunState.UnlockState.NumberOfRuns==0&&p.RunState.MapPointHistory.SelectMany(history=>history).Count(point=>point.HasRoomOfType(RoomType.Treasure))<=1
            &&!RelicEligibilityResolver.IsEligible(p,"RELIC.GORGET","NATIVE_FIRST_TREASURE_FIXED_REWARD",true))
            throw new CompatibilitySourceUnavailableException("First-run treasure source has a fixed Custom Gorget reward; unavailable before presentation");
        foreach(var rarity in new[]{MegaCrit.Sts2.Core.Entities.Relics.RelicRarity.Common,MegaCrit.Sts2.Core.Entities.Relics.RelicRarity.Uncommon,MegaCrit.Sts2.Core.Entities.Relics.RelicRarity.Rare})
        {
            var native=NativeSourceBudgetResolver.NativeRelicBranch(p.RunState.SharedRelicGrabBag,rarity,p.RunState,_=>true);
            if(native.Count==0)native=[MegaCrit.Sts2.Core.Factories.RelicFactory.FallbackRelic];
            if(!RelicEligibilityResolver.Prepare(p,"TREASURE_BUDGET:"+rarity,native).CompleteBudget)
                throw new CompatibilitySourceUnavailableException("Treasure source unavailable before generation: "+rarity);
        }
    }
}
[HarmonyPatch(typeof(TreasureRoomRelicSynchronizer),nameof(TreasureRoomRelicSynchronizer.BeginRelicPicking))]
public static class GenericTreasureNativePicking
{
    static bool Prefix(TreasureRoomRelicSynchronizer __instance)
    {
        var p=RunManager.Instance.DebugOnlyGetState()?.Players.FirstOrDefault(GenericCompatibility.Enabled);if(p==null)return true;
        var state=GenericTreasureSource.State(p);
        if(state.Complete)return false;
        if(state.RolledRelics.Count==0){GenericTreasureSource.ValidateBudget(p);return true;}
        var relics=state.RolledRelics.Select(id=>{var parts=id.Split('.');return ModelDb.GetById<RelicModel>(new(parts[0],parts[1]));}).ToList();
        if(relics.Any(r=>!RelicEligibilityResolver.IsEligible(p,r.Id.ToString(),"TREASURE_RESTORE",true)))throw new InvalidDataException("COMPATIBILITY_SAVE_MIGRATION_REQUIRED: treasure contents");
        AccessTools.Field(typeof(TreasureRoomRelicSynchronizer),"_currentRelics").SetValue(__instance,relics);
        var votes=(List<TreasureRoomRelicSynchronizer.PlayerVote>)AccessTools.Field(typeof(TreasureRoomRelicSynchronizer),"_votes").GetValue(__instance)!;
        votes.Clear();foreach(var player in p.RunState.Players)votes.Add(new());
        AccessTools.Field(typeof(TreasureRoomRelicSynchronizer),"_predictedVote").SetValue(__instance,null);return false;
    }
    static void Postfix(TreasureRoomRelicSynchronizer __instance)
    {
        var p=RunManager.Instance.DebugOnlyGetState()?.Players.FirstOrDefault(GenericCompatibility.Enabled);if(p==null)return;
        var state=GenericTreasureSource.State(p);if(state.Complete)return;
        var relics=__instance.CurrentRelics??throw new InvalidOperationException("Treasure source did not produce its complete native reward");
        if(relics.Count!=p.RunState.Players.Count||relics.Any(r=>!RelicEligibilityResolver.IsEligible(p,r.Id.ToString(),"TREASURE_ROLL",true)))throw new CompatibilitySourceUnavailableException("Unprepared treasure reward source");
        state.RolledRelics=relics.Select(r=>r.Id.ToString()).ToList();
    }
}
[HarmonyPatch(typeof(TreasureRoomRelicSynchronizer),nameof(TreasureRoomRelicSynchronizer.PickRelicLocally))]
public static class GenericTreasureMemberBeforeVote
{
    static readonly AsyncLocal<bool> Prepared=new();
    static bool Prefix(TreasureRoomRelicSynchronizer __instance,int? index)
    {
        var p=RunManager.Instance.DebugOnlyGetState()?.Players.FirstOrDefault(GenericCompatibility.Enabled);
        if(p==null||Prepared.Value)return true;
        TaskHelper.RunSafely(Pick(__instance,p,index));return false;
    }
    static async Task Pick(TreasureRoomRelicSynchronizer source,Player p,int? index)
    {
        if(index is int i)
        {
            var relic=source.CurrentRelics![i];
            if(!await GenericMemberEffects.Prepare(p,relic,"AfterObtained"))return;
            GenericTreasureSource.RememberPreselection(p,relic.Id.ToString());
        }
        else{var state=GenericTreasureSource.State(p);state.Complete=true;state.Skipped=true;await ContractSave.Checkpoint(p,"TREASURE_SKIPPED");}
        Prepared.Value=true;try{source.PickRelicLocally(index);}finally{Prepared.Value=false;}
    }
}
[HarmonyPatch(typeof(OneOffSynchronizer),"DoTreasureRoomRewards")]
public static class GenericTreasureGoldOnce
{
    static bool Prefix(Player player,ref Task<int> __result)
    {if(GenericCompatibility.Enabled(player)&&GenericTreasureSource.State(player).GoldProcessed){__result=Task.FromResult(0);return false;}return true;}
    static void Postfix(Player player,ref Task<int> __result)
    {if(GenericCompatibility.Enabled(player))__result=After(__result,player);}
    static async Task<int> After(Task<int> original,Player p)
    {int result=await original;GenericTreasureSource.State(p).GoldProcessed=true;await ContractSave.Checkpoint(p,"TREASURE_GOLD_RESOLVED");return result;}
}
[HarmonyPatch(typeof(RelicCmd),nameof(RelicCmd.Obtain),[typeof(RelicModel),typeof(Player),typeof(int)])]
public static class GenericTreasureAcquisitionCheckpoint
{
    static void Postfix(Player player,RelicModel relic,ref Task<RelicModel> __result)
    {
        if(!GenericCompatibility.Enabled(player)||!GenericMemberEffects.IsPrepared(relic)||player.RunState.CurrentRoom is not TreasureRoom)return;
        __result=After(__result,player,relic);NativeRewardTransactions.Track(__result);
    }
    static async Task<RelicModel> After(Task<RelicModel> original,Player p,RelicModel relic)
    {
        var result=await original;var state=GenericTreasureSource.State(p);
        if(state.RolledRelics.Contains(relic.Id.ToString())){state.Complete=true;await ContractSave.Checkpoint(p,"TREASURE_RELIC_RESOLVED");}
        return result;
    }
}
[HarmonyPatch(typeof(NTreasureRoom),nameof(NTreasureRoom._Ready))]
public static class GenericTreasureCompletedUi
{
    static void Postfix(NTreasureRoom __instance)
    {
        var p=RunManager.Instance.DebugOnlyGetState()?.Players.FirstOrDefault(GenericCompatibility.Enabled);if(p==null||!GenericTreasureSource.State(p).Complete)return;
        __instance.GetNode<NButton>("%Chest").Disable();
        AccessTools.Field(typeof(NTreasureRoom),"_hasChestBeenOpened").SetValue(__instance,true);
        __instance.ProceedButton.UpdateText(NProceedButton.ProceedLoc);__instance.ProceedButton.Enable();
        MegaCrit.Sts2.Core.Nodes.Screens.Map.NMapScreen.Instance?.SetTravelEnabled(true);
    }
}
[HarmonyPatch(typeof(TreasureRoom),nameof(TreasureRoom.EnterInternal))]
public static class GenericTreasureEntryCheckpoint
{
    static void Postfix(ref Task __result)=>__result=After(__result);
    static async Task After(Task original)
    {await original;var p=RunManager.Instance.DebugOnlyGetState()?.Players.FirstOrDefault(GenericCompatibility.Enabled);if(p!=null)await ContractSave.Checkpoint(p,"COMPATIBLE_TREASURE_ENTERED");}
}
