using System.Reflection;
using MegaCrit.Sts2.Core.ControllerInput;
using MegaCrit.Sts2.Core.Nodes.CommonUi;
using MegaCrit.Sts2.Core.Nodes.GodotExtensions;
using MegaCrit.Sts2.Core.Nodes.Rooms;
using MegaCrit.Sts2.Core.Nodes.Screens.ScreenContext;
namespace RinArcherCore;

// A short-lived input context for these three native Rest buttons only.
// Keep physical hover and Godot focus intact; choose one source for effective focus.
public sealed class RestFocusInput
{
    internal static RestFocusInput? Current{get;private set;}
    static readonly Dictionary<NClickableControl,RestFocusInput> Contexts=[];
    static readonly MethodInfo Refresh=AccessTools.Method(typeof(NClickableControl),"RefreshFocus");
    readonly List<NPopupYesNoButton> buttons;
    readonly Control defaultFocus;
    readonly Control? memberPopup;
    bool navigation;
    public RestFocusInput(List<NPopupYesNoButton> buttons,Control defaultFocus,Control? memberPopup=null)
    {
        this.buttons=buttons;this.defaultFocus=defaultFocus;this.memberPopup=memberPopup;navigation=GameApi.IsDirectionalNavigation;foreach(var b in buttons)Contexts.Add(b,this);Current=this;
        NControllerManager.Instance!.ControllerDetected+=ControllerDetected;
        NControllerManager.Instance.MouseDetected+=MouseDetected;
        if(navigation)defaultFocus.GrabFocus();else GetViewport().GuiReleaseFocus();
        RefreshButtons();
    }
    public void Detach()
    {
        if(Current!=this)return;Current=null;
        if(NControllerManager.Instance is {} manager){manager.ControllerDetected-=ControllerDetected;manager.MouseDetected-=MouseDetected;}
        foreach(var b in buttons)Contexts.Remove(b);
    }
    Viewport GetViewport()=>defaultFocus.GetViewport();
    void RefreshButtons(){foreach(var b in buttons)if(GodotObject.IsInstanceValid(b)&&b.IsInsideTree())Refresh.Invoke(b,null);}
    void ControllerDetected(){navigation=true;RefreshButtons();}
    void MouseDetected(){navigation=false;GetViewport().GuiReleaseFocus();RefreshButtons();}
    internal void HandleInput(InputEvent input)
    {
        if(memberPopup!=null?MemberTargetUi.Current!=memberPopup:ActiveScreenContext.Instance.GetCurrentScreen()!=NRestSiteRoom.Instance)return;
        // Native controller warps / synthetic screen-context motion are not human motion.
        if(input is InputEventMouseButton||input is InputEventMouseMotion m&&m.Relative.LengthSquared()>0&&m.Relative.LengthSquared()<=250000)
        {MouseDetected();return;}
        if(!navigation&&Controller.AllControllerInputs.Any(a=>input.IsActionPressed(a)))
        {
            navigation=true;defaultFocus.GrabFocus();RefreshButtons();
            // A slow mouse event may leave native controller icon modality active.
            // Re-enter this context without consuming a navigation step or selecting.
            if(GameApi.IsDirectionalNavigation)GetViewport().SetInputAsHandled();
            return;
        }
        bool keyboard=input is InputEventKey key&&key.Pressed&&(key.Keycode is Key.Left or Key.Right or Key.Up or Key.Down or Key.Tab or Key.Enter or Key.Space);
        if(keyboard&&!navigation)
        {
            navigation=true;defaultFocus.GrabFocus();RefreshButtons();
            // Match native controller switching: first navigation input establishes focus.
            GetViewport().SetInputAsHandled();
        }
    }
    internal static bool TryEffectiveFocus(NClickableControl button,bool hovered,bool controllerFocused,out bool focused)
    {
        focused=false;if(!Contexts.TryGetValue(button,out var context))return false;
        focused=button.IsEnabled&&button.IsVisibleInTree()&&(context.navigation?controllerFocused&&button.HasFocus():hovered);
        return true;
    }
    internal static void MemberFocusVisual(NClickableControl button)
    {
        if(!button.HasMeta("ContractMemberButton")||!Contexts.TryGetValue(button,out var context)||button is not NPopupYesNoButton popup)return;
        // Keep native hover animation/green face. Navigation alone gets a blue
        // outline, so a keyboard focus is distinguishable from gold mouse hover.
        if(AccessTools.Field(typeof(NPopupYesNoButton),"_outline").GetValue(popup) is CanvasItem outline&&(bool)AccessTools.Property(typeof(NClickableControl),"IsFocused").GetValue(button)!)
            outline.SelfModulate=context.navigation?new Color("8bbfff"):(Color)AccessTools.Field(typeof(NPopupYesNoButton),"_goldOutline").GetValue(popup)!;
    }
}

[HarmonyPatch(typeof(NControllerManager),nameof(NControllerManager._Input))]
public static class RestFocusInputEvents
{
    static void Prefix(InputEvent inputEvent)=>RestFocusInput.Current?.HandleInput(inputEvent);
}

[HarmonyPatch(typeof(NClickableControl),"RefreshFocus")]
public static class RestFocusArbitration
{
    static readonly PropertyInfo EffectiveFocus=AccessTools.Property(typeof(NClickableControl),"IsFocused");
    static readonly MethodInfo OnFocus=AccessTools.Method(typeof(NPopupYesNoButton),"OnFocus");
    static readonly MethodInfo OnUnfocus=AccessTools.Method(typeof(NPopupYesNoButton),"OnUnfocus");
    static bool Prefix(NClickableControl __instance,bool ____isHovered,bool ____isControllerFocused)
    {
        if(!RestFocusInput.TryEffectiveFocus(__instance,____isHovered,____isControllerFocused,out bool focused))return true;
        if((bool)EffectiveFocus.GetValue(__instance)! == focused)return false;
        EffectiveFocus.SetValue(__instance,focused);
        __instance.EmitSignal(focused?NClickableControl.SignalName.Focused:NClickableControl.SignalName.Unfocused,__instance);
        // Native popup owns its outline, scale, shader, sound and focus transitions.
        (focused?OnFocus:OnUnfocus).Invoke(__instance,null);
        return false;
    }
    static void Postfix(NClickableControl __instance)=>RestFocusInput.MemberFocusVisual(__instance);
}
