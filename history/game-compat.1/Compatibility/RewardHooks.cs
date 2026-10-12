using MegaCrit.Sts2.Core.Hooks;
using MegaCrit.Sts2.Core.Combat.History;
namespace RinArcherCore;
[HarmonyPatch(typeof(CardModel),nameof(CardModel.OnPlayWrapper))]
public static class AlphaResolvedHook
{
    static bool Prefix(CardModel __instance,PlayerChoiceContext choiceContext,Creature? target,bool isAutoPlay,ResourceInfo resources,bool skipCardPileVisuals,ref Task __result)
    {
        if(__instance is not StarterCard c||!GameplayCatalog.Cards.ContainsKey(c.SourceCardId)||ContractRuntime.For(c.Owner) is not {} d)return true;
        __result=Run(c,d,choiceContext,target,isAutoPlay,resources,skipCardPileVisuals);return false;
    }
    static async Task Run(StarterCard c,ContractRuntime d,PlayerChoiceContext ctx,Creature? target,bool auto,ResourceInfo resources,bool visuals)
    {
        if(d.Active.CharacterId!=c.OwnerCharacterId)return;
        if(auto)
        {
            if(!await GameplayChoice.Prepare(c,target,true))return;
            d.RecordPayment(c,d.Mana,0,c.Plan!.AdditionalMana);
            var r=d.Receipt(c);r.IsAutoPlay=true;
            // Native autoplay has no energy or printed-Mana payment and cannot consume IA/U15.
            if(!d.SpendMana(r.Plan.AdditionalMana))return;
            for(int i=0;i<r.Plan.DirectJewels;i++)if(!d.DirectJewelConsume(c))return;
            if(r.Plan.Boost&&!d.UseJewelBoost(c,true))return;
            if(r.U12Tuning&&r.Plan.ReserveMember is {} member&&r.Plan.ReserveCards.Length>0)await d.Tune(ctx,d.Member(member),r.Plan.ReserveCards);
        }
        d.Receipt(c);
        try{await Original(c,ctx,target,auto,resources,visuals);}
        finally{d.CompleteAlphaPlay(c);c.Plan=null;}
    }
    [HarmonyReversePatch]
    [HarmonyPatch(typeof(CardModel),nameof(CardModel.OnPlayWrapper))]
    [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.NoInlining)]
    static Task Original(CardModel instance,PlayerChoiceContext choiceContext,Creature? target,bool isAutoPlay,ResourceInfo resources,bool skipCardPileVisuals)=>throw new NotImplementedException();
}
// This event is emitted after the direct effect and attachments actually finish,
// including lethal cards for which native AfterCardPlayed is intentionally skipped.
[HarmonyPatch(typeof(CombatHistory),nameof(CombatHistory.CardPlayFinished))]
public static class GameplaySuccessfulCardEvent
{static void Postfix(CardPlay cardPlay)=>ContractRuntime.For(cardPlay.Card.Owner)?.NativePlayFinished(cardPlay);}
[HarmonyPatch(typeof(Hook),nameof(Hook.AfterCardPlayed))]
public static class GameplayAfterSuccessfulCard
{
    static void Postfix(PlayerChoiceContext choiceContext,CardPlay cardPlay,ref Task __result)
    {if(ContractRuntime.For(cardPlay.Card.Owner) is {} d)__result=After(__result,d,choiceContext,cardPlay);}
    static async Task After(Task original,ContractRuntime d,PlayerChoiceContext ctx,CardPlay play){await original;await d.SettleSuccessfulPlay(ctx,play);}
}
#if GAME_0107
[HarmonyPatch(typeof(Hook),nameof(Hook.BeforeTurnEnd))]
#else
[HarmonyPatch(typeof(Hook),nameof(Hook.BeforeSideTurnEnd))]
#endif
public static class AlphaEndTurnHook
{static void Prefix(ICombatState combatState,CombatSide side){if(side==CombatSide.Player)foreach(var d in combatState.Players.Select(ContractRuntime.For).OfType<ContractRuntime>())d.EndAlphaTurn();}}
[HarmonyPatch(typeof(CardEnergyCost),nameof(CardEnergyCost.GetWithModifiers))]
public static class GameplayEnergyDiscount
{
    [ThreadStatic] static bool readingBase;
    static readonly System.Reflection.FieldInfo CardField=AccessTools.Field(typeof(CardEnergyCost),"_card");
    public static bool Eligible(ContractRuntime d,StarterCard c)
    {
        if(!d.U15Pending||c.OwnerCharacterId!="CHAR_ARCHER"||c.EnergyCost.CostsX)return false;
        readingBase=true;try{return c.EnergyCost.GetWithModifiers(CostModifiers.All)>0;}finally{readingBase=false;}
    }
    static void Postfix(CardEnergyCost __instance,CostModifiers modifiers,ref int __result)
    {
        if(readingBase||modifiers!=CostModifiers.All||__instance.CostsX||__result<=0)return;
        if(CardField.GetValue(__instance) is StarterCard c&&ContractRuntime.For(c.Owner) is {} d&&c.OwnerCharacterId=="CHAR_ARCHER"&&d.EnergyDiscountActive(c))__result=Math.Max(0,__result-1);
    }
}
