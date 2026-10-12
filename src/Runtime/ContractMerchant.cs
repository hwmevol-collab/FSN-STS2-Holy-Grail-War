using System.Runtime.CompilerServices;
using MegaCrit.Sts2.Core.Entities.Merchant;
using MegaCrit.Sts2.Core.Entities.Gold;
using MegaCrit.Sts2.Core.Random;
using MegaCrit.Sts2.Core.Odds;
using MegaCrit.Sts2.Core.Extensions;
using MegaCrit.Sts2.Core.Hooks;
using MegaCrit.Sts2.Core.Nodes.Rooms;
using MegaCrit.Sts2.Core.Models.CardPools;
using MegaCrit.Sts2.Core.Saves.Runs;
namespace RinArcherCore;
public sealed record ShopBinding(Player Player,ShopState Shop,ShopCardState? Card);
public static class ContractMerchant
{
    static readonly ConditionalWeakTable<MerchantEntry,ShopBinding> Bindings=new();
    static readonly HashSet<Player> Busy=[];
    public static bool TryBegin(Player p)=>Busy.Add(p);
    public static void End(Player p)=>Busy.Remove(p);
    public static bool IsBusy(Player p)=>Busy.Contains(p);
    public static readonly AsyncLocal<Player?> RemovalOwner=new();
    public static PlayerRngSet? PricingPlayer;
    public static Rng? PricingRng;
    public static bool Bound(MerchantEntry entry,out ShopBinding binding)=>Bindings.TryGetValue(entry,out binding!);
    public static ShopState State(Player p)=>ContractSave.Get(p).Shops.Single(s=>s.MerchantId==RunEconomy.RoomKey(p));
    static void SetCard(MerchantCardEntry e,CardCreationResult? card)=>AccessTools.Property(typeof(MerchantCardEntry),nameof(MerchantCardEntry.CreationResult)).SetValue(e,card);
    static void SetCost(MerchantEntry e,int cost)=>AccessTools.Field(typeof(MerchantEntry),"_cost").SetValue(e,cost);
    // Persist the native base price; Cost applies live merchant modifiers once.
    static int BaseCost(MerchantEntry e)=>(int)AccessTools.Field(typeof(MerchantEntry),"_cost").GetValue(e)!;
    public static MerchantInventory Create(Player p)
    {
        var inv=new MerchantInventory(p);var key=RunEconomy.RoomKey(p);var all=ContractSave.Get(p).Shops;var shop=all.SingleOrDefault(s=>s.MerchantId==key);bool generated=shop==null;
        if(shop==null)
        {
            shop=new(){MerchantId=key,RemovalPrice=new MerchantCardRemovalEntry(p).Cost,RemovalAvailable=RunEconomy.Permanent(p).Any(c=>c.IsRemovable)};
            int sale=new Rng(p.RunState.Rng.Seed,$"SHOP_SALE:{p.RunState.GetPlayerSlotIndex(p)}:{key}").NextInt(5);
            foreach(string owner in new[]{RunEconomy.Rin,RunEconomy.Archer})
            {
                var rng=new Rng(p.RunState.Rng.Seed,$"SHOP_{(owner==RunEconomy.Rin?"RIN":"ARCHER")}_CARDS:{p.RunState.GetPlayerSlotIndex(p)}:{key}");
                var odds=new CardRarityOdds(rng);var candidates=AlphaRewardRegistry.Pool(owner).OrderBy(c=>c.Id,StringComparer.Ordinal).ToList();
                for(int i=0;i<2;i++)
                {
                    var rarity=odds.RollWithoutChangingFutureOdds(CardRarityOddsType.Shop);for(int tries=0;!candidates.Any(c=>c.Rarity==rarity);tries++){if(tries>3)throw new InvalidOperationException("Shop rarity unavailable");rarity=rarity.GetNextHighestRarityWithWrapping();}
                    var selected=rng.NextItem(candidates.Where(c=>c.Rarity==rarity))!;candidates.Remove(selected);
                    var e=new MerchantCardEntry(p,inv,[],rarity);SetCard(e,new(p.RunState.CreateCard(AlphaRewardRegistry.Card(selected.Id),p)));
                    bool onSale=shop.Cards.Count==sale;AccessTools.Property(typeof(MerchantCardEntry),nameof(MerchantCardEntry.IsOnSale)).SetValue(e,onSale);
                    // Use the native pricing function with this owner's isolated shop RNG stream.
                    PricingPlayer=p.PlayerRng;PricingRng=rng;try{e.CalcCost();}finally{PricingPlayer=null;PricingRng=null;}
                    shop.Cards.Add(new(){CardId=selected.Id,Owner=owner,Price=BaseCost(e),OnSale=onSale});
                }
            }
            // Fifth owner is rolled once from the native Shops stream and persisted.
            string fifthOwner=p.PlayerRng.Shops.NextInt(2)==0?RunEconomy.Rin:RunEconomy.Archer;
            var fifthPool=AlphaRewardRegistry.Pool(fifthOwner).Where(c=>!shop.Cards.Any(s=>s.CardId==c.Id)).Select(c=>AlphaRewardRegistry.Card(c.Id)).ToList();
            var fifthRarity=p.PlayerOdds.CardRarity.RollWithoutChangingFutureOdds(CardRarityOddsType.Shop);
            var fifth=new MerchantCardEntry(p,inv,fifthPool,fifthRarity);fifth.Populate();if(sale==4)fifth.SetOnSale();
            shop.Cards.Add(new(){CardId=((StarterCard)fifth.CreationResult!.Card).SourceCardId,Owner=fifthOwner,Price=BaseCost(fifth),OnSale=fifth.IsOnSale});
            // Exact supported subset of the real native unlocked pool; no unlock injection.
            var colorlessPool=ModelDb.CardPool<ColorlessCardPool>().GetUnlockedCards(p.UnlockState,p.RunState.CardMultiplayerConstraint).Where(NativePermanentCards.ShopSupported).ToList();
            foreach(var rarity in new[]{CardRarity.Uncommon,CardRarity.Rare})
            {
                if(!colorlessPool.Any(c=>c.Rarity==rarity))throw new InvalidOperationException("COLORLESS_SHOP_NATIVE_BUDGET_UNAVAILABLE: "+rarity);
                var entry=new MerchantCardEntry(p,inv,colorlessPool,rarity);entry.Populate();
                var card=entry.CreationResult!.Card;
                shop.Colorless.Add(new(){CardId=card.Id.ToString(),Price=BaseCost(entry),NativeCard=card.ToSerializable()});
                colorlessPool.RemoveAll(c=>c.Id==card.Id);
            }
            if(GenericCompatibility.Enabled(p))GenericMerchantStock.Generate(p,inv,shop);
            all.Add(shop);
            ContractSave.Log(p,"MERCHANT_GENERATED",new{merchantId=key,rinCards=shop.Cards.Where(c=>c.Owner==RunEconomy.Rin).Select(c=>c.CardId),archerCards=shop.Cards.Where(c=>c.Owner==RunEconomy.Archer).Select(c=>c.CardId),cards=shop.Cards,rngStreams=new[]{"SHOP_RIN_CARDS","SHOP_ARCHER_CARDS"}});
        }
        foreach(var card in shop.Colorless)
        {
            if(card.NativeCard==null)throw new InvalidDataException("Native merchant card snapshot missing");
            var native=CardModel.FromSerializable(card.NativeCard);p.RunState.AddCard(native,p);
            if(!NativePermanentCards.Supported(native))throw new InvalidDataException("Unaudited saved colorless shop card");
            var e=new MerchantCardEntry(p,inv,[],native.Rarity);SetCard(e,card.Sold?null:new(native));SetCost(e,card.Price);
            ((List<MerchantCardEntry>)AccessTools.Field(typeof(MerchantInventory),"_colorlessCardEntries").GetValue(inv)!).Add(e);Bindings.Add(e,new(p,shop,card));
        }
        foreach(var card in shop.Cards)
        {
            var native=p.RunState.CreateCard(AlphaRewardRegistry.Card(card.CardId),p);if(((StarterCard)native).OwnerCharacterId!=card.Owner)throw new InvalidOperationException("Saved merchant owner mismatch");
            var e=new MerchantCardEntry(p,inv,[],native.Rarity);SetCard(e,card.Sold?null:new(native));AccessTools.Property(typeof(MerchantCardEntry),nameof(MerchantCardEntry.IsOnSale)).SetValue(e,card.OnSale);SetCost(e,card.Price);
            ((List<MerchantCardEntry>)AccessTools.Field(typeof(MerchantInventory),"_characterCardEntries").GetValue(inv)!).Add(e);Bindings.Add(e,new(p,shop,card));
        }
        if(GenericCompatibility.Enabled(p)&&!generated)GenericMerchantStock.Restore(p,inv,shop);
        var remove=new MerchantCardRemovalEntry(p);SetCost(remove,shop.RemovalPrice);if(shop.RemovalUsed)remove.SetUsed();AccessTools.Property(typeof(MerchantInventory),nameof(MerchantInventory.CardRemovalEntry)).SetValue(inv,remove);Bindings.Add(remove,new(p,shop,null));
        var update=(Action<PurchaseStatus,MerchantEntry>)AccessTools.Method(typeof(MerchantInventory),"UpdateEntries").CreateDelegate(typeof(Action<PurchaseStatus,MerchantEntry>),inv);
        foreach(var e in inv.AllEntries)e.PurchaseCompleted+=update;
        if(generated)ContractSave.Sync(p);return inv;
    }
    public static Task<bool> Purchase(MerchantCardEntry entry)
    {var task=PurchaseCore(entry);NativeRewardTransactions.Track(task);return task;}
    static async Task<bool> PurchaseCore(MerchantCardEntry entry)
    {
        var b=Bindings.GetValue(entry,_=>throw new InvalidOperationException());var p=b.Player;
        if(!Busy.Add(p))return false;
        var ui=NMerchantRoom.Instance?.Inventory;
        try
        {
            // Native shop dialogue has no FailureOutOfStock line. A sold slot
            // follows the native no-op path rather than starting a second sale.
            if(!entry.IsStocked||b.Card!.Sold)return false;
            if(!entry.EnoughGold){entry.InvokePurchaseFailed(PurchaseStatus.FailureGold);return false;}
            ui?.BlockInput();var card=entry.CreationResult!.Card;string owner=b.Card.Owner;
            if(b.Card.NativeCard!=null)
            {
                owner=await MemberTargetResolver.Choose(p,"COLORLESS_SHOP_PURCHASE",[],FsnLoc.Format("SHOP_COLORLESS_OWNER",card.Title),true)??"";
                if(owner.Length==0){ContractSave.Log(p,"MERCHANT_COLORLESS_CANCELLED",new{cardId=b.Card.CardId,p.Gold});return false;}
                if(!entry.IsStocked||b.Card.Sold||!entry.EnoughGold)return false;
            }
            int before=p.Gold,price=entry.Cost;var s=ContractSave.Get(p);string instance=$"permanent:{owner}:{++s.NextPermanentInstance}";
            if(card is StarterCard owned)owned.InstanceId=instance;else NativePermanentCards.Bind(card,owner,instance);
            CardPileAddResult added;RemovalOwner.Value=p;try{added=await CardPileCmd.Add(card,ContractSave.Deck(p,owner));}finally{RemovalOwner.Value=null;}
            if(!added.success){entry.InvokePurchaseFailed(PurchaseStatus.FailureSpace);return false;}
            await PlayerCmd.LoseGold(price,p,GoldLossType.Spent);RunManager.Instance.RewardSynchronizer.SyncLocalGoldLost(price);RunManager.Instance.RewardSynchronizer.SyncLocalObtainedCard(card);
            if(b.Card.NativeCard!=null)p.RunState.CurrentMapPointHistoryEntry?.GetEntry(p.NetId).BoughtColorless.Add(card.Id);
            b.Card.Owner=owner;b.Card.Sold=true;SetCard(entry,null);await Hook.AfterItemPurchased(p.RunState,p,entry,price);entry.InvokePurchaseCompleted(entry);
            if(owner==RunEconomy.Rin)s.Economy.RinCardsPurchased++;else s.Economy.ArcherCardsPurchased++;s.Economy.GoldSpentCards+=price;
            ContractSave.Log(p,"MERCHANT_CARD_PURCHASED",new{merchantId=b.Shop.MerchantId,owner,cardId=b.Card.CardId,instanceId=instance,price,goldBefore=before,goldAfter=p.Gold,colorless=b.Card.NativeCard!=null});
            await ContractSave.Checkpoint(p,"AFTER_MERCHANT_PURCHASE");return true;
        }
        finally{Busy.Remove(p);if(ui!=null&&GodotObject.IsInstanceValid(ui))ui.UnblockInput();}
    }
    public static async Task<bool> SelectRemoval(MerchantCardRemovalEntry entry)
    {
        var b=Bindings.GetValue(entry,_=>throw new InvalidOperationException());var p=b.Player;
        if(Busy.Contains(p)||entry.Used||b.Shop.RemovalUsed)return false;
        if(!entry.EnoughGold){entry.InvokePurchaseFailed(PurchaseStatus.FailureGold);return false;}
        ContractSave.Log(p,"CARD_REMOVE_OPENED",new{merchantId=b.Shop.MerchantId,price=entry.Cost,targetCount=1});
        var cards=await DualDeckCardSelector.Select(p,DeckServiceAction.Remove,1,c=>c.IsRemovable,true,FsnLoc.Format("UI_FB9699A5274F", entry.Cost));if(cards.Count==0)return false;
        var task=Remove(entry,cards[0]);NativeRewardTransactions.Track(task);return await task;
    }
    public static async Task<bool> Remove(MerchantCardRemovalEntry entry,CardModel selected)
    {
        var b=Bindings.GetValue(entry,_=>throw new InvalidOperationException());var p=b.Player;
        if(!Busy.Add(p))return false;var ui=NMerchantRoom.Instance?.Inventory;
        try
        {
            if(entry.Used||b.Shop.RemovalUsed||!entry.EnoughGold||!RunEconomy.IsPermanent(p,selected)||!selected.IsRemovable)return false;
            ui?.BlockInput();var c=selected;int price=entry.Cost,count=p.ExtraFields.CardShopRemovalsUsed,gold=p.Gold;
            await PlayerCmd.LoseGold(price,p,GoldLossType.Spent);
            RemovalOwner.Value=p;try{await CardPileCmd.RemoveFromDeck(selected);}finally{RemovalOwner.Value=null;}
            p.ExtraFields.CardShopRemovalsUsed++;b.Shop.RemovalUsed=true;b.Shop.RemovalAvailable=false;entry.SetUsed();ui?.OnCardRemovalUsed();
            await Hook.AfterItemPurchased(p.RunState,p,entry,price);entry.InvokePurchaseCompleted(entry);
            var metrics=ContractSave.Get(p).Economy;if(NativePermanentCards.Owner(c)==RunEconomy.Rin)metrics.CardsRemovedRin++;else metrics.CardsRemovedArcher++;metrics.RemovalGoldSpent+=price;
            ContractSave.Log(p,"CARD_REMOVED",new{merchantId=b.Shop.MerchantId,owner=NativePermanentCards.Owner(c),cardId=NativePermanentCards.Id(c),instanceId=NativePermanentCards.Instance(c),price,removalCountBefore=count,removalCountAfter=p.ExtraFields.CardShopRemovalsUsed,goldBefore=gold,goldAfter=p.Gold});
            await ContractSave.Checkpoint(p,"AFTER_CARD_REMOVAL");return true;
        }
        finally{Busy.Remove(p);if(ui!=null&&GodotObject.IsInstanceValid(ui))ui.UnblockInput();}
    }
    public static PileType NativeRemovalPileType(CardPile pile)
    {
        // Native permanent effects (e.g. Swipe) also remove/return real Archer
        // deck cards outside merchant selection. Recognize only this exact bank.
        var p=RemovalOwner.Value??pile.Cards.FirstOrDefault()?.Owner??CompatibilityExecution.Current?.Player;
        return p!=null&&RunEconomy.Enabled(p)&&ReferenceEquals(pile,ContractSave.Deck(p,RunEconomy.Archer))?PileType.Deck:pile.Type;
    }
}
