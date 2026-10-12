using MegaCrit.Sts2.Core.Nodes.Cards;
using MegaCrit.Sts2.Core.Nodes.Combat;
using MegaCrit.Sts2.Core.Nodes.Rooms;
namespace RinArcherCore;

// Display-only recipient resolution. Native Player ownership is shared by Rin and Archer;
// do not change CardModel.TargetType, IsValidTarget, or the target submitted to card play.
public static class CardTargetPreview
{
    public static bool TryResolve(CardModel? model,Creature? hovered,out IReadOnlyList<Creature> recipients)
    {
        recipients=[];
        if(model is not StarterCard card||ContractRuntime.For(card.Owner) is not {} d||d.Finished)return false;
        IEnumerable<Creature> candidates=card switch
        {
            Hrunting=>[], // Its explicit ANY choice happens after native submission.
            Cover=>[d.Rin.Creature],
            KanshouBakuya=>d.Enemy is {} enemy?[enemy.Active]:[],
            RhoAias arm=>arm.Reinforced?[d.Archer.Creature,d.Rin.Creature]:[d.Archer.Creature],
            _ when card.TargetType==TargetType.AnyEnemy=>hovered!=null&&card.IsValidTarget(hovered)?[hovered]:[],
            _ when card.TargetType==TargetType.Self=>[d.Member(card.OwnerCharacterId).Creature],
            _=>[]
        };
        recipients=candidates.Where(c=>c.IsAlive&&c.IsHittable).Distinct().ToArray();
        return true;
    }
}

// Shared by mouse drag, keyboard shortcuts and controller multi-recipient previews.
[HarmonyPatch(typeof(NCardPlay),"ShowMultiCreatureTargetingVisuals")]
public static class ContractMultiTargetPreviewHook
{
    static bool Prefix(NCardPlay __instance)
    {
        var node=__instance.Holder?.CardNode;
        if(!CardTargetPreview.TryResolve(node?.Model,null,out var recipients)||NCombatRoom.Instance is not {} room)return true;
        foreach(var creature in room.CreatureNodes)creature.HideMultiselectReticle();
        node!.SetPreviewTarget(recipients.Count==1?recipients[0]:null);
        node.UpdateVisuals((node.Model?.Pile?.Type).GetValueOrDefault(),CardPreviewMode.Normal);
        foreach(var recipient in recipients)room.GetCreatureNode(recipient)?.ShowMultiselectReticle();
        return false;
    }
}

// The native selector accepts all living enemies. Its display must also respect the
// card's existing FRONT legality, so hovering Reserve never advertises a legal target.
[HarmonyPatch(typeof(NTargetManager),nameof(NTargetManager.StartTargeting),[typeof(TargetType),typeof(Control),typeof(TargetMode),typeof(Func<bool>),typeof(Func<Node,bool>)])]
public static class ContractSingleTargetPreviewHook
{
    static void Prefix(Control control,ref Func<Node,bool>? nodeFilter)
    {
        if(control is not NCard {Model:StarterCard card}||ContractRuntime.For(card.Owner)==null)return;
        var previous=nodeFilter;
        nodeFilter=node=>(previous==null||previous(node))&&node is NCreature creature&&card.IsValidTarget(creature.Entity);
    }
}

// Archer's existing visual reparent exits/re-enters the tree. The native reticle's
// readonly cancellation token stays cancelled, so native OnDeselect then does nothing.
// Preserve its native fade for this live contract visual without changing combat setup.
[HarmonyPatch(typeof(NSelectionReticle),nameof(NSelectionReticle.OnDeselect))]
public static class ArcherPreviewClearHook
{
    static readonly System.Reflection.FieldInfo Token=AccessTools.Field(typeof(NSelectionReticle),"_cancelToken");
    static readonly System.Reflection.FieldInfo Tween=AccessTools.Field(typeof(NSelectionReticle),"_currentTween");
    static readonly System.Reflection.MethodInfo Select=AccessTools.PropertySetter(typeof(NSelectionReticle),nameof(NSelectionReticle.IsSelected));
    static bool Prefix(NSelectionReticle __instance)
    {
        if(!__instance.IsInsideTree()||!((CancellationTokenSource)Token.GetValue(__instance)!).IsCancellationRequested)return true;
        Node? parent=__instance.GetParent();while(parent!=null&&parent is not NCreature)parent=parent.GetParent();
        if(parent is not NCreature creature||ContractRuntime.For(creature.Entity) is not {} d||creature.Entity!=d.Archer.Creature)return true;
        (Tween.GetValue(__instance) as Godot.Tween)?.Kill();
        var fade=__instance.CreateTween().SetParallel();
        fade.TweenProperty(__instance,"modulate:a",0f,0.2).SetEase(Godot.Tween.EaseType.Out).SetTrans(Godot.Tween.TransitionType.Sine);
        fade.TweenProperty(__instance,"scale",Vector2.One*1.05f,0.2).SetEase(Godot.Tween.EaseType.Out).SetTrans(Godot.Tween.TransitionType.Sine);
        Tween.SetValue(__instance,fade);Select.Invoke(__instance,[false]);return false;
    }
}
