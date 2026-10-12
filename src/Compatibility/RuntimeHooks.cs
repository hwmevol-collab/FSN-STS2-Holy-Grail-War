using MegaCrit.Sts2.Core.Hooks;
using MegaCrit.Sts2.Core.Models;
using MegaCrit.Sts2.Core.Nodes.Combat;
using MegaCrit.Sts2.Core.Commands.Builders;
using MegaCrit.Sts2.Core.Entities.Actions;
using MegaCrit.Sts2.Core.Entities.Multiplayer;
using MegaCrit.Sts2.Core.GameActions;
using MegaCrit.Sts2.Core.TestSupport;
namespace RinArcherCore;
[HarmonyPatch(typeof(Hook),nameof(Hook.BeforeCombatStart))]
public static class InitializeContractHook
{
    static void Postfix(CombatState combatState,ref Task __result)=>__result=Initialize(__result,combatState);
    static async Task Initialize(Task original,CombatState combat)
    {
        await original;
        foreach(var p in combat.Players.Where(p=>p.Character is RinContractCharacter&&!GenericCompatibility.Enabled(p)))
        {
            var d=await ContractRuntime.Initialize(p,combat,new ThrowingPlayerChoiceContext());
            var selected=TestMode.IsOn?"CHAR_ARCHER":await CoreHud.ChooseStarting(d);
            d.SelectStartingActive(selected);
            if(!TestMode.IsOn)CoreHud.Attach(d);
        }
    }
}
[HarmonyPatch(typeof(CombatManager),"StartTurn")]
public static class ContractTurnBeginHook
{
    static void Prefix(CombatManager __instance)
    {
        if(__instance.DebugOnlyGetState() is not {} state||state.CurrentSide!=CombatSide.Player)return;
        foreach(var p in state.Players)ContractRuntime.For(p)?.BeginSharedTurn();
    }
}
[HarmonyPatch(typeof(CombatManager),"SetupPlayerTurn")]
public static class ContractTurnSetupHook
{
    static bool Prefix(Player player,HookPlayerChoiceContext playerChoiceContext,ref Task __result)
    {
        if(ContractRuntime.For(player) is not {} d)return true;
        __result=Setup(d,playerChoiceContext);return false;
    }
    static async Task Setup(ContractRuntime d,PlayerChoiceContext ctx)
    {
        if(GenericCompatibility.Enabled(d.Player))await Hook.AfterEnergyReset(d.Combat,d.Player);
        await Hook.AfterSideTurnStart(d.Combat,CombatSide.Player,d.Combat.Allies);
        if(d.Finished)return;
        await Hook.BeforeHandDraw(d.Combat,d.Player,ctx);
        await d.SetupActiveHand(ctx);
        await Hook.AfterPlayerTurnStart(d.Combat,ctx,d.Player);
    }
}
[HarmonyPatch(typeof(Hook),nameof(Hook.AfterSideTurnStart))]
public static class ContractStartStatusOrderHook
{
    static bool Prefix(ICombatState combatState,CombatSide side,ref Task __result)
    {
        if(side!=CombatSide.Player||combatState.Players.Any(p=>p.Character is not RinContractCharacter))return true;
        var contracts=combatState.Players.Select(ContractRuntime.For).OfType<ContractRuntime>().ToArray();
        if(contracts.Length==0||contracts.Any(d=>d.Turn==0))return true;
        if(contracts.All(d=>d.StartStatusesAppliedTurn==d.Turn)){__result=Task.CompletedTask;return false;}
        foreach(var d in contracts)d.StartStatusesAppliedTurn=d.Turn;
        return true;
    }
}

