using System.Reflection;
using MegaCrit.Sts2.Core.Models.Events;
using MegaCrit.Sts2.Core.Models.Relics;
using MegaCrit.Sts2.Core.Models.Powers;
using MegaCrit.Sts2.Core.Entities.Ascension;
using MegaCrit.Sts2.Core.Extensions;
using MegaCrit.Sts2.Core.HoverTips;
using MegaCrit.Sts2.Core.Rooms;
namespace RinArcherCore;

// Only the missing third-act transaction and its fixed native dependency.
public static class FullActThirdAncientBridge
{
    public const string Cape="RELIC.DISTINGUISHED_CAPE";
    public static readonly IReadOnlySet<string> Ids=new HashSet<string>(["EVENT.VAKUU","EVENT.NONUPEIPE","EVENT.TANX"]);
    public static bool Ready(Player p)=>FullActRoomSpine.Enabled(p)&&GenericCompatibility.Registry.IsValid;
    public static bool CapeSource(string source)=>source is "E2B_NATIVE_ANCIENT_OPTION" or "NATIVE_OBTAIN";
}

[HarmonyPatch]
public static class FullActThirdAncientOptionPools
{
    static IEnumerable<MethodBase> TargetMethods()=>new[]{"Pool1","Pool2","Pool3"}.Select(n=>AccessTools.PropertyGetter(typeof(Vakuu),n))
        .Concat(new[]{AccessTools.PropertyGetter(typeof(Nonupeipe),"OptionPool"),AccessTools.PropertyGetter(typeof(Tanx),"BaseOptionPool")});
    static void Postfix(AncientEventModel __instance,ref IEnumerable<MegaCrit.Sts2.Core.Events.EventOption> __result)
    {
        var p=__instance.IsMutable?__instance.Owner:FullActAncientBridge.Generating.Value;
        if(p!=null&&FullActThirdAncientBridge.Ready(p))__result=__result.Where(o=>o.Relic is {} r&&FullActAncientBridge.Allowed(p,r)).ToArray();
    }
}

[HarmonyPatch]
public static class FullActThirdAncientDistinctOffers
{
    static IEnumerable<MethodBase> TargetMethods()=>new[]{AccessTools.Method(typeof(Nonupeipe),"GenerateInitialOptions"),AccessTools.Method(typeof(Tanx),"GenerateInitialOptions")};
    static bool Prefix(AncientEventModel __instance,ref IReadOnlyList<MegaCrit.Sts2.Core.Events.EventOption> __result)
    {
        var p=__instance.Owner;if(p==null||!FullActThirdAncientBridge.Ready(p))return true;
        var name=__instance is Nonupeipe?"OptionPool":"BaseOptionPool";
        var options=((IEnumerable<MegaCrit.Sts2.Core.Events.EventOption>)AccessTools.Property(__instance.GetType(),name).GetValue(__instance)!).ToList();
        // The optional enchantment relics remain C/unavailable; do not inject
        // them after filtering the native base pool, or shorten a three-offer roll.
        if(options.Count<3)throw new CompatibilitySourceUnavailableException("THIRD_ANCIENT_DISTINCT_BUDGET_UNAVAILABLE");
        __result=options.UnstableShuffle(__instance.Rng).Take(3).ToArray();return false;
    }
}

// Mirror the native public entry heal, including ascension's missing-HP fraction.
// A stable room receipt prevents repeat entry/Continue from granting it again.
[HarmonyPatch(typeof(AncientEventModel),"BeforeEventStarted")]
public static class FullActContractAncientHeal
{
    static string Key(Player p)=>"V13_ANCIENT_ENTRY_HEAL/"+RunEconomy.RoomKey(p);
    static bool Prefix(AncientEventModel __instance,bool isPreFinished,ref Task __result)
    {
        if(!isPreFinished&&__instance.Owner is {} p&&FullActRoomSpine.Enabled(p)&&ContractSave.Get(p).RunFlags.GetValueOrDefault(Key(p)))
        {__result=Task.CompletedTask;return false;}return true;
    }
    static void Postfix(AncientEventModel __instance,bool isPreFinished,ref Task __result)
    {
        var p=__instance.Owner;if(!isPreFinished&&p!=null&&FullActRoomSpine.Enabled(p)&&!ContractSave.Get(p).RunFlags.GetValueOrDefault(Key(p)))__result=After(__result,p,__instance);
    }
    static async Task After(Task original,Player p,AncientEventModel ancient)
    {
        await original;
        var c=MemberTargetResolver.Creature(p,RunEconomy.Archer);int before=c.CurrentHp;
        if(ancient is Neow)c.SetCurrentHpInternal(0);
        decimal amount=c.MaxHp-c.CurrentHp;
        if(RunManager.Instance.HasAscension(AscensionLevel.WearyTraveler))amount*=0.8m;
        await CreatureCmd.Heal(c,amount,playAnim:false);
        MemberTargetResolver.Synchronize(p);ContractSave.Get(p).RunFlags[Key(p)]=true;
        ContractSave.Log(p,"CONTRACT_ANCIENT_ENTRY_HEAL",new{ancient=ancient.Id.ToString(),archerBefore=before,archerAfter=c.CurrentHp,archerMax=c.MaxHp,rinAfter=p.Creature.CurrentHp,amount});
    }
}

