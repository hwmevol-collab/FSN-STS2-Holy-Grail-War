using MegaCrit.Sts2.Core.Models.Relics;
using MegaCrit.Sts2.Core.Models.Potions;
using MegaCrit.Sts2.Core.Models.Events;
using MegaCrit.Sts2.Core.Models.PotionPools;
using MegaCrit.Sts2.Core.Models.Powers;
using MegaCrit.Sts2.Core.Entities.Potions;
using MegaCrit.Sts2.Core.Rewards;
using MegaCrit.Sts2.Core.Localization;
using System.Reflection;
namespace RinArcherCore;

// Exact curated additions to Matrix04. Classification and native pools stay authoritative.
public static class E2CCustomAdapters
{
    public const string Revision="E2C_CUSTOM_ADAPTERS_01";
    public static readonly IReadOnlySet<string> Ids=new HashSet<string>([
        "RELIC.ICE_CREAM","RELIC.ODDLY_SMOOTH_STONE","RELIC.KUNAI",
        "POTION.DEXTERITY_POTION","POTION.FOUL_POTION","EVENT.POTION_COURIER"],StringComparer.Ordinal);
    public static bool Audited(string id)=>Ids.Contains(id);
    public static IReadOnlySet<string> Ready(Player p)=>GenericCompatibility.Enabled(p)&&GenericCompatibility.Registry.IsValid?Ids:new HashSet<string>();
    public static bool IsReady(string id,CompatibilityEligibilityContext c)=>c.CustomReadyContentIds?.Contains(id)==true&&Ids.Contains(id);
    public static bool ClosedConditionalBranch(CompatibilityDependency edge,CompatibilityEligibilityContext c)
        =>edge.SourceId=="POTION.FOUL_POTION"&&edge.TargetId=="EVENT.FAKE_MERCHANT"&&edge.Semantics=="CONDITIONAL_BRANCH"
          &&IsReady(edge.SourceId,c)&&c.CustomReadyContentIds?.Contains(edge.TargetId)!=true;
    public static bool ResetEnergy(ContractRuntime d)=>!GenericCompatibility.Enabled(d.Player)||MegaCrit.Sts2.Core.Hooks.Hook.ShouldPlayerResetEnergy(d.Combat,d.Player);
}

// Fake Merchant remains closed, including use of a saved Foul bottle in that room.
// Normal shop/combat paths retain the untouched native effect and complete budget.
[HarmonyPatch(typeof(FoulPotion),"get_PassesCustomUsabilityCheck")]
public static class E2CFoulClosedBranch
{
    public static bool Blocked(PotionModel p)=>p is FoulPotion&&GenericCompatibility.Enabled(p.Owner)
        &&p.Owner.RunState.CurrentRoom is MegaCrit.Sts2.Core.Rooms.EventRoom {CanonicalEvent:FakeMerchant};
    static void Postfix(FoulPotion __instance,ref bool __result){if(Blocked(__instance))__result=false;}
}

// One root cause: native Dexterity reads Player.Creature, while both card owners share Player.
// Resolve the actual instance's member; non-Contract powers use untouched native code.
[HarmonyPatch(typeof(DexterityPower),nameof(DexterityPower.ModifyBlockAdditive))]
public static class E2CDexterityMember
{
    static bool Prefix(DexterityPower __instance,Creature target,ValueProp props,CardModel? cardSource,ref decimal __result)
    {
        var d=ContractRuntime.For(__instance.Owner);if(d==null||!GenericCompatibility.Enabled(d.Player))return true;
        Creature owner=cardSource is StarterCard s?d.Member(s.OwnerCharacterId).Creature:target;
        __result=owner==__instance.Owner&&props.IsPoweredCardOrMonsterMoveBlock()?__instance.Amount:0;return false;
    }
}

// Keep both native event choices. Fixed three bottles remain three rewards; the random
// Uncommon branch validates/filter its native pool before the single native RNG roll.
[HarmonyPatch(typeof(PotionCourier),"Ransack")]
public static class E2CCourierRandomReward
{
    static bool Prefix(PotionCourier __instance,ref Task __result)
    {
        if(!E2CCustomAdapters.Ready(__instance.Owner!).Contains(__instance.Id.ToString()))return true;
        __result=Ransack(__instance);return false;
    }
    static async Task Ransack(PotionCourier ev)
    {
        var p=ev.Owner!;
        var native=p.Character.PotionPool.GetUnlockedPotions(p.UnlockState).Concat(ModelDb.PotionPool<SharedPotionPool>().GetUnlockedPotions(p.UnlockState)).Where(x=>x.Rarity==PotionRarity.Uncommon).ToArray();
        var candidates=PotionEligibilityResolver.Prepare(p,"E2C_POTION_COURIER_RANSACK",native);
        if(!candidates.CompleteBudget)throw new CompatibilitySourceUnavailableException(candidates.RejectionReason);
        var potion=p.PlayerRng.Rewards.NextItem(candidates.Candidates)!;
        await RewardsCmd.OfferCustom(p,[new PotionReward(potion.ToMutable(),p)]);
        AccessTools.Method(typeof(EventModel),"SetEventFinished").Invoke(ev,[new LocString("events","POTION_COURIER.pages.RANSACK.description")]);
        ContractSave.Log(p,"E2C_COURIER_REWARD",new{count=1,potion=potion.Id.ToString(),nativeRarity="Uncommon"});
    }
}
