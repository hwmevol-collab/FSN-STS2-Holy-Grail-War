using STS2RitsuLib.RunData;
using MegaCrit.Sts2.Core.Runs;
namespace RinArcherCore;
// Vanilla saves at room boundaries, not arbitrary mid-action combat checkpoints.
// Permanent Archer deck uses Ritsu's RunPersistent pile serializer; HP uses this slot.
public sealed class ContractRunData
{
    public int Schema{get;set;}=1;
    public string ContractId{get;set;}=ContractRuntime.ContractId;
    public int ArcherHp{get;set;}=76;
    public int ArcherMaxHp{get;set;}=76;
}
public static class ContractSave
{
    public static PlayerRunSavedData<ContractRunData> Slot=null!;
    public static void Register()=>Slot=RunSavedDataStore.For("RinArcherCore").RegisterPerPlayer<ContractRunData>("contract_alpha");
    public static ContractRunData Get(Player p)=>Slot.Get((RunState)p.RunState,p.NetId);
    public static void Store(ContractRuntime d)=>Slot.Set((RunState)d.Player.RunState,d.Player.NetId,new(){ArcherHp=d.Archer.Creature.CurrentHp,ArcherMaxHp=d.Archer.Creature.MaxHp});
}
