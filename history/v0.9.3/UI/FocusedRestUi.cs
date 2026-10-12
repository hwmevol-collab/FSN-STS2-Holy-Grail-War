using MegaCrit.Sts2.Core.Nodes.GodotExtensions;
using MegaCrit.Sts2.Core.ControllerInput;
using MegaCrit.Sts2.Core.Nodes.CommonUi;
using MegaCrit.Sts2.Core.Nodes.Rooms;
using MegaCrit.Sts2.Core.Helpers;
using MegaCrit.Sts2.addons.mega_text;
namespace RinArcherCore;
public static class FocusedRestUi
{
    public static Control? DefaultFocus{get;private set;}
    static TaskCompletionSource<string?>? pending;
    static string PreviewText(RestPreview preview)=>FsnLoc.Format("UI_65049F10D084", (preview.FocusOwner==RunEconomy.Rin?FsnLoc.Text("UI_043F19C4E63F"):"Archer"), preview.Rin.Before, preview.Rin.Max, preview.Rin.After, preview.Rin.Max, preview.Rin.Heal, preview.Archer.Before, preview.Archer.Max, preview.Archer.After, preview.Archer.Max, preview.Archer.Heal);
    public static void Cancel()=>pending?.TrySetResult(null);
    public static async Task<bool> Select(Player p)
    {
        var room=NRestSiteRoom.Instance!;var container=room.GetNode<Control>("%ChoicesContainer");
        var header=room.GetNode<MegaLabel>("%Header");var originalHeader=header.Text;header.SetTextAutoSize(FsnLoc.Text("UI_32CB9C9202DE"));
        room.SetText(FsnLoc.Text("UI_8B8797FCF5F7"));
        var originals=container.GetChildren().OfType<Control>().ToList();foreach(var old in originals)old.Hide();
        var tcs=new TaskCompletionSource<string?>();pending=tcs;var buttons=new List<NPopupYesNoButton>();
        foreach(var owner in new[]{RunEconomy.Rin,RunEconomy.Archer})
        {
            string capture=owner;var preview=RunEconomy.Preview(p,owner);
            var button=EconomyNativeUi.Button(container,owner==RunEconomy.Rin?"D2FocusRin":"D2FocusArcher",owner==RunEconomy.Rin?FsnLoc.Text("UI_995EA67EA60E"):FsnLoc.Text("UI_328380ADF034"),new(owner==RunEconomy.Rin?0:430,30),()=>{if(tcs.TrySetResult(capture))foreach(var b in buttons)b.Disable();});
            button.Connect(NClickableControl.SignalName.Focused,Callable.From<NButton>(_=>{room.SetText(PreviewText(preview));ContractSave.Log(p,"REST_PREVIEW",new{focus=capture,focusOwner=capture,focusHeal=preview.Focus.Heal,partnerHeal=preview.Partner.Heal,focusOverheal=preview.Focus.Overheal,partnerOverheal=preview.Partner.Overheal,rinHpBefore=preview.Rin.Before,rinHpAfter=preview.Rin.After,archerHpBefore=preview.Archer.Before,archerHpAfter=preview.Archer.After});}));
            if(!RunEconomy.CanFocus(p,owner))button.Disable();buttons.Add(button);
        }
        buttons.Add(EconomyNativeUi.Button(container,"D2FocusCancel",FsnLoc.Text("UI_572CF45BA436"),new(215,125),()=>tcs.TrySetResult(null),MegaInput.cancel));
        var navigable=buttons.Take(2).Where(b=>b.IsEnabled).ToList();for(int i=0;i<navigable.Count;i++){var b=navigable[i];b.FocusNeighborLeft=navigable[(i+navigable.Count-1)%navigable.Count].GetPath();b.FocusNeighborRight=navigable[(i+1)%navigable.Count].GetPath();b.FocusNeighborBottom=buttons[2].GetPath();}
        container.TreeExiting+=()=>tcs.TrySetResult(null);
        DefaultFocus=buttons.First(b=>b.Name=="D2FocusCancel"||RunEconomy.CanFocus(p,b.Name=="D2FocusRin"?RunEconomy.Rin:RunEconomy.Archer));buttons[2].FocusNeighborTop=DefaultFocus.GetPath();
        var input=new RestFocusInput(buttons,DefaultFocus);
        try
        {
            var focus=await tcs.Task;if(focus==null)return false;var preview=RunEconomy.Preview(p,focus);room.SetText(PreviewText(preview));
            input.Detach();
            var commit=RunEconomy.Rest(p,focus);NativeRewardTransactions.Track(commit);return await commit;
        }
        finally{DefaultFocus=null;pending=null;input.Detach();if(GodotObject.IsInstanceValid(header))header.SetTextAutoSize(originalHeader);foreach(var button in buttons)if(GodotObject.IsInstanceValid(button))button.QueueFree();foreach(var old in originals)if(GodotObject.IsInstanceValid(old))old.Show();}
    }
}
[HarmonyPatch(typeof(NRestSiteRoom),"get_DefaultFocusedControl")]
public static class D2RestDefaultFocus
{static void Postfix(ref Control? __result){if(FocusedRestUi.DefaultFocus is {} focus&&GodotObject.IsInstanceValid(focus)&&focus.IsInsideTree())__result=focus;}}

