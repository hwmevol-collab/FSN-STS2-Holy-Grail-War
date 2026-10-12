using System.Runtime.CompilerServices;
using MegaCrit.Sts2.Core.GameActions;
using MegaCrit.Sts2.Core.Entities.Multiplayer;
namespace RinArcherCore;
// Gather cancellable choices while the native card is still in Hand, before SpendResources.
[HarmonyPatch(typeof(PlayCardAction),"ExecuteAction")]
public static class AlphaPrePlayHook
{
    static bool Prefix(PlayCardAction __instance,ref Task __result)
    {
        var card=__instance.NetCombatCard.ToCardModel();
        if(card is not StarterCard c||!GameplayCatalog.Cards.ContainsKey(c.SourceCardId)||ContractRuntime.For(card.Owner)==null)return true;
        __result=Choose(__instance,card);return false;
    }
    static async Task Choose(PlayCardAction action,CardModel card)
    {
        if(card.Pile?.Type!=PileType.Hand||!card.CanPlay(out _,out _)){action.Cancel();return;}
        var c=(StarterCard)card;
        if(!await GameplayChoice.Prepare(c,action.Target)){c.Plan=null;action.Cancel();return;}
        try{await Original(action);}finally{c.Plan=null;if(card is Trace t)t.PreparedArmId=null;if(card is Hrunting arm)arm.PreparedTarget=null;if(card is AlphaRewardCard r)r.ClearChoice();}
    }
    [HarmonyReversePatch]
    [HarmonyPatch(typeof(PlayCardAction),"ExecuteAction")]
    [MethodImpl(MethodImplOptions.NoInlining)]
    static Task Original(PlayCardAction instance)=>throw new NotImplementedException("Harmony reverse patch");
}
public sealed class QaAlphaAction(ContractRuntime d,bool suppress):GameAction
{
    public override ulong OwnerId=>d.Player.NetId;
    public override GameActionType ActionType=>GameActionType.CombatPlayPhaseOnly;
    protected override Task ExecuteAction(){if(d.Enemy==null)throw new InvalidOperationException("QA-only action requires explicit QA encounter");if(suppress)d.QaSuppressField();else d.QaGuardMaster();return Task.CompletedTask;}
    public override INetAction ToNetAction()=>new MegaCrit.Sts2.Core.DevConsole.NetConsoleCmdGameAction{cmd=suppress?"RinArcherCore/QA_SUPPRESS_FIELD":"RinArcherCore/QA_GUARD_MASTER_ACTION",inCombat=true};
}
// Native ingress, before block/HP/hooks: covers QA resolver and ordinary AttackCommand damage.
#if GAME_0107
[HarmonyPatch(typeof(CreatureCmd),nameof(CreatureCmd.Damage),[typeof(PlayerChoiceContext),typeof(IEnumerable<Creature>),typeof(decimal),typeof(ValueProp),typeof(Creature),typeof(CardModel)])]
#else
[HarmonyPatch(typeof(CreatureCmd),nameof(CreatureCmd.Damage),[typeof(PlayerChoiceContext),typeof(IEnumerable<Creature>),typeof(decimal),typeof(ValueProp),typeof(Creature),typeof(CardModel),typeof(CardPlay)])]
#endif
public static class AlphaDamageIngress
{
    static void Prefix(ref IEnumerable<Creature> targets,ref decimal amount,ValueProp props,Creature? dealer)
    {
        var list=targets.ToArray();if(list.Length==0)return;
        var d=list[0].CombatState?.Players.Select(ContractRuntime.For).OfType<ContractRuntime>().FirstOrDefault();if(d==null||d.Finished)return;
        bool attack=props.HasFlag(ValueProp.Move)&&!props.HasFlag(ValueProp.Unpowered)&&dealer!=null&&dealer.IsAlive;
        int pressure=FieldStatus.Pressure(d,dealer,attack);amount+=pressure;
        if(pressure!=0)d.Log("FIELD_PRESSURE_DAMAGE",new{bonus=pressure,amount});
        // Do not Distinct: BOTH with a guard still consists of two separately resolved hits.
        targets=list.Select(t=>d.Intercept(t,dealer,attack)).ToArray();
    }
}
[HarmonyPatch]
public static class ArmFateHook
{
    static System.Reflection.MethodBase TargetMethod()=>GameApi.PileAdd;
    static void Prefix(IEnumerable<CardModel> cards,CardPile newPile)
    {
        if(cards.Any(c=>c is ProjectedArm)&&(newPile.Type==PileType.Deck||newPile.Type==CardBanks.ArcherDeck.PileType))throw new InvalidOperationException("PROJECTED_PERMANENT_ISOLATION");
        foreach(var reward in cards.OfType<AlphaRewardCard>())
        {if(reward.Owner?.Character is not RinContractCharacter)throw new InvalidOperationException("ALPHA_REWARD_OUTSIDE_OWNER_CONTRACT");if(newPile.Type==CardBanks.ArcherDeck.PileType&&reward.OwnerCharacterId!="CHAR_ARCHER")throw new InvalidOperationException("ALPHA_REWARD_WRONG_OWNER_DECK");}
    }
    static void Postfix(IEnumerable<CardModel> cards,CardPile newPile,ref Task<IReadOnlyList<CardPileAddResult>> __result)=>__result=After(__result,cards.ToArray(),newPile);
    static async Task<IReadOnlyList<CardPileAddResult>> After(Task<IReadOnlyList<CardPileAddResult>> original,CardModel[] cards,CardPile pile)
    {
        var result=await original;
        foreach(var arm in cards.OfType<ProjectedArm>())
        {
            var d=ContractRuntime.For(arm.Owner);if(d==null||d.Switching)continue;
            string? fate=pile==d.Archer.Exhaust?"EXHAUSTED":pile==d.Archer.Discard?"DISCARDED":null;
            if(fate!=null)d.Log(fate,arm.Metadata());
            if(fate=="EXHAUSTED")await d.ProjectedExhaust(d.EventChoiceContext(),arm,arm.ExhaustSource);
        }
        return result;
    }
}
