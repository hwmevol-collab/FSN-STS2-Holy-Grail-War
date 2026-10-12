using System.Collections.Frozen;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace RinArcherCore;

public sealed record VanillaVersionSignature(string GameVersion,string Commit,string AssemblySha256,string AssemblyMvid);

// NativeAllowed describes an already evaluated acquisition path, not an alternative pool.
public sealed record CompatibilityEligibilityContext(bool RinContract,bool NativeAllowed,string Source,IReadOnlySet<string> ReadyContentIds,
    IReadOnlyDictionary<string,CompatibilityGenerationBudget>? GenerationBudgets=null,IReadOnlySet<string>? CustomReadyContentIds=null);

// Every branch is the caller's native, character/act/unlock/rarity-filtered pool.
// RequestedCount is the complete native quantity, before any RNG or presentation.
public sealed record CompatibilityGenerationBudget(int RequestedCount,bool Distinct,
    IReadOnlyDictionary<string,IReadOnlyList<string>> NativeBranches,IReadOnlySet<string>? AuditedReplacementProviderIds=null);
public sealed record CompatibilityDependency(string SourceId,string TargetId,string Semantics,string Type,bool BeforePresentation,JsonElement Evidence);

public sealed record CompatibilityEffect(string EffectId,string Trigger,string Scope,string Classification,string? AdapterFamily,JsonElement Evidence,string TargetSourceKind="");
public sealed record CompatibilityPowerDependency(string ModelType,IReadOnlyList<string> Hooks);
public sealed record CompatibilityContent(string ContentId,string Classification,string Recommendation,IReadOnlyList<CompatibilityEffect> Effects,IReadOnlyList<string> AdapterFamilies,string? ModelType=null,IReadOnlyList<CompatibilityPowerDependency>? PowerDependencies=null);

public sealed class VanillaCompatibilityRegistry
{
    public const string GenericRecommendation="ENABLE_AFTER_E2_GENERIC";
    static readonly string[] Categories=["relics","potions","events","rooms"];
    static readonly string[] Documents=["adapter-families","dependency-graph","events","potions","public-alpha-allowlist-draft","relics","rooms","summary"];
    static readonly FrozenSet<string> Classifications=new[]{"NATIVE_SAFE","GENERIC_ADAPTER","CUSTOM_ADAPTER","FILTERED_PUBLIC_ALPHA"}.ToFrozenSet(StringComparer.Ordinal);
    static readonly FrozenSet<string> Scopes=new[]{"CONTRACT","ACTIVE_AT_TRIGGER","CARD_OWNER","DAMAGE_TARGET","CHOOSE_MEMBER","CHOOSE_DECK","DUAL_DECK_SELECTOR","RANDOM_PERMANENT_CARD_UNION","ACTIVE_HAND","ENEMY","UNSAFE"}.ToFrozenSet(StringComparer.Ordinal);
    readonly FrozenDictionary<string,CompatibilityContent> entries;
    readonly FrozenDictionary<string,string> categories;
    readonly FrozenDictionary<string,string> quarantined;
    readonly FrozenDictionary<string,CompatibilityDependency[]> dependencies;
    public bool IsValid{get;}
    public string FailureReason{get;}
    public string MatrixSignature{get;}
    public IReadOnlyCollection<CompatibilityContent> Entries=>entries.Values;

    VanillaCompatibilityRegistry(bool valid,string reason,string signature,Dictionary<string,CompatibilityContent> content,Dictionary<string,string> category,IDictionary<string,string>? quarantine,Dictionary<string,CompatibilityDependency[]>? graph=null)
    {
        IsValid=valid;FailureReason=reason;MatrixSignature=signature;
        entries=content.ToFrozenDictionary(StringComparer.Ordinal);categories=category.ToFrozenDictionary(StringComparer.Ordinal);
        var blocked=CompatibilityMatrixFingerprint.QuarantinedContent.ToDictionary(e=>e.Key,e=>e.Value,StringComparer.Ordinal);
        if(quarantine!=null)foreach(var item in quarantine)blocked.TryAdd(item.Key,item.Value);
        quarantined=blocked.ToFrozenDictionary(StringComparer.Ordinal);
        dependencies=(graph??new()).ToFrozenDictionary(StringComparer.Ordinal);
    }

