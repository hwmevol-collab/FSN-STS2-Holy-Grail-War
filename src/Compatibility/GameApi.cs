using System.Reflection;
using MegaCrit.Sts2.Core.Nodes.CommonUi;
using MegaCrit.Sts2.Core.Entities.Creatures;
using MegaCrit.Sts2.Core.ValueProps;
namespace RinArcherCore;

// Keep the real dealer and play; the new convenience overload derives dealer from Player.Creature.
public static class GameApi
{
    public static MethodInfo PileAdd=>AccessTools.Method(typeof(CardPileCmd),nameof(CardPileCmd.Add),
#if GAME_0107
        [typeof(IEnumerable<CardModel>),typeof(CardPile),typeof(CardPilePosition),typeof(AbstractModel),typeof(bool)]);
#else
        [typeof(IEnumerable<CardModel>),typeof(CardPile),typeof(CardPilePosition),typeof(AbstractModel),typeof(bool),typeof(bool)]);
#endif
    internal static readonly AsyncLocal<CardPlay?> CurrentPlay=new();
    public static Task<IEnumerable<DamageResult>> Damage(PlayerChoiceContext ctx,Creature target,decimal amount,ValueProp props,Creature? dealer,CardModel? source,CardPlay? play=null)
    {
#if GAME_0107
        return CreatureCmd.Damage(ctx,target,amount,props,dealer,source);
#else
        return CreatureCmd.Damage(ctx,target,amount,props,dealer,source,play??(CurrentPlay.Value?.Card==source?CurrentPlay.Value:null));
#endif
    }
    public static bool IsDirectionalNavigation=>
#if GAME_0107
        NControllerManager.Instance?.IsUsingController??false;
#else
        NControllerManager.Instance?.IsUsingDirectionalNavigation??false;
#endif
}
#if !GAME_0107
[HarmonyPatch]
public static class GameCardPlayScope
{
    static IEnumerable<MethodBase> TargetMethods()=>typeof(StarterCard).Assembly.GetTypes().Where(t=>typeof(StarterCard).IsAssignableFrom(t))
        .SelectMany(t=>t.GetMethods(BindingFlags.Instance|BindingFlags.NonPublic|BindingFlags.DeclaredOnly)).Where(m=>m.Name=="OnPlay"&&m.ReturnType==typeof(Task));
    static void Prefix(CardPlay __1,out CardPlay? __state){__state=GameApi.CurrentPlay.Value;GameApi.CurrentPlay.Value=__1;}
    static void Postfix(CardPlay? __state)=>GameApi.CurrentPlay.Value=__state;
    static Exception? Finalizer(Exception? __exception,CardPlay? __state){GameApi.CurrentPlay.Value=__state;return __exception;}
}
#endif
