using System.Reflection;
using System.Reflection.Emit;
using MegaCrit.Sts2.Core.Nodes.Screens.CharacterSelect;

namespace RinArcherCore;

// Rin deliberately has no starting relic. Skip only the native relic preview;
// preserve the native lobby selection, ready/embark flow and unlock decisions.
[HarmonyPatch(typeof(NCharacterSelectScreen),nameof(NCharacterSelectScreen.SelectCharacter))]
public static class NativeEmptyStartingRelicPreview
{
    public static int GuardedSites { get; private set; }
    public static bool IsEmptyRin(CharacterModel character)=>character is RinContractCharacter&&character.StartingRelics.Count==0;
    public static void Clear(NCharacterSelectScreen screen)
    {
        var relic=screen.GetNode<Control>("InfoPanel/VBoxContainer/Relic");
        relic.GetNode<MegaCrit.Sts2.addons.mega_text.MegaRichTextLabel>("Name/RichTextLabel").Text="";
        relic.GetNode<MegaCrit.Sts2.addons.mega_text.MegaRichTextLabel>("Description").Text="";
        relic.GetNode<TextureRect>("Icon").Texture=null;
        relic.GetNode<TextureRect>("Icon/Outline").Texture=null;
    }
    static void Prefix(NCharacterSelectScreen __instance,CharacterModel characterModel)
    {
        __instance.GetNode<Control>("InfoPanel/VBoxContainer/Relic").Visible=!IsEmptyRin(characterModel);
    }
    static void Postfix(NCharacterSelectScreen __instance,NCharacterSelectButton charSelectButton,CharacterModel characterModel)
    {
        if(characterModel is RinContractCharacter&&!charSelectButton.IsLocked)
            GD.Print("[RIN_ARCHER_ENTRY] Native selection completed; lobby="+__instance.Lobby.LocalPlayer.character.Id+"; zero starting relics preserved.");
    }
    [HarmonyPriority(Priority.Last)]
    static IEnumerable<CodeInstruction> Transpiler(IEnumerable<CodeInstruction> instructions,ILGenerator generator)
    {
        var code=instructions.ToList();var ranges=new List<(int start,int end)>();
        var getter=AccessTools.PropertyGetter(typeof(CharacterModel),nameof(CharacterModel.StartingRelics));
        var outline=AccessTools.Field(typeof(NCharacterSelectScreen),"_relicIconOutline");
        for(int i=0;i<code.Count;i++)
        {
            if(!code[i].Calls(getter))continue;
            if(i==0||code[i-1].opcode!=OpCodes.Ldarg_2)throw new InvalidOperationException("Native relic preview character load changed");
            int end=-1;
            for(int j=i+1;j<Math.Min(code.Count,i+100);j++)
            {
                if(code[j].operand is not MethodInfo method||method.Name!="set_SelfModulate")continue;
                if(code.Skip(Math.Max(i,j-5)).Take(j-Math.Max(i,j-5)).Any(c=>c.LoadsField(outline))) {end=j+1;break;}
            }
            if(end<0)throw new InvalidOperationException("Native relic preview boundary changed");
            ranges.Add((i-1,end));
        }
        if(ranges.Count!=2)throw new InvalidOperationException("Expected exactly two native starting-relic preview sites");
        foreach(var (start,end) in ranges.OrderByDescending(r=>r.start))
        {
            var original=generator.DefineLabel();var after=generator.DefineLabel();
            var first=new CodeInstruction(OpCodes.Ldarg_2);first.labels.AddRange(code[start].labels);code[start].labels.Clear();
            code[start].labels.Add(original);code[end].labels.Add(after);
            code.InsertRange(start,[first,new(OpCodes.Call,AccessTools.Method(typeof(NativeEmptyStartingRelicPreview),nameof(IsEmptyRin))),new(OpCodes.Brfalse,original),new(OpCodes.Ldarg_0),new(OpCodes.Call,AccessTools.Method(typeof(NativeEmptyStartingRelicPreview),nameof(Clear))),new(OpCodes.Br,after)]);
        }
        GuardedSites=ranges.Count;return code;
    }
}

// Historical B/C/D launchers remain available in their own QA profiles. The
// native E2B manual flow uses the ordinary singleplayer character selector.
[HarmonyPatch(typeof(CoreHud),nameof(CoreHud.AttachLauncher))]
public static class NativeE2BMenuWithoutLegacyQaOverlay
{
    static bool Prefix()
    {
        if(!FullActIndependentRunInitialization.Requested())return true;
        CoreHud.ClearLauncher();return false;
    }
}
