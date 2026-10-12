namespace RinArcherCore;
public static class NativeMemberConditionContext
{
    static readonly AsyncLocal<HashSet<(AbstractModel Model,string Trigger)>?> NoEffect=new();
    public static bool UsesNativeRecipient(AbstractModel model,string trigger)=>NoEffect.Value?.Contains((model,trigger))==true;
    public static async Task RunWithoutPersonalEffect(AbstractModel model,string trigger,Func<Task> action)
    {
        var before=NoEffect.Value;NoEffect.Value=before==null?[]:new(before);NoEffect.Value.Add((model,trigger));
        try{await action();}finally{NoEffect.Value=before;}
    }
    public static bool AnyEligible(Player p,AbstractModel model,string trigger,object[] args)
        =>new[]{RunEconomy.Rin,RunEconomy.Archer}.Any(member=>NativeMemberTriggerConditions.Eligible(model,trigger,p,MemberTargetResolver.Creature(p,member),args));
    public static bool PrivateBool(AbstractModel model,Player p,Creature creature,string trigger,string method)
    {
        using var lease=CompatibilityExecution.Bind(new(p,model.Id.ToString(),trigger,[],creature,null));
        return (bool)AccessTools.Method(model.GetType(),method).Invoke(model,null)!;
    }
}
