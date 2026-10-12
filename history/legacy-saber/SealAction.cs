using MegaCrit.Sts2.Core.GameActions;
using MegaCrit.Sts2.Core.Entities.Multiplayer;
namespace FateStayNight;
// Single-player input uses the native action queue, so seal effects cannot race card resolution.
public sealed class SealAction(Duo duo,int option) : GameAction
{
    public override ulong OwnerId=>duo.Player.NetId;
    public override GameActionType ActionType=>GameActionType.CombatPlayPhaseOnly;
    protected override Task ExecuteAction()=>duo.UseSeal(option,new ThrowingPlayerChoiceContext());
    // Use the engine's existing string-payload action envelope. No console command is executed.
    public override INetAction ToNetAction()=>new MegaCrit.Sts2.Core.DevConsole.NetConsoleCmdGameAction{cmd="FSN/Seal/v1/"+option,inCombat=true};
}
[HarmonyPatch(typeof(MegaCrit.Sts2.Core.DevConsole.NetConsoleCmdGameAction),nameof(MegaCrit.Sts2.Core.DevConsole.NetConsoleCmdGameAction.ToGameAction))]
public static class SealReplayPatch{
    static bool Prefix(MegaCrit.Sts2.Core.DevConsole.NetConsoleCmdGameAction __instance,Player player,ref GameAction __result){
        if(!__instance.inCombat||!__instance.cmd.StartsWith("FSN/Seal/v1/",StringComparison.Ordinal))return true;
        if(!int.TryParse(__instance.cmd[12..],out var option)||option is <0 or >2||Duo.For(player) is not {} duo)throw new InvalidOperationException("Invalid FSN seal action payload.");
        __result=new SealAction(duo,option);return false;
    }
}
