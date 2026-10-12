using MegaCrit.Sts2.Core.Models.CardPools;
using MegaCrit.Sts2.Core.Factories;
namespace RinArcherCore;
public static class VanillaGeneration
{
    public static bool NativeCardDependency(string id)
    {
        if(!id.StartsWith("CARD.",StringComparison.Ordinal))return false;
        try{return ModelDb.GetById<CardModel>(new ModelId("CARD",id[5..])).GetType().Assembly==typeof(ModelDb).Assembly;}catch(KeyNotFoundException){return false;}
    }
    public static void AddBudgets(Player p,Dictionary<string,CompatibilityGenerationBudget> budgets)
    {
        var colorless=ModelDb.CardPool<ColorlessCardPool>().GetUnlockedCards(p.UnlockState,p.RunState.CardMultiplayerConstraint).Where(c=>c.CanBeGeneratedByModifiers).ToArray();
        void Cards(string id,int count,Func<CardModel,bool> predicate,bool nativeColorless)
        {
            var branches=new Dictionary<string,IReadOnlyList<string>>(StringComparer.Ordinal);
            foreach(string member in new[]{RunEconomy.Rin,RunEconomy.Archer})
            {
                var candidates=nativeColorless?colorless:AlphaRewardRegistry.Pool(member).Select(x=>AlphaRewardRegistry.Card(x.Id)).ToArray();
                branches[member]=candidates.Where(predicate).Select(c=>c.Id.ToString()).ToArray();
            }
            budgets[id+"->POOL.NATIVE_CARDS"]=new(count,true,branches,branches.Values.SelectMany(x=>x).ToHashSet(StringComparer.Ordinal));
        }
        Cards("EVENT.BRAIN_LEECH",5,_=>true,false);
        Cards("EVENT.INFESTED_AUTOMATON",1,c=>c.Type==CardType.Power,false);
        var zeros=new[]{RunEconomy.Rin,RunEconomy.Archer}.ToDictionary(m=>m,m=>(IReadOnlyList<string>)AlphaRewardRegistry.Pool(m).Select(x=>AlphaRewardRegistry.Card(x.Id)).Where(c=>c.EnergyCost.Canonical==0&&!c.EnergyCost.CostsX).Select(c=>c.Id.ToString()).ToArray());
        var prior=budgets["EVENT.INFESTED_AUTOMATON->POOL.NATIVE_CARDS"];
        budgets["EVENT.INFESTED_AUTOMATON->POOL.NATIVE_CARDS"]=prior with{NativeBranches=prior.NativeBranches.Concat(zeros.Select(x=>new KeyValuePair<string,IReadOnlyList<string>>(x.Key+"/ZERO",x.Value))).ToDictionary(x=>x.Key,x=>x.Value),AuditedReplacementProviderIds=prior.AuditedReplacementProviderIds!.Concat(zeros.Values.SelectMany(x=>x)).ToHashSet(StringComparer.Ordinal)};
        Cards("RELIC.ARCANE_SCROLL",ModelDb.Relic<MegaCrit.Sts2.Core.Models.Relics.ArcaneScroll>().DynamicVars.Cards.IntValue,c=>c.Rarity==CardRarity.Rare,false);
        Cards("RELIC.ORANGE_DOUGH",ModelDb.Relic<MegaCrit.Sts2.Core.Models.Relics.OrangeDough>().DynamicVars.Cards.IntValue,_=>true,true);
        Cards("RELIC.TOOLBOX",ModelDb.Relic<MegaCrit.Sts2.Core.Models.Relics.Toolbox>().DynamicVars.Cards.IntValue,_=>true,true);
        Cards("RELIC.ASTROLABE",ModelDb.Relic<MegaCrit.Sts2.Core.Models.Relics.Astrolabe>().DynamicVars.Cards.IntValue,c=>c.Rarity is CardRarity.Common or CardRarity.Uncommon or CardRarity.Rare,false);
        budgets["RELIC.WONGOS_MYSTERY_TICKET->POOL.NATIVE_RELICS"]=budgets["POOL.NATIVE_RELICS"] with{RequestedCount=3};
    }
}
// An original character-pool grant uses the selected Contract member's existing
// reward pool. Colorless, foreign-character and explicitly custom pools are untouched.
[HarmonyPatch(typeof(CardCreationOptions),nameof(CardCreationOptions.GetPossibleCards))]
public static class VanillaContractGenerationPool
{
    static void Postfix(CardCreationOptions __instance,Player player,ref IEnumerable<CardModel> __result)
    {
        if(!GenericCompatibility.Enabled(player)||CompatibilityExecution.Current is not {} f||f.Player!=player||!VanillaExpandedAdapters.Audited(f.ContentId)||!__instance.CardPools.Any(p=>p is RinArcherPool))return;
        string member=VanillaCardAcquisition.Member(player)??throw new InvalidOperationException("Choose member before native character-card roll");
        __result=__instance.CardPools.SelectMany(pool=>pool is RinArcherPool
            ?AlphaRewardRegistry.Pool(member).Select(x=>AlphaRewardRegistry.Card(x.Id))
            :pool.GetUnlockedCards(player.UnlockState,player.RunState.CardMultiplayerConstraint)).Where(c=>__instance.CardPoolFilter?.Invoke(c)??true);
    }
}
