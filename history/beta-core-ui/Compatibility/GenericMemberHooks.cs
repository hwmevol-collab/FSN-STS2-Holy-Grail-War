using System.Globalization;
using System.Reflection;
using System.Text.RegularExpressions;
using MegaCrit.Sts2.Core.Entities.Merchant;
using MegaCrit.Sts2.Core.Rewards;
namespace RinArcherCore;

public static class GenericMemberEffects
{
    static readonly AsyncLocal<HashSet<AbstractModel>?> Prepared=new();
    public static bool IsPrepared(AbstractModel model)=>Prepared.Value?.Contains(model)==true;
    static bool NeedsMember(AbstractModel model,string trigger)=>FriendlyPotionTargeting.ChoosesHand(model,trigger)||GenericCompatibility.Registry.GetEffectScopes(model.Id.ToString()).Any(r=>r.Scope=="CHOOSE_MEMBER"&&r.Trigger==trigger);
    public static IReadOnlyList<MemberValuePreview> Preview(Player p,AbstractModel model,string trigger="AfterObtained",object[]? args=null)
    {
        var rows=GenericCompatibility.Registry.GetEffectScopes(model.Id.ToString()).Where(r=>r.Scope=="CHOOSE_MEMBER"&&r.Trigger==trigger&&r.Evidence.TryGetProperty("api",out _)).ToArray();
        var previews=MemberTargetResolver.Preview(p,c=>
        {
            int hp=c.CurrentHp,max=c.MaxHp;
            if(!NativeMemberTriggerConditions.Eligible(model,trigger,p,c,args??[]))return(hp,max);
            foreach(var row in rows)
            {
                string api=row.Evidence.GetProperty("api").GetString()!;
                if(api is not ("CreatureCmd.Heal" or "CreatureCmd.GainMaxHp" or "CreatureCmd.LoseMaxHp"))continue;
                string expression=row.Evidence.GetProperty("arguments")[1].GetString()!;
                var amount=expression=="creature.MaxHp - creature.CurrentHp"?max-hp:Amount(model,expression,c,args??[]);
                if(api=="CreatureCmd.Heal")hp=(int)Math.Clamp(hp+amount,0,max);
                else if(api=="CreatureCmd.GainMaxHp"){max=(int)(max+amount);hp=(int)Math.Min(max,hp+amount);}
                else{max=(int)Math.Max(1,max-amount);hp=Math.Min(hp,max);}
            }
            return(hp,max);
        });
        return previews.Select(preview=>preview with{Eligible=NativeMemberTriggerConditions.Eligible(model,trigger,p,MemberTargetResolver.Creature(p,preview.Member),args??[])}).ToArray();
    }
    static decimal Amount(AbstractModel model,string expression,Creature target,object[] args)
    {
        string value=Regex.Replace(expression,@"\s+","");
        var match=Regex.Match(value,"base\\.DynamicVars(?:\\.(?<key>\\w+)|\\[\"(?<key>[^\"]+)\"\\])");
        decimal amount;
        if(match.Success)
        {
            var variables=model switch{RelicModel r=>r.DynamicVars,PotionModel p=>p.DynamicVars,_=>throw new InvalidOperationException("Unsupported preview model")};
            amount=variables[match.Groups["key"].Value].BaseValue;
        }
        else if(!decimal.TryParse(value.TrimEnd('m'),NumberStyles.Number,CultureInfo.InvariantCulture,out amount))throw new InvalidOperationException("MEMBER_VALUE_PREVIEW_NOT_VALIDATED: "+expression);
        string remainder=match.Success?value.Remove(match.Index,match.Length):value;
        if(remainder.Contains(".MaxHp",StringComparison.Ordinal))
        {
            if(!value.Contains("/100m",StringComparison.Ordinal)&&!value.Contains("/100",StringComparison.Ordinal))throw new InvalidOperationException("MEMBER_PERCENT_PREVIEW_NOT_VALIDATED: "+expression);
            amount=target.MaxHp*amount/100m;
        }
        else if(remainder==".BaseValue*(decimal)num")
        {
            // Native count expression, bound to the real hook argument. It does
            // not roll content, spend resources or execute the effect for preview.
            var creatures=args.OfType<IReadOnlyList<Creature>>().Single();
            amount*=creatures.Count(c=>c!=target&&c.Powers.All(power=>power.ShouldOwnerDeathTriggerFatal()));
        }
        else if(match.Success&&remainder is not (".BaseValue" or ".IntValue"))throw new InvalidOperationException("MEMBER_VALUE_EXPRESSION_NOT_VALIDATED: "+expression);
        return amount;
    }
    public static async Task<bool> Prepare(Player p,AbstractModel model,string trigger,bool cancellable=true,object[]? args=null)
    {
        if(model.Id.ToString()==FullActThirdAncientBridge.Cape&&trigger=="AfterObtained"&&FullActThirdAncientBridge.Ready(p))
            return await FullActVakuuCapeEffect.ChooseBeforeObtain(p,(RelicModel)model,cancellable);
        bool deck=GenericCompatibility.Registry.GetEffectScopes(model.Id.ToString()).Any(r=>r.Scope=="CHOOSE_DECK"&&r.Trigger==trigger);
        if(!NeedsMember(model,trigger)&&!deck)return true;
        string title=model switch{RelicModel r=>r.Title.GetFormattedText(),PotionModel potion=>potion.Title.GetFormattedText(),_=>throw new InvalidOperationException("Unsupported member effect model")};
        if(deck)title+="\n选择永久牌组\nMASTER — Rin: "+ContractSave.Deck(p,RunEconomy.Rin).Cards.Count+" 张\nSERVANT — Archer: "+ContractSave.Deck(p,RunEconomy.Archer).Cards.Count+" 张";
        var selected=await MemberTargetResolver.Choose(p,model.Id+"/"+trigger,deck?[]:Preview(p,model,trigger,args),title,cancellable);
        if(selected==null)return false;
        if(NeedsMember(model,trigger))MemberTargetResolver.Persist(p,model.Id+"/"+trigger,selected);
        foreach(var row in GenericCompatibility.Registry.GetEffectScopes(model.Id.ToString()).Where(r=>r.Scope is "CHOOSE_MEMBER" or "CHOOSE_DECK"&&r.Trigger==trigger))
            MemberTargetResolver.Persist(p,model.Id+"/"+row.Trigger,selected);
        return true;
    }
    public static async Task<T> InvokePrepared<T>(AbstractModel model,Func<Task<T>> original)
    {
        var before=Prepared.Value;Prepared.Value=before==null?new(ReferenceEqualityComparer.Instance):new(before,ReferenceEqualityComparer.Instance);Prepared.Value.Add(model);
        try{return await original();}finally{Prepared.Value=before;}
    }
    public static async Task Use(PotionModel potion,PlayerChoiceContext choice,Creature? target,MethodBase original)
    {
        var p=potion.Owner;
        if(!PotionEligibilityResolver.IsEligible(p,potion.Id.ToString(),"NATIVE_POTION_USE",true))throw new CompatibilitySourceUnavailableException("Potion source budget/readiness unavailable before consumption");
        if(FriendlyPotionTargeting.ConsumeSelection(potion,target,out var chosen))
        {
            MemberTargetResolver.Persist(p,potion.Id+"/OnUse",chosen!);
            ContractSave.Log(p,"MEMBER_TARGET_SELECTED",new{effectId=potion.Id+"/OnUse",member=chosen,presentation="FRIENDLY_POTION_TARGETING"});
        }
        else if(!await Prepare(p,potion,"OnUse")){potion.AfterUsageCanceled();return;}
        if(ContractSave.Get(p).Compatibility.MemberBindings.TryGetValue(potion.Id+"/OnUse",out var member))target=MemberTargetResolver.Creature(p,member);
        await InvokePrepared(potion,async()=>{await (Task)original.Invoke(potion,[choice,target])!;return true;});
        MemberTargetResolver.Synchronize(p);
    }
    public static async Task<RelicModel> Obtain(RelicModel relic,Player p,int index,MethodBase original)
    {
        if(!GenericTreasureSource.ConsumePreselection(p,relic.Id.ToString())&&!await Prepare(p,relic,"AfterObtained"))throw new OperationCanceledException("Member target selection cancelled before relic acquisition");
        var result=await InvokePrepared(relic,()=> (Task<RelicModel>)original.Invoke(null,[relic,p,index])!);
        MemberTargetResolver.Synchronize(p);ContractSave.Log(p,"COMPAT_CONTENT_ACQUIRED",new{contentId=relic.Id.ToString(),source="NATIVE_RELIC_OBTAIN"});return result;
    }
}
[HarmonyPatch(typeof(PotionModel),nameof(PotionModel.OnUseWrapper))]
public static class GenericMemberPotionUse
{
    static bool Prefix(PotionModel __instance,PlayerChoiceContext choiceContext,Creature? target,MethodBase __originalMethod,ref Task __result)
    {if(!GenericCompatibility.Enabled(__instance.Owner)||GenericMemberEffects.IsPrepared(__instance))return true;__result=GenericMemberEffects.Use(__instance,choiceContext,target,__originalMethod);return false;}
}
[HarmonyPatch(typeof(PotionModel),nameof(PotionModel.IsValidTarget))]
public static class GenericMemberPotionTarget
{
    static void Postfix(PotionModel __instance,Creature? target,ref bool __result)
    {
        if(target==null||!target.IsAlive||!GenericCompatibility.Enabled(__instance.Owner))return;
        if(FriendlyPotionTargeting.RequiresMember(__instance))
            __result=target==MemberTargetResolver.Creature(__instance.Owner,RunEconomy.Rin)||target==MemberTargetResolver.Creature(__instance.Owner,RunEconomy.Archer);
    }
}
[HarmonyPatch(typeof(RelicCmd),nameof(RelicCmd.Obtain),[typeof(RelicModel),typeof(Player),typeof(int)])]
public static class GenericMemberRelicObtain
{
    static bool Prefix(RelicModel relic,Player player,int index,MethodBase __originalMethod,ref Task<RelicModel> __result)
    {if(!GenericCompatibility.Enabled(player)||GenericMemberEffects.IsPrepared(relic))return true;__result=GenericMemberEffects.Obtain(relic,player,index,__originalMethod);return false;}
}
[HarmonyPatch(typeof(RelicReward),"OnSelect")]
public static class GenericRelicRewardSelection
{
    static readonly AsyncLocal<bool> Original=new();
    static bool Prefix(RelicReward __instance,MethodBase __originalMethod,ref Task<bool> __result)
    {if(Original.Value||!GenericCompatibility.Enabled(__instance.Player))return true;__result=Select(__instance,__originalMethod);return false;}
    static async Task<bool> Select(RelicReward reward,MethodBase method)
    {
        var relic=reward.Relic??throw new InvalidOperationException("Unpopulated relic source");
        if(!await GenericMemberEffects.Prepare(reward.Player,relic,"AfterObtained"))return false;
        bool result=await GenericMemberEffects.InvokePrepared(relic,async()=>{Original.Value=true;try{return await (Task<bool>)method.Invoke(reward,null)!;}finally{Original.Value=false;}});
        if(result){MemberTargetResolver.Synchronize(reward.Player);ContractSave.Log(reward.Player,"COMPAT_CONTENT_ACQUIRED",new{contentId=relic.Id.ToString(),source="NATIVE_RELIC_REWARD"});}
        return result;
    }
}
[HarmonyPatch(typeof(MerchantEntry),nameof(MerchantEntry.OnTryPurchaseWrapper))]
public static class GenericMerchantMemberSelection
{
    static readonly AsyncLocal<bool> Original=new();
    static bool Prefix(MerchantEntry __instance,MerchantInventory? inventory,bool ignoreCost,MethodBase __originalMethod,ref Task<bool> __result)
    {
        if(Original.Value||__instance is not MerchantRelicEntry {Model:{} model})return true;
        var p=(Player)AccessTools.Field(typeof(MerchantEntry),"_player").GetValue(__instance)!;
        if(!GenericCompatibility.Enabled(p)||!__instance.IsStocked||!ignoreCost&&!__instance.EnoughGold)return true;
        __result=Purchase(__instance,p,model,inventory,ignoreCost,__originalMethod);return false;
    }
    static async Task<bool> Purchase(MerchantEntry entry,Player p,RelicModel model,MerchantInventory? inventory,bool ignoreCost,MethodBase original)
    {
        if(!await GenericMemberEffects.Prepare(p,model,"AfterObtained"))return false;
        bool result=await GenericMemberEffects.InvokePrepared(model,async()=>{Original.Value=true;try{return await (Task<bool>)original.Invoke(entry,[inventory,ignoreCost])!;}finally{Original.Value=false;}});
        if(result){MemberTargetResolver.Synchronize(p);ContractSave.Log(p,"COMPAT_CONTENT_ACQUIRED",new{contentId=model.Id.ToString(),source="NATIVE_MERCHANT"});}
        return result;
    }
}
