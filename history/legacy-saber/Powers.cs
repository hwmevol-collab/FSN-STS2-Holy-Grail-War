namespace FateStayNight;
public abstract class FatePower : CustomPowerModel
{
    public override PowerType Type=>PowerType.Buff;
    public override PowerStackType StackType=>PowerStackType.Counter;
    protected abstract string NameText{get;}
    protected virtual string RulesText=>NameText;
    public override string CustomPackedIconPath=>ModelDb.Power<BufferPower>().PackedIconPath;
    public override List<(string,string)> Localization=>[("title",NameText),("description",RulesText)];
}
public sealed class ReinforcePower : FatePower
{
    protected override string NameText=>"强化魔术";
    public override async Task AfterSideTurnEnd(PlayerChoiceContext ctx,CombatSide side,IEnumerable<Creature> participants){if(side==CombatSide.Player)await PowerCmd.Remove(this);}
}
public sealed class AnalysisPower : FatePower
{
    protected override string NameText=>"解明构造";
    public int Used;
    public override Task BeforeHandDraw(Player player,PlayerChoiceContext ctx,ICombatState state){if(player==Owner.Player)Used=0;return Task.CompletedTask;}
}
public sealed class TemporaryArtifact : FatePower
{
    protected override string NameText=>"临时人工制品";
    public override bool TryModifyPowerAmountReceived(PowerModel canonicalPower,Creature target,decimal amount,Creature? applier,out decimal modifiedAmount){
        modifiedAmount=amount;
        if(target!=Owner||canonicalPower.GetTypeForAmount(amount)!=PowerType.Debuff||!canonicalPower.IsVisible)return false;
        modifiedAmount=0;return true;
    }
    public override async Task AfterModifyingPowerAmountReceived(PowerModel power)=>await PowerCmd.Decrement(this);
    public override async Task BeforeHandDraw(Player player,PlayerChoiceContext ctx,ICombatState state){if(player==Owner.Player)await PowerCmd.Remove(this);}
}
public sealed class PrecautionBuffer : FatePower
{
    protected override string NameText=>"预防措施";
    public override PowerInstanceType InstanceType=>PowerInstanceType.Instanced;
    public CardModel? Card;
    public override decimal ModifyHpLostAfterOstyLate(Creature target,decimal amount,ValueProp props,Creature? dealer,CardModel? source)=>target==Owner?0:amount;
    public override async Task AfterModifyingHpLostAfterOsty()=>await PowerCmd.Remove(this);
    public override async Task BeforeHandDraw(Player player,PlayerChoiceContext ctx,ICombatState state){
        if(player!=Owner.Player)return;
        await PowerCmd.Remove(this);
        if(Card?.Pile?.IsCombatPile==true)await CardPileCmd.RemoveFromCombat(Card);
    }
}
public sealed class SurvivalTicket
{
    public int LuckyPercent;
}
public sealed class SurvivalPower : FatePower
{
    protected override string NameText=>"保命";
    List<SurvivalTicket> tickets=[];
    SurvivalTicket? pending;
    bool immune;
    Creature? creditor;
    decimal debt,damage;
    protected override void DeepCloneFields(){base.DeepCloneFields();tickets=[];pending=null;immune=false;creditor=null;debt=damage=0;}
    public override Task AfterPowerAmountChanged(PlayerChoiceContext ctx,PowerModel power,decimal amount,Creature? applier,CardModel? source){
        if(power==this&&amount>0&&source!=null)tickets.Add(new SurvivalTicket{LuckyPercent=source is LuckyProtection?10:0});return Task.CompletedTask;
    }
    public void SetLastLucky(int percent){if(tickets.LastOrDefault() is {} last)last.LuckyPercent=percent;}
    public override Task BeforeDamageReceived(PlayerChoiceContext ctx,Creature target,decimal amount,ValueProp props,Creature? dealer,CardModel? source){if(target==Owner)damage=amount;return Task.CompletedTask;}
    public override decimal ModifyDamageCap(Creature? target,ValueProp props,Creature? dealer,CardModel? source)=>target==Owner&&immune?0:decimal.MaxValue;
    public override decimal ModifyHpLostAfterOstyLate(Creature target,decimal amount,ValueProp props,Creature? dealer,CardModel? source){
        if(target!=Owner)return amount;
        if(immune)return 0;
        int temporary=Duo.For(Owner.Player)?.Current.TemporaryHp??0;
        if(amount<Owner.CurrentHp+temporary)return amount;
        pending=tickets.FirstOrDefault(t=>t.LuckyPercent==0||Duo.For(Owner.Player)?.BetweenTurns==true||Owner.CombatState?.CurrentSide==CombatSide.Enemy);
        if(pending==null)return amount;
        if(pending.LuckyPercent==0){immune=true;creditor=dealer?.IsEnemy==true?dealer:null;debt=damage;}
        return 0;
    }
    public override async Task AfterModifyingHpLostAfterOsty(){
        if(pending==null)return;
        var ticket=pending;pending=null;tickets.Remove(ticket);
        if(ticket.LuckyPercent>0)await CreatureCmd.SetCurrentHp(Owner,Math.Max(1,(int)Math.Ceiling(Owner.MaxHp*ticket.LuckyPercent/100m)));
        // Keep the model alive during immunity even after its last stored charge is spent.
        await PowerCmd.ModifyAmount(new ThrowingPlayerChoiceContext(),this,tickets.Count+(immune?1:0)-Amount,Owner,null);
    }
    public override async Task BeforeHandDraw(Player player,PlayerChoiceContext ctx,ICombatState state){
        if(player!=Owner.Player)return;
        tickets.RemoveAll(t=>t.LuckyPercent>0);
        if(immune){immune=false;if(creditor?.IsAlive==true&&debt>0)await PowerCmd.Apply<VigorPower>(ctx,creditor,debt,Owner,null);creditor=null;debt=0;}
        if(tickets.Count==0)await PowerCmd.Remove(this);
        else await PowerCmd.ModifyAmount(ctx,this,tickets.Count-Amount,Owner,null);
    }
}
