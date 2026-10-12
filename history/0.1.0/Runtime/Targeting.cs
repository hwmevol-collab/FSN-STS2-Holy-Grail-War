namespace RinArcherCore;
public enum ContractTarget{FRONT,MASTER,SERVANT,BOTH,LOCKED,ANY_CONTRACT_MEMBER}
public static class Targeting
{
    public static IReadOnlyList<Creature> Resolve(ContractRuntime d,ContractTarget type,bool enemy=false,Creature? locked=null)
    {
        var master=enemy?d.Enemy!.Master:d.Rin.Creature;var servant=enemy?d.Enemy!.Servant:d.Archer.Creature;
        return type switch{
            ContractTarget.FRONT=>[enemy?d.Enemy!.Active:d.Active.Creature],ContractTarget.MASTER=>[master],ContractTarget.SERVANT=>[servant],ContractTarget.BOTH=>[master,servant],
            ContractTarget.LOCKED when locked==master||locked==servant=>[locked!],
            _=>throw new NotSupportedException("Target requires explicit future selection: "+type)};
    }
    public static async Task Damage(PlayerChoiceContext ctx,ContractRuntime d,ContractTarget type,int amount,Creature source,CardModel? card,bool enemy=false,int hit=1)
    {
        var targets=Resolve(d,type,enemy);d.Log("TARGET_RESOLVE",new{target=type.ToString(),enemy,hit,targets=targets.Select(c=>c.CombatId)});
        foreach(var target in targets)
        {
            int hp=target.CurrentHp,block=target.Block;d.Log("BEFORE_DAMAGE",new{target=target.CombatId,damage=amount,hit,card=(card as StarterCard)?.SourceCardId,cardOwner=(card as StarterCard)?.OwnerCharacterId});
            await CreatureCmd.Damage(ctx,target,amount,ValueProp.Move,source,card);
            d.Log("AFTER_DAMAGE",new{target=target.CombatId,damage=hp-target.CurrentHp,block=block-target.Block,hp=target.CurrentHp,hit});
        }
        await d.CheckLethal(ctx);d.Log("LETHAL_CHECK");
    }
    public static Task EnemyDamage(PlayerChoiceContext ctx,ContractRuntime d,ContractTarget type,int amount,Creature source,CardModel card,int hit=1)=>Damage(ctx,d,type,amount,source,card,true,hit);
    public static void Refresh(ContractRuntime d)=>d.Log("TARGETING_ACTIVE",new{player=d.Active.CharacterId,enemy=d.Enemy?.ActiveId});
}
