using MegaCrit.Sts2.Core.MonsterMoves.Intents;
using MegaCrit.Sts2.Core.MonsterMoves.MonsterMoveStateMachine;
using MegaCrit.Sts2.Core.Nodes.Combat;
using MegaCrit.Sts2.Core.Rooms;
using BaseLib.Patches.Content;
namespace RinArcherCore;
public sealed class QaPairBasic:EncounterModel,ICustomModel
{
    public const string EncounterId="QA_PAIR_BASIC";
    public QaPairBasic(){CustomContentDictionary.RegisterType(GetType());}
    public override RoomType RoomType=>RoomType.Monster;
    public override bool IsDebugEncounter=>true;
    public override bool ShouldGiveRewards=>false;
    public override IEnumerable<MonsterModel> AllPossibleMonsters=>[ModelDb.Monster<QaMaster>(),ModelDb.Monster<QaServant>()];
    protected override IReadOnlyList<(MonsterModel,string?)> GenerateMonsters()=>[(ModelDb.Monster<QaMaster>().ToMutable(),null),(ModelDb.Monster<QaServant>().ToMutable(),null)];
}
public abstract class GeometricBody:CustomMonsterModel,ILocalizationProvider
{
    public List<(string,string)> Localization=>[("name",GetType().Name=="ArcherBody"?"ARCHER PLACEHOLDER":GetType().Name=="QaMaster"?"QA MASTER":"QA SERVANT")];
    public override bool HasDeathSfx=>false;
    public override bool ShouldShowInCompendium=>false;
    public override IEnumerable<string> AssetPaths=>[];
    public override NCreatureVisuals? CreateCustomVisuals()=>PlaceholderVisuals.Creature(GetType().Name.ToUpperInvariant(),new Color("527087"));
    protected override MonsterMoveStateMachine GenerateMoveStateMachine()
    {
        var wait=new MoveState("WAIT",_=>Task.CompletedTask,new SleepIntent());wait.FollowUpState=wait;return new([wait],wait);
    }
}
public sealed class ArcherBody:GeometricBody
{
    public override int MinInitialHp=>76;public override int MaxInitialHp=>76;
    public override NCreatureVisuals? CreateCustomVisuals()=>PlaceholderVisuals.Creature("ARCHER PLACEHOLDER",new Color("527087"));
}
public sealed class QaMaster:GeometricBody
{
    public const string EnemyId="QA_PAIR_BASIC_MASTER";
    public override int MinInitialHp=>34;public override int MaxInitialHp=>34;
    public override NCreatureVisuals? CreateCustomVisuals()=>PlaceholderVisuals.Creature("QA MASTER",new Color("6b617f"));
}
public sealed class QaServant:GeometricBody
{
    public const string EnemyId="QA_PAIR_BASIC_SERVANT";
    public override int MinInitialHp=>48;public override int MaxInitialHp=>48;
    public override NCreatureVisuals? CreateCustomVisuals()=>PlaceholderVisuals.Creature("QA SERVANT",new Color("88734a"));
    protected override MonsterMoveStateMachine GenerateMoveStateMachine()
    {
        Task Move(IReadOnlyList<Creature> _)=>ContractRuntime.For(Creature.CombatState!.Players[0])!.Enemy!.Execute(new ThrowingPlayerChoiceContext());
        var a=new MoveState("FRONT_10",Move,new SingleAttackIntent(10));
        var b=new MoveState("SWITCH_MASTER_MANA_2_FRONT_6",Move,new SingleAttackIntent(6));
        var c=new MoveState("SWITCH_SERVANT_MASTER_12",Move,new SingleAttackIntent(12));
        var e=new MoveState("BOTH_7",Move,new SingleAttackIntent(7));a.FollowUpState=b;b.FollowUpState=c;c.FollowUpState=e;e.FollowUpState=a;
        return new([a,b,c,e],a);
    }
}
public sealed class QaEnemyContract
{
    readonly ContractRuntime contract;
    public Creature Master{get;}
    public Creature Servant{get;}
    public Creature Active{get;private set;}
    public string ActiveId=>Active==Master?QaMaster.EnemyId:QaServant.EnemyId;
    public int NextStep{get;private set;}=1;
    public int Mana{get;private set;}=2;
    public int MaxMana=>6;
    public string Intent=>NextStep switch{1=>"10 → FRONT",2=>"Switch → Master; +2 Mana; 6 → FRONT",3=>"Switch → Servant; 12 → MASTER",4=>"7 → BOTH",_=>throw new InvalidOperationException()};
    public QaEnemyContract(ContractRuntime d){contract=d;Master=d.Combat.Enemies.Single(c=>c.Monster is QaMaster);Servant=d.Combat.Enemies.Single(c=>c.Monster is QaServant);Active=Servant;}
    public async Task Execute(PlayerChoiceContext ctx)
    {
        if(contract.Finished)return;
        int step=NextStep;
        if(step==2){Active=Master;Mana=Math.Min(6,Mana+2);}
        if(step==3)Active=Servant;
        contract.Log("ENEMY_INTENT",new{step,intent=Intent,mana=Mana,active=ActiveId});
        await Targeting.Damage(ctx,contract,step==3?ContractTarget.MASTER:step==4?ContractTarget.BOTH:ContractTarget.FRONT,step switch{1=>10,2=>6,3=>12,4=>7,_=>0},Active,null);
        NextStep=step%4+1;Targeting.Refresh(contract);
    }
}
