using STS2RitsuLib.RunData;
using System.Text.Json;
using MegaCrit.Sts2.Core.Saves;
using MegaCrit.Sts2.Core.Rooms;
namespace RinArcherCore;
public sealed record PermanentCardState(string CardId,string OwnerCharacterId,int UpgradeLevel,string InstanceId);
public sealed class RunCombatSummary
{
    public string RunSeed{get;set;}="";
    public int Act{get;set;}
    public int RoomIndex{get;set;}
    public int RinHpStart{get;set;}
    public int RinHpEnd{get;set;}
    public int ArcherHpStart{get;set;}
    public int ArcherHpEnd{get;set;}
    public int RinDeckSizeStart{get;set;}
    public int RinDeckSizeEnd{get;set;}
    public int ArcherDeckSizeStart{get;set;}
    public int ArcherDeckSizeEnd{get;set;}
    public List<PermanentCardState> CardsAddedThisRoom{get;set;}=[];
}
public sealed class RunMemberState
{
    public string CharacterId{get;set;}="";
    public int CurrentHp{get;set;}
    public int MaxHp{get;set;}
    public List<PermanentCardState> PermanentDeck{get;set;}=[];
}
// Adapter metadata: native Player/Deck and Ritsu RunPersistent Archer pile stay authoritative.
// Snapshots validate save topology; they never run a second deck engine.
public class ContractRunState
{
    public int Schema{get;set;}=2;
    public string GameplayRevision{get;set;}="";
    public string CardPoolRevision{get;set;}="";
    public string ContractId{get;set;}=ContractRuntime.ContractId;
    public RunMemberState Master{get;set;}=new(){CharacterId="CHAR_RIN",CurrentHp=58,MaxHp=58};
    public RunMemberState Servant{get;set;}=new(){CharacterId="CHAR_ARCHER",CurrentHp=76,MaxHp=76};
    public int ArcherHp{get=>Servant.CurrentHp;set=>Servant.CurrentHp=value;}
    public int ArcherMaxHp{get=>Servant.MaxHp;set=>Servant.MaxHp=value;}
    public int Gold{get;set;}
    public string RunSeed{get;set;}="";
    public int Act{get;set;}
    public int RoomIndex{get;set;}
    public string RoomIdentity{get;set;}="";
    public float RinRewardRarityState{get;set;}=-0.05f;
    public float ArcherRewardRarityState{get;set;}=-0.05f;
    public int NextRewardIndex{get;set;}
    public int NextPermanentInstance{get;set;}
    public int CommandSpellCount{get;set;}=3;
    public bool CommandSpellGameplayEnabled{get;set;}=false;
    public Dictionary<string,bool> RunFlags{get;set;}=[];
    public List<DualRewardState> DualRewards{get;set;}=[];
    public List<ContractBossRewardState> BossRewards{get;set;}=[];
    public int NextBossRewardIndex{get;set;}
    public Dictionary<string,string> CompletedNativeEvents{get;set;}=[];
    public Dictionary<string,string> NativeEventDescriptions{get;set;}=[];
    public RoomRewardState? RoomRewards{get;set;}
    public string SavePhase{get;set;}="RUN_START";
    public RunCombatSummary? CombatSummary{get;set;}
    public List<CampfireState> Campfires{get;set;}=[];
    public List<ShopState> Shops{get;set;}=[];
    public EconomyMetrics Economy{get;set;}=new();
    public CompatibilityRunState Compatibility{get;set;}=new();
    public List<CompatibleTreasureState> CompatibleTreasures{get;set;}=[];
    public DualRewardPhase DualRewardState=>DualRewards.LastOrDefault()?.Phase??DualRewardPhase.NONE;
}
// Retain the original slot/type for the accepted A save regression and additive compatibility.
public sealed class ContractRunData:ContractRunState;
public static class ContractSave
{
    static readonly System.Threading.SemaphoreSlim SaveGate=new(1,1);
    public static PlayerRunSavedData<ContractRunData> Slot=null!;
    public static void Register()=>Slot=RunSavedDataStore.For("RinArcherCore").RegisterPerPlayer<ContractRunData>("contract_alpha");
    public static ContractRunData Get(Player p)=>Slot.Get((RunState)p.RunState,p.NetId);
    public static void InitializeGameplay(Player p)
    {var state=Get(p);state.Schema=3;state.GameplayRevision=GameplayCatalog.GameplayRevision;state.CardPoolRevision=GameplayCatalog.CardPoolRevision;Slot.Set((RunState)p.RunState,p.NetId,state);}
    public static void ValidateGameplay(Player p)
    {
        var s=Get(p);
        if(s.Schema!=3||s.GameplayRevision!=GameplayCatalog.GameplayRevision||s.CardPoolRevision!=GameplayCatalog.CardPoolRevision)
            throw new InvalidDataException(FsnLoc.Text("UI_CBF27B62B2F7")+s.GameplayRevision+" / "+s.CardPoolRevision);
    }
    public static CardPile Deck(Player p,string owner)=>owner switch{"CHAR_RIN"=>p.Deck,"CHAR_ARCHER"=>CardPile.Get(CardBanks.ArcherDeck.PileType,p)!,_=>throw new ArgumentException("Unknown permanent owner")};
    public static string RoomKey(Player p)=>$"{p.RunState.CurrentActIndex}:{p.RunState.CurrentMapCoord}:{p.RunState.TotalFloor}";
    public static void EnsureDecks(Player p)
    {
        var state=Get(p);var deck=Deck(p,"CHAR_ARCHER");
        if(deck.IsEmpty&&!state.RunFlags.GetValueOrDefault("ARCHER_DECK_INITIALIZED"))
        {foreach(var definition in StarterDefinitions.Archer)deck.AddInternal(p.RunState.CreateCard(definition,p),silent:true);state.RunFlags["ARCHER_DECK_INITIALIZED"]=true;}
        foreach(var owner in new[]{"CHAR_RIN","CHAR_ARCHER"})
        {
            var cards=Deck(p,owner).Cards;
            for(int i=0;i<cards.Count;i++)
            {
                var card=cards[i];
                if(card is StarterCard c)
                {
                    if(c is ProjectedArm||c.OwnerCharacterId!=owner)throw new InvalidOperationException("Permanent deck owner/type violation");
                    if(c.InstanceId.Length==0)c.InstanceId=$"permanent:{owner}:{++state.NextPermanentInstance}";
                }
                else NativePermanentCards.Restore(p,owner,card,i);
            }
        }
        Slot.Set((RunState)p.RunState,p.NetId,state);
    }
    static List<PermanentCardState> Snapshot(CardPile deck,string owner)=>deck.Cards.Select(c=>c is not ProjectedArm&&NativePermanentCards.Owner(c)==owner
        ?new PermanentCardState(NativePermanentCards.Id(c),owner,c.CurrentUpgradeLevel,NativePermanentCards.Instance(c)):throw new InvalidOperationException("Persistent owner invalid")).ToList();
    public static void Sync(Player p,bool validateLoaded=false)
    {
        var state=Get(p);var rin=Snapshot(Deck(p,"CHAR_RIN"),"CHAR_RIN");var archer=Snapshot(Deck(p,"CHAR_ARCHER"),"CHAR_ARCHER");
        if(validateLoaded&&state.Master.PermanentDeck.Count>0&&(!state.Master.PermanentDeck.SequenceEqual(rin)||!state.Servant.PermanentDeck.SequenceEqual(archer)))
            throw new InvalidOperationException("Loaded permanent deck identity/owner/upgrade differs from saved native piles");
        if(rin.Concat(archer).Select(c=>c.InstanceId).Distinct().Count()!=rin.Count+archer.Count)throw new InvalidOperationException("Duplicate permanent instance identity");
        state.Master.CurrentHp=p.Creature.CurrentHp;state.Master.MaxHp=p.Creature.MaxHp;state.Master.PermanentDeck=rin;state.Servant.PermanentDeck=archer;
        state.Gold=p.Gold;state.RunSeed=p.RunState.Rng.StringSeed;state.Act=p.RunState.CurrentActIndex;state.RoomIndex=p.RunState.TotalFloor;state.RoomIdentity=RoomKey(p);
        Slot.Set((RunState)p.RunState,p.NetId,state);
    }
    public static void Store(ContractRuntime d)
    {
        var state=Get(d.Player);state.ArcherHp=d.Archer.Creature.CurrentHp;state.ArcherMaxHp=d.Archer.Creature.MaxHp;
        Slot.Set((RunState)d.Player.RunState,d.Player.NetId,state);
    }
    public static async Task Checkpoint(Player p,string phase)
    {
        await SaveGate.WaitAsync();
        try{await WriteCheckpoint(p,phase);}finally{SaveGate.Release();}
    }
    static async Task WriteCheckpoint(Player p,string phase)
    {
        Sync(p);var s=Get(p);s.SavePhase=phase;Slot.Set((RunState)p.RunState,p.NetId,s);
        if(RunManager.Instance.ShouldSave)
        {
            var room=p.RunState.CurrentRoom as CombatRoom;
            if(room!=null&&!room.IsPreFinished)throw new InvalidOperationException("D1 refuses an unsafe mid-combat save");
            int expectedHp=p.Creature.CurrentHp,expectedGold=p.Gold,expectedArcherHp=s.ArcherHp;string expectedSeed=p.RunState.Rng.StringSeed;
            var boundary=p.RunState.CurrentRoom;
            await SaveManager.Instance.SaveRun(boundary is {IsPreFinished:true}?boundary:room,saveProgress:false);
            // SaveManager logs/catches write errors. Confirm the native file and sidecar before
            // accepting the checkpoint, so an error cannot silently advance a reward phase.
            var saved=SaveManager.Instance.LoadRunSave();var native=saved.SaveData?.Players.SingleOrDefault(x=>x.NetId==p.NetId);
            if(!saved.Success||native==null||saved.SaveData!.SerializableRng.Seed!=expectedSeed||native.CurrentHp!=expectedHp||native.Gold!=expectedGold)
                throw new InvalidOperationException("D1_NATIVE_SAVE_READBACK_FAILED");
            var path=ProjectSettings.GlobalizePath(SaveManager.Instance.GetProfileScopedPath("saves/current_run.save"));
            using var json=JsonDocument.Parse(System.IO.File.ReadAllText(path));
            var data=json.RootElement.GetProperty("_ritsulib").GetProperty("run_saved_data").GetProperty("RinArcherCore").GetProperty("contract_alpha").GetProperty("players").GetProperty(p.NetId.ToString());
            if(data.GetProperty("SavePhase").GetString()!=phase||data.GetProperty("ArcherHp").GetInt32()!=expectedArcherHp)
                throw new InvalidOperationException("D1_SIDECAR_SAVE_READBACK_FAILED");
        }
        Log(p,"RUN_STATE_SAVED",new{phase,nativeDiskReadback=RunManager.Instance.ShouldSave});
    }
    public static void Log(Player p,string ev,object? detail=null)
    {
        var text=JsonSerializer.Serialize(new{ev,runSeed=p.RunState.Rng.StringSeed,act=p.RunState.CurrentActIndex,roomIndex=p.RunState.TotalFloor,detail});GD.Print("[RIN_ARCHER_RUN] "+text);
        if(!MegaCrit.Sts2.Core.TestSupport.TestMode.IsOn)DiagnosticLog.Write("rin-archer-run-telemetry.jsonl",text);
    }
}
