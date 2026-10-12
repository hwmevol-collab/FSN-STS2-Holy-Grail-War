namespace RinArcherCore;
// Combat-only ordinary cards. No reward-pool attribute and no run-persistent collection.
public abstract class ProjectedArm(CardType type,int energy):StarterCard(type,TargetType.Self,energy,false)
{
    public abstract string ArmId{get;}
    public abstract IReadOnlyList<string> ArmTags{get;}
    public override string SourceCardId=>ArmId;
    public override string OwnerCharacterId=>"CHAR_ARCHER";
    public override int PrintedManaCost=>1;
    public override string Title=>(Reinforced?"强化 · ":"")+base.Title;
    public bool Reinforced{get;set;}
    public bool CombatFree{get;set;}
    public bool ReinforcedByAllProjection{get;set;}
    public bool TemporaryZeroMana{get;set;}
    public int ManaDiscount{get;set;}
    public int TemporaryManaDiscount{get;set;}
    public int TemporaryDiscountTurn{get;set;}
    public int? TemporaryEnergyOverride{get;set;}
    public string GeneratedBy{get;set;}="";
    public string ExhaustSource{get;set;}="NORMAL_PLAY";
    internal Creature? PreparedTarget;
    public override int ModifiedManaCost=>CombatFree?0:TemporaryZeroMana&&ContractRuntime.For(Owner)?.Turn==TemporaryDiscountTurn?0:Math.Max(0,PrintedManaCost-ManaDiscount-(ContractRuntime.For(Owner)?.Turn==TemporaryDiscountTurn?TemporaryManaDiscount:0));
    public override IEnumerable<CardKeyword> CanonicalKeywords=>[CardKeyword.Exhaust];
    protected string Marker=>Reinforced?"强化 · ":"";
    protected string Costs=>$"\n契约魔力费用：{ModifiedManaCost}。";
    public object Metadata()=>new{instanceId=InstanceId,armId=ArmId,ownerCharacterId=OwnerCharacterId,sourceCardId=SourceCardId,generatedBy=GeneratedBy,reinforced=Reinforced,reinforcedByAllProjection=ReinforcedByAllProjection,tags=ArmTags,printedManaCost=PrintedManaCost,instanceManaDiscount=ManaDiscount,temporaryManaDiscount=TemporaryManaDiscount,temporaryZeroMana=TemporaryZeroMana,temporaryEnergyOverride=TemporaryEnergyOverride};
    public void ExpireTemporary(int turn){if(turn==TemporaryDiscountTurn)return;TemporaryManaDiscount=0;TemporaryZeroMana=false;TemporaryEnergyOverride=null;EnergyCost.EndOfTurnCleanup();}
    protected override void OnUpgrade(){}
}
public sealed class KanshouBakuya():ProjectedArm(CardType.Attack,0)
{
    public override string ArmId=>"ARM_KANSHOU_BAKUYA";
    public override IReadOnlyList<string> ArmTags=>["PROJECTED","WEAPON","MELEE"];
    protected override string NameText=>"干将·莫邪";
    protected override string RulesText=>Marker+(Reinforced?"对前排造成 6 点伤害 2 次。消耗。":"对前排造成 6 点伤害。消耗。")+Costs;
    protected override async Task OnPlay(PlayerChoiceContext ctx,CardPlay play)
    {await PresentationEffects.Play(Runtime,this);await Hit(ctx,6,Reinforced?2:1);}
}
public sealed class RhoAias():ProjectedArm(CardType.Skill,0)
{
    public override string ArmId=>"ARM_RHO_AIAS";
    public override IReadOnlyList<string> ArmTags=>["PROJECTED","DEFENSE"];
    protected override string NameText=>"炽天覆七重圆环";
    protected override string RulesText=>Marker+"弓兵获得 8 点格挡。"+(Reinforced?"\n凛获得 8 点格挡。":"")+"\n消耗。"+Costs;
    protected override async Task OnPlay(PlayerChoiceContext ctx,CardPlay play){await PresentationEffects.Play(Runtime,this);await Block(play,8,Runtime.Archer);if(Reinforced)await Block(play,8,Runtime.Rin);}
}
public sealed class Hrunting():ProjectedArm(CardType.Attack,1)
{
    public override string ArmId=>"ARM_HRUNTING";
    public override IReadOnlyList<string> ArmTags=>["PROJECTED","WEAPON","RANGED"];
    protected override string NameText=>"赤原猎犬";
    protected override string RulesText=>Marker+$"对一个敌人，造成 {(Reinforced?22:15)} 点伤害。消耗。"+Costs;
    protected override async Task OnPlay(PlayerChoiceContext ctx,CardPlay play)
    {
        await PresentationEffects.Play(Runtime,this);
        var target=Runtime.PlayTarget(this)??PreparedTarget;
        if(target==null)target=await AlphaChoice.AskTarget(this);
        if(target==null)throw new InvalidOperationException("Hrunting requires explicit legal target before payment");
        if(target.IsAlive)await Targeting.Damage(ctx,Runtime,ContractTarget.ANY_CONTRACT_MEMBER,Runtime.DamageProfile(this,Reinforced?22:15,1)[0],Runtime.Archer.Creature,this,true,locked:target);
    }
}
public static class Arsenal
{
    public static readonly IReadOnlyList<string> Ids=Array.AsReadOnly(new[]{"ARM_KANSHOU_BAKUYA","ARM_RHO_AIAS","ARM_HRUNTING"});
    public static CardModel Get(string id)=>id switch{
        "ARM_KANSHOU_BAKUYA"=>ModelDb.Card<KanshouBakuya>(),"ARM_RHO_AIAS"=>ModelDb.Card<RhoAias>(),"ARM_HRUNTING"=>ModelDb.Card<Hrunting>(),_=>throw new ArgumentException("Unknown Alpha Arsenal entry: "+id)};
}