    public static VanillaVersionSignature InstalledSignature()
    {
        var assembly=typeof(ModelDb).Assembly;
        var directory=Path.GetDirectoryName(OS.GetExecutablePath())!;
        using var release=JsonDocument.Parse(File.ReadAllText(Path.Combine(directory,"release_info.json")));
        return new(release.RootElement.GetProperty("version").GetString()!,release.RootElement.GetProperty("commit").GetString()!,
            Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(assembly.Location))),assembly.ManifestModule.ModuleVersionId.ToString());
    }

    // No gameplay hooks are installed by loading the registry. A generic model must
    // be separately validated and registered as ready before production eligibility.
    public static VanillaCompatibilityRegistry LoadEmbedded(VanillaVersionSignature actual,IDictionary<string,string>? quarantine=null)
    {
        var assembly=typeof(VanillaCompatibilityRegistry).Assembly;
        return Load(name=>{
            using var stream=assembly.GetManifestResourceStream("RinArcherCore.Compatibility."+name+".json")??throw new InvalidDataException("Missing matrix document: "+name);
            using var memory=new MemoryStream();stream.CopyTo(memory);return memory.ToArray();
        },CompatibilityMatrixFingerprint.Hashes,actual,quarantine);
    }

    public static VanillaCompatibilityRegistry Load(Func<string,byte[]> read,IReadOnlyDictionary<string,string> expectedHashes,VanillaVersionSignature actual,IDictionary<string,string>? quarantine=null)
    {
        var content=new Dictionary<string,CompatibilityContent>(StringComparer.Ordinal);var category=new Dictionary<string,string>(StringComparer.Ordinal);
        var parsed=new Dictionary<string,JsonDocument>(StringComparer.Ordinal);
        try
        {
            var hashes=new Dictionary<string,string>(StringComparer.Ordinal);
            foreach(var name in Documents)
            {
                var bytes=read(name);var hash=Convert.ToHexString(SHA256.HashData(bytes));
                if(!expectedHashes.TryGetValue(name,out var expected)||hash!=expected)throw new InvalidDataException("MATRIX_INTEGRITY_MISMATCH: "+name);
                hashes.Add(name,hash);var document=JsonDocument.Parse(bytes);parsed.Add(name,document);
                Check(document.RootElement.GetProperty("schemaVersion").GetInt32()==1,"MATRIX_SCHEMA_VERSION: "+name);
            }
            var summary=parsed["summary"].RootElement;var game=summary.GetProperty("game");
            Check(summary.GetProperty("status").GetString()=="RIN_ARCHER_VANILLA_COMPATIBILITY_MATRIX_E1_AMENDED_PASS","E1_MATRIX_NOT_PASS");
            Check(Text(summary,"matrixRevision")==CompatibilityMatrixFingerprint.Revision,"MATRIX_REVISION_MISMATCH");
            Check(Text(summary,"supersedesMatrixSignature")==CompatibilityMatrixFingerprint.Supersedes,"MATRIX_HISTORY_MISMATCH");
            foreach(var flag in new[]{"UNKNOWN_RELICS","UNKNOWN_POTIONS","UNKNOWN_EVENTS","UNKNOWN_ROOM_TYPES","DESIGN_DEVIATIONS","DESIGN_CONTRACT_CONFLICT","IMPLEMENTATION_BLOCKERS","E1_MATRIX_CORRECTION_REQUIRED"})Check(summary.GetProperty(flag).GetInt32()==0,flag);
            foreach(var flag in new[]{"TARGET_SCOPE_SOURCE_CONSISTENCY_PASS","TRANSITIVE_ELIGIBILITY_CLOSURE_PASS","FIXED_REWARD_DEPENDENCY_PASS","MULTI_TARGET_EFFECT_SPLITTING_PASS","ZERO_UNRESOLVED_MATRIX_CORRECTIONS"})Check(summary.GetProperty("gates").GetProperty(flag).GetBoolean(),flag);
            Check(actual==new VanillaVersionSignature(Text(game,"version"),Text(game,"commit"),Text(game,"assemblySha256"),Text(game,"assemblyMvid")),"VANILLA_COMPATIBILITY_VERSION_MISMATCH");
            var interfaces=parsed["adapter-families"].RootElement.GetProperty("interfaces").EnumerateArray().Select(e=>Text(e,"family")).ToHashSet(StringComparer.Ordinal);
            var draft=parsed["public-alpha-allowlist-draft"].RootElement.GetProperty("items");
            foreach(var name in Categories)
            {
                var doc=parsed[name].RootElement;
                Check(Text(doc,"gameVersion")==actual.GameVersion&&Text(doc,"gameCommit")==actual.Commit,"MATRIX_DOCUMENT_VERSION: "+name);
                var recommendations=draft.GetProperty(name).EnumerateArray().ToDictionary(e=>Text(e,"contentId"),e=>Text(e,"recommendation"),StringComparer.Ordinal);
                string previous="";
                foreach(var item in doc.GetProperty("items").EnumerateArray())
                {
                    var id=Text(item,name=="rooms"?"roomTypeId":"contentId");var tier=Text(item,"classification");
                    Check(string.CompareOrdinal(previous,id)<0,"UNSORTED_OR_DUPLICATE_ID: "+id);previous=id;
                    Check(Classifications.Contains(tier),"UNKNOWN_CLASSIFICATION: "+id);
                    var recommendation=recommendations[id];
                    Check(recommendation==(tier is "NATIVE_SAFE" or "GENERIC_ADAPTER"?GenericRecommendation:tier=="CUSTOM_ADAPTER"?"ENABLE_AFTER_CUSTOM_ADAPTER":"KEEP_FILTERED_FOR_V0_0_0_0_1"),"RECOMMENDATION_CONFLICT: "+id);
                    var effects=new List<CompatibilityEffect>();
                    var effectIds=new HashSet<string>(StringComparer.Ordinal);
                    var commands=new HashSet<string>(StringComparer.Ordinal);
                    if(item.TryGetProperty("effects",out var rows))foreach(var row in rows.EnumerateArray())
                    {
                        var scope=Text(row,"proposedDualScope");var effectTier=Text(row,"classification");
                        string? family=row.GetProperty("adapterFamily").GetString();
                        Check(Scopes.Contains(scope)&&Classifications.Contains(effectTier),"INVALID_EFFECT: "+id);
                        Check(effectTier!="GENERIC_ADAPTER"||family!=null&&interfaces.Contains(family),"MISSING_ADAPTER_FAMILY: "+id);
                        Check(effectIds.Add(Text(row,"effectId")),"DUPLICATE_EFFECT_ID: "+id);
                        var target=row.GetProperty("targetSource");var kind=Text(target,"kind");
                        Check(kind.Length>0&&target.GetProperty("path").GetArrayLength()>0,"MISSING_TARGET_SOURCE: "+id);
                        if(kind.StartsWith("ENEMY",StringComparison.Ordinal)||kind=="BOUND_ENEMY")Check(scope=="ENEMY","TARGET_SCOPE_SOURCE_CONSISTENCY: "+id);
                        if(kind is "OWNER_CREATURE" or "MEMBER_PARAMETER" or "BOUND_MEMBER")Check(scope!="ENEMY","TARGET_SCOPE_SOURCE_CONSISTENCY: "+id);
                        if(kind=="MIXED_REAL_RECIPIENTS")Check(scope=="DAMAGE_TARGET","TARGET_SCOPE_SOURCE_CONSISTENCY: "+id);
                        var evidence=row.GetProperty("evidence");
                        if(evidence.TryGetProperty("api",out var api)&&evidence.TryGetProperty("arguments",out _))
                            Check(commands.Add(Text(evidence,"source")+":"+evidence.GetProperty("line").GetInt32()+":"+api.GetString()+":"+(evidence.TryGetProperty("parentEffectId",out var parent)?parent.GetString():"")),"MULTI_TARGET_EFFECT_SPLITTING: "+id);
                        effects.Add(new(Text(row,"effectId"),Text(row,"trigger"),scope,effectTier,family,evidence.Clone(),kind));
                    }
                    Check(name=="rooms"||effects.Count>0,"MISSING_EFFECTS: "+id);
                    var families=name=="rooms"?item.GetProperty("adapterFamily").EnumerateArray().Select(e=>e.GetString()!).ToArray()
                        :effects.Where(e=>e.AdapterFamily!=null).Select(e=>e.AdapterFamily!).Distinct(StringComparer.Ordinal).Order(StringComparer.Ordinal).ToArray();
                    Check(tier!="GENERIC_ADAPTER"||families.Length>0&&families.All(interfaces.Contains),"MISSING_CONTENT_ADAPTER_FAMILY: "+id);
                    var powers=item.TryGetProperty("dependencies",out var dependencies)?dependencies.EnumerateArray()
                        .Where(d=>d.TryGetProperty("kind",out var kind)&&kind.GetString()=="power")
                        .Select(d=>new CompatibilityPowerDependency(d.GetProperty("modelType").GetString()!,
                            d.GetProperty("hooks").EnumerateArray().Select(h=>h.GetString()!).ToArray())).ToArray():[];
                    content.Add(id,new(id,tier,recommendation,effects.AsReadOnly(),Array.AsReadOnly(families),item.TryGetProperty("modelType",out var modelType)?modelType.GetString():null,powers));category.Add(id,name);
                }
                Check(content.Count(e=>category[e.Key]==name)==recommendations.Count,"ALLOWLIST_COVERAGE: "+name);
            }
            var graphRoot=parsed["dependency-graph"].RootElement;
            Check(Text(graphRoot,"matrixRevision")==CompatibilityMatrixFingerprint.Revision,"DEPENDENCY_GRAPH_REVISION");
            var nodes=graphRoot.GetProperty("nodes").EnumerateArray().ToDictionary(n=>Text(n,"id"),n=>n.Clone(),StringComparer.Ordinal);
            foreach(var row in content.Values)
                Check(nodes.TryGetValue(row.ContentId,out var node)&&Text(node,"classification")==row.Classification&&node.GetProperty("matrixAudited").GetBoolean(),"DEPENDENCY_NODE_COVERAGE: "+row.ContentId);
            var edges=new List<CompatibilityDependency>();
            var semantics=new HashSet<string>(["REQUIRED_FIXED_DEPENDENCY","OPTIONAL_CANDIDATE_POOL","INDIRECT_RANDOM_GENERATION","CONDITIONAL_BRANCH"],StringComparer.Ordinal);
            foreach(var edge in graphRoot.GetProperty("edges").EnumerateArray())
            {
                var source=Text(edge,"sourceId");var target=Text(edge,"targetId");var semantic=Text(edge,"dependencySemantics");
                Check(nodes.ContainsKey(source)&&nodes.ContainsKey(target)&&semantics.Contains(semantic),"UNRESOLVED_DEPENDENCY");
                Check(!edge.GetProperty("terminalFilteringAllowed").GetBoolean()&&edge.GetProperty("preserveBudget").GetBoolean(),"DEPENDENCY_BUDGET_POLICY");
                bool required=edge.GetProperty("requiredBeforePresentation").GetBoolean();
                if(semantic=="REQUIRED_FIXED_DEPENDENCY")Check(required,"FIXED_REWARD_DEPENDENCY");
                edges.Add(new(source,target,semantic,Text(edge,"dependencyType"),required,edge.Clone()));
            }
            var signature=Convert.ToHexString(SHA256.HashData(Encoding.UTF8.GetBytes(string.Join('\n',hashes.OrderBy(e=>e.Key,StringComparer.Ordinal).Select(e=>e.Key+":"+e.Value)))));
            Check(signature==CompatibilityMatrixFingerprint.Signature,"UNAPPROVED_MATRIX_SIGNATURE");
            var manifestBytes=read("matrix-signature");
            Check(Convert.ToHexString(SHA256.HashData(manifestBytes))==CompatibilityMatrixFingerprint.ManifestSha256,"MATRIX_MANIFEST_INTEGRITY");
            using var manifest=JsonDocument.Parse(manifestBytes);var root=manifest.RootElement;
            Check(root.GetProperty("schemaVersion").GetInt32()==1&&Text(root,"matrixSignature")==signature&&Text(root,"matrixRevision")==CompatibilityMatrixFingerprint.Revision&&Text(root,"supersedesMatrixSignature")==CompatibilityMatrixFingerprint.Supersedes,"MATRIX_MANIFEST_CONFLICT");
            Check(root.GetProperty("signedDocuments").EnumerateObject().Count()==hashes.Count,"MATRIX_MANIFEST_COVERAGE");
            foreach(var hash in hashes)Check(Text(root.GetProperty("signedDocuments"),hash.Key)==hash.Value,"MATRIX_MANIFEST_HASH: "+hash.Key);
            return new(true,"",signature,content,category,quarantine,edges.GroupBy(e=>e.SourceId,StringComparer.Ordinal).ToDictionary(g=>g.Key,g=>g.ToArray(),StringComparer.Ordinal));
        }
        catch(Exception e) when(e is not OutOfMemoryException)
        {
            // Reject the whole partial parse; no successfully read prefix may become eligible.
            return new(false,e.Message,"",new(),new(),quarantine);
        }
        finally{foreach(var doc in parsed.Values)doc.Dispose();}
    }
    static void Check(bool condition,string message){if(!condition)throw new InvalidDataException(message);}
    static string Text(JsonElement row,string name)=>row.GetProperty(name).GetString()??throw new InvalidDataException("Null field: "+name);
    public string GetClassification(string contentId)=>entries.TryGetValue(contentId,out var row)?row.Classification:"UNKNOWN";
    public string GetRecommendation(string contentId)=>entries.TryGetValue(contentId,out var row)?row.Recommendation:"KEEP_FILTERED_FOR_V0_0_0_0_1";
    public IReadOnlyList<CompatibilityEffect> GetEffectScopes(string contentId)=>entries.TryGetValue(contentId,out var row)?row.Effects:[];
    public IReadOnlyList<string> GetAdapterFamilies(string contentId)=>entries.TryGetValue(contentId,out var row)?row.AdapterFamilies:[];
    public IReadOnlyList<CompatibilityDependency> GetDependencies(string contentId)=>dependencies.TryGetValue(contentId,out var rows)?rows:[];
    public string RejectionReason(string contentId,CompatibilityEligibilityContext context,string expectedCategory)
        =>RejectionReasonCore(contentId,context,expectedCategory,new HashSet<string>(StringComparer.Ordinal));
    string RejectionReasonCore(string contentId,CompatibilityEligibilityContext context,string expectedCategory,HashSet<string> visiting)
    {
        if(!context.NativeAllowed)return "NATIVE_ACQUISITION_CONDITIONS_REJECTED";
        if(!context.RinContract)return "";
        if(!IsValid)return FailureReason;
        if(!entries.TryGetValue(contentId,out var row)||categories[contentId]!=expectedCategory)return "UNAUDITED_CONTENT";
        if(quarantined.TryGetValue(contentId,out var reason))return reason;
        if(row.Classification=="CUSTOM_ADAPTER")return context.CustomReadyContentIds?.Contains(contentId)==true&&
            (expectedCategory=="events"&&(FullActEventBridge.Ids.Contains(contentId)||FullActThirdAncientBridge.Ids.Contains(contentId))||expectedCategory=="relics"&&(contentId==FullActFirstTreasureBridge.Id&&FullActFirstTreasureBridge.SourceAllowed(context.Source)||contentId==FullActThirdAncientBridge.Cape&&FullActThirdAncientBridge.CapeSource(context.Source)))?"":"WAITING_FOR_CUSTOM_ADAPTER";
        if(row.Classification=="FILTERED_PUBLIC_ALPHA")return "FILTERED_PUBLIC_ALPHA";
        if(row.Recommendation!=GenericRecommendation)return "UNAPPROVED_RECOMMENDATION";
        if(row.Classification=="GENERIC_ADAPTER"&&!context.ReadyContentIds.Contains(contentId))return "GENERIC_ADAPTER_NOT_VALIDATED";
        return DependencyRejection(contentId,context,visiting);
    }
    string DependencyRejection(string id,CompatibilityEligibilityContext context,HashSet<string> visiting)
    {
        if(!visiting.Add(id))return "DEPENDENCY_CYCLE_NOT_VALIDATED";
        try
        {
            foreach(var edge in GetDependencies(id))
            {
                if(edge.Semantics is "OPTIONAL_CANDIDATE_POOL" or "INDIRECT_RANDOM_GENERATION")
                {
                    if(context.GenerationBudgets==null||(!context.GenerationBudgets.TryGetValue(id+"->"+edge.TargetId,out var budget)&&!context.GenerationBudgets.TryGetValue(edge.TargetId,out budget)))return "GENERATION_BUDGET_NOT_VALIDATED: "+edge.TargetId;
                    var reason=GenerationBudgetRejectionCore(edge.TargetId,budget,context,visiting);
                    if(reason.Length>0)return reason;
                    continue;
                }
                if(!entries.TryGetValue(edge.TargetId,out var target))return "UNAUDITED_DEPENDENCY: "+edge.TargetId;
                if(target.Classification is "CUSTOM_ADAPTER" or "FILTERED_PUBLIC_ALPHA")return "BLOCKING_DEPENDENCY: "+edge.TargetId;
                if(target.Classification=="GENERIC_ADAPTER"&&!context.ReadyContentIds.Contains(edge.TargetId))return "DEPENDENCY_ADAPTER_NOT_VALIDATED: "+edge.TargetId;
                var nested=DependencyRejection(edge.TargetId,context,visiting);if(nested.Length>0)return nested;
            }
            return "";
        }
        finally{visiting.Remove(id);}
    }
    public string GenerationBudgetRejection(string poolId,CompatibilityGenerationBudget budget,CompatibilityEligibilityContext context)
        =>GenerationBudgetRejectionCore(poolId,budget,context,new HashSet<string>(StringComparer.Ordinal));
    string GenerationBudgetRejectionCore(string poolId,CompatibilityGenerationBudget budget,CompatibilityEligibilityContext context,HashSet<string> visiting)
    {
        if(!context.RinContract)return "";
        if(!IsValid)return FailureReason;
        string? category=poolId switch{"POOL.NATIVE_POTIONS"=>"potions","POOL.NATIVE_RELICS"=>"relics",_=>null};
        if(category==null&&!(poolId=="POOL.NATIVE_CARDS"&&budget.AuditedReplacementProviderIds!=null))return "UNSUPPORTED_GENERATION_POOL: "+poolId;
        if(!context.NativeAllowed||budget.RequestedCount<=0||budget.NativeBranches.Count==0)return "INVALID_NATIVE_GENERATION_BUDGET";
        foreach(var branch in budget.NativeBranches)
        {
            // Native candidates are the only input. The registry never substitutes a
            // rarer, different-character or lower-count payload to fill a shortage.
            var eligible=category==null?branch.Value.Where(id=>budget.AuditedReplacementProviderIds!.Contains(id)):
                branch.Value.Where(id=>RejectionReasonCore(id,context,category,visiting).Length==0);
            int capacity=budget.Distinct?eligible.Distinct(StringComparer.Ordinal).Count():eligible.Any()?budget.RequestedCount:0;
            if(capacity<budget.RequestedCount)return "INSUFFICIENT_NATIVE_COMPATIBLE_BUDGET: "+branch.Key;
        }
        return "";
    }
    bool Eligible(string id,CompatibilityEligibilityContext context,string category)=>RejectionReason(id,context,category).Length==0;
    public bool IsRelicEligible(string contentId,CompatibilityEligibilityContext context)=>Eligible(contentId,context,"relics");
    public bool IsPotionEligible(string contentId,CompatibilityEligibilityContext context)=>Eligible(contentId,context,"potions");
    public bool IsEventEligible(string contentId,CompatibilityEligibilityContext context)=>Eligible(contentId,context,"events");
    public bool IsRoomEligible(string type,CompatibilityEligibilityContext context)=>Eligible(type,context,"rooms");
    public IReadOnlyList<T> FilterNativeCandidates<T>(IEnumerable<T> nativeCandidates,Func<T,string> identify,string category,CompatibilityEligibilityContext context)
    {
        // Enumerate only the caller's native candidates, preserve order and duplicates.
        // Classification never supplies new candidates, even for native-safe content.
        return nativeCandidates.Where(item=>Eligible(identify(item),context,category)).ToArray();
    }
}
