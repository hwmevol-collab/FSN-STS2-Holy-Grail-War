using MegaCrit.Sts2.Core.Hooks;
using MegaCrit.Sts2.Core.Extensions;
namespace RinArcherCore;
// The existing member banks remain authoritative. No active pointer or pile swap.
public sealed partial class ContractRuntime
{
    public PlayerChoiceContext EventChoiceContext()=>MegaCrit.Sts2.Core.TestSupport.TestMode.IsOn?new ThrowingPlayerChoiceContext():
        RunManager.Instance.ActionExecutor.CurrentlyRunningAction is {} action?new GameActionPlayerChoiceContext(action):
        new HookPlayerChoiceContext(Player,MegaCrit.Sts2.Core.Context.LocalContext.NetId??Player.NetId,MegaCrit.Sts2.Core.Entities.Multiplayer.GameActionType.Combat);
    public readonly HashSet<string> TuningUsedByMember=[];
    public CardModel[] TuningCards(CharacterRuntime member,CardModel? source=null)=>member.Hand.Cards
        .Where(c=>c!=source&&c.Owner==Player&&!c.IsSlyThisTurn&&
            (c is StarterCard owned&&owned.OwnerCharacterId==member.CharacterId||GenericCombatCardOwnership.Get(c)?.Member==member.CharacterId)).ToArray();
    public bool CanTune(CharacterRuntime member,CardModel? source=null)=>TuningCards(member,source).Length>0;
    public async Task<bool> Tune(PlayerChoiceContext ctx,CharacterRuntime member,IReadOnlyList<CardModel> selected)
    {
        if(selected.Count==0)return false;
        if(!CanTune(member)||selected.Distinct().Count()!=selected.Count||selected.Any(c=>!TuningCards(member).Contains(c)))
            throw new InvalidOperationException("手牌整理所选真实实例已失效");
        TuningUsedByMember.Add(member.CharacterId); // Mark before native callbacks can re-enter.
        await DiscardMember(ctx,member,selected,selected.Count);
        Log("HAND_TUNING",new{member=member.CharacterId,selected=selected.Select(c=>c is StarterCard s?s.InstanceId:GenericCombatCardOwnership.Get(c)!.InstanceId)});
        return true;
    }
    public async Task DiscardMember(PlayerChoiceContext ctx,CharacterRuntime member,IReadOnlyList<CardModel> selected,int draw)
    {
        if(selected.Count==0||selected.Any(c=>!TuningCards(member).Contains(c)))throw new InvalidOperationException("非法弃牌实例");
        if(member.IsActive){await CardCmd.DiscardAndDraw(ctx,selected,draw);return;}
        using var scope=CompatibilityExecution.Bind(new(Player,"CONTRACT_HAND_TUNING","DiscardAndDraw",[],member.Creature,null));
        foreach(var card in selected)
        {
            await CardPileCmd.Add(card,member.Discard,skipVisuals:true);
            CombatManager.Instance.History.CardDiscarded(Combat,card);
            await Hook.AfterCardDiscarded(Combat,ctx,card);
        }
        member.Discard.InvokeContentsChanged();
        await DrawMember(ctx,member,draw);
    }
    public async Task DrawMember(PlayerChoiceContext ctx,CharacterRuntime member,int count)
    {
        if(Finished||CombatManager.Instance.IsOverOrEnding||count<=0)return;
        if(member.IsActive){await CardPileCmd.Draw(ctx,count,Player);return;}
        using var scope=CompatibilityExecution.Bind(new(Player,"CONTRACT_MEMBER_DRAW","Draw",[],member.Creature,null));
        if(!Hook.ShouldDraw(Combat,Player,false,out var preventer)){await Hook.AfterPreventingDraw(Combat,preventer!);Log("MEMBER_DRAW_BLOCKED",new{member=member.CharacterId});return;}
        for(int i=0;i<count&&!Finished&&!CombatManager.Instance.IsOverOrEnding;i++)
        {
            if(member.Hand.Cards.Count>=CardPile.MaxCardsInHand){Log("MEMBER_HAND_FULL",new{member=member.CharacterId});break;}
            if(member.DrawPile.IsEmpty&&!member.Discard.IsEmpty)
            {
                var cards=member.Discard.Cards.ToList();cards.StableShuffle(Player.RunState.Rng.Shuffle);
                Hook.ModifyShuffleOrder(Combat,Player,cards,isInitialShuffle:false);
                foreach(var card in cards)await CardPileCmd.Add(card,member.DrawPile,skipVisuals:true);
                await Hook.AfterShuffle(Combat,ctx,Player);
            }
            var next=member.DrawPile.Cards.FirstOrDefault();if(next==null)break;
            await CardPileCmd.Add(next,member.Hand,skipVisuals:true);
            CombatManager.Instance.History.CardDrawn(Combat,next,false);
            await Hook.AfterCardDrawn(Combat,ctx,next,false);next.InvokeDrawn();
        }
    }
}
