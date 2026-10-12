using MegaCrit.Sts2.Core.Rewards;
using MegaCrit.Sts2.Core.Saves.Runs;
using MegaCrit.Sts2.Core.Random;
using MegaCrit.Sts2.Core.Localization;
namespace RinArcherCore;

public sealed class ContractBossRewardState
{
    public int RewardIndex{get;set;}
    public string RoomIdentity{get;set;}="";
    public List<RewardOfferCard> Offer{get;set;}=[];
    public bool Complete{get;set;}
    public string? Pick{get;set;}
    public string? Owner{get;set;}
    public string? InstanceId{get;set;}
}
public static class ContractBossRewardEngine
{
    public static bool Budget(Player p)=>new[]{RunEconomy.Rin,RunEconomy.Archer}.SelectMany(AlphaRewardRegistry.Pool).Count(c=>c.Rarity==CardRarity.Rare)>=3;
    public static ContractBossRewardState Create(Player p,CardRarityOddsType rarity)
    {
        if(!FullActRoomSpine.Enabled(p)||!GenericCompatibility.Registry.IsValid||rarity!=CardRarityOddsType.BossEncounter||!Budget(p))throw new CompatibilitySourceUnavailableException("E2B_BOSS_NATIVE_RARE_BUDGET_UNAVAILABLE");
        var state=ContractSave.Get(p);string room=ContractSave.RoomKey(p);
        if(state.BossRewards.SingleOrDefault(r=>r.RoomIdentity==room) is {} frozen)return frozen;
        var reward=new ContractBossRewardState{RewardIndex=state.NextBossRewardIndex++,RoomIdentity=room};
        var rng=new Rng(p.RunState.Rng.Seed,$"CONTRACT_BOSS_CARD_REWARD:{p.RunState.GetPlayerSlotIndex(p)}:{reward.RewardIndex}:{room}");
        var pool=new[]{RunEconomy.Rin,RunEconomy.Archer}.SelectMany(owner=>AlphaRewardRegistry.Pool(owner).Where(c=>c.Rarity==CardRarity.Rare).Select(c=>new RewardOfferCard(c.Id,owner))).OrderBy(c=>c.CardId,StringComparer.Ordinal).ToList();
        for(int i=0;i<3;i++){var card=rng.NextItem(pool)!;reward.Offer.Add(card);pool.Remove(card);}
        state.BossRewards.Add(reward);ContractSave.Sync(p);ContractSave.Log(p,"CONTRACT_BOSS_OFFER_CREATED",reward);return reward;
    }
    public static void Decide(Player p,ContractBossRewardState reward,string? cardId)
    {
        if(reward.Complete)throw new InvalidOperationException("Boss reward already committed");
        if(reward.RoomIdentity!=ContractSave.RoomKey(p)||!ContractSave.Get(p).BossRewards.Contains(reward))throw new InvalidOperationException("Boss reward transaction identity mismatch");
        if(cardId!=null)
        {
            var offer=reward.Offer.SingleOrDefault(c=>c.CardId==cardId)??throw new ArgumentException("Unoffered Boss card");
            var state=ContractSave.Get(p);var card=(StarterCard)p.RunState.CreateCard(AlphaRewardRegistry.Card(cardId),p);
            if(card.OwnerCharacterId!=offer.Owner||card.Rarity!=CardRarity.Rare)throw new InvalidOperationException("Boss reward owner/rarity mismatch");
            card.InstanceId=$"permanent:{offer.Owner}:{++state.NextPermanentInstance}";
            if(offer.UpgradeLevel>0)CardCmd.Upgrade(card);
            ContractSave.Deck(p,offer.Owner).AddInternal(card);reward.Pick=cardId;reward.Owner=offer.Owner;reward.InstanceId=card.InstanceId;
            state.CombatSummary?.CardsAddedThisRoom.Add(new(card.SourceCardId,offer.Owner,card.IsUpgraded?1:0,card.InstanceId));
        }
        reward.Complete=true;ContractSave.Sync(p);ContractSave.Log(p,"CONTRACT_BOSS_REWARD_COMPLETE",reward);
    }
}
public sealed class ContractBossCardReward(Player player,ContractBossRewardState state):Reward(player)
{
    public ContractBossRewardState State{get;}=state;
    protected override RewardType RewardType=>RewardType.Card;
    public override int RewardsSetIndex=>5;
    public override bool IsPopulated=>State.Offer.Count==3&&State.Offer.Select(c=>c.CardId).Distinct().Count()==3;
    public override LocString Description=>new("gameplay_ui","COMBAT_REWARD_ADD_CARD");
    protected override string IconPath=>MegaCrit.Sts2.Core.Helpers.ImageHelper.GetImagePath("ui/reward_screen/reward_icon_card.png");
    public override void Populate(){}
    protected override async Task<bool> OnSelect()
    {
        if(State.Complete)return true;
        var choice=await ContractBossRewardUi.Ask(Player,State);
        if(choice.Cancelled)return false;
        ContractBossRewardEngine.Decide(Player,State,choice.CardId);
        await ContractSave.Checkpoint(Player,"CONTRACT_BOSS_REWARD_COMPLETE");ContractBossRewardUi.CloseCommitted();return true;
    }
    public override void OnSkipped(){if(!State.Complete)ContractBossRewardEngine.Decide(Player,State,null);}
    public override void MarkContentAsSeen(){}
    public override SerializableReward ToSerializable()=>new(){RewardType=RewardType.Card,OptionCount=3,CardPoolIds=[ModelDb.CardPool<RinAlphaRewardPool>().Id,ModelDb.CardPool<ArcherAlphaRewardPool>().Id],Source=CardCreationSource.Encounter,RarityOdds=CardRarityOddsType.BossEncounter};
}
