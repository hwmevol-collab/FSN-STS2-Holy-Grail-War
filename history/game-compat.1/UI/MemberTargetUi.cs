using MegaCrit.Sts2.Core.Nodes.CommonUi;
using MegaCrit.Sts2.Core.Nodes;
using MegaCrit.Sts2.Core.Nodes.Multiplayer;
using MegaCrit.Sts2.Core.Nodes.GodotExtensions;
using MegaCrit.Sts2.Core.Helpers;
using MegaCrit.Sts2.Core.ControllerInput;
namespace RinArcherCore;

public static class MemberTargetUi
{
    public static NGenericPopup? Current{get;private set;}
    public static async Task<string?> Choose(string description,IReadOnlyList<MemberValuePreview> previews,bool cancellable)
    {
        // Native acquisition tutorials can own the modal slot until dismissed.
        // Queue this chooser behind them instead of creating an unattached popup.
        while(NModalContainer.Instance!.OpenModal!=null)
            await NGame.Instance!.ToSignal(NGame.Instance.GetTree(),SceneTree.SignalName.ProcessFrame);
        var popup=NGenericPopup.Create()!;popup.Name="ContractMemberChooser";Current=popup;
        NModalContainer.Instance!.Add(popup);
        // AddChildSafely may defer attachment when called from a native async
        // potion/event continuation. Child button labels exist only after Ready.
        if(!popup.IsNodeReady())await popup.ToSignal(popup,Node.SignalName.Ready);
        var completion=new TaskCompletionSource<string?>(TaskCreationOptions.RunContinuationsAsynchronously);
        string? selection=null;bool closing=false;
        void Select(string? id){if(closing)return;closing=true;selection=id;if(ReferenceEquals(NModalContainer.Instance!.OpenModal,popup))NModalContainer.Instance.Clear();else if(GodotObject.IsInstanceValid(popup))popup.QueueFreeSafely();}
        var vertical=popup.GetNode<NVerticalPopup>("VerticalPopup");
        vertical.SetText(FsnLoc.Text("UI_4A910A1A0ECC"),description+"\n\n"+string.Join("\n",previews.Select(p=>p.Text)));
        var rin=popup.GetNode<NPopupYesNoButton>("VerticalPopup/YesButton");var archer=popup.GetNode<NPopupYesNoButton>("VerticalPopup/NoButton");
        foreach(var button in new[]{rin,archer}){button.DisconnectHotkeys();button.SetMeta("ContractMemberButton",true);button.Visible=true;button.FocusMode=Control.FocusModeEnum.All;button.Enable();}
        rin.SetText(FsnLoc.Text("RIN_ROLE"));archer.SetText(FsnLoc.Text("ARCHER_ROLE"));
        if(previews.Any(p=>p.Member==RunEconomy.Rin&&!p.Eligible))rin.Disable();
        if(previews.Any(p=>p.Member==RunEconomy.Archer&&!p.Eligible))archer.Disable();
        rin.Connect(NClickableControl.SignalName.Released,Callable.From<NButton>(_=>Select(RunEconomy.Rin)));
        archer.Connect(NClickableControl.SignalName.Released,Callable.From<NButton>(_=>Select(RunEconomy.Archer)));
        var inputButtons=new List<NPopupYesNoButton>{rin,archer};
        if(cancellable)
        {
            var cancel=EconomyNativeUi.Button(vertical,"CancelMemberSelection",FsnLoc.Text("UI_2CD0F3BE8738"),Vector2.Zero,()=>Select(null),MegaCrit.Sts2.Core.ControllerInput.MegaInput.cancel);
            cancel.SetMeta("ContractMemberCancel",true);
            inputButtons.Add(cancel);
            var buttons=new[]{rin,archer,cancel};
            for(int i=0;i<buttons.Length;i++)
            {var button=buttons[i];button.SetAnchorsPreset(Control.LayoutPreset.TopLeft);button.Position=new(vertical.Size.X/2-290+i*200,vertical.Size.Y-100);button.Size=new(180,72);}
            rin.FocusNeighborRight=rin.GetPathTo(archer);archer.FocusNeighborLeft=archer.GetPathTo(rin);archer.FocusNeighborRight=archer.GetPathTo(cancel);cancel.FocusNeighborLeft=cancel.GetPathTo(archer);
        }
        rin.FocusNeighborBottom=rin.GetPathTo(archer);archer.FocusNeighborTop=archer.GetPathTo(rin);
        var input=new RestFocusInput(inputButtons,rin.IsEnabled?rin:archer,popup);
        popup.TreeExited+=()=>completion.TrySetResult(selection);
        try{return await completion.Task;}
        finally{input.Detach();if(ReferenceEquals(Current,popup))Current=null;}
    }
}
[HarmonyPatch(typeof(NPopupYesNoButton),"get_Hotkeys")]
public static class MemberChooserNativeHotkeys
{
    static void Postfix(NPopupYesNoButton __instance,ref string[] __result)
    {
        if(__instance.HasMeta("ContractMemberCancel"))__result=[MegaCrit.Sts2.Core.ControllerInput.MegaInput.cancel];
        else if(__instance.HasMeta("ContractMemberButton"))__result=[];
    }
}
[HarmonyPatch(typeof(NGenericPopup),"get_DefaultFocusedControl")]
public static class MemberChooserNativeFocus
{
    static void Postfix(NGenericPopup __instance,ref Control? __result)
    {if(__instance==MemberTargetUi.Current)__result=!GameApi.IsDirectionalNavigation?null:__instance.GetNodeOrNull<NPopupYesNoButton>("VerticalPopup/YesButton") is {IsEnabled:true} rin?rin:__instance.GetNodeOrNull<Control>("VerticalPopup/NoButton");}
}