// Native player-turn end participants contain Player.Creature only (Rin).
// Both real Contract bodies share this clock. Expand the participant identity
// once; dispatch the original hooks once, preserving native heal/decrement order.
[HarmonyPatch]
public static class ContractEndStatusParticipants
{
    static IEnumerable<System.Reflection.MethodBase> TargetMethods()
#if GAME_0107
        =>new[]{AccessTools.Method(typeof(Hook),nameof(Hook.BeforeTurnEnd)),AccessTools.Method(typeof(Hook),nameof(Hook.AfterTurnEnd))};
#else
        =>new[]{AccessTools.Method(typeof(Hook),nameof(Hook.BeforeSideTurnEnd)),AccessTools.Method(typeof(Hook),nameof(Hook.AfterSideTurnEnd))};
#endif
    static void Prefix(CombatSide side,ref IEnumerable<Creature> participants)
    {
        if(side!=CombatSide.Player)return;
        var original=participants.ToArray();
        participants=original.Concat(original.Select(ContractRuntime.For).OfType<ContractRuntime>()
            .Where(d=>!d.Finished).SelectMany(d=>new[]{d.Rin.Creature,d.Archer.Creature})).Distinct().ToArray();
    }
}
[HarmonyPatch(typeof(Creature),nameof(Creature.AfterTurnStart))]
public static class ContractBlockClearOrderHook
{
    static bool Prefix(Creature __instance,CombatSide side,ref Task __result)
    {
        if(side!=CombatSide.Player||ContractRuntime.For(__instance)==null)return true;
        // Both members were cleared before status hooks by BeginSharedTurn. Preserve any
        // block those hooks grant; reserve still participates in every native status hook.
        __result=Task.CompletedTask;return false;
    }
}
[HarmonyPatch]
public static class OwnerPileRouteHook
{
    static System.Reflection.MethodBase TargetMethod()=>GameApi.PileAdd;
    static bool Prefix(IEnumerable<CardModel> cards,ref CardPile newPile,ref bool skipVisuals)
    {
        var list=cards.ToArray();if(list.Length==0||list[0] is not StarterCard first||ContractRuntime.For(first.Owner) is not {} d||d.Switching)return true;
        if(list.Any(c=>c is not StarterCard s||s.OwnerCharacterId!=first.OwnerCharacterId))throw new InvalidOperationException("Mixed owner pile operation rejected");
        var owner=d.Member(first.OwnerCharacterId);
        if(newPile.Type==PileType.Deck)newPile=owner.Deck;
        else if(d.PileTypes.Contains(newPile.Type)&&owner!=d.Active){newPile=owner.Pile(newPile.Type);skipVisuals=true;}
        return true;
    }
}
[HarmonyPatch(typeof(CardModel),nameof(CardModel.SpendResources))]
public static class ContractManaPaymentHook
{
    static void Prefix(CardModel __instance,out bool __state)
    {
        __state=false;if(__instance is not StarterCard c)return;
        var d=ContractRuntime.For(c.Owner)??throw new InvalidOperationException("Missing contract");
        int before=c.ModifiedManaCost;bool eligible=c.OwnerCharacterId=="CHAR_ARCHER"&&c.PrintedManaCost==1&&before==1&&d.IndependentActionAvailable;
        int final=d.EffectiveManaCost(c.OwnerCharacterId,c.PrintedManaCost,before);
        var plan=c.Plan??new GameplayPlayPlan();
        if(c.Plan!=null&&!GameplayRules.ValidPlan(d,c,plan))throw new InvalidOperationException(FsnLoc.Text("UI_714DE3FDD8D0"));
        bool discount=GameplayEnergyDiscount.Eligible(d,c);
        int manaBefore=d.Mana,energyPaid=c.EnergyCost.GetAmountToSpend();
        if(d.Active.CharacterId!=c.OwnerCharacterId||!d.CanSpendMana(final+plan.AdditionalMana)||!d.CommitManaCost(c.OwnerCharacterId,c.PrintedManaCost,before))throw new InvalidOperationException("Invalid owner/mana payment");
        __state=eligible;d.RecordPayment(c,manaBefore,energyPaid,final+plan.AdditionalMana,eligible,discount);
        if(!d.SpendMana(plan.AdditionalMana))throw new InvalidOperationException("Additional Mana unavailable");
        for(int i=0;i<plan.DirectJewels;i++)if(!d.DirectJewelConsume(c))throw new InvalidOperationException("Direct Jewel unavailable");
        if(plan.Boost&&!d.UseJewelBoost(c,true))throw new InvalidOperationException("Jewel Boost unavailable");
        if(c is ProjectedArm arm)d.Log("PLAYED",new{instanceId=arm.InstanceId,armId=arm.ArmId,arm.Reinforced,printedManaCost=c.PrintedManaCost,instanceManaDiscount=arm.ManaDiscount,temporaryManaDiscount=arm.TemporaryManaDiscount,finalManaCostWhenPlayed=final,independentActionEligible=eligible,independentActionTriggered=eligible,manaBeforeIA=before,manaAfterIA=final});
        d.Log("CARD_PLAYED",new{card=c.SourceCardId,cardOwner=c.OwnerCharacterId,instanceId=c.InstanceId});
    }
    static void Postfix(CardModel __instance,bool __state,ref Task<(int,int)> __result){if(__instance is StarterCard c)__result=After(__result,ContractRuntime.For(c.Owner)!,c,__state);}
    static async Task<(int,int)> After(Task<(int,int)> task,ContractRuntime d,StarterCard c,bool ia)
    {var result=await task;if(ia)await d.IaEngineBlock();var r=d.Receipt(c);if(r.U12Tuning&&r.Plan.ReserveMember is {} member&&r.Plan.ReserveCards.Length>0)await d.Tune(d.EventChoiceContext(),d.Member(member),r.Plan.ReserveCards);return result;}
}
[HarmonyPatch(typeof(CardModel),nameof(CardModel.IsValidTarget))]
public static class FrontCardTargetHook
{
    static void Postfix(CardModel __instance,Creature target,ref bool __result)
    {
        if(__instance is StarterCard c&&c.Type==CardType.Attack&&c.TargetType==TargetType.AnyEnemy&&ContractRuntime.For(c.Owner)?.Enemy is {} enemy)__result&=target==enemy.Active;
    }
}
[HarmonyPatch(typeof(AttackCommand),"GetPossibleTargets")]
public static class OrdinaryFrontHook
{
    static void Postfix(AttackCommand __instance,ref IReadOnlyList<Creature> __result)
    {
        if(__instance.Attacker?.IsEnemy!=true||__instance.IsMultiTargeted)return;
        __result=__result.Select(c=>ContractRuntime.For(c)?.Active.Creature??c).Distinct().ToArray();
    }
}
[HarmonyPatch(typeof(Hook),nameof(Hook.AfterDeath))]
public static class ContractDeathHook
{
    static void Postfix(Creature creature,bool wasRemovalPrevented,ref Task __result)
    {
        // Native prevention heals after AfterDeath(true); HP is temporarily zero here.
        if(wasRemovalPrevented)return;
        var d=ContractRuntime.For(creature)??creature.CombatState?.Players.Select(ContractRuntime.For).OfType<ContractRuntime>().FirstOrDefault(d=>d.Enemy?.Master==creature||d.Enemy?.Servant==creature);
        if(d!=null)__result=Check(__result,d,new ThrowingPlayerChoiceContext());
    }
    static async Task Check(Task task,ContractRuntime d,PlayerChoiceContext ctx){await task;await d.CheckLethal(ctx);}
}
[HarmonyPatch(typeof(Hook),nameof(Hook.AfterCombatEnd))]
public static class ContractEndHook
{
    static void Postfix(ICombatState combatState){foreach(var p in combatState.Players)ContractRuntime.For(p)?.Finish();}
}
public sealed class SwitchAction(ContractRuntime contract):GameAction
{
    public override ulong OwnerId=>contract.Player.NetId;
    public override GameActionType ActionType=>GameActionType.CombatPlayPhaseOnly;
    protected override async Task ExecuteAction()=>await contract.Switch();
    public override INetAction ToNetAction()=>new MegaCrit.Sts2.Core.DevConsole.NetConsoleCmdGameAction{cmd="RinArcherCore/Switch/v1",inCombat=true};
}
[HarmonyPatch(typeof(MegaCrit.Sts2.Core.DevConsole.NetConsoleCmdGameAction),nameof(MegaCrit.Sts2.Core.DevConsole.NetConsoleCmdGameAction.ToGameAction))]
public static class SwitchReplayHook
{
    static bool Prefix(MegaCrit.Sts2.Core.DevConsole.NetConsoleCmdGameAction __instance,Player player,ref GameAction __result)
    {
        if(__instance.cmd=="RinArcherCore/QA_RESERVE_DEBUFF_TARGET"){__result=new QaReserveDebuffAction(ContractRuntime.For(player)??throw new InvalidOperationException("QA reserve helper outside contract"));return false;}
        if(__instance.cmd is "RinArcherCore/QA_SUPPRESS_FIELD" or "RinArcherCore/QA_GUARD_MASTER_ACTION")
        {__result=new QaAlphaAction(ContractRuntime.For(player)??throw new InvalidOperationException("QA action outside contract"),__instance.cmd.EndsWith("QA_SUPPRESS_FIELD"));return false;}
        if(__instance.cmd!="RinArcherCore/Switch/v1")return true;
        __result=new SwitchAction(ContractRuntime.For(player)??throw new InvalidOperationException("Switch replay has no contract"));return false;
    }
}
