using MegaCrit.Sts2.Core.Random;
using MegaCrit.Sts2.Core.Odds;
using MegaCrit.Sts2.Core.Rewards;
using MegaCrit.Sts2.Core.Saves.Runs;
using MegaCrit.Sts2.Core.Entities.Cards;
using MegaCrit.Sts2.Core.Extensions;
using MegaCrit.Sts2.Core.Localization;
using System.Text.Json.Serialization;
namespace RinArcherCore;
public enum DualRewardPhase{NONE,MASTER_PENDING,MASTER_COMPLETE,SERVANT_PENDING,SERVANT_COMPLETE,COMPLETE}
public sealed record RewardOfferCard(string CardId,string Owner,int UpgradeLevel=0);
public sealed class DualRewardState
{
    public int RewardIndex{get;set;}
    public string RoomIdentity{get;set;}="";
    public CardRarityOddsType RarityOdds{get;set;}=CardRarityOddsType.RegularEncounter;
    public DualRewardPhase Phase{get;set;}=DualRewardPhase.MASTER_PENDING;
    public List<RewardOfferCard> RinOffer{get;set;}=[];
    public List<RewardOfferCard> ArcherOffer{get;set;}=[];
    public bool RinDecided{get;set;}
    public bool ArcherDecided{get;set;}
    public string? RinPick{get;set;}
    public string? ArcherPick{get;set;}
    public string? RinInstanceId{get;set;}
    public string? ArcherInstanceId{get;set;}
    [JsonIgnore] public bool Complete=>Phase==DualRewardPhase.COMPLETE;
    [JsonIgnore] public string PendingOwner=>Phase==DualRewardPhase.MASTER_PENDING?"CHAR_RIN":Phase is DualRewardPhase.MASTER_COMPLETE or DualRewardPhase.SERVANT_PENDING?"CHAR_ARCHER":throw new InvalidOperationException("No pending owner");
    public IReadOnlyList<RewardOfferCard> Offer(string owner)=>owner=="CHAR_RIN"?RinOffer:owner=="CHAR_ARCHER"?ArcherOffer:throw new ArgumentException("Owner");
}
public sealed class RoomRewardEntry
{
    public string? NativeCardOwner{get;set;}
    public string? NativeCardInstance{get;set;}
    public SerializableReward Native{get;set;}=new();
    public int? DualIndex{get;set;}
    public int? BossIndex{get;set;}
    public bool Resolved{get;set;}
}
public sealed class RoomRewardState
{
    public string RoomIdentity{get;set;}="";
    public List<RoomRewardEntry> Entries{get;set;}=[];
}
public static class DualRewardEngine
{
    public static DualRewardState Create(Player p,CardRarityOddsType type)
    {
        var s=ContractSave.Get(p);var reward=new DualRewardState{RewardIndex=s.NextRewardIndex++,RoomIdentity=ContractSave.RoomKey(p),RarityOdds=type};
        reward.RinOffer=Generate(p,"CHAR_RIN",reward.RewardIndex,type);
        s.DualRewards.Add(reward);ContractSave.Slot.Set((RunState)p.RunState,p.NetId,s);
        ContractSave.Log(p,"DUAL_REWARD_CREATED",new{reward.RewardIndex,rinOffer=reward.RinOffer,archerOffer=reward.ArcherOffer});return reward;
    }
    public static List<RewardOfferCard> Generate(Player p,string owner,int index,CardRarityOddsType type)
    {
        var s=ContractSave.Get(p);
        var rng=new Rng(p.RunState.Rng.Seed,$"DUAL_REWARD_{(owner=="CHAR_RIN"?"RIN":"ARCHER")}:{p.RunState.GetPlayerSlotIndex(p)}:{index}");
        var odds=new CardRarityOdds(owner=="CHAR_RIN"?s.RinRewardRarityState:s.ArcherRewardRarityState,rng);
        var candidates=AlphaRewardRegistry.Pool(owner).OrderBy(c=>c.Id,StringComparer.Ordinal).ToList();var result=new List<RewardOfferCard>();
        int count=GenericCompatibility.Enabled(p)?DualRewardModifierResolver.Count(p,index,owner):3;
        if(count<1||count>candidates.Count)throw new InvalidOperationException("DUAL_REWARD_COMPLETE_BUDGET_UNAVAILABLE");
        for(int i=0;i<count;i++)
        {
            var rarity=odds.Roll(type);for(int tries=0;!candidates.Any(c=>c.Rarity==rarity);tries++)
            {if(tries>3)throw new InvalidOperationException("Reward pool has no allowed rarity");rarity=rarity.GetNextHighestRarityWithWrapping();}
            var selected=rng.NextItem(candidates.Where(c=>c.Rarity==rarity))!;result.Add(new(selected.Id,owner));candidates.Remove(selected);
        }
        if(owner=="CHAR_RIN")s.RinRewardRarityState=odds.CurrentValue;else s.ArcherRewardRarityState=odds.CurrentValue;
        if(GenericCompatibility.Enabled(p))result=DualRewardModifierResolver.ApplyOptionModifiers(p,index,owner,result,type);
        ContractSave.Slot.Set((RunState)p.RunState,p.NetId,s);return result;
    }
    public static void Decide(Player p,DualRewardState reward,string owner,string? cardId)
    {
        if(reward.Complete||reward.PendingOwner!=owner)throw new InvalidOperationException("Dual reward phase/owner mismatch");
        var offer=reward.Offer(owner);if(cardId!=null&&!offer.Any(c=>c.CardId==cardId&&c.Owner==owner))throw new ArgumentException("UnOffered reward pick");
        var s=ContractSave.Get(p);string? instance=null;
        if(cardId!=null)
        {
            var card=(StarterCard)p.RunState.CreateCard(AlphaRewardRegistry.Card(cardId),p);
            if(card.OwnerCharacterId!=owner||card is ProjectedArm)throw new InvalidOperationException("Reward owner rejected");
            card.InstanceId=instance=$"permanent:{owner}:{++s.NextPermanentInstance}";
            if(offer.Single(c=>c.CardId==cardId).UpgradeLevel>0)CardCmd.Upgrade(card);
            ContractSave.Deck(p,owner).AddInternal(card);
            s.CombatSummary?.CardsAddedThisRoom.Add(new(card.SourceCardId,owner,card.IsUpgraded?1:0,card.InstanceId));
        }
        if(owner=="CHAR_RIN")
        {
            reward.RinDecided=true;reward.RinPick=cardId;reward.RinInstanceId=instance;
            // Generate exactly once after Master resolves; the same transaction checkpoints this offer.
            if(reward.ArcherOffer.Count==0)reward.ArcherOffer=Generate(p,"CHAR_ARCHER",reward.RewardIndex,reward.RarityOdds);
            reward.Phase=DualRewardPhase.SERVANT_PENDING;
            ContractSave.Log(p,"SERVANT_REWARD_CREATED",new{reward.RewardIndex,archerOffer=reward.ArcherOffer});
        }
        else{reward.ArcherDecided=true;reward.ArcherPick=cardId;reward.ArcherInstanceId=instance;reward.Phase=DualRewardPhase.COMPLETE;}
        ContractSave.Slot.Set((RunState)p.RunState,p.NetId,s);ContractSave.Sync(p);
        ContractSave.Log(p,cardId==null?"REWARD_SKIP":"REWARD_PICK",new{owner,cardId,instanceId=instance,reward.RewardIndex});
        if(reward.Complete)
        {
            ContractSave.Log(p,"DUAL_REWARD_COMPLETE",new{reward.RewardIndex});
            if(s.CombatSummary is {} summary){summary.RinDeckSizeEnd=p.Deck.Cards.Count;summary.ArcherDeckSizeEnd=ContractSave.Deck(p,"CHAR_ARCHER").Cards.Count;ContractSave.Log(p,"COMBAT_SUMMARY_RUN",summary);}
        }
    }
}
public sealed class DualCardReward(Player player,DualRewardState state):Reward(player)
{
    public DualRewardState State{get;}=state;
    protected override RewardType RewardType=>RewardType.Card;
    public override int RewardsSetIndex=>5;
    public override bool IsPopulated=>State.RinOffer.Count==(GenericCompatibility.Enabled(Player)?DualRewardModifierResolver.Count(Player,State.RewardIndex,RunEconomy.Rin):3)
        &&(State.Phase==DualRewardPhase.MASTER_PENDING||State.ArcherOffer.Count==(GenericCompatibility.Enabled(Player)?DualRewardModifierResolver.Count(Player,State.RewardIndex,RunEconomy.Archer):3));
    public override LocString Description=>new("gameplay_ui","COMBAT_REWARD_ADD_CARD");
    protected override string IconPath=>MegaCrit.Sts2.Core.Helpers.ImageHelper.GetImagePath("ui/reward_screen/reward_icon_card.png");
    public override void Populate(){}
    protected override async Task<bool> OnSelect()
    {
        while(!State.Complete)
        {
            var owner=State.PendingOwner;var selected=await DualRewardUi.Ask(Player,State,owner);
            if(selected.Cancelled)return false;
            DualRewardEngine.Decide(Player,State,owner,selected.CardId);
            await ContractSave.Checkpoint(Player,State.Phase.ToString());
            DualRewardUi.CloseCommitted();
        }
        return true;
    }
    public override void OnSkipped(){if(!State.Complete)throw new InvalidOperationException("Dual reward must decide both owners before leaving room");}
    public override void MarkContentAsSeen(){}
    public override SerializableReward ToSerializable()=>new(){RewardType=RewardType.Card,OptionCount=3,CardPoolIds=[ModelDb.CardPool<RinAlphaRewardPool>().Id],Source=CardCreationSource.Encounter,RarityOdds=CardRarityOddsType.RegularEncounter};
}
