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
        foreach(var p in combat.Players.Where(p=>p.Character is RinContractCharacter))
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
[HarmonyPatch(typeof(CardPileCmd),nameof(CardPileCmd.Add),[typeof(IEnumerable<CardModel>),typeof(CardPile),typeof(CardPilePosition),typeof(AbstractModel),typeof(bool)])]
public static class OwnerPileRouteHook
{
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
    static void Prefix(CardModel __instance)
    {
        if(__instance is not StarterCard c)return;
        var d=ContractRuntime.For(c.Owner)??throw new InvalidOperationException("Missing contract");
        if(d.Active.CharacterId!=c.OwnerCharacterId||!d.CommitManaCost(c.OwnerCharacterId,c.PrintedManaCost,c.PrintedManaCost))throw new InvalidOperationException("Invalid owner/mana payment");
        d.Log("CARD_PLAYED",new{card=c.SourceCardId,cardOwner=c.OwnerCharacterId,instanceId=c.InstanceId});
    }
}
[HarmonyPatch(typeof(CardModel),nameof(CardModel.IsValidTarget))]
public static class FrontCardTargetHook
{
    static void Postfix(CardModel __instance,Creature target,ref bool __result)
    {
        if(__instance is StarterCard c&&c.Type==CardType.Attack&&ContractRuntime.For(c.Owner)?.Enemy is {} enemy)__result&=target==enemy.Active;
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
    static void Postfix(Creature creature,ref Task __result)
    {
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
        if(__instance.cmd!="RinArcherCore/Switch/v1")return true;
        __result=new SwitchAction(ContractRuntime.For(player)??throw new InvalidOperationException("Switch replay has no contract"));return false;
    }
}
