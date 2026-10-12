namespace RinArcherCore;
public static class PublicUiMode
{
    public const string Flag="PUBLIC_UI_MODE";
    public static bool CreatingDebugRun;
    // Legacy D1 saves adopt public presentation; explicit QA entries opt out.
    public static bool IsPublic(Player p)=>p.Character is RinContractCharacter&&ContractSave.Get(p).RunFlags.GetValueOrDefault(Flag,true);
}
