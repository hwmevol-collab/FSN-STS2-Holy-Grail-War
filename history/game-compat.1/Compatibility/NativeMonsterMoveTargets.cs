using MegaCrit.Sts2.Core.Models.Monsters;
namespace RinArcherCore;

// Shrinker has no stored member lock: its move receives all native player bodies.
// Adapt this audited FRONT debuff only. Other moves may require Player identities
// or explicit locks, so do not globally rewrite their target lists/PowerCmd calls.
[HarmonyPatch(typeof(ShrinkerBeetle),"ShrinkMove")]
public static class NativeMonsterMoveTargets
{
    public static int PatchedSites=>1;
    public static IReadOnlyList<Creature> FrontTargets(IReadOnlyList<Creature> targets)
        =>targets.Select(c=>ContractRuntime.For(c) is {Finished:false} d&&FullActRoomSpine.Enabled(d.Player)?d.Active.Creature:c).Distinct().ToArray();
    static void Prefix(ref IReadOnlyList<Creature> targets)=>targets=FrontTargets(targets);
}
