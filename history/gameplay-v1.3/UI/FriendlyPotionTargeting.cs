using MegaCrit.Sts2.Core.Nodes;
using MegaCrit.Sts2.Core.Nodes.Combat;
using MegaCrit.Sts2.Core.Nodes.Potions;
using MegaCrit.Sts2.Core.Nodes.Rooms;
using MegaCrit.Sts2.Core.Nodes.CommonUi;
using MegaCrit.Sts2.Core.Nodes.GodotExtensions;
using MegaCrit.Sts2.Core.ControllerInput;
using MegaCrit.Sts2.Core.TestSupport;
using MegaCrit.Sts2.Core.HoverTips;
using MegaCrit.Sts2.Core.Nodes.HoverTips;
namespace RinArcherCore;

public static class FriendlyPotionTargeting
{
    static readonly Dictionary<PotionModel,Creature> Selected=new(ReferenceEqualityComparer.Instance);
    public static PotionModel? Current{get;private set;}
    public static bool RequiresMember(PotionModel potion)=>GenericCompatibility.Enabled(potion.Owner)
        &&GenericCompatibility.Registry.GetEffectScopes(potion.Id.ToString()).Any(r=>r.Trigger=="OnUse"&&r.Scope=="CHOOSE_MEMBER");
    public static bool InCombat(PotionModel potion)=>RequiresMember(potion)&&CombatManager.Instance.IsInProgress
        &&ContractRuntime.For(potion.Owner) is {Finished:false} d&&d.Combat==potion.Owner.Creature.CombatState;
    public static bool IsLegal(PotionModel potion,Creature? target)
    {
        if(target==null||!target.IsAlive||!target.IsHittable||ContractRuntime.For(potion.Owner) is not {Finished:false} d)return false;
        string? member=target==d.Rin.Creature?RunEconomy.Rin:target==d.Archer.Creature?RunEconomy.Archer:null;
        return member!=null&&GenericMemberEffects.Preview(potion.Owner,potion,"OnUse").Any(p=>p.Member==member&&p.Eligible);
    }
    public static bool ConsumeSelection(PotionModel potion,Creature? recipient,out string? member)
    {
        member=null;
        if(!Selected.Remove(potion,out var selected))return false;
        if(selected!=recipient||!IsLegal(potion,recipient))throw new InvalidOperationException("Friendly potion recipient changed before effect commit");
        var d=ContractRuntime.For(potion.Owner)!;member=recipient==d.Rin.Creature?RunEconomy.Rin:RunEconomy.Archer;
        return true;
    }
    public static bool HasPendingSelection(PotionModel potion)=>Selected.ContainsKey(potion)||Current==potion;
    public static void Rollback(PotionModel potion)
    {
        Selected.Remove(potion);
        if(Current==potion&&NRun.Instance!=null)NTargetManager.Instance.CancelTargeting();
        if(!TestMode.IsOn&&NRun.Instance!=null&&potion.Owner.Potions.Contains(potion))
            NRun.Instance.GlobalUi.TopBar.PotionContainer.OnPotionUseOrDiscardCanceled(potion);
    }
    public static async Task Target(NPotionHolder holder,PotionModel potion)
    {
        if(Current!=null)return;
        Current=potion;bool enqueued=false;
        var room=NCombatRoom.Instance!;var manager=NTargetManager.Instance;
        var d=ContractRuntime.For(potion.Owner)!;
        RunManager.Instance.HoveredModelTracker.OnLocalPotionSelected(potion);
        NHoverTipSet? valuePreview=null;
        try
        {
            foreach(var node in room.CreatureNodes){node.HideSingleSelectReticle();node.HideMultiselectReticle();}
            bool controller=NControllerManager.Instance!.IsUsingController;
            if(!controller)holder.GetViewport().GuiReleaseFocus();
            var preview=GenericMemberEffects.Preview(potion.Owner,potion,"OnUse");
            manager.StartTargeting(TargetType.AnyPlayer,holder.GlobalPosition+new Vector2(holder.Size.X/2,50),
                controller?TargetMode.Controller:TargetMode.ClickMouseToTarget,
                ()=>!CombatManager.Instance.IsInProgress||d.Finished||!potion.Owner.Potions.Contains(potion),
                node=>node is NCreature creature&&IsLegal(potion,creature.Entity));
            // The native use-button callback removes its popup/hover tips after
            // launching targeting. Wait for that teardown, then show only this
            // approved value preview through the native tooltip renderer.
            await holder.ToSignal(holder.GetTree(),SceneTree.SignalName.ProcessFrame);
            if(manager.IsInSelection&&preview.Any(p=>p.CurrentHp!=p.AfterHp||p.MaxHp!=p.AfterMaxHp))
            {
                bool blocked=NHoverTipSet.shouldBlockHoverTips;NHoverTipSet.shouldBlockHoverTips=false;
                try
                {
                    valuePreview=NHoverTipSet.CreateAndShow(room,new HoverTip(potion.Title,"指向要接受药水的角色；取消不消耗药水。\n\n"+string.Join("\n",preview.Select(p=>p.Text))));
                    valuePreview?.SetGlobalPosition(holder.GlobalPosition+Vector2.Down*85);
                }
                finally{NHoverTipSet.shouldBlockHoverTips=blocked;}
            }
            if(controller)
            {
                var targets=new[]{d.Rin.Creature,d.Archer.Creature}.Where(c=>IsLegal(potion,c)).Select(c=>room.GetCreatureNode(c)??throw new InvalidOperationException("Member creature view missing")).ToArray();
                if(targets.Length==0){manager.CancelTargeting();return;}
                room.RestrictControllerNavigation(targets.Select(n=>n.Hitbox));
                // Archer's view is reparented into AllyContainer after native
                // combat construction. Its cached absolute navigation paths can
                // still name EnemyContainer. Bind only the live legal hitboxes
                // for this targeting session; native Enable restores navigation.
                for(int i=0;i<targets.Length;i++)
                {
                    var hitbox=targets[i].Hitbox;
                    hitbox.FocusNeighborLeft=targets[(i+targets.Length-1)%targets.Length].Hitbox.GetPath();
                    hitbox.FocusNeighborRight=targets[(i+1)%targets.Length].Hitbox.GetPath();
                    hitbox.FocusNeighborTop=hitbox.GetPath();hitbox.FocusNeighborBottom=hitbox.GetPath();
                }
                targets[0].Hitbox.GrabFocus();
            }
            var selected=await manager.SelectionFinished();
            // Native FinishTargeting completes its task before clearing arrow,
            // input-sync and selection mode. Resume after that native cleanup;
            // cancelling inline here would re-enter its SetResult transaction.
            await holder.ToSignal(holder.GetTree(),SceneTree.SignalName.ProcessFrame);
            if(selected is NCreature recipient&&IsLegal(potion,recipient.Entity))
            {
                Selected[potion]=recipient.Entity;
                potion.EnqueueManualUse(recipient.Entity);enqueued=true;
            }
        }
        finally
        {
            if(manager.IsInSelection)manager.CancelTargeting();
            room.EnableControllerNavigation();
            foreach(var node in room.CreatureNodes){node.HideSingleSelectReticle();node.HideMultiselectReticle();}
            RunManager.Instance.HoveredModelTracker.OnLocalPotionDeselected();Current=null;
            if(valuePreview!=null)NHoverTipSet.Remove(room);
            if(!enqueued)potion.AfterUsageCanceled();
            if(GodotObject.IsInstanceValid(holder))holder.TryGrabFocus();
        }
    }
}
[HarmonyPatch(typeof(NPotionHolder),nameof(NPotionHolder.UsePotion))]
public static class FriendlyPotionNativeInput
{
    static bool Prefix(NPotionHolder __instance,ref Task __result)
    {
        if(__instance.Potion?.Model is not {} potion||!FriendlyPotionTargeting.InCombat(potion))return true;
        __result=FriendlyPotionTargeting.Target(__instance,potion);return false;
    }
}
[HarmonyPatch(typeof(NPotionPopup),nameof(NPotionPopup._Ready))]
public static class FriendlyPotionNativeUseLabel
{
    static void Postfix(NPotionPopup __instance,NPotionHolder ____holder)
    {
        if(____holder.Potion?.Model is {} potion&&FriendlyPotionTargeting.InCombat(potion))
            __instance.GetNode<NPotionPopupButton>("%UseButton").SetLocKey("POTION_POPUP.throw");
    }
}
// Archer is a real allied creature, deliberately not a Player/pet. Preserve that
// combat identity and extend only this live targeting context's native predicate.
[HarmonyPatch(typeof(NTargetManager),"AllowedToTargetCreature")]
public static class FriendlyPotionNativeTargetLegality
{
    static bool Prefix(Creature creature,ref bool __result)
    {
        if(FriendlyPotionTargeting.Current is not {} potion)return true;
        __result=FriendlyPotionTargeting.IsLegal(potion,creature);return false;
    }
}
[HarmonyPatch(typeof(PotionModel),nameof(PotionModel.AfterUsageCanceled))]
public static class MemberPotionCancelRollback
{
    static void Postfix(PotionModel __instance)
    {if(FriendlyPotionTargeting.RequiresMember(__instance))FriendlyPotionTargeting.Rollback(__instance);}
}

// Escape also owns the native pause button's key-release hotkey. Once its press
// cancelled this targeting session, consume that same release so it cannot open
// Pause after targeting has already cleared. Scope and lifetime are transient.
[HarmonyPatch(typeof(NControllerManager),nameof(NControllerManager._Input))]
public static class FriendlyPotionEscapeInput
{
    static NRun? canceledIn;
    static void Prefix(NControllerManager __instance,InputEvent inputEvent)
    {
        if(inputEvent is not InputEventKey key||(key.Keycode!=Key.Escape&&key.PhysicalKeycode!=Key.Escape))return;
        if(key.Pressed)
        {
            if(FriendlyPotionTargeting.Current!=null&&NRun.Instance!=null&&NTargetManager.Instance.IsInSelection)canceledIn=NRun.Instance;
        }
        else if(canceledIn!=null)
        {
            if(canceledIn==NRun.Instance)__instance.GetViewport().SetInputAsHandled();
            canceledIn=null;
        }
    }
}
