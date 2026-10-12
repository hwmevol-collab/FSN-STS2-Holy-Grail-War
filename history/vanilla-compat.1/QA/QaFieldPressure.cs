using BaseLib.Patches.Content;
using MegaCrit.Sts2.Core.MonsterMoves.Intents;
using MegaCrit.Sts2.Core.MonsterMoves.MonsterMoveStateMachine;
using MegaCrit.Sts2.Core.Rooms;
namespace RinArcherCore;
public sealed class QaFieldPressure:EncounterModel,ICustomModel
{
    public const string EncounterId="QA_FIELD_PRESSURE";
    public QaFieldPressure(){CustomContentDictionary.RegisterType(GetType());}
    public override RoomType RoomType=>RoomType.Monster;
    public override bool IsDebugEncounter=>true;
    public override bool ShouldGiveRewards=>false;
    public override IEnumerable<MonsterModel> AllPossibleMonsters=>[ModelDb.Monster<QaFieldMaster>(),ModelDb.Monster<QaFieldServant>()];
    protected override IReadOnlyList<(MonsterModel,string?)> GenerateMonsters()=>[(ModelDb.Monster<QaFieldMaster>().ToMutable(),null),(ModelDb.Monster<QaFieldServant>().ToMutable(),null)];
}
public sealed class QaFieldMaster:GeometricBody
{
    public override int MinInitialHp=>42;public override int MaxInitialHp=>42;
    public override MegaCrit.Sts2.Core.Nodes.Combat.NCreatureVisuals? CreateCustomVisuals()=>PlaceholderVisuals.Creature("战场验收御主",new Color("6b617f"));
}
public sealed class QaFieldServant:GeometricBody
{
    public override int MinInitialHp=>56;public override int MaxInitialHp=>56;
    public override MegaCrit.Sts2.Core.Nodes.Combat.NCreatureVisuals? CreateCustomVisuals()=>PlaceholderVisuals.Creature("战场验收从者",new Color("88734a"));
    protected override MonsterMoveStateMachine GenerateMoveStateMachine()
    {
        ContractRuntime? D()=>ContractRuntime.For(Creature.CombatState!.Players[0]);
        Task Move(IReadOnlyList<Creature> _)=>D()!.Enemy!.Execute(new ThrowingPlayerChoiceContext());
        decimal Amount(int n)=>n+(D() is {} d?FieldStatus.Pressure(d,Creature,true):3);
        var a=new MoveState("FIELD_FRONT_12",Move,new SingleAttackIntent(()=>Amount(9)));
        var b=new MoveState("FIELD_BOTH_8",Move,new SingleAttackIntent(()=>Amount(5)));
        var c=new MoveState("FIELD_MASTER_14",Move,new SingleAttackIntent(()=>Amount(11)));
        var e=new MoveState("FIELD_BLOCK_10_SWITCH",Move,new SleepIntent());a.FollowUpState=b;b.FollowUpState=c;c.FollowUpState=e;e.FollowUpState=a;return new([a,b,c,e],a);
    }
}
