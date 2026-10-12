using System.Reflection;
using System.Runtime.CompilerServices;
using MegaCrit.Sts2.Core.Modding;
using MegaCrit.Sts2.Core.Hooks;
using MegaCrit.Sts2.Core.Models.CardPools;
using MegaCrit.Sts2.Core.Rooms;
using MegaCrit.Sts2.Core.Nodes.Combat;
using MegaCrit.Sts2.Core.Context;
namespace FateStayNight;
[ModInitializer(nameof(Initialize))]
public static class Entry
{
    public static void Initialize(){new Harmony("Murasame.FateStayNight").PatchAll();GD.Print("[FSN] v0.2.0 initialized for game v0.107.1");}
}
[HarmonyPatch(typeof(ModelDb),nameof(ModelDb.AllCardPools),MethodType.Getter)]
public static class AdditionalFatePoolsPatch
{
    static void Postfix(ref IEnumerable<CardPoolModel> __result){__result=__result.Concat([ModelDb.CardPool<SaberPool>(),ModelDb.CardPool<FateEventPool>()]).Distinct().ToArray();}
}
[HarmonyPatch(typeof(CardModel),nameof(CardModel.Pile),MethodType.Getter)]
public static class FrozenPilePatch
{
    static void Postfix(CardModel __instance,ref CardPile? __result){
        if(__result!=null||!Duo.CardOwners.TryGetValue(__instance,out var owner))return;
        __result=owner.fighter.Piles.Values.Append(owner.fighter.Deck).FirstOrDefault(p=>p.Cards.Contains(__instance));
    }
}
[HarmonyPatch(typeof(CardPileCmd),nameof(CardPileCmd.Add),[typeof(IEnumerable<CardModel>),typeof(CardPile),typeof(CardPilePosition),typeof(AbstractModel),typeof(bool)])]
public static class RoutePilePatch
{
    static bool Prefix(IEnumerable<CardModel> cards,ref CardPile newPile,CardPilePosition position,AbstractModel? clonedBy,ref bool skipVisuals,ref Task<IReadOnlyList<CardPileAddResult>> __result){
        var list=cards.ToList();if(list.Count==0)return true;
        var duo=Duo.For(list[0].Owner);if(duo==null)return true;
        if(newPile.Type==PileType.Deck&&!duo.Switching){
            var accepted=list.Where(c=>duo.ContractActive||!Rules.SaberCard(c)).ToArray();
            foreach(var c in accepted)Duo.CardOwners[c]=(duo,Rules.SaberCard(c)?duo.Saber:duo.Master);
            var groups=accepted.GroupBy(c=>Rules.SaberCard(c)?(duo.IsSaber?duo.Player.Deck:duo.Saber.Deck):(duo.IsSaber?duo.Master.Deck:duo.Player.Deck)).ToArray();
            if(groups.Length!=1||accepted.Length!=list.Count){__result=AddGroups(groups,position,clonedBy,skipVisuals);return false;}
            newPile=groups[0].Key;
        }
        if(Duo.CardOwners.TryGetValue(list[0],out var own)&&own.duo==duo&&own.fighter!=duo.Current&&newPile.IsCombatPile){newPile=own.fighter.Piles[newPile.Type];skipVisuals=true;}
        return true;
    }
    static async Task<IReadOnlyList<CardPileAddResult>> AddGroups(IEnumerable<IGrouping<CardPile,CardModel>> groups,CardPilePosition position,AbstractModel? clonedBy,bool skipVisuals){var results=new List<CardPileAddResult>();foreach(var group in groups)results.AddRange(await CardPileCmd.Add(group,group.Key,position,clonedBy,skipVisuals));return results;}
    static void Postfix(IEnumerable<CardModel> cards,ref Task<IReadOnlyList<CardPileAddResult>> __result){__result=After(__result,cards.ToArray());}
    static async Task<IReadOnlyList<CardPileAddResult>> After(Task<IReadOnlyList<CardPileAddResult>> task,CardModel[] cards){var result=await task;foreach(var d in cards.Select(c=>Duo.For(c.Owner)).OfType<Duo>().Distinct())d.Save();return result;}
}
[HarmonyPatch(typeof(CardPoolModel),nameof(CardPoolModel.GetUnlockedCards))]
public static class BorrowedPoolPatch
{
    static void Postfix(CardPoolModel __instance,ref IEnumerable<CardModel> __result){
        if(__instance is not EmiyaPool)return;
        var player=LocalContext.GetMe(MegaCrit.Sts2.Core.Runs.RunManager.Instance.DebugOnlyGetState());
        var d=Duo.For(player);
        __result=__result.Concat(ModelDb.CardPool<IroncladCardPool>().GetUnlockedCards(player?.UnlockState??MegaCrit.Sts2.Core.Unlocks.UnlockState.all,CardMultiplayerConstraint.SingleplayerOnly))
            .Concat(ModelDb.CardPool<SaberPool>().AllCards).Where(c=>c.Rarity!=CardRarity.Basic&&(!(d?.Seal.Released??false)||!Rules.Linked(c)&&!Rules.SaberCard(c))).DistinctBy(c=>c.Id).ToArray();
    }
}
[HarmonyPatch(typeof(CardModel),nameof(CardModel.SpendResources))]
public static class ReinforceBeforeCostPatch
{
    static void Prefix(CardModel __instance){
        var power=__instance.Owner?.Creature.GetPower<ReinforcePower>();if(power==null||power.Amount<=0)return;
        if(__instance.IsUpgradable)CardCmd.Upgrade(__instance);
        power.SetAmount(power.Amount-1);
        if(power.Amount<=0)power.RemoveInternal();
    }
}
[HarmonyPatch(typeof(CardModel),nameof(CardModel.UpgradeInternal))]
public static class AnalysisUpgradePatch
{
    [ThreadStatic]static bool adding;
    static void Postfix(CardModel __instance){
        if(adding||__instance.Pile==null||__instance.MaxUpgradeLevel<=1||!__instance.IsUpgradable)return;
        var p=__instance.Owner?.Creature.GetPower<AnalysisPower>();if(p==null||p.Used>=p.Amount)return;
        p.Used++;adding=true;try{CardCmd.Upgrade(__instance,MegaCrit.Sts2.Core.Nodes.CommonUi.CardPreviewStyle.None);}finally{adding=false;}
    }
}
[HarmonyPatch(typeof(Creature),nameof(Creature.LoseHpInternal))]
public static class TemporaryLifePatch
{
    static void Prefix(Creature __instance,ref decimal amount){var d=Duo.For(__instance.Player);if(d?.Combat==null||d.Current.TemporaryHp<=0||amount<=0)return;int taken=Math.Min(d.Current.TemporaryHp,(int)amount);d.Current.TemporaryHp-=taken;amount-=taken;Art.RefreshFighter(d);}
}
[HarmonyPatch(typeof(Player),nameof(Player.ToSerializable))]
public static class SaveDuoPatch
{
    static void Prefix(Player __instance){Duo.For(__instance)?.Save();}
    static void Postfix(Player __instance,SerializablePlayer __result){
        if(Duo.For(__instance) is not {} d||!d.IsSaber)return;
        __result.CurrentHp=d.Master.Hp;__result.MaxHp=d.Master.MaxHp;
        __result.Deck=d.Master.Deck.Cards.Select(c=>c.ToSerializable()).ToList();
        __result.Relics=d.Master.Relics.Prepend(d.Seal).Select(r=>r.ToSerializable()).ToList();
    }
}
[HarmonyPatch(typeof(Hook),nameof(Hook.AfterCombatVictory))]
public static class AfterVictoryPatch
{
    static void Postfix(IRunState runState,ref Task __result){__result=Finish(__result,runState);}
    static async Task Finish(Task task,IRunState state){await task;foreach(var p in state.Players)Duo.For(p)?.Finish();}
}
[HarmonyPatch(typeof(CombatRoom),nameof(CombatRoom.OfferRoomEndRewards))]
public static class EscapeRewardPatch
{
    static bool Prefix(CombatRoom __instance,ref Task __result){if(__instance.CombatState.Players.Any(p=>Duo.For(p) is {} d&&(d.Escaping||d.Seal.EscapeRewardsPending))){__result=MegaCrit.Sts2.Core.Nodes.Rooms.NCombatRoom.Instance?.Ui.ProceedWithoutRewards()??Task.CompletedTask;return false;}return true;}
}
[HarmonyPatch(typeof(CardModel),nameof(CardModel.OnPlayWrapper))]
public static class CompleteSwitchingCardPatch
{
    static void Postfix(CardModel __instance,PlayerChoiceContext choiceContext,ref Task __result){if(__instance is Coordination)__result=Complete(__result,__instance,choiceContext);}
    static async Task Complete(Task task,CardModel card,PlayerChoiceContext ctx){await task;if(Duo.For(card.Owner) is {} d)await d.CompleteCard(card,ctx);}
}
[HarmonyPatch(typeof(PlayerCombatState),nameof(PlayerCombatState.HasEnoughResourcesFor))]
public static class ReinforceAffordabilityPatch
{
    static void Prefix(ref CardModel card){
        if(!card.IsUpgradable||card.Owner?.Creature.GetPower<ReinforcePower>()?.Amount is not >0)return;
        card=(CardModel)card.MutableClone();card.UpgradeInternal();card.FinalizeUpgradeInternal();
    }
}
[HarmonyPatch(typeof(CardModel),nameof(CardModel.AfflictInternal))]
public static class ImmortalAfflictPatch
{
    static bool Prefix(CardModel __instance)=>!Rules.Immortal(__instance);
}
[HarmonyPatch(typeof(CardModel),nameof(CardModel.DowngradeInternal))]
public static class ImmortalDowngradePatch
{
    static bool Prefix(CardModel __instance)=>!Rules.Immortal(__instance);
}
[HarmonyPatch(typeof(NIntent),"_Process")]
public static class IntentVisibilityPatch
{
    static readonly ConditionalWeakTable<NIntent,IntentHidden> Hidden=new();
    sealed class IntentHidden{public bool OldVisible;}
    static void Postfix(NIntent __instance){
        var p=LocalContext.GetMe(CombatManager.Instance.DebugOnlyGetState());
        if(p?.GetRelic<EmiyaHouse>()!=null){if(!Hidden.TryGetValue(__instance,out _))Hidden.Add(__instance,new(){OldVisible=__instance.Visible});__instance.Visible=false;}
        else if(Hidden.TryGetValue(__instance,out var old)){__instance.Visible=old.OldVisible;Hidden.Remove(__instance);}
    }
}
[HarmonyPatch(typeof(PlayerCmd),nameof(PlayerCmd.EndTurn))]
public static class EndTurnWindowPatch
{
    static void Prefix(Player player){if(Duo.For(player) is {} d)d.BetweenTurns=true;}
}
