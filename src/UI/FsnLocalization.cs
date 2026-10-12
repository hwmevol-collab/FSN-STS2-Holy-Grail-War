using MegaCrit.Sts2.Core.Localization;
using MegaCrit.Sts2.Core.Modding;
using BaseLib.Abstracts;
using System.Reflection;
namespace RinArcherCore;

// Native LocManager tables and SmartFormat; one mod, native locale, English fallback.
public static class FsnLoc
{
    public static bool Chinese=>LocManager.Instance?.Language=="zhs";
    static readonly Dictionary<string,string> textCache=new(StringComparer.Ordinal);
    static string? cachedLanguage;
    public static string Text(string key)
    {
        string? language=LocManager.Instance?.Language;
        if(cachedLanguage!=language){textCache.Clear();cachedLanguage=language;}
        if(textCache.TryGetValue(key,out var value))return value;
        return textCache[key]=new LocString("rest_site_ui","FSN_"+key).GetFormattedText();
    }
    public static string Format(string key,params object?[] args)
    {var loc=new LocString("rest_site_ui","FSN_"+key);for(int i=0;i<args.Length;i++)loc.Add("v"+i,args[i]?.ToString()??"");return loc.GetFormattedText();}
    public static string Name(StarterCard c)=>Text("CARD_"+c.SourceCardId+"_TITLE");
    public static string Rules(StarterCard c,bool? upgraded=null)=>Text("CARD_"+c.SourceCardId+((upgraded??c.IsUpgraded)?"_UP":"_NORMAL"));
    public static void RefreshModels()
    {
        textCache.Clear();
        if(LocManager.Instance==null||AccessTools.Field(typeof(ModelDb),"_contentById").GetValue(null) is not Dictionary<ModelId,AbstractModel> models)return;
        foreach(var (id,model) in models)
        {
            if(model.GetType().Assembly!=typeof(FsnLoc).Assembly||model is not ILocalizationProvider provider||provider.Localization==null)continue;
            string? table=model switch{CardModel=>"cards",CharacterModel=>"characters",PowerModel=>"powers",MonsterModel=>"monsters",RelicModel=>"relics",_=>null};
            if(table==null)continue;
            LocManager.Instance.GetTable(table).MergeWith(provider.Localization.ToDictionary(x=>id.Entry+"."+x.Item1,x=>x.Item2));
        }
    }
}
[HarmonyPatch(typeof(ModManager),nameof(ModManager.GetModdedLocTables))]
public static class FsnNativeLocaleTables
{
    [HarmonyPriority(Priority.Last)]
    static void Postfix(string language,string file,ref IEnumerable<string> __result)
    {
        if(file!="rest_site_ui.json")return;
        string folder=Path.Combine(ContentPaths.Root,"Localization");
        // Native mod discovery treats every loose .json as a manifest. JSON text
        // uses .loc in the install package; keep legacy .json lookup for editors.
        string Table(string locale){string original=Path.Combine(folder,locale,file);string packed=Path.ChangeExtension(original,".loc");return File.Exists(packed)?packed:original;}
        string english=Table("eng"),zh=Table("zhs");
        __result=__result.Concat(File.Exists(english)?new[]{english}:Array.Empty<string>()).Concat(language=="zhs"&&File.Exists(zh)?new[]{zh}:Array.Empty<string>());
    }
}
[HarmonyPatch(typeof(ModelDb),"Init")]
public static class FsnModelLocaleInitialization
{[HarmonyPriority(Priority.Last)]static void Postfix()=>FsnLoc.RefreshModels();}
[HarmonyPatch(typeof(LocManager),nameof(LocManager.SetLanguage))]
public static class FsnModelLocaleRefresh
{[HarmonyPriority(Priority.Last)]static void Postfix()=>FsnLoc.RefreshModels();}
