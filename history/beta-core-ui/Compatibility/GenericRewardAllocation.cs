using System.Reflection;
using MegaCrit.Sts2.Core.Rewards;
namespace RinArcherCore;
[HarmonyPatch(typeof(RewardsSet),nameof(RewardsSet.GenerateWithoutOffering))]
public static class GenericRewardAllocationBeforeHiddenRoll
{
    static readonly AsyncLocal<bool> Prepared=new();
    [HarmonyPriority(Priority.First)]
    static bool Prefix(RewardsSet __instance,MethodBase __originalMethod,ref Task __result)
    {
        var p=__instance.Player;
        if(Prepared.Value||!GenericCompatibility.Enabled(p)||!__instance.Rewards.Any(r=>r is CardReward)||!DualRewardModifierResolver.HasOptionModifiers(p))return true;
        __result=Generate(__instance,__originalMethod);return false;
    }
    static async Task Generate(RewardsSet set,MethodBase method)
    {
        var p=set.Player;int index=ContractSave.Get(p).NextRewardIndex;
        if(!ContractSave.Get(p).Compatibility.RewardOptionModifierOwners.ContainsKey(index))
        {
            string owner=(await MemberTargetResolver.Choose(p,"DUAL_REWARD_OPTION_MODIFIER:"+index,[],"选择本次卡牌奖励加成的牌组\n奖励结果将在选择后生成。",false))??throw new InvalidOperationException("Reward bonus owner selection required");
            DualRewardModifierResolver.AllocateOptionModifiers(p,index,owner);
        }
        bool before=Prepared.Value;Prepared.Value=true;
        try{await (Task)method.Invoke(set,null)!;}
        finally{Prepared.Value=before;}
    }
}
