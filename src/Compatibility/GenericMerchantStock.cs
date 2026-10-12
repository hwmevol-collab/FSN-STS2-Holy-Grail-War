using System.Reflection;
using System.Runtime.CompilerServices;
using MegaCrit.Sts2.Core.Entities.Merchant;
using MegaCrit.Sts2.Core.Entities.Relics;
using MegaCrit.Sts2.Core.Entities.Potions;
using MegaCrit.Sts2.Core.Factories;
namespace RinArcherCore;

public static class GenericMerchantStock
{
    sealed record StockBinding(Player Player,ShopState Shop,ShopVanillaItemState Item);
    static readonly ConditionalWeakTable<MerchantEntry,StockBinding> Bindings=new();
    public static bool IsBound(MerchantEntry entry)=>Bindings.TryGetValue(entry,out _);
    static int RawPrice(MerchantEntry entry)=>(int)AccessTools.Field(typeof(MerchantEntry),"_cost").GetValue(entry)!;
    static void Price(MerchantEntry entry,int value)=>AccessTools.Field(typeof(MerchantEntry),"_cost").SetValue(entry,value);
    static List<MerchantPotionEntry> Potions(MerchantInventory inventory)=>(List<MerchantPotionEntry>)AccessTools.Field(typeof(MerchantInventory),"_potionEntries").GetValue(inventory)!;
    public static bool CompleteBudget(Player p)
    {
        var potionOptions=
#if GAME_0107
            PotionFactory.GetPotionOptions(p,[]).ToArray();
#else
            PotionFactory.GetPotionOptions(p).ToArray();
#endif
        if(new[]{PotionRarity.Common,PotionRarity.Uncommon,PotionRarity.Rare}.Any(r=>potionOptions.Count(x=>x.Rarity==r)<3))return false;
        // Two independent rarity rolls plus the shop relic can consume at most
        // three distinct relics from any native bucket/fallback branch.
        return new[]{RelicRarity.Common,RelicRarity.Uncommon,RelicRarity.Rare,RelicRarity.Shop}.All(r=>
        {
            var native=NativeSourceBudgetResolver.NativeRelicBranch(p.RelicGrabBag,r,p.RunState,relic=>relic.IsAllowedInShops);
            return RelicEligibilityResolver.Prepare(p,"MERCHANT_BUDGET:"+r,native,r==RelicRarity.Shop?1:3).CompleteBudget;
        });
    }
    public static void Generate(Player p,MerchantInventory inventory,ShopState shop)
    {
        if(!CompleteBudget(p))throw new CompatibilitySourceUnavailableException("Merchant source unavailable before stock generation: complete native budget required");
        AccessTools.Method(typeof(MerchantInventory),"PopulateRelicEntries").Invoke(inventory,null);
        AccessTools.Method(typeof(MerchantInventory),"PopulatePotionEntries").Invoke(inventory,null);
        foreach(var entry in inventory.RelicEntries)
        {var item=new ShopVanillaItemState{ContentId=entry.Model!.Id.ToString(),RawPrice=RawPrice(entry)};shop.Relics.Add(item);Bindings.Add(entry,new(p,shop,item));}
        foreach(var entry in inventory.PotionEntries)
        {var item=new ShopVanillaItemState{ContentId=entry.Model!.Id.ToString(),RawPrice=RawPrice(entry)};shop.Potions.Add(item);Bindings.Add(entry,new(p,shop,item));}
    }
    static ModelId Id(string id){var parts=id.Split('.');return new(parts[0],parts[1]);}
    public static void Restore(Player p,MerchantInventory inventory,ShopState shop)
    {
        if(shop.Relics.Count!=3||shop.Potions.Count!=3)throw new InvalidOperationException("COMPATIBILITY_SAVE_MIGRATION_REQUIRED: native merchant budget missing");
        var rng=p.PlayerRng.ToSerializable();
        try
        {
            foreach(var item in shop.Relics)
            {
                var entry=new MerchantRelicEntry(ModelDb.GetById<RelicModel>(Id(item.ContentId)).ToMutable(),p);Price(entry,item.RawPrice);
                if(item.Sold)AccessTools.Property(typeof(MerchantRelicEntry),nameof(MerchantRelicEntry.Model)).SetValue(entry,null);
                inventory.AddRelicEntry(entry);Bindings.Add(entry,new(p,shop,item));
            }
            foreach(var item in shop.Potions)
            {
                var entry=new MerchantPotionEntry(ModelDb.GetById<PotionModel>(Id(item.ContentId)).ToMutable(),p);Price(entry,item.RawPrice);
                if(item.Sold)AccessTools.Property(typeof(MerchantPotionEntry),nameof(MerchantPotionEntry.Model)).SetValue(entry,null);
                Potions(inventory).Add(entry);Bindings.Add(entry,new(p,shop,item));
            }
        }
        finally{p.PlayerRng.LoadFromSerializable(rng);}
    }
    public static async Task AfterPurchase(MerchantEntry entry)
    {
        if(!Bindings.TryGetValue(entry,out var binding))return;
        binding.Item.Sold=!entry.IsStocked;ContractSave.Sync(binding.Player);
        await ContractSave.Checkpoint(binding.Player,"AFTER_COMPATIBLE_MERCHANT_PURCHASE");
    }
}
[HarmonyPatch(typeof(MerchantEntry),nameof(MerchantEntry.OnTryPurchaseWrapper))]
public static class GenericMerchantStockTransaction
{
    static readonly AsyncLocal<HashSet<MerchantEntry>?> Prepared=new();
    [HarmonyPriority(Priority.First)]
    static bool Prefix(MerchantEntry __instance,MerchantInventory? inventory,bool ignoreCost,MethodBase __originalMethod,ref Task<bool> __result)
    {
        if(!GenericMerchantStock.IsBound(__instance)||Prepared.Value?.Contains(__instance)==true)return true;
        var p=(Player)AccessTools.Field(typeof(MerchantEntry),"_player").GetValue(__instance)!;
        __result=Purchase(__instance,p,inventory,ignoreCost,__originalMethod);NativeRewardTransactions.Track(__result);return false;
    }
    static async Task<bool> Purchase(MerchantEntry entry,Player p,MerchantInventory? inventory,bool ignoreCost,MethodBase method)
    {
        if(!ContractMerchant.TryBegin(p))return false;
        var before=Prepared.Value;Prepared.Value=before==null?new(ReferenceEqualityComparer.Instance):new(before,ReferenceEqualityComparer.Instance);Prepared.Value.Add(entry);
        try
        {
            bool result=await (Task<bool>)method.Invoke(entry,[inventory,ignoreCost])!;
            if(result)await GenericMerchantStock.AfterPurchase(entry);return result;
        }
        finally{Prepared.Value=before;ContractMerchant.End(p);}
    }
}