// Keep the original 9 MaxHP + three Apparitions budget on one chosen member.
[HarmonyPatch(typeof(DistinguishedCape),nameof(RelicModel.AfterObtained))]
public static class FullActVakuuCapeEffect
{
    static string Binding=>FullActThirdAncientBridge.Cape+"/AfterObtained";
    public static async Task<bool> ChooseBeforeObtain(Player p,RelicModel relic,bool cancellable)
    {
        int loss=relic.DynamicVars.HpLoss.IntValue;
        var preview=MemberTargetResolver.Preview(p,c=>(Math.Min(c.CurrentHp,c.MaxHp-loss),c.MaxHp-loss)).Select(v=>v with{Eligible=v.MaxHp>loss}).ToArray();
        // Native Ancient options commit WasChosen before acquiring their relic.
        // Once committed, select a member without offering an unusable rollback.
        bool canCancel=cancellable&&p.RunState.CurrentRoom is not EventRoom {CanonicalEvent:AncientEventModel};
        var member=await MemberTargetResolver.Choose(p,Binding,preview,"选择承担9点生命上限损失并获得3张灵体的成员",canCancel);
        if(member==null)return false;
        MemberTargetResolver.Persist(p,Binding,member);return true;
    }
    static bool Prefix(DistinguishedCape __instance,ref Task __result)
    {if(!FullActThirdAncientBridge.Ready(__instance.Owner))return true;__result=Obtain(__instance);return false;}
    static async Task Obtain(DistinguishedCape relic)
    {
        var p=relic.Owner;var state=ContractSave.Get(p);string key=FullActThirdAncientBridge.Cape+"/"+RunEconomy.RoomKey(p);
        if(state.RunFlags.GetValueOrDefault(key))return;
        int loss=relic.DynamicVars.HpLoss.IntValue;
        if(!state.Compatibility.MemberBindings.ContainsKey(Binding)&&!await ChooseBeforeObtain(p,relic,false))throw new OperationCanceledException();
        string member=state.Compatibility.MemberBindings[Binding];
        await CreatureCmd.LoseMaxHp(new ThrowingPlayerChoiceContext(),MemberTargetResolver.Creature(p,member),loss,isFromCard:false);
        var results=new List<MegaCrit.Sts2.Core.Entities.Cards.CardPileAddResult>();
        for(int i=0;i<relic.DynamicVars.Cards.IntValue;i++)
        {
            var c=(FullActOwnedApparition)p.RunState.CreateCard(ModelDb.Card<FullActOwnedApparition>(),p);
            c.NativeCardOwner=member;c.InstanceId="native-apparition:"+member+":"+(++state.NextPermanentInstance);
            results.Add(await CardPileCmd.Add(c,ContractSave.Deck(p,member)));
        }
        CardCmd.PreviewCardPileAdd(results,2f);state.RunFlags[key]=true;MemberTargetResolver.Synchronize(p);
    }
}

[Pool(typeof(RinArcherPool))]
public sealed class FullActOwnedApparition():StarterCard(CardType.Skill,TargetType.Self,1,false,CardRarity.Ancient)
{
    [MegaCrit.Sts2.Core.Saves.Runs.SavedProperty] public string NativeCardOwner{get;set;}=RunEconomy.Rin;
    public override string SourceCardId=>"VANILLA_APPARITION";
    public override string OwnerCharacterId=>NativeCardOwner;
    public override IEnumerable<CardKeyword> CanonicalKeywords=>[CardKeyword.Ethereal,CardKeyword.Exhaust];
    protected override IEnumerable<DynamicVar> CanonicalVars=>[new PowerVar<IntangiblePower>(1)];
    protected override IEnumerable<IHoverTip> ExtraHoverTips=>[HoverTipFactory.FromPower<IntangiblePower>()];
    protected override string NameText=>"灵体";
    protected override string RulesText=>"获得1层无实体。消耗。"+(IsUpgraded?"":"虚无。");
    protected override Task OnPlay(PlayerChoiceContext ctx,CardPlay play)=>PowerCmd.Apply<IntangiblePower>(ctx,Runtime.Member(OwnerCharacterId).Creature,1,Runtime.Member(OwnerCharacterId).Creature,this);
    protected override void OnUpgrade()=>RemoveKeyword(CardKeyword.Ethereal);
}
