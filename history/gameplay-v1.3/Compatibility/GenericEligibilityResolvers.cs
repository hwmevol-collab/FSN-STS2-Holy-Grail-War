namespace RinArcherCore;

public sealed record CompatibilityCandidateSet<T>(string Source,IReadOnlyList<T> Candidates,bool CompleteBudget,string RejectionReason);
public static class CompatibilityCandidateResolver
{
    public static CompatibilityEligibilityContext Context(Player p,string source,bool nativeAllowed=true,IReadOnlyDictionary<string,CompatibilityGenerationBudget>? budgets=null)
        =>new(p.Character is RinContractCharacter,nativeAllowed,source,GenericCompatibility.Ready(p),budgets??(p.Character is RinContractCharacter?NativeSourceBudgetResolver.Plans(p):null),p.Character is RinContractCharacter?FullActEventBridge.Ready(p).Concat(FullActFirstTreasureBridge.Ready(p)?new[]{FullActFirstTreasureBridge.Id}:Array.Empty<string>()).ToHashSet(StringComparer.Ordinal):null);
    public static CompatibilityCandidateSet<T> Prepare<T>(Player p,string source,string category,IEnumerable<T> nativeCandidates,
        Func<T,string> identify,int count,bool distinct=true,IReadOnlyDictionary<string,IReadOnlyList<T>>? nativeBranches=null,
        IReadOnlyDictionary<string,CompatibilityGenerationBudget>? dependencies=null)
    {
        var original=nativeCandidates.ToArray();var context=Context(p,source,true,dependencies);
        var candidates=GenericCompatibility.Registry.FilterNativeCandidates(original,identify,category,context);
        foreach(var item in original)
        {
            string id=identify(item);var reason=GenericCompatibility.Registry.RejectionReason(id,context,category);
            if(context.RinContract)
            {
                ContractSave.Log(p,"COMPAT_CONTENT_ROLLED",new{contentId=id,classification=GenericCompatibility.Registry.GetClassification(id),source,eligible=reason.Length==0});
                if(reason.Length>0)ContractSave.Log(p,"CONTENT_FILTERED",new{contentId=id,classification=GenericCompatibility.Registry.GetClassification(id),source,reason});
            }
        }
        int Capacity(IEnumerable<T> values)=>distinct?values.Select(identify).Distinct(StringComparer.Ordinal).Count():values.Any()?count:0;
        string rejection=count<0?"INVALID_NATIVE_BUDGET":Capacity(candidates)<count?"INSUFFICIENT_NATIVE_COMPATIBLE_BUDGET":"";
        if(nativeBranches!=null)foreach(var branch in nativeBranches)
        {
            // Branches must be subsets of the original native acquisition candidates.
            if(branch.Value.Any(item=>!original.Contains(item)))throw new InvalidOperationException("Native branch attempted pool expansion");
            if(Capacity(GenericCompatibility.Registry.FilterNativeCandidates(branch.Value,identify,category,context))<count)rejection="INSUFFICIENT_NATIVE_COMPATIBLE_BUDGET: "+branch.Key;
        }
        return new(source,candidates,rejection.Length==0,rejection);
    }
}
public static class RelicEligibilityResolver
{
    public static bool IsEligible(Player p,string id,string source,bool nativeAllowed,IReadOnlyDictionary<string,CompatibilityGenerationBudget>? dependencies=null)
        =>GenericCompatibility.Registry.IsRelicEligible(id,CompatibilityCandidateResolver.Context(p,source,nativeAllowed,dependencies));
    public static CompatibilityCandidateSet<RelicModel> Prepare(Player p,string source,IEnumerable<RelicModel> native,int count=1,
        IReadOnlyDictionary<string,IReadOnlyList<RelicModel>>? branches=null,IReadOnlyDictionary<string,CompatibilityGenerationBudget>? dependencies=null)
        =>CompatibilityCandidateResolver.Prepare(p,source,"relics",native,r=>r.Id.ToString(),count,true,branches,dependencies);
}
public static class PotionEligibilityResolver
{
    public static bool IsEligible(Player p,string id,string source,bool nativeAllowed,IReadOnlyDictionary<string,CompatibilityGenerationBudget>? dependencies=null)
        =>GenericCompatibility.Registry.IsPotionEligible(id,CompatibilityCandidateResolver.Context(p,source,nativeAllowed,dependencies));
    public static CompatibilityCandidateSet<PotionModel> Prepare(Player p,string source,IEnumerable<PotionModel> native,int count=1,
        IReadOnlyDictionary<string,IReadOnlyList<PotionModel>>? branches=null,IReadOnlyDictionary<string,CompatibilityGenerationBudget>? dependencies=null)
        =>CompatibilityCandidateResolver.Prepare(p,source,"potions",native,potion=>potion.Id.ToString(),count,true,branches,dependencies);
}
public static class EventEligibilityResolver
{
    public static bool IsEligible(Player p,string id,string source,bool nativeAllowed,IReadOnlyDictionary<string,CompatibilityGenerationBudget>? dependencies=null)
        =>GenericCompatibility.Registry.IsEventEligible(id,CompatibilityCandidateResolver.Context(p,source,nativeAllowed,dependencies));
    public static CompatibilityCandidateSet<EventModel> Prepare(Player p,string source,IEnumerable<EventModel> native,
        IReadOnlyDictionary<string,CompatibilityGenerationBudget>? dependencies=null)
        =>CompatibilityCandidateResolver.Prepare(p,source,"events",native,ev=>ev.Id.ToString(),1,true,null,dependencies);
}
