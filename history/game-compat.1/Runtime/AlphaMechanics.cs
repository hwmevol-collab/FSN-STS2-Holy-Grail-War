namespace RinArcherCore;
public sealed class PendingProjectionReinforcement
{
    public bool Active{get;set;}
    public int ManaDiscount{get;set;}
}
// Battlefield state, independent of either character's active/reserve powers.
public sealed class FieldStatus
{
    public string FieldId{get;init;}="FIELD_PRESSURE";
    public string Owner{get;init;}="ENEMY_CONTRACT";
    // -1 means combat-long, 0 means expired. Finite durations tick while suppressed.
    public int Duration{get;set;}
    public bool Suppressed{get;set;}
    public int SuppressUntil{get;set;}
    public void BeginTurn(ContractRuntime d)
    {
        if(Duration>0)Duration--;
        if(Suppressed&&d.Turn>=SuppressUntil){Suppressed=false;d.Log("FIELD_RECOVERED",new{FieldId,Duration});}
    }
    public static int Pressure(ContractRuntime d,Creature? source,bool attack)=>attack&&source?.IsEnemy==true&&d.FieldStatuses.Any(f=>f.FieldId=="FIELD_PRESSURE"&&f.Duration!=0&&!f.Suppressed)?3:0;
}
