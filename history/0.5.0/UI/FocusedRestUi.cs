using MegaCrit.Sts2.Core.Nodes.GodotExtensions;
using MegaCrit.Sts2.Core.ControllerInput;
using MegaCrit.Sts2.Core.Nodes.CommonUi;
using MegaCrit.Sts2.Core.Nodes.Rooms;
using MegaCrit.Sts2.Core.Helpers;
namespace RinArcherCore;
public static class FocusedRestUi
{
    public static Control? DefaultFocus{get;private set;}
    static TaskCompletionSource<string?>? pending;
    public static void Cancel()=>pending?.TrySetResult(null);
    public static async Task<bool> Select(Player p)
    {
        var room=NRestSiteRoom.Instance!;var container=room.GetNode<Control>("%ChoicesContainer");
        var originals=container.GetChildren().OfType<Control>().ToList();foreach(var old in originals)old.Hide();
        var tcs=new TaskCompletionSource<string?>();pending=tcs;var buttons=new List<NPopupYesNoButton>();
        foreach(var owner in new[]{RunEconomy.Rin,RunEconomy.Archer})
        {
            string capture=owner;var preview=RunEconomy.Preview(p,owner);
            var button=EconomyNativeUi.Button(container,owner==RunEconomy.Rin?"D2FocusRin":"D2FocusArcher",owner==RunEconomy.Rin?"Focus Master — Rin":"Focus Servant — Archer",new(owner==RunEconomy.Rin?0:430,30),()=>tcs.TrySetResult(capture));
            button.Connect(NClickableControl.SignalName.Focused,Callable.From<NButton>(_=>{room.SetText(preview.Text);ContractSave.Log(p,"REST_PREVIEW",new{focus=capture,focusOwner=capture,focusHeal=preview.Focus.Heal,partnerHeal=preview.Partner.Heal,focusOverheal=preview.Focus.Overheal,partnerOverheal=preview.Partner.Overheal,rinHpBefore=preview.Rin.Before,rinHpAfter=preview.Rin.After,archerHpBefore=preview.Archer.Before,archerHpAfter=preview.Archer.After});}));
            if(!RunEconomy.CanFocus(p,owner))button.Disable();buttons.Add(button);
        }
        buttons.Add(EconomyNativeUi.Button(container,"D2FocusCancel","返回",new(215,125),()=>tcs.TrySetResult(null),MegaInput.cancel));
        var navigable=buttons.Where(b=>b.IsEnabled).ToList();for(int i=0;i<navigable.Count;i++){var b=navigable[i];b.FocusNeighborLeft=navigable[(i+navigable.Count-1)%navigable.Count].GetPath();b.FocusNeighborRight=navigable[(i+1)%navigable.Count].GetPath();}
        container.TreeExiting+=()=>tcs.TrySetResult(null);
        DefaultFocus=buttons.First(b=>b.Name=="D2FocusCancel"||RunEconomy.CanFocus(p,b.Name=="D2FocusRin"?RunEconomy.Rin:RunEconomy.Archer));DefaultFocus.GrabFocus();
        try
        {
            var focus=await tcs.Task;if(focus==null)return false;var preview=RunEconomy.Preview(p,focus);room.SetText(preview.Text);
            if(!await EconomyNativeUi.Confirm("REST — Focus",preview.Text,"确认休息"))return false;
            var commit=RunEconomy.Rest(p,focus);NativeRewardTransactions.Track(commit);return await commit;
        }
        finally{DefaultFocus=null;pending=null;foreach(var button in buttons)if(GodotObject.IsInstanceValid(button))button.QueueFree();foreach(var old in originals)if(GodotObject.IsInstanceValid(old))old.Show();}
    }
}
[HarmonyPatch(typeof(NRestSiteRoom),"get_DefaultFocusedControl")]
public static class D2RestDefaultFocus
{static void Postfix(ref Control? __result){if(FocusedRestUi.DefaultFocus is {} focus&&GodotObject.IsInstanceValid(focus)&&focus.IsInsideTree())__result=focus;}}

