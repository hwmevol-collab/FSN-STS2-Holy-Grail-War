using MegaCrit.Sts2.Core.Nodes;
using MegaCrit.Sts2.Core.Nodes.Audio;
using MegaCrit.Sts2.Core.Nodes.Screens.CharacterSelect;
using MegaCrit.Sts2.Core.Saves;
namespace RinArcherCore;

// Selection audio travels with the MOD; missing or corrupt tracks retain native BGM.
public sealed partial class ContractSelectMusic:Node
{
    static ContractSelectMusic? current;
    AudioStreamPlayer? player;NCharacterSelectScreen? screen;
    bool wanted;float blend;string loadedPath="";
    public static bool NativeVolumeWrite;
    public static bool Suppressing=>current is {blend:>0};
    public static float Mix=>current?.blend??0;
    public static bool Playing=>current?.player?.Playing==true;
    public static string Source=>current?.loadedPath??"";
    public static void Select(NCharacterSelectScreen s,bool contract)
    {
        if(current==null||!GodotObject.IsInstanceValid(current))
        {
            current=new ContractSelectMusic{ProcessMode=ProcessModeEnum.Always};NGame.Instance!.AddChild(current);
            // This mod uses the game's runtime assemblies without Godot source generators.
            // Connect native signals explicitly, as the existing presentation nodes do.
            current.GetTree().ProcessFrame+=current.AudioFrame;
            current.TreeExiting+=current.Release;
        }
        current.screen=s;current.wanted=contract;
        if(!contract||current.player!=null)return;
        string path=Path.Combine(ContentPaths.Root,"Presentation","Audio","this-illusion-remix.ogg");
        if(!File.Exists(path))return;
        try
        {
            var stream=AudioStreamOggVorbis.LoadFromFile(path);if(stream==null)return;
            stream.Loop=true;current.player=new AudioStreamPlayer{Name="ContractSelectionBgm",Stream=stream,VolumeDb=-80};
            current.AddChild(current.player);current.loadedPath=path;current.player.Play();
        }
        catch(Exception e){GD.Print("[FSN] Bundled selection music fallback: "+e.GetType().Name);}
    }
    void AudioFrame()=>UpdateAudio(GetProcessDeltaTime());
    void UpdateAudio(double delta)
    {
        bool visible=wanted&&screen!=null&&GodotObject.IsInstanceValid(screen)&&screen.IsVisibleInTree();
        if(player==null)return;
        float target=visible?1:0;
        blend=Mathf.MoveToward(blend,target,(float)delta/(visible?.35f:.18f));
        var settings=SaveManager.Instance.SettingsSave;
        float gain=Math.Clamp(settings.VolumeMaster*settings.VolumeBgm*blend,0,1);
        player.VolumeDb=gain>0?Mathf.LinearToDb(gain):-80;
        WriteNative(settings.VolumeBgm*(1-blend));
        if(!visible&&blend==0){player.Stop();player.QueueFree();player=null;loadedPath="";}
    }
    static void WriteNative(float value)
    {try{NativeVolumeWrite=true;NAudioManager.Instance?.SetBgmVol(value);}finally{NativeVolumeWrite=false;}}
    void Release()
    {GetTree().ProcessFrame-=AudioFrame;player?.Stop();WriteNative(SaveManager.Instance.SettingsSave.VolumeBgm);current=null;}
}
[HarmonyPatch(typeof(NCharacterSelectScreen),nameof(NCharacterSelectScreen.SelectCharacter))]
public static class ContractSelectionMusicLifecycle
{static void Postfix(NCharacterSelectScreen __instance,CharacterModel characterModel)=>ContractSelectMusic.Select(__instance,characterModel is RinContractCharacter);}
[HarmonyPatch(typeof(NAudioManager),nameof(NAudioManager.SetBgmVol))]
public static class ContractSelectionMusicVolume
{
    static void Prefix(ref float __0)
    {if(!ContractSelectMusic.NativeVolumeWrite&&ContractSelectMusic.Suppressing)__0*=1-ContractSelectMusic.Mix;}
}
