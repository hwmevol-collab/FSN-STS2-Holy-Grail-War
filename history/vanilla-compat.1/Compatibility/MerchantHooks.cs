using System.Reflection;
using System.Reflection.Emit;
using System.Runtime.CompilerServices;
using MegaCrit.Sts2.Core.Entities.Merchant;
using MegaCrit.Sts2.Core.Random;
using MegaCrit.Sts2.Core.Rooms;
using MegaCrit.Sts2.Core.Nodes.Rooms;
using MegaCrit.Sts2.Core.Nodes.Screens.Shops;
using MegaCrit.Sts2.addons.mega_text;
using MegaCrit.Sts2.Core.Nodes.HoverTips;
namespace RinArcherCore;
[HarmonyPatch(typeof(PlayerRngSet),"get_Shops")]
public static class D2PricingRng
{static void Postfix(PlayerRngSet __instance,ref Rng __result){if(ReferenceEquals(__instance,ContractMerchant.PricingPlayer)&&ContractMerchant.PricingRng is {} rng)__result=rng;}}
[HarmonyPatch(typeof(MerchantInventory),nameof(MerchantInventory.CreateForNormalMerchant))]
public static class D2MerchantFactory
{static bool Prefix(Player player,ref MerchantInventory __result){if(!RunEconomy.Enabled(player))return true;__result=ContractMerchant.Create(player);return false;}}
[HarmonyPatch(typeof(MerchantEntry),nameof(MerchantEntry.OnTryPurchaseWrapper))]
public static class D2MerchantPurchase
{static bool Prefix(MerchantEntry __instance,ref Task<bool> __result){if(__instance is not MerchantCardEntry card||!ContractMerchant.Bound(card,out _))return true;__result=ContractMerchant.Purchase(card);return false;}}
[HarmonyPatch(typeof(MerchantCardRemovalEntry),nameof(MerchantCardRemovalEntry.OnTryPurchaseWrapper))]
public static class D2MerchantRemove
{static bool Prefix(MerchantCardRemovalEntry __instance,ref Task<bool> __result){if(!ContractMerchant.Bound(__instance,out _))return true;__result=ContractMerchant.SelectRemoval(__instance);return false;}}
[HarmonyPatch(typeof(MerchantCardRemovalEntry),"get_IsStocked")]
public static class D2RemovalAvailability
{static void Postfix(MerchantCardRemovalEntry __instance,ref bool __result){if(ContractMerchant.Bound(__instance,out var b))__result=b.Shop.RemovalAvailable&&!b.Shop.RemovalUsed&&RunEconomy.Permanent(b.Player).Any(c=>c.IsRemovable);}}
[HarmonyPatch(typeof(NMerchantCardRemoval),"UpdateVisual")]
public static class D2RemovalDisabledVisual
{
    static void Postfix(NMerchantCardRemoval __instance)
    {if(__instance.Entry is not MerchantCardRemovalEntry e||!ContractMerchant.Bound(e,out _)||e.Used||e.IsStocked)return;__instance.GetNode<Control>("%Hitbox").MouseFilter=Control.MouseFilterEnum.Ignore;__instance.FocusMode=Control.FocusModeEnum.None;__instance.GetNode<Sprite2D>("%Visual").Modulate=new Color(.45f,.45f,.45f);}
}
[HarmonyPatch(typeof(NMerchantRoom),nameof(NMerchantRoom.Create))]
public static class D2MerchantSceneEligibility
{
    static void Postfix(MerchantRoom room,NMerchantRoom? __result)
    {
        if(__result==null||!room.Inventories.Any(i=>RunEconomy.Enabled(i.Player)))return;
        var inventory=__result.GetNode<NMerchantInventory>("%Inventory");
        // Prune only this D2 scene instance before _Ready/Initialize. Original native scenes
        // and relic/potion/colorless generation remain available outside the capability.
        foreach(var group in new[]{"%CharacterCards","%ColorlessCards","%Relics","%Potions"})
        {
            var stock=room.Inventories.First(i=>RunEconomy.Enabled(i.Player));
            var container=inventory.GetNode<Control>(group);int keep=group=="%CharacterCards"?stock.CharacterCardEntries.Count:group=="%ColorlessCards"?stock.ColorlessCardEntries.Count:group is "%Relics" or "%Potions"&&room.Inventories.Any(i=>GenericCompatibility.Enabled(i.Player))?3:0;
            foreach(var node in container.GetChildren().Skip(keep).ToList()){container.RemoveChild(node);node.Free();}
        }
    }
}
[HarmonyPatch(typeof(NMerchantInventory),nameof(NMerchantInventory.Initialize))]
public static class D2MerchantOwnerLabels
{
    static void Postfix(NMerchantInventory __instance,MerchantInventory inventory)
    {
        if(!RunEconomy.Enabled(inventory.Player))return;var cards=__instance.GetNode<Control>("%CharacterCards");
        for(int i=0;i<inventory.CharacterCardEntries.Count;i++)
        {var slot=cards.GetChild<Control>(i);var label=slot.GetNodeOrNull<MegaLabel>("D2OwnerLabel");if(label==null){label=(MegaLabel)slot.GetNode<MegaLabel>("%CostLabel").Duplicate();label.Name="D2OwnerLabel";label.UniqueNameInOwner=false;label.SetAnchorsPreset(Control.LayoutPreset.TopLeft);label.Position=new(-130,-280);label.Modulate=Colors.White;label.Size=new(260,48);label.MouseFilter=Control.MouseFilterEnum.Ignore;label.HorizontalAlignment=HorizontalAlignment.Center;label.AddThemeFontSizeOverride("font_size",24);slot.AddChild(label);}if(ContractMerchant.Bound(inventory.CharacterCardEntries[i],out var binding))label.SetTextAutoSize(binding.Card!.Owner==RunEconomy.Rin?FsnLoc.Text("RIN_ROLE"):FsnLoc.Text("ARCHER_ROLE"));}
    }
}
[HarmonyPatch(typeof(NMerchantCard),"CreateHoverTip")]
public static class D2MerchantHoverLifecycle
{
    static void Prefix(NMerchantCard __instance)
    {if(__instance.Entry is {} entry&&ContractMerchant.Bound(entry,out _))NHoverTipSet.Remove(__instance);}
}
[HarmonyPatch(typeof(NMerchantSlot),"OnMouseReleased")]
public static class D2MerchantMouseAfterController
{
    static void Prefix(NMerchantSlot __instance)
    {
        if(__instance.Entry is not {} entry||!ContractMerchant.Bound(entry,out _)||!entry.IsStocked)return;
        var hitbox=__instance.GetNode<Control>("%Hitbox");
        // The native controller-to-mouse transition releases GUI focus after MouseEntered,
        // clearing its shared hover flag. Use the real hitbox for this release event.
        if(hitbox.GetGlobalRect().HasPoint(hitbox.GetGlobalMousePosition()))AccessTools.Field(typeof(NMerchantSlot),"_isHovered").SetValue(__instance,true);
    }
}
[HarmonyPatch(typeof(MerchantRoom),nameof(MerchantRoom.EnterInternal))]
public static class D2MerchantCheckpoint
{
    static void Postfix(ref Task __result)=>__result=After(__result);
    static async Task After(Task original){await original;var p=RunManager.Instance.DebugOnlyGetState()?.Players.FirstOrDefault(RunEconomy.Enabled);if(p!=null)await ContractSave.Checkpoint(p,"MERCHANT_ENTERED");}
}
[HarmonyPatch]
public static class D2NativePermanentRemoval
{
    static MethodBase TargetMethod()=>AccessTools.Method(typeof(CardPileCmd),nameof(CardPileCmd.RemoveFromDeck),[typeof(IReadOnlyList<CardModel>),typeof(bool)]).GetCustomAttribute<AsyncStateMachineAttribute>()!.StateMachineType.GetMethod("MoveNext",BindingFlags.NonPublic|BindingFlags.Instance)!;
    static IEnumerable<CodeInstruction> Transpiler(IEnumerable<CodeInstruction> instructions)
    {var list=instructions.ToList();var getter=AccessTools.PropertyGetter(typeof(CardPile),nameof(CardPile.Type));var indexes=list.Select((c,i)=>(c,i)).Where(x=>x.c.Calls(getter)).ToList();if(indexes.Count!=1)throw new InvalidOperationException("Native removal guard changed");var c=indexes[0].c;c.opcode=OpCodes.Call;c.operand=AccessTools.Method(typeof(ContractMerchant),nameof(ContractMerchant.NativeRemovalPileType));return list;}
}
[HarmonyPatch]
public static class D2NativePermanentAcquisition
{
    static MethodBase TargetMethod()=>AccessTools.Method(typeof(CardPileCmd),nameof(CardPileCmd.Add),[typeof(IEnumerable<CardModel>),typeof(CardPile),typeof(CardPilePosition),typeof(AbstractModel),typeof(bool)]).GetCustomAttribute<AsyncStateMachineAttribute>()!.StateMachineType.GetMethod("MoveNext",BindingFlags.NonPublic|BindingFlags.Instance)!;
    static IEnumerable<CodeInstruction> Transpiler(IEnumerable<CodeInstruction> instructions)
    {var getter=AccessTools.PropertyGetter(typeof(CardPile),nameof(CardPile.Type));int count=0;foreach(var c in instructions){if(c.Calls(getter)){c.opcode=OpCodes.Call;c.operand=AccessTools.Method(typeof(ContractMerchant),nameof(ContractMerchant.NativeRemovalPileType));count++;}yield return c;}if(count==0)throw new InvalidOperationException("Native deck acquisition guards changed");}
}
[HarmonyPatch(typeof(NMerchantSlot),"OnSelected")]
public static class D2TrackNativeMerchantSelection
{static void Postfix(NMerchantSlot __instance,Task __result){if(__instance.Entry is {} e&&ContractMerchant.Bound(e,out _))NativeRewardTransactions.Track(__result);}}

