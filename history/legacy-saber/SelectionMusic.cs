using MegaCrit.Sts2.Core.Nodes;
using MegaCrit.Sts2.Core.Nodes.Audio;
using MegaCrit.Sts2.Core.Nodes.Screens.CharacterSelect;
using MegaCrit.Sts2.Core.Saves;
using MegaCrit.Sts2.Core.TestSupport;
namespace FateStayNight;

public static class SelectionMusic
{
    static AudioStreamPlayer? Player;
    static Godot.Timer? Clock;
    static float Gain,Target;
    static bool RestoreMenu;
    public static bool Playing=>Player!=null&&GodotObject.IsInstanceValid(Player)&&Player.Playing;
    public static float VolumeDb=>Playing?Player!.VolumeDb:-80;
    public static double Position=>Playing?Player!.GetPlaybackPosition():0;
    public static double Length=>Player?.Stream?.GetLength()??0;
    public static void Select(NCharacterSelectScreen screen,bool fsn){
        if(TestMode.IsOn)return;
        if(!fsn){Stop(true);return;}
        string path=System.IO.Path.Combine(Art.Directory,"MenuBgm.ogg");if(!System.IO.File.Exists(path))return;
        if(Player==null||!GodotObject.IsInstanceValid(Player)){
            var stream=AudioStreamOggVorbis.LoadFromFile(path);if(stream==null)return;stream.Loop=true;
            Player=new AudioStreamPlayer{Name="FSNSelectionBgm",Stream=stream,VolumeDb=-80};NGame.Instance!.AddChild(Player);
            Clock=new Godot.Timer{WaitTime=0.04,Autostart=true};Player.AddChild(Clock);Clock.Timeout+=Tick;
        }
        RestoreMenu=false;Target=1;Clock?.Start();
        if(!Player.Playing){Gain=0;NAudioManager.Instance?.StopMusic();Player.Play();GD.Print("[FSN audio] selection started; loop=true; native BGM stopped");}
    }
    static void Tick(){
        if(Player==null||!GodotObject.IsInstanceValid(Player))return;
        Gain=Mathf.MoveToward(Gain,Target,0.08f);
        var settings=SaveManager.Instance.SettingsSave;
        float linear=Gain*Mathf.Pow(settings.VolumeMaster,2)*Mathf.Pow(settings.VolumeBgm,2);
        if(SaveManager.Instance.PrefsSave.MuteInBackground&&!DisplayServer.WindowIsFocused())linear=0;
        Player.VolumeDb=linear>0?Mathf.LinearToDb(linear):-80;
        if(Target==0&&Gain==0){Player.Stop();Clock?.Stop();if(RestoreMenu){RestoreMenu=false;NAudioManager.Instance?.PlayMusic("event:/music/menu_update");}GD.Print("[FSN audio] selection stopped");}
    }
    public static void Stop(bool restoreMenu,bool immediately=false){
        if(!Playing)return;
        RestoreMenu=restoreMenu;Target=0;
        if(immediately){Gain=0;Player!.Stop();Clock?.Stop();RestoreMenu=false;GD.Print("[FSN audio] cleared before native music transition");}
    }
    public static void SeekForTest(double seconds){if(Playing)Player!.Seek((float)seconds);}
    public static void ResumeClock(){if(Clock!=null&&GodotObject.IsInstanceValid(Clock))Clock.Start();}
}
[HarmonyPatch(typeof(NCharacterSelectScreen),nameof(NCharacterSelectScreen.OnSubmenuClosed))]
public static class SelectionMusicClosePatch{static void Prefix()=>SelectionMusic.Stop(true);}
[HarmonyPatch(typeof(NCharacterSelectScreen),nameof(NCharacterSelectScreen.SelectCharacter))]
public static class SelectionMusicClockPatch{static void Postfix()=>SelectionMusic.ResumeClock();}
[HarmonyPatch(typeof(NGame),nameof(NGame.StartNewSingleplayerRun))]
public static class SelectionMusicRunPatch{static void Prefix()=>SelectionMusic.Stop(false);}
[HarmonyPatch(typeof(NAudioManager),nameof(NAudioManager.PlayMusic))]
public static class SelectionMusicNativePatch{static void Prefix()=>SelectionMusic.Stop(false,true);}
