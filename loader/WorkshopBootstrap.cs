using System.Reflection;
using System.Reflection.Metadata;
using System.Reflection.PortableExecutable;
using System.Runtime.Loader;
using System.Security.Cryptography;
using System.Text.Json;
using MegaCrit.Sts2.Core.Debug;
using MegaCrit.Sts2.Core.Modding;
using Godot;
namespace RinArcherCore.Loader;

public sealed record GameIdentity(string GameVersion,string Commit,string AssemblySha256,string AssemblyMvid);
public sealed record ContentVariant(GameIdentity Game,string Directory,string PayloadSha256);
public sealed record VariantManifest(int Schema,List<ContentVariant> Variants);

// Initializer forwarding and native assembly registration follow STS2-Template (MIT).
// FSN additionally requires exact reviewed identities; no minimum-version fallback.
[ModInitializer(nameof(Initialize))]
public static class WorkshopBootstrap
{
    static readonly GameIdentity[] Known=[
        new("v0.107.1","59260271","A1F9E653F1E28E4076558FEE1E60D218619CB7E057B887C6417F62C62C6D7A52","97f10687-c306-4798-ab75-8b9f23f34dfb"),
        new("v0.111.0","41cef1ea","0861BFA1DF347538D932F22D580E75420F08082792EB914E53B4882764ACDBE9","73b63ee0-6c0a-47bb-b0d1-b21f6d94222e")];
    public static ContentVariant Select(VariantManifest manifest,GameIdentity actual)
    {
        if(manifest.Schema!=1||!Known.Contains(actual))throw new InvalidDataException("FSN_GAME_BUILD_NOT_VERIFIED: "+actual);
        return manifest.Variants.SingleOrDefault(v=>v.Game==actual)??throw new InvalidDataException("FSN_GAME_VARIANT_UNAVAILABLE: "+actual.GameVersion);
    }
    public static string PayloadPath(string root,ContentVariant variant)
    {
        var path=Path.GetFullPath(Path.Combine(root,variant.Directory,"RinArcherCore.dll"));
        var prefix=Path.GetFullPath(Path.Combine(root,"lib"))+Path.DirectorySeparatorChar;
        if(!path.StartsWith(prefix,OperatingSystem.IsWindows()?StringComparison.OrdinalIgnoreCase:StringComparison.Ordinal))throw new InvalidDataException("FSN_VARIANT_PATH_OUTSIDE_LIB");
        return path;
    }
    // Same policy as the content compatibility gate: never resolve Location against cwd.
    static string ResolveGameAssemblyPath(string location,string dataDir)
    {
        if(Path.IsPathFullyQualified(location)&&File.Exists(location))return location;
        if(string.IsNullOrWhiteSpace(dataDir)||!Path.IsPathFullyQualified(dataDir))throw new InvalidDataException("FSN_GAME_ASSEMBLY_PATH_UNCONFIRMED: Location="+location);
        return Path.Combine(dataDir,".godot","mono","publish","arm64","sts2.dll");
    }
    public static GameIdentity Actual()
    {
        var game=typeof(ModManager).Assembly;
        var paths=AppDomain.CurrentDomain.GetAssemblies().Select(a=>a.GetType("STS2Mobile.Android.AppPaths",false)).FirstOrDefault(t=>t!=null);
        string Property(string name)=>paths?.GetProperty(name,BindingFlags.Public|BindingFlags.Static)?.GetValue(null) as string??"";
        var release=ReleaseInfoManager.Instance.ReleaseInfo;string? version=release?.Version,commit=release?.Commit;
        if(release==null)
        {
            string config=Property("ReleaseInfoPath");if(config.Length==0)config=Path.Combine(Path.GetDirectoryName(OS.GetExecutablePath())!,"release_info.json");
            using var doc=JsonDocument.Parse(File.ReadAllText(config));version=doc.RootElement.GetProperty("version").GetString();commit=doc.RootElement.GetProperty("commit").GetString();
        }
        string rawLocation=game.Location;
        string location=ResolveGameAssemblyPath(rawLocation,Property("DataDir"));
        GD.Print("[RIN_ARCHER_LOADER] GAME_ASSEMBLY_PATH "+JsonSerializer.Serialize(new{rawLocation,resolvedPath=location}));
        using var file=File.OpenRead(location);string hash=Convert.ToHexString(SHA256.HashData(file));file.Position=0;using var pe=new PEReader(file);var m=pe.GetMetadataReader();var mvid=m.GetGuid(m.GetModuleDefinition().Mvid);
        if(!m.IsAssembly||m.GetString(m.GetAssemblyDefinition().Name)!=game.GetName().Name||mvid==Guid.Empty||mvid!=game.ManifestModule.ModuleVersionId)throw new InvalidDataException("FSN_RUNTIME_FILE_IDENTITY_MISMATCH");
        return new(version??"",commit??"",hash,mvid.ToString());
    }
    public static void Initialize()
    {
        string root=Path.GetDirectoryName(typeof(WorkshopBootstrap).Assembly.Location)??throw new InvalidDataException("FSN_LOADER_PATH_UNCONFIRMED");
        var manifest=JsonSerializer.Deserialize<VariantManifest>(File.ReadAllText(Path.Combine(root,"mod-variants.manifest")))??throw new InvalidDataException("FSN_VARIANTS_MANIFEST_INVALID");
        var actual=Actual();var selected=Select(manifest,actual);string path=PayloadPath(root,selected);
        if(Convert.ToHexString(SHA256.HashData(File.ReadAllBytes(path)))!=selected.PayloadSha256)throw new InvalidDataException("FSN_VARIANT_PAYLOAD_HASH_MISMATCH");
        var owner=ModManager.Mods.Single(m=>m.manifest?.id=="RinArcherCore"&&Path.GetFullPath(m.path)==Path.GetFullPath(root));
        Assembly content=(AssemblyLoadContext.GetLoadContext(typeof(WorkshopBootstrap).Assembly)??AssemblyLoadContext.Default).LoadFromAssemblyPath(path);
        var initializers=content.GetTypes().Where(t=>t.GetCustomAttribute<ModInitializerAttribute>()!=null).ToArray();
        if(initializers.Length==0)throw new InvalidDataException("FSN_VARIANT_INITIALIZER_MISSING");
        foreach(var type in initializers){var attribute=type.GetCustomAttribute<ModInitializerAttribute>()!;var method=type.GetMethod(attribute.initializerMethod,BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Static)??throw new MissingMethodException(type.FullName,attribute.initializerMethod);method.Invoke(null,null);}
        GameAssemblyRegistration.Register(owner,content);
        GD.Print("[RIN_ARCHER_LOADER] VERIFIED "+JsonSerializer.Serialize(new{actual,selected.Directory,selected.PayloadSha256}));
    }
}
