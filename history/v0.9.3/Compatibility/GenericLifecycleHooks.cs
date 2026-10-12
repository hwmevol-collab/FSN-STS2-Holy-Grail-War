using MegaCrit.Sts2.Core.Hooks;
using MegaCrit.Sts2.Core.TestSupport;
namespace RinArcherCore;
[HarmonyPatch(typeof(Hook),nameof(Hook.BeforeCombatStart))]
public static class GenericCombatStartOrder
{
    static readonly AsyncLocal<bool> Dispatching=new();
    static bool Prefix(IRunState runState,CombatState combatState,ref Task __result)
    {
        if(Dispatching.Value||!combatState.Players.Any(GenericCompatibility.Enabled))return true;
        __result=Start(runState,combatState);return false;
    }
    static async Task Start(IRunState run,CombatState combat)
    {
        foreach(var p in combat.Players.Where(GenericCompatibility.Enabled))
        {
            var d=await ContractRuntime.Initialize(p,combat,new ThrowingPlayerChoiceContext());
            string selected=TestMode.IsOn?RunEconomy.Archer:await StartingActiveChoiceUi.Choose(d);
            d.SelectStartingActive(selected);d.DeferActiveOpeningForNativeDraw();if(!TestMode.IsOn)CoreHud.Attach(d);
        }
        Dispatching.Value=true;
        try{await Hook.BeforeCombatStart(run,combat);}
        finally{Dispatching.Value=false;}
    }
}
[HarmonyPatch(typeof(CardPileCmd),nameof(CardPileCmd.Draw),[typeof(PlayerChoiceContext),typeof(decimal),typeof(Player),typeof(bool)])]
public static class GenericActiveDrawGuard
{
    static bool Prefix(PlayerChoiceContext choiceContext,decimal count,Player player,bool fromHandDraw,ref Task<IEnumerable<CardModel>> __result)
    {
        if(CompatibilityExecution.Current is {ContentId:"POTION.SWIFT_POTION",Trigger:"OnUse",PersonalRecipient:{} recipient} selected&&selected.Player==player
            &&ContractRuntime.For(player) is {Finished:false} d&&recipient==d.Reserve.Creature)
        {__result=DrawSelectedHand(d,choiceContext,count);return false;}
        if(CompatibilityExecution.Current is {ActiveSnapshot:{} active} frame&&frame.Player==player&&frame.Rows.Any(r=>r.Scope=="ACTIVE_HAND")&&active.Contract.Active.CharacterId!=active.Member)
            throw new InvalidOperationException("ACTIVE_HAND_TRIGGER_BINDING_CHANGED");
        return true;
    }
    static async Task<IEnumerable<CardModel>> DrawSelectedHand(ContractRuntime d,PlayerChoiceContext ctx,decimal count)
    {
        var member=d.Reserve;var before=member.Hand.Cards.ToHashSet();
        await d.DrawMember(ctx,member,count>0?(int)Math.Ceiling(count):0);
        return member.Hand.Cards.Where(c=>!before.Contains(c)).ToArray();
    }
}
