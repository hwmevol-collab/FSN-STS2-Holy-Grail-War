using System.Reflection;
using MegaCrit.Sts2.Core.CardSelection;
namespace RinArcherCore;

// Exact additions reviewed against the v0.107.1 effect rows. Native eligibility is
// still evaluated first; readiness neither changes classification nor creates a pool.
public static class VanillaExpandedAdapters
{
    public const string Revision="VANILLA_COMPAT_20261012_01";
    public static readonly IReadOnlySet<string> Ids=new HashSet<string>([
        "EVENT.ABYSSAL_BATHS","EVENT.BATTLEWORN_DUMMY","EVENT.BRAIN_LEECH","EVENT.BUGSLAYER","EVENT.BYRDONIS_NEST",
        "EVENT.DENSE_VEGETATION","EVENT.DROWNING_BEACON","EVENT.FIELD_OF_MAN_SIZED_HOLES","EVENT.GRAVE_OF_THE_FORGOTTEN",
        "EVENT.INFESTED_AUTOMATON","EVENT.LUMINOUS_CHOIR","EVENT.MORPHIC_GROVE","EVENT.PUNCH_OFF","EVENT.RANWID_THE_ELDER",
        "EVENT.ROUND_TEA_PARTY","EVENT.SAPPHIRE_SEED","EVENT.SELF_HELP_BOOK","EVENT.SPIRALING_WHIRLPOOL","EVENT.SPIRIT_GRAFTER",
        "EVENT.STONE_OF_ALL_TIME","EVENT.SUNKEN_STATUE","EVENT.SUNKEN_TREASURY","EVENT.TEA_MASTER","EVENT.THE_LEGENDS_WERE_TRUE",
        "EVENT.THIS_OR_THAT","EVENT.TRASH_HEAP","EVENT.UNREST_SITE","EVENT.WATERLOGGED_SCRIPTORIUM","EVENT.AROMA_OF_CHAOS",
        "EVENT.WELCOME_TO_WONGOS","EVENT.WELLSPRING","EVENT.WHISPERING_HOLLOW","EVENT.WOOD_CARVINGS","EVENT.ZEN_WEAVER",
        "RELIC.ARCANE_SCROLL","RELIC.BEAUTIFUL_BRACELET","RELIC.BIG_HAT","RELIC.BIIIG_HUG","RELIC.BLACK_STAR",
        "RELIC.BLOOD_SOAKED_ROSE","RELIC.CALLING_BELL","RELIC.CURSED_PEARL","RELIC.DOLLYS_MIRROR","RELIC.DREAM_CATCHER",
        "RELIC.DUSTY_TOME","RELIC.ETERNAL_FEATHER","RELIC.FROZEN_EGG","RELIC.GNARLED_HAMMER","RELIC.JEWELRY_BOX","RELIC.KIFUDA",
        "RELIC.LAVA_ROCK","RELIC.MASSIVE_SCROLL","RELIC.MEAT_CLEAVER","RELIC.MOLTEN_EGG","RELIC.ORANGE_DOUGH",
        "RELIC.PUNCH_DAGGER","RELIC.PRAYER_WHEEL","RELIC.PRESERVED_FOG","RELIC.REGAL_PILLOW","RELIC.ROYAL_STAMP",
        "RELIC.SELF_FORMING_CLAY","RELIC.STURDY_CLAMP","RELIC.SERE_TALON","RELIC.STORYBOOK","RELIC.TEA_OF_DISCOURTESY","RELIC.TINY_MAILBOX",
        "RELIC.TOOLBOX","RELIC.TOXIC_EGG","RELIC.TRI_BOOMERANG","RELIC.WHITE_BEAST_STATUE","RELIC.WHITE_STAR",
        "RELIC.LIZARD_TAIL","RELIC.PEN_NIB","RELIC.THE_BOOT","RELIC.JUZU_BRACELET","RELIC.WINGED_BOOTS",
        "RELIC.BELT_BUCKLE","RELIC.RED_SKULL","RELIC.FRESNEL_LENS","RELIC.SWORD_OF_STONE","RELIC.WONGOS_MYSTERY_TICKET",
        "RELIC.AMETHYST_AUBERGINE","RELIC.GORGET","RELIC.NEOWS_TORMENT","RELIC.WING_CHARM","RELIC.NEW_LEAF","RELIC.ASTROLABE"
    ],StringComparer.Ordinal);
    public static bool Audited(string id)=>Ids.Contains(id);
    public static IReadOnlySet<string> Ready(Player p)=>GenericCompatibility.Enabled(p)&&GenericCompatibility.Registry.IsValid?Ids:new HashSet<string>();
    public static bool IsReady(string id,CompatibilityEligibilityContext c)=>Ids.Contains(id)&&c.CustomReadyContentIds?.Contains(id)==true;
    public static string EventKey(Player p,EventModel ev)=>Revision+"/"+RunEconomy.RoomKey(p)+"/"+ev.Id;
    public static EffectScopeBinding EventBinding(Player p,EventModel ev,string trigger)
    {
        var rows=GenericCompatibility.Registry.GetEffectScopes(ev.Id.ToString());
        var key=EventKey(p,ev);
        var member=ContractSave.Get(p).Compatibility.MemberBindings.GetValueOrDefault(key);
        return new(p,ev.Id.ToString(),trigger,rows,member==null?null:MemberTargetResolver.Creature(p,member),null,rows.Any(r=>r.Scope=="CHOOSE_DECK")?member:null);
    }
}
[HarmonyPatch]
public static class VanillaEventMemberBeforeDisclosure
{
    [ThreadStatic] static bool invoking;
    static IEnumerable<MethodBase> TargetMethods()=>new[]{AccessTools.Method(typeof(EventModel),"BeforeEventStarted")}.Concat(GenericCompatibility.Registry.Entries.Where(e=>e.ContentId.StartsWith("EVENT.")&&VanillaExpandedAdapters.Audited(e.ContentId)).Select(e=>AccessTools.Method(typeof(ModelDb).Assembly.GetType(e.ModelType!),"BeforeEventStarted"))).Distinct();
    [HarmonyPriority(Priority.First+200)]
    static bool Prefix(EventModel __instance,bool isPreFinished,MethodBase __originalMethod,ref Task __result)
    {
        if(invoking||__instance.Owner is not {} player||!GenericCompatibility.Enabled(player)||!VanillaExpandedAdapters.Audited(__instance.Id.ToString()))return true;
        __result=Begin(__instance,player,isPreFinished,__originalMethod);return false;
    }
    static async Task Begin(EventModel ev,Player p,bool finished,MethodBase method)
    {
        string key=VanillaExpandedAdapters.EventKey(p,ev);
        var bindings=ContractSave.Get(p).Compatibility.MemberBindings;
        var rows=GenericCompatibility.Registry.GetEffectScopes(ev.Id.ToString());
        if(!finished&&!bindings.ContainsKey(key)&&rows.Any(r=>r.Scope is "CHOOSE_MEMBER" or "CHOOSE_DECK"))
        {
            var selected=await MemberTargetResolver.Choose(p,key,MemberTargetResolver.Preview(p,c=>(c.CurrentHp,c.MaxHp)),
                ev.Title.GetFormattedText()+"\n选择本次事件的角色；生命变化及新增卡牌归该角色，金币和奖励预算保持原版。",false);
            if(selected==null)throw new OperationCanceledException("Event member required before disclosure");
            MemberTargetResolver.Persist(p,key,selected);
        }
        using var scope=CompatibilityExecution.Bind(VanillaExpandedAdapters.EventBinding(p,ev,"BeginEvent"));
        Task task;invoking=true;try{task=(Task)method.Invoke(ev,[finished])!;}finally{invoking=false;}
        await task;MemberTargetResolver.Synchronize(p);
    }
}
[HarmonyPatch(typeof(EventModel),nameof(EventModel.BeginEvent))]
public static class VanillaEventInitializationScope
{
    static void Prefix(EventModel __instance,Player player,out IDisposable? __state)
    {__state=GenericCompatibility.Enabled(player)&&VanillaExpandedAdapters.Audited(__instance.Id.ToString())?CompatibilityExecution.Bind(VanillaExpandedAdapters.EventBinding(player,__instance,"BeginEvent")):null;}
    static void Postfix(IDisposable? __state)=>__state?.Dispose();
    static Exception? Finalizer(Exception? __exception,IDisposable? __state){__state?.Dispose();return __exception;}
}
[HarmonyPatch]
public static class VanillaEventTransactionScope
{
    static IEnumerable<MethodBase> TargetMethods()=>GenericCompatibility.Registry.Entries.Where(e=>e.ContentId.StartsWith("EVENT.")&&VanillaExpandedAdapters.Audited(e.ContentId))
        .Select(e=>typeof(ModelDb).Assembly.GetType(e.ModelType!)!).SelectMany(t=>t.GetMethods(BindingFlags.Instance|BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.DeclaredOnly)).Where(m=>m.ReturnType==typeof(Task)&&!m.ContainsGenericParameters);
    static void Prefix(EventModel __instance,MethodBase __originalMethod,out IDisposable? __state)
    {__state=__instance.Owner is {} p&&GenericCompatibility.Enabled(p)?CompatibilityExecution.Bind(VanillaExpandedAdapters.EventBinding(p,__instance,__originalMethod.Name)):null;}
    static void Postfix(EventModel __instance,IDisposable? __state,ref Task __result)
    {
        __state?.Dispose();
        if(__instance.Owner is {} p&&GenericCompatibility.Enabled(p))__result=After(__result,p);
    }
    static async Task After(Task task,Player p){await task;MemberTargetResolver.Synchronize(p);}
    static Exception? Finalizer(Exception? __exception,IDisposable? __state){__state?.Dispose();return __exception;}
}
// Generic/enchantment selectors share the actual permanent instance union and native prefs.
[HarmonyPatch(typeof(CardSelectCmd),nameof(CardSelectCmd.FromDeckGeneric))]
public static class VanillaDeckGenericSelection
{
    [HarmonyPriority(Priority.First+200)]
    static bool Prefix(Player player,CardSelectorPrefs prefs,Func<CardModel,bool>? filter,ref Task<IEnumerable<CardModel>> __result)
    {
        if(!GenericCompatibility.Enabled(player)||CompatibilityExecution.Current is not {} frame||!frame.Rows.Any(r=>r.Scope is "DUAL_DECK_SELECTOR" or "RANDOM_PERMANENT_CARD_UNION"))return true;
        __result=Select(player,prefs,filter,frame.DeckMember);return false;
    }
    static async Task<IEnumerable<CardModel>> Select(Player p,CardSelectorPrefs prefs,Func<CardModel,bool>? filter,string? member)
    {
        var cards=(member==null?DualDeckCardSelector.LegalPermanentUnion(p,c=>filter?.Invoke(c)??true):ContractSave.Deck(p,member).Cards.Where(c=>filter?.Invoke(c)??true).ToArray());
        if(CardSelectCmd.Selector!=null)return await CardSelectCmd.Selector.GetSelectedCards(cards,prefs.MinSelect,prefs.MaxSelect);
        return await CardSelectCmd.FromSimpleGrid(new BlockingPlayerChoiceContext(),cards,p,prefs);
    }
}
