using MegaCrit.Sts2.Core.Factories;
using MegaCrit.Sts2.Core.Models.PotionPools;
using MegaCrit.Sts2.Core.Models.RelicPools;
using MegaCrit.Sts2.Core.Entities.Potions;
using MegaCrit.Sts2.Core.Entities.Relics;
namespace RinArcherCore;
public sealed record NativeGenerationBudgetPlan(string ContentId,string TargetPool,string QuantityKind,string? QuantityKey,int FixedCount,bool Distinct);
public static class NativeSourceBudgetResolver
{
    public static IReadOnlyDictionary<string,CompatibilityGenerationBudget> Plans(Player p)
    {
        // These are native pools, not the 297/65-entry classification catalog.
        var potions=p.Character.PotionPool.GetUnlockedPotions(p.UnlockState).Concat(ModelDb.PotionPool<SharedPotionPool>().GetUnlockedPotions(p.UnlockState)).Distinct().ToArray();
        var result=new Dictionary<string,CompatibilityGenerationBudget>(StringComparer.Ordinal);
        foreach(var plan in NativeGenerationBudgetPlans.Plans)
        {
            int count=plan.FixedCount;
            if(plan.QuantityKind=="POTION_SLOT_CAPACITY")count=Math.Max(1,p.MaxPotionCount);
            else if(plan.QuantityKind=="DYNAMIC_VAR")
            {
                var model=ModelDb.GetById<AbstractModel>(new ModelId(plan.ContentId.Split('.')[0],plan.ContentId.Split('.')[1]));
                count=model switch{RelicModel r=>r.DynamicVars[plan.QuantityKey!].IntValue,PotionModel potion=>potion.DynamicVars[plan.QuantityKey!].IntValue,_=>throw new InvalidOperationException("Unknown native quantity model")};
            }
            IReadOnlyDictionary<string,IReadOnlyList<string>> branches=plan.TargetPool=="POOL.NATIVE_POTIONS"
                ?new[]{PotionRarity.Common,PotionRarity.Uncommon,PotionRarity.Rare}.ToDictionary(r=>r.ToString(),r=>(IReadOnlyList<string>)potions.Where(potion=>potion.Rarity==r).Select(potion=>potion.Id.ToString()).ToArray(),StringComparer.Ordinal)
                :new[]{RelicRarity.Common,RelicRarity.Uncommon,RelicRarity.Rare}.ToDictionary(r=>r.ToString(),r=>(IReadOnlyList<string>)NativeRelicBranch(p.RelicGrabBag,r,p.RunState,_=>true).Select(relic=>relic.Id.ToString()).ToArray(),StringComparer.Ordinal);
            result.Add(plan.ContentId+"->"+plan.TargetPool,new(count,plan.Distinct,branches));
        }
        // The accepted C/D1 reward provider already replaces the player's native
        // card reward. This explicit proof is confined to Monster room domains;
        // it cannot approve vanilla generated cards or widen any acquisition pool.
        var cardBranches=new[]{RunEconomy.Rin,RunEconomy.Archer}.ToDictionary(owner=>owner,
            owner=>(IReadOnlyList<string>)AlphaRewardRegistry.Pool(owner).Select(c=>c.Id).ToArray(),StringComparer.Ordinal);
        var provider=cardBranches.Values.SelectMany(ids=>ids).ToHashSet(StringComparer.Ordinal);
        foreach(string room in new[]{"MapPointType.Monster","RoomType.Monster"})
            result[room+"->POOL.NATIVE_CARDS"]=new(3,true,cardBranches,provider);
        foreach(string room in new[]{"MapPointType.Shop","RoomType.Shop"})
            result[room+"->POOL.NATIVE_CARDS"]=new(2,true,cardBranches,provider);
        var nativePotionBranches=new[]{PotionRarity.Common,PotionRarity.Uncommon,PotionRarity.Rare}.ToDictionary(r=>r.ToString(),
            r=>(IReadOnlyList<string>)potions.Where(x=>x.Rarity==r).Select(x=>x.Id.ToString()).ToArray(),StringComparer.Ordinal);
        result["POOL.NATIVE_POTIONS"]=new(1,true,nativePotionBranches);
        var nativeRelicBranches=new[]{RelicRarity.Common,RelicRarity.Uncommon,RelicRarity.Rare}.ToDictionary(r=>r.ToString(),
            r=>(IReadOnlyList<string>)NativeRelicBranch(p.RelicGrabBag,r,p.RunState,_=>true).Select(x=>x.Id.ToString()).ToArray(),StringComparer.Ordinal);
        result["POOL.NATIVE_RELICS"]=new(1,true,nativeRelicBranches);
        VanillaGeneration.AddBudgets(p,result);return result;
    }
    public static IReadOnlyList<RelicModel> NativeRelicBranch(RelicGrabBag bag,RelicRarity rarity,IRunState run,Func<RelicModel,bool> nativeFilter)
    {
        var deques=(Dictionary<RelicRarity,List<RelicModel>>)AccessTools.Field(typeof(RelicGrabBag),"_deques").GetValue(bag)!;
        bool refresh=(bool)AccessTools.Field(typeof(RelicGrabBag),"_refreshAllowed").GetValue(bag)!;
        var originals=(List<RelicModel>?)AccessTools.Field(typeof(RelicGrabBag),"_originalRelics").GetValue(bag);
        bool first=true;
        while(rarity!=RelicRarity.None)
        {
            var allowed=(deques.GetValueOrDefault(rarity)??[]).Where(r=>r.IsAllowed(run)).ToArray();
            if(first&&refresh&&allowed.Length==0)allowed=(originals??[]).Where(r=>r.Rarity==rarity&&r.IsAllowed(run)).ToArray();
            var result=allowed.Where(nativeFilter).ToArray();if(result.Length>0)return result;
            rarity=rarity switch{RelicRarity.Shop=>RelicRarity.Common,RelicRarity.Common=>RelicRarity.Uncommon,RelicRarity.Uncommon=>RelicRarity.Rare,_=>RelicRarity.None};first=false;
        }
        return ((List<RelicModel>)AccessTools.Field(typeof(RelicGrabBag),"_mpFallbackDequeue").GetValue(bag)!).Where(r=>r.IsAllowed(run)&&nativeFilter(r)).ToArray();
    }
}
