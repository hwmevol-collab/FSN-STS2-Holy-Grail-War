using MegaCrit.Sts2.Core.Nodes.CommonUi;
using System.Runtime.CompilerServices;
using MegaCrit.Sts2.Core.Entities.RestSite;
using MegaCrit.Sts2.Core.Hooks;
using MegaCrit.Sts2.Core.Rooms;
using MegaCrit.Sts2.Core.Rewards;
namespace RinArcherCore;
public sealed class CampfireState
{
    public string RoomIdentity{get;set;}="";
    public bool Entered{get;set;}
    public bool Completed{get;set;}
    public string Action{get;set;}="";
    public string FocusOwner{get;set;}="";
    public string InstanceId{get;set;}="";
}
public sealed class ShopCardState
{
    public string CardId{get;set;}="";
    public string Owner{get;set;}="";
    public int Price{get;set;}
    public bool OnSale{get;set;}
    public bool Sold{get;set;}
}
public sealed class ShopState
{
    public string MerchantId{get;set;}="";
    public List<ShopCardState> Cards{get;set;}=[];
    public List<ShopVanillaItemState> Relics{get;set;}=[];
    public List<ShopVanillaItemState> Potions{get;set;}=[];
    public int RemovalPrice{get;set;}
    public bool RemovalAvailable{get;set;}=true;
    public bool RemovalUsed{get;set;}
}
public sealed class ShopVanillaItemState
{
    public string ContentId{get;set;}="";
    public int RawPrice{get;set;}
    public bool Sold{get;set;}
}
public sealed class EconomyMetrics
{
    [System.Text.Json.Serialization.JsonPropertyName("campfiresVisited")]
    public int CampfiresVisited{get;set;}
    [System.Text.Json.Serialization.JsonPropertyName("rests")]
    public int Rests{get;set;}
    [System.Text.Json.Serialization.JsonPropertyName("restFocusRin")]
    public int RestFocusRin{get;set;}
    [System.Text.Json.Serialization.JsonPropertyName("restFocusArcher")]
    public int RestFocusArcher{get;set;}
    [System.Text.Json.Serialization.JsonPropertyName("smiths")]
    public int Smiths{get;set;}
    [System.Text.Json.Serialization.JsonPropertyName("rinCardsPurchased")]
    public int RinCardsPurchased{get;set;}
    [System.Text.Json.Serialization.JsonPropertyName("archerCardsPurchased")]
    public int ArcherCardsPurchased{get;set;}
    [System.Text.Json.Serialization.JsonPropertyName("goldSpentCards")]
    public int GoldSpentCards{get;set;}
    [System.Text.Json.Serialization.JsonPropertyName("cardsRemovedRin")]
    public int CardsRemovedRin{get;set;}
    [System.Text.Json.Serialization.JsonPropertyName("cardsRemovedArcher")]
    public int CardsRemovedArcher{get;set;}
    [System.Text.Json.Serialization.JsonPropertyName("removalGoldSpent")]
    public int RemovalGoldSpent{get;set;}
}
public sealed record HealPreview(string Owner,int Before,int Max,decimal Amount,int After,int Heal,int Overheal);
public sealed record RestPreview(string FocusOwner,HealPreview Rin,HealPreview Archer)
{
    public HealPreview Focus=>FocusOwner==RunEconomy.Rin?Rin:Archer;
    public HealPreview Partner=>FocusOwner==RunEconomy.Rin?Archer:Rin;
    public string Text=>$"Focus {(FocusOwner==RunEconomy.Rin?"Master — Rin":"Servant — Archer")}\nRin: {Rin.Before}/{Rin.Max} → {Rin.After}/{Rin.Max}  (+{Rin.Heal})\nArcher: {Archer.Before}/{Archer.Max} → {Archer.After}/{Archer.Max}  (+{Archer.Heal})\nFocus 30% / Partner 10% · excess healing stays unused";
}
public static class RunEconomy
{
    public const string Rin="CHAR_RIN",Archer="CHAR_ARCHER";
    // Eligibility is additive and deliberately limited to the accepted D2 QA capability.
    public static bool Enabled(Player p)=>p.Character is RinContractCharacter&&(ContractSave.Get(p).RunFlags.GetValueOrDefault("QA_D2_RUN")||GenericCompatibility.Enabled(p));
    // Native Continue may temporarily append the reconstructed non-combat room to
    // floor history. Act and map coordinate identify the same service across reloads.
    public static string RoomKey(Player p)=>$"{p.RunState.CurrentActIndex}:{p.RunState.CurrentMapCoord}";
    public static Player Owner(RestSiteOption option)=>(Player)AccessTools.Property(typeof(RestSiteOption),"Owner").GetValue(option)!;
    public static IEnumerable<CardModel> Permanent(Player p)=>ContractSave.Deck(p,Rin).Cards.Concat(ContractSave.Deck(p,Archer).Cards).Where(c=>c is StarterCard and not ProjectedArm);
    public static bool IsPermanent(Player p,CardModel card)=>card is StarterCard s&&s is not ProjectedArm&&ContractSave.Deck(p,s.OwnerCharacterId).Cards.Contains(card);
    public static CampfireState Campfire(Player p)
    {
        var all=ContractSave.Get(p).Campfires;var key=RoomKey(p);
        var state=all.SingleOrDefault(c=>c.RoomIdentity==key);if(state==null){state=new(){RoomIdentity=key};all.Add(state);}return state;
    }
    static readonly ConditionalWeakTable<Player,Creature> Bodies=new();
    static readonly ConditionalWeakTable<Creature,Player> ServiceOwners=new();
    public static Creature Servant(Player p)
    {
        var live=ContractRuntime.For(p);
        var creature=live?.Finished==true?live.Archer.Creature:Bodies.GetValue(p,x=>
        {var s=ContractSave.Get(x);var c=new Creature(ModelDb.Monster<ArcherBody>().ToMutable(),CombatSide.Player,null);c.SetMaxHpInternal(s.ArcherMaxHp);c.SetCurrentHpInternal(s.ArcherHp);return c;});
        ServiceOwners.Remove(creature);ServiceOwners.Add(creature,p);return creature;
    }
    public static bool HealEndingGuard(Creature c)=>c.IsPlayer||(!CombatManager.Instance.IsInProgress&&ServiceOwners.TryGetValue(c,out var p)&&Enabled(p));
    public static RestPreview Preview(Player p,string focus)
    {
        if(focus is not (Rin or Archer))throw new ArgumentException("Unknown rest focus");
        var a=Servant(p);return new(focus,PreviewOne(p,p.Creature,Rin,focus==Rin),PreviewOne(p,a,Archer,focus==Archer));
    }
    static HealPreview PreviewOne(Player p,Creature c,string owner,bool focus)
    {
        decimal amount=Hook.ModifyRestSiteHealAmount(p.RunState,c,HealRestSiteOption.GetBaseHealAmount(c)/(focus?1:3));
        // Match native HealInternal's integer truncation, including the current HP before clamping.
        int after=(int)Math.Clamp(c.CurrentHp+amount,0,c.MaxHp),heal=after-c.CurrentHp;
        return new(owner,c.CurrentHp,c.MaxHp,amount,after,heal,Math.Max(0,(int)amount-heal));
    }
    public static bool CanFocus(Player p,string focus)
    {var v=Preview(p,focus);return !Campfire(p).Completed&&v.Rin.Before>0&&v.Archer.Before>0&&v.Focus.Before<v.Focus.Max;}
    static readonly HashSet<CampfireState> RestCommits=new(ReferenceEqualityComparer.Instance);
    public static async Task<bool> Rest(Player p,string focus)
    {
        if(!Enabled(p)||!CanFocus(p,focus))return false;
        var committingRoom=Campfire(p);if(!RestCommits.Add(committingRoom))return false;
        try
        {
        var v=Preview(p,focus);var a=Servant(p);
        await CreatureCmd.Heal(p.Creature,v.Rin.Amount);
        await CreatureCmd.Heal(a,v.Archer.Amount);
        if(p.Creature.CurrentHp!=v.Rin.After||a.CurrentHp!=v.Archer.After)throw new InvalidOperationException("Native dual heal differed from preview");
        var s=ContractSave.Get(p);s.ArcherHp=a.CurrentHp;s.ArcherMaxHp=a.MaxHp;
        // One contract Rest action and two character-level healing pipelines.
        await Hook.AfterRestSiteHeal(p.RunState,p,false);
        var rewards=new List<Reward>();Hook.ModifyRestSiteHealRewards(p.RunState,p,rewards,false);await RewardsCmd.OfferCustom(p,rewards);
        var room=Campfire(p);room.Completed=true;room.Action="REST";room.FocusOwner=focus;
        s.Economy.Rests++;if(focus==Rin)s.Economy.RestFocusRin++;else s.Economy.RestFocusArcher++;
        ContractSave.Log(p,"REST_COMMITTED",new{focusOwner=focus,focusHeal=v.Focus.Heal,partnerHeal=v.Partner.Heal,focusOverheal=v.Focus.Overheal,partnerOverheal=v.Partner.Overheal,rinHpBefore=v.Rin.Before,rinHpAfter=p.Creature.CurrentHp,archerHpBefore=v.Archer.Before,archerHpAfter=a.CurrentHp});
        await ContractSave.Checkpoint(p,"AFTER_REST");return true;
        }
        finally{RestCommits.Remove(committingRoom);}
    }
    public static async Task<bool> Smith(Player p,CardModel card)
    {
        if(!Enabled(p)||Campfire(p).Completed||!IsPermanent(p,card)||!card.IsUpgradable)return false;
        var c=(StarterCard)card;int before=card.CurrentUpgradeLevel;CardCmd.Upgrade(card,CardPreviewStyle.None);
        await Hook.AfterRestSiteSmith(p.RunState,p);var room=Campfire(p);room.Completed=true;room.Action="SMITH";room.InstanceId=c.InstanceId;
        ContractSave.Get(p).Economy.Smiths++;
        ContractSave.Log(p,"SMITH_COMMITTED",new{owner=c.OwnerCharacterId,cardId=c.SourceCardId,instanceId=c.InstanceId,upgradeLevelBefore=before,upgradeLevelAfter=card.CurrentUpgradeLevel});
        await ContractSave.Checkpoint(p,"AFTER_SMITH");return true;
    }
}


