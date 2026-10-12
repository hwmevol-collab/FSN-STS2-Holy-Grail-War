using System.Reflection;
using System.Text.RegularExpressions;
using System.Runtime.CompilerServices;
using MegaCrit.Sts2.Core.Nodes.Screens.CharacterSelect;
using MegaCrit.Sts2.Core.Nodes.RestSite;
using MegaCrit.Sts2.Core.Nodes.Screens.Shops;
using MegaCrit.Sts2.Core.Context;
using MegaCrit.Sts2.Core.Helpers;
using MegaCrit.Sts2.Core.Nodes.Relics;
using MegaCrit.Sts2.Core.Nodes.Combat;
namespace FateStayNight;
[HarmonyPatch(typeof(MegaCrit.Sts2.Core.Nodes.Screens.InspectScreens.NInspectRelicScreen),"UpdateRelicDisplay")]
public static class RelicInspectIconPatch{
    static void Postfix(MegaCrit.Sts2.Core.Nodes.Screens.InspectScreens.NInspectRelicScreen __instance){var type=__instance.GetType();var relics=(IReadOnlyList<RelicModel>)AccessTools.Field(type,"_relics").GetValue(__instance)!;int index=(int)AccessTools.Field(type,"_index").GetValue(__instance)!;var unlocked=(IReadOnlySet<RelicModel>)AccessTools.Field(type,"_allUnlockedRelics").GetValue(__instance)!;if(relics[index] is FateRelic relic&&unlocked.Contains(relic.CanonicalInstance)&&Art.Icon(relic.GetType().Name) is {} icon)((TextureRect)AccessTools.Field(type,"_relicImage").GetValue(__instance)!).Texture=icon;}
}
[HarmonyPatch(typeof(MegaCrit.sts2.Core.Nodes.TopBar.NTopBarPortrait),"Initialize")]
public static class TopPortraitPatch{
    static void Postfix(MegaCrit.sts2.Core.Nodes.TopBar.NTopBarPortrait __instance,Player player){if(player.Character is not EmiyaShirou||Art.Texture("ShirouFace") is not {} t)return;foreach(var child in __instance.GetChildren())if(child is CanvasItem c)c.Visible=false;var icon=new TextureRect{Name="FSNFighterIcon",ExpandMode=TextureRect.ExpandModeEnum.IgnoreSize,StretchMode=TextureRect.StretchModeEnum.KeepAspectCentered,MouseFilter=Control.MouseFilterEnum.Ignore,Texture=t,Size=new Vector2(60,60)};__instance.AddChild(icon);icon.Size=new(60,60);}
}
[HarmonyPatch(typeof(NRelic),"Reload")]
public static class RelicNodeIconPatch{
    static void Postfix(NRelic __instance){var model=AccessTools.Field(typeof(NRelic),"_model").GetValue(__instance);if(!__instance.IsNodeReady()||model is not FateRelic||Art.Icon(model.GetType().Name) is not {} icon)return;__instance.Icon.Texture=icon;__instance.Outline.Texture=icon;__instance.Outline.Visible=false;}
}
[HarmonyPatch(typeof(NPower),"Reload")]
public static class PowerNodeIconPatch{
    static void Postfix(NPower __instance){var model=AccessTools.Field(typeof(NPower),"_model").GetValue(__instance);if(!__instance.IsNodeReady()||model is not FatePower||Art.Icon(model.GetType().Name) is not {} icon)return;((TextureRect)AccessTools.Field(typeof(NPower),"_icon").GetValue(__instance)!).Texture=icon;if(AccessTools.Field(typeof(NPower),"_powerFlash").GetValue(__instance) is CpuParticles2D flash)flash.Texture=icon;}
}
[HarmonyPatch(typeof(CharacterModel),nameof(CharacterModel.IconTexture),MethodType.Getter)]
public static class CharacterIconTexturePatch{
    static void Postfix(CharacterModel __instance,ref Texture2D __result){if(__instance is EmiyaShirou&&Art.Texture("ShirouIcon") is {} t)__result=t;}
}
[HarmonyPatch]
public static class RelicIconPatch{
    static IEnumerable<MethodBase> TargetMethods()=>new[]{"Icon","IconOutline","BigIcon"}.Select(n=>AccessTools.PropertyGetter(typeof(RelicModel),n));
    static bool Prefix(RelicModel __instance,ref Texture2D __result){if(__instance is not FateRelic||Art.Icon(__instance.GetType().Name) is not {} icon)return true;__result=icon;return false;}
}
[HarmonyPatch]
public static class PowerIconPatch{
    static IEnumerable<MethodBase> TargetMethods()=>new[]{"Icon","BigIcon"}.Select(n=>AccessTools.PropertyGetter(typeof(PowerModel),n));
    static bool Prefix(PowerModel __instance,ref Texture2D __result){if(__instance is not FatePower||Art.Icon(__instance.GetType().Name) is not {} icon)return true;__result=icon;return false;}
}
[HarmonyPatch(typeof(NCharacterSelectButton),nameof(NCharacterSelectButton.Init))]
public static class SelectionIconPatch{
    static void Postfix(NCharacterSelectButton __instance,CharacterModel character){if(character is EmiyaShirou&&Art.Texture("ShirouFace") is {} t)((TextureRect)AccessTools.Field(typeof(NCharacterSelectButton),"_icon").GetValue(__instance)!).Texture=t;}
}
[HarmonyPatch(typeof(NCharacterSelectScreen),nameof(NCharacterSelectScreen.SelectCharacter))]
public static class SelectionPortraitPatch{
    static readonly ConditionalWeakTable<NCharacterSelectScreen,OutlineState> Outlines=new();
    sealed class OutlineState{public bool Visible;}
    static void Postfix(NCharacterSelectScreen __instance,CharacterModel characterModel){
        SelectionMusic.Select(__instance,characterModel is EmiyaShirou);
        var bg=(Control)AccessTools.Field(typeof(NCharacterSelectScreen),"_bgContainer").GetValue(__instance)!;
        foreach(var oldBoard in bg.GetChildren().Where(n=>n.Name=="FSNSelection").ToArray()){bg.RemoveChild(oldBoard);oldBoard.QueueFree();}
        var outline=(TextureRect)AccessTools.Field(typeof(NCharacterSelectScreen),"_relicIconOutline").GetValue(__instance)!;
        if(characterModel is not EmiyaShirou){if(Outlines.TryGetValue(__instance,out var original)){outline.Visible=original.Visible;Outlines.Remove(__instance);}return;}
        if(!Outlines.TryGetValue(__instance,out _))Outlines.Add(__instance,new(){Visible=outline.Visible});
        if(Art.Icon(nameof(CommandSeals)) is {} sealIcon)((TextureRect)AccessTools.Field(typeof(NCharacterSelectScreen),"_relicIcon").GetValue(__instance)!).Texture=sealIcon;
        outline.Visible=false;
        foreach(var child in bg.GetChildren())if(child is CanvasItem c)c.Visible=false;
        var board=new Control{Name="FSNSelection",MouseFilter=Control.MouseFilterEnum.Ignore};bg.AddChild(board);
        Skin.SelectionBackdrop(board);
        var caption=new Label{Text="Fate / stay night",Position=new(1710,943)};
        caption.AddThemeFontSizeOverride("font_size",30);caption.Modulate=new("e7dab8");board.AddChild(caption);
        var sub=new Label{Text="此身为剑所成",Position=new(1714,995)};
        sub.AddThemeFontSizeOverride("font_size",20);sub.Modulate=new("a5cee3");board.AddChild(sub);
    }
}
[HarmonyPatch(typeof(NRestSiteCharacter),"_Ready")]
public static class RestPortraitPatch{
    static void Postfix(NRestSiteCharacter __instance){if(__instance.Player.Character is not EmiyaShirou)return;foreach(var child in __instance.GetChildren())if(child is Node2D n)n.Visible=false;Art.Portrait(__instance,"Shirou",new(0,-130),290);}
}
[HarmonyPatch(typeof(NMerchantCharacter),"_Ready")]
public static class MerchantPortraitPatch{
    static void Postfix(NMerchantCharacter __instance){var p=LocalContext.GetMe(RunManager.Instance.DebugOnlyGetState());if(p?.Character is not EmiyaShirou)return;if(__instance.GetChild(0) is CanvasItem c)c.Visible=false;Art.Portrait(__instance,"Shirou",new(0,-140),290);}
}
[HarmonyPatch]
public static class ExactKeywordTextPatch{
    static MethodBase TargetMethod()=>typeof(CardModel).GetMethods(BindingFlags.NonPublic|BindingFlags.Instance).Single(m=>m.Name=="GetDescriptionForPile");
    static void Postfix(CardModel __instance,ref string __result){
        CardKeyword[] redundant=__instance switch{Coordination=>[CardKeyword.Innate,CardKeyword.Retain],DesperateFlight=>[CardKeyword.Ethereal],FateNight or GemWind=>[CardKeyword.Exhaust],_=>[]};
        var words=redundant.Select(k=>new MegaCrit.Sts2.Core.Localization.LocString("card_keywords",StringHelper.Slugify(k.ToString())+".title").GetFormattedText()+new MegaCrit.Sts2.Core.Localization.LocString("card_keywords","PERIOD").GetRawText()).ToHashSet();
        __result=string.Join('\n',__result.Split('\n').Where(l=>!words.Contains(Regex.Replace(l,@"\[[^\]]*\]",""))));
    }
}

