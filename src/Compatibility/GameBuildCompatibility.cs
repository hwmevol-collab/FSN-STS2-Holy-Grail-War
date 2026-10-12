namespace RinArcherCore;

// Native effect classification stays bound to the immutable 0.107.1 Matrix.
// The 0.111 bridge changes API calls / hook names, not native acquisition or effect budgets.
public static class GameBuildCompatibility
{
    public static readonly VanillaVersionSignature MatrixBaseline=new("v0.107.1","59260271","A1F9E653F1E28E4076558FEE1E60D218619CB7E057B887C6417F62C62C6D7A52","97f10687-c306-4798-ab75-8b9f23f34dfb");
#if GAME_0107
    public static VanillaVersionSignature Expected=>MatrixBaseline;
#else
    public static VanillaVersionSignature Expected=>new("v0.111.0","41cef1ea","0861BFA1DF347538D932F22D580E75420F08082792EB914E53B4882764ACDBE9","73b63ee0-6c0a-47bb-b0d1-b21f6d94222e");
#endif
    public static VanillaVersionSignature ForMatrix(VanillaVersionSignature actual)
        =>actual==Expected?MatrixBaseline:throw new InvalidDataException("VANILLA_COMPATIBILITY_VERSION_MISMATCH: "+actual);
    public static CompatibilityContent ApplyNativeDelta(CompatibilityContent entry)
    {
#if !GAME_0107
        string? oldHook=null,newHook=null;
        switch(entry.ContentId)
        {
            case "RELIC.BONE_TEA":oldHook="AfterSideTurnStart";newHook="AfterPlayerTurnStart";break;
            case "RELIC.FIDDLE":oldHook="ModifyHandDrawLate";newHook="ModifyHandDraw";break;
            case "RELIC.HAND_DRILL":oldHook="AfterDamageGiven";newHook="AfterBlockBroken";break;
            case "RELIC.PENDULUM":oldHook="AfterPlayerTurnStart";newHook="BeforeHandDraw";break;
            case "RELIC.POLLINOUS_CORE":oldHook="BeforeSideTurnStart";newHook="BeforeHandDraw";break;
            case "RELIC.TOASTY_MITTENS":oldHook="BeforeHandDraw";newHook="AfterPlayerTurnStart";break;
        }
        if(oldHook!=null)entry=entry with{Effects=entry.Effects.Select(e=>e.Trigger==oldHook?e with{Trigger=newHook!}:e).ToArray()};
        if(entry.ContentId=="RELIC.PENDULUM")
        {
            var old=entry.Effects.First(e=>e.Trigger=="BeforeHandDraw");
            entry=entry with{Effects=entry.Effects.Append(old with{EffectId="v111:ModifyHandDraw",Trigger="ModifyHandDraw"}).ToArray()};
        }
        // In 0.111 the native relic grants 20 Block + 1 Blur on the first turn;
        // its old turn-card counter and DiamondDiademPower no longer exist.
        if(entry.ContentId=="RELIC.DIAMOND_DIADEM")
        {
            var evidence=System.Text.Json.JsonSerializer.SerializeToElement(new{source="v0.111.0/41cef1ea/DiamondDiadem.AfterSideTurnStart",api="CreatureCmd.GainBlock + PowerCmd.Apply<BlurPower>",nativeAmount="BlockVar(20), Blur(1)",review="GAME_COMPAT_20261013_01"});
            var row=new CompatibilityEffect("v111:AfterSideTurnStart","AfterSideTurnStart","ACTIVE_AT_TRIGGER","GENERIC_ADAPTER","ActiveCharacterEffectResolver",evidence,"OWNER_CREATURE");
            return entry with{Effects=new[]{row},PowerDependencies=new[]{new CompatibilityPowerDependency("MegaCrit.Sts2.Core.Models.Powers.BlurPower",new[]{"ShouldClearBlock","AfterSideTurnStart"})}};
        }
#endif
        return entry;
    }
}
