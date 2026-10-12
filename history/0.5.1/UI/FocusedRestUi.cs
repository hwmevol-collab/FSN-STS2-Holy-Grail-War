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
    static string PreviewText(RestPreview preview)=>$"重点恢复：{(preview.FocusOwner==RunEconomy.Rin?"御主 — 远坂凛":"从者 — Archer")}\n远坂凛：{preview.Rin.Before}/{preview.Rin.Max} → {preview.Rin.After}/{preview.Rin.Max}  (+{preview.Rin.Heal})\nArcher：{preview.Archer.Before}/{preview.Archer.Max} → {preview.Archer.After}/{preview.Archer.Max}  (+{preview.Archer.Heal})\n重点角色 30% / 搭档 10% · 超量治疗不转移";
    public static void Cancel()=>pending?.TrySetResult(null);
    public static async Task<bool> Select(Player p)
    {
        var room=NRestSiteRoom.Instance!;var container=room.GetNode<Control>("%ChoicesContainer");
        var header=room.GetNode<MegaLabel>("%Header");var originalHeader=header.Text;header.SetTextAutoSize("选择重点恢复的角色");
        room.SetText("选择一位角色专注休息：重点角色恢复最大生命的 30%，搭档恢复 10%。\n分别限制至各自最大生命；超量治疗不转移。确认前显示双方生命变化。");
        var originals=container.GetChildren().OfType<Control>().ToList();foreach(var old in originals)old.Hide();
        var tcs=new TaskCompletionSource<string?>();pending=tcs;var buttons=new List<NPopupYesNoButton>();
        foreach(var owner in new[]{RunEconomy.Rin,RunEconomy.Archer})
        {
            string capture=owner;var preview=RunEconomy.Preview(p,owner);
            var button=EconomyNativeUi.Button(container,owner==RunEconomy.Rin?"D2FocusRin":"D2FocusArcher",owner==RunEconomy.Rin?"御主 · 远坂凛":"从者 · Archer",new(owner==RunEconomy.Rin?0:430,30),()=>tcs.TrySetResult(capture));
            button.Connect(NClickableControl.SignalName.Focused,Callable.From<NButton>(_=>{room.SetText(PreviewText(preview));ContractSave.Log(p,"REST_PREVIEW",new{focus=capture,focusOwner=capture,focusHeal=preview.Focus.Heal,partnerHeal=preview.Partner.Heal,focusOverheal=preview.Focus.Overheal,partnerOverheal=preview.Partner.Overheal,rinHpBefore=preview.Rin.Before,rinHpAfter=preview.Rin.After,archerHpBefore=preview.Archer.Before,archerHpAfter=preview.Archer.After});}));
            if(!RunEconomy.CanFocus(p,owner))button.Disable();buttons.Add(button);
        }
        buttons.Add(EconomyNativeUi.Button(container,"D2FocusCancel","返回",new(215,125),()=>tcs.TrySetResult(null),MegaInput.cancel));
        var navigable=buttons.Take(2).Where(b=>b.IsEnabled).ToList();for(int i=0;i<navigable.Count;i++){var b=navigable[i];b.FocusNeighborLeft=navigable[(i+navigable.Count-1)%navigable.Count].GetPath();b.FocusNeighborRight=navigable[(i+1)%navigable.Count].GetPath();b.FocusNeighborBottom=buttons[2].GetPath();}
        container.TreeExiting+=()=>tcs.TrySetResult(null);
        DefaultFocus=buttons.First(b=>b.Name=="D2FocusCancel"||RunEconomy.CanFocus(p,b.Name=="D2FocusRin"?RunEconomy.Rin:RunEconomy.Archer));buttons[2].FocusNeighborTop=DefaultFocus.GetPath();
        var input=new RestFocusInput(buttons,DefaultFocus);
        try
        {
            var focus=await tcs.Task;if(focus==null)return false;var preview=RunEconomy.Preview(p,focus);room.SetText(PreviewText(preview));
            input.Detach();
            if(!await EconomyNativeUi.Confirm("休息 — 重点恢复",PreviewText(preview),"确认休息"))return false;
            var commit=RunEconomy.Rest(p,focus);NativeRewardTransactions.Track(commit);return await commit;
        }
        finally{DefaultFocus=null;pending=null;input.Detach();if(GodotObject.IsInstanceValid(header))header.SetTextAutoSize(originalHeader);foreach(var button in buttons)if(GodotObject.IsInstanceValid(button))button.QueueFree();foreach(var old in originals)if(GodotObject.IsInstanceValid(old))old.Show();}
    }
}
[HarmonyPatch(typeof(NRestSiteRoom),"get_DefaultFocusedControl")]
public static class D2RestDefaultFocus
{static void Postfix(ref Control? __result){if(FocusedRestUi.DefaultFocus is {} focus&&GodotObject.IsInstanceValid(focus)&&focus.IsInsideTree())__result=focus;}}

