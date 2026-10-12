using System.Runtime.CompilerServices;
using System.Text.Json;
using MegaCrit.Sts2.Core.Hooks;
using MegaCrit.Sts2.Core.Nodes.Combat;
using MegaCrit.Sts2.Core.Nodes.Cards;
using MegaCrit.Sts2.Core.Nodes.Relics;
namespace FateStayNight;

public sealed class Fighter
{
    public int Hp,MaxHp,TemporaryHp,Turns,TurnNumber=1;
    public bool Entered;
    public int LastBaseDrawTurn=-1;
    public readonly CardPile Deck=new(PileType.Deck);
    public readonly Dictionary<PileType,CardPile> Piles=Enum.GetValues<PileType>().Where(t=>t is PileType.Hand or PileType.Draw or PileType.Discard or PileType.Exhaust or PileType.Play).ToDictionary(t=>t,t=>new CardPile(t));
    public readonly List<PowerModel> Powers=[];
    public readonly List<RelicModel> Relics=[];
    public readonly List<SerializableCard> OpeningDeck=[];
    public int Block;
}
public sealed class SaberSave
{
    public int Hp{get;set;}=50;public int MaxHp{get;set;}=50;
    public List<SerializableCard> Cards{get;set;}=[];
    public List<SerializableRelic> Relics{get;set;}=[];
}
public sealed class Duo
{
    static readonly ConditionalWeakTable<Player,Duo> States=new();
    public static readonly Dictionary<CardModel,(Duo duo,Fighter fighter)> CardOwners=new(ReferenceEqualityComparer.Instance);
    public static readonly JsonSerializerOptions JsonOptions=new(){IncludeFields=true};
    public Player Player{get;}
    public CommandSeals Seal{get;}
    public Fighter Master{get;}=new();public Fighter Saber{get;}=new();
    public bool IsSaber{get;private set;}
    public Fighter Current=>IsSaber?Saber:Master;
    public Fighter Other=>IsSaber?Master:Saber;
    public bool ContractActive=>!Seal.Released;
    public CombatState? Combat{get;private set;}
    public bool Switching{get;private set;}
    public bool Escaping{get;private set;}
    public bool BetweenTurns;
    public int ActualPlayerTurn{get;private set;}
    readonly Dictionary<CardModel,int> pendingSwitches=[];
    public void RequestSwitch(CardModel card){pendingSwitches[card]=pendingSwitches.GetValueOrDefault(card)+1;}
    public async Task CompleteCard(CardModel card,PlayerChoiceContext ctx){if(!pendingSwitches.Remove(card,out var count))return;for(int i=0;i<count;i++)await Switch(ctx);}
    public static Duo? For(Player? p){
        if(p?.Character is not EmiyaShirou)return null;
        if(States.TryGetValue(p,out var state))return state;
        if(p.GetRelic<CommandSeals>() is not {} seal)return null;
        state=new Duo(p,seal);States.Add(p,state);return state;
    }
    Duo(Player p,CommandSeals seal){
        Player=p;Seal=seal;Master.Hp=p.Creature.CurrentHp;Master.MaxHp=p.Creature.MaxHp;
        if(seal.SaberData.Length>0){
            var s=JsonSerializer.Deserialize<SaberSave>(seal.SaberData,JsonOptions)!;Saber.Hp=s.Hp;Saber.MaxHp=s.MaxHp;
            foreach(var save in s.Cards)AddPermanentSaber(CardModel.FromSerializable(save));
            foreach(var save in s.Relics){var relic=RelicModel.FromSerializable(save);RegisterSaberRelic(relic);}
        }else if(!seal.Released){
            Saber.Hp=Saber.MaxHp=50;
            for(int i=0;i<4;i++){AddPermanentSaber(ModelDb.Card<SwiftStrike>().ToMutable());AddPermanentSaber(ModelDb.Card<SwordGuard>().ToMutable());}
            AddPermanentSaber(ModelDb.Card<Coordination>().ToMutable());
            foreach(var relic in new RelicModel[]{ModelDb.Relic<WindBarrier>().ToMutable(),ModelDb.Relic<KingsArmor>().ToMutable()})RegisterSaberRelic(relic);
            Save();
        }
    }
    void RegisterSaberRelic(RelicModel relic){Player.AddRelicInternal(relic,silent:true);((List<RelicModel>)AccessTools.Field(typeof(Player),"_relics").GetValue(Player)!).Remove(relic);Saber.Relics.Add(relic);}
    public void AddPermanentSaber(CardModel c){Player.RunState.AddCard(c,Player);Saber.Deck.AddInternal(c,silent:true);CardOwners[c]=(this,Saber);}
    public void Save(){
        if(Combat!=null){Current.Hp=Player.Creature.CurrentHp;Current.MaxHp=Player.Creature.MaxHp;}
        var deck=IsSaber?Player.Deck:Saber.Deck;
        var relics=IsSaber?Player.Relics.Where(r=>r!=Seal):Saber.Relics;
        Seal.SaberData=JsonSerializer.Serialize(new SaberSave{Hp=Saber.Hp,MaxHp=Saber.MaxHp,Cards=deck.Cards.Select(c=>c.ToSerializable()).ToList(),Relics=relics.Select(r=>r.ToSerializable()).ToList()},JsonOptions);
    }
    public void Start(CombatState combat){
        Combat=combat;IsSaber=false;Seal.UsedThisCombat=false;Seal.EscapeRewardsPending=false;Escaping=false;BetweenTurns=false;
        pendingSwitches.Clear();
        ActualPlayerTurn=0;Master.LastBaseDrawTurn=Saber.LastBaseDrawTurn=-1;
        Master.Turns=Saber.Turns=0;Master.TurnNumber=Saber.TurnNumber=1;Master.Entered=true;Saber.Entered=false;
        Master.Powers.Clear();Saber.Powers.Clear();Master.TemporaryHp=Saber.TemporaryHp=0;
        Master.Hp=Player.Creature.CurrentHp;Master.MaxHp=Player.Creature.MaxHp;
        Master.OpeningDeck.Clear();Master.OpeningDeck.AddRange(Player.Deck.Cards.Select(c=>c.ToSerializable()));
        Saber.OpeningDeck.Clear();Saber.OpeningDeck.AddRange(Saber.Deck.Cards.Select(c=>c.ToSerializable()));
        foreach(var c in Player.Deck.Cards.Concat(Player.PlayerCombatState!.AllCards))CardOwners[c]=(this,Master);
        foreach(var p in Master.Piles.Values.Concat(Saber.Piles.Values))p.Clear(true);
        Master.Relics.Clear();Master.Relics.AddRange(Player.Relics.Where(r=>r!=Seal));
        foreach(var relic in Master.Relics.Concat(Saber.Relics).OfType<FateRelic>())relic.ResetCombatFlags();
    }
    void Capture(Fighter f){
        var creature=Player.Creature;f.Hp=creature.CurrentHp;f.MaxHp=creature.MaxHp;f.Block=creature.Block;f.TurnNumber=Player.PlayerCombatState!.TurnNumber;
        f.Powers.Clear();f.Powers.AddRange(creature.Powers);
        foreach(var power in creature.Powers.ToArray())creature.RemovePowerInternal(power); // detach without executing gameplay removal hooks
        f.Relics.Clear();f.Relics.AddRange(Player.Relics.Where(r=>r!=Seal));
        if(!MegaCrit.Sts2.Core.TestSupport.TestMode.IsOn&&NPlayerHand.Instance is {} hand)foreach(var c in Player.PlayerCombatState!.Hand.Cards.ToArray())hand.Remove(c);
        MovePile(Player.Deck,f.Deck);
        foreach(var pile in Player.PlayerCombatState!.AllPiles)MovePile(pile,f.Piles[pile.Type]);
        foreach(var c in f.Piles.Values.SelectMany(p=>p.Cards).Concat(f.Deck.Cards))CardOwners[c]=(this,f);
    }
    static void MovePile(CardPile from,CardPile to,bool silentDestination=true){foreach(var c in from.Cards.ToArray()){from.RemoveInternal(c);to.AddInternal(c,silent:silentDestination);}if(!silentDestination)to.InvokeCardAddFinished();}
    void Restore(Fighter f,bool restoreCombat=true){
        var creature=Player.Creature;creature.SetMaxHpInternal(f.MaxHp);creature.SetCurrentHpInternal(f.Hp);
        if(restoreCombat){AccessTools.PropertySetter(typeof(PlayerCombatState),nameof(PlayerCombatState.TurnNumber)).Invoke(Player.PlayerCombatState,[f.TurnNumber]);
        creature.LoseBlockInternal(creature.Block);creature.GainBlockInternal(f.Block);
        foreach(var power in f.Powers)creature.ApplyPowerInternal(power);}
        MovePile(f.Deck,Player.Deck,false);
        if(restoreCombat)foreach(var pile in Player.PlayerCombatState!.AllPiles)MovePile(f.Piles[pile.Type],pile,false);
        var rels=(List<RelicModel>)AccessTools.Field(typeof(Player),"_relics").GetValue(Player)!;
        var old=rels.ToArray();rels.Clear();rels.Add(Seal);rels.AddRange(f.Relics);
        if(Art.Find<NRelicInventory>() is {} inventory){
            foreach(var r in old)AccessTools.Method(typeof(NRelicInventory),"OnRelicRemoved").Invoke(inventory,[r]);
            foreach(var r in rels)AccessTools.Method(typeof(NRelicInventory),"Add").Invoke(inventory,[r,true,-1]);
            AccessTools.Method(typeof(NRelicInventory),"UpdateNavigation").Invoke(inventory,[]);
        }
        Art.RefreshFighter(this);
        var hand=NPlayerHand.Instance;
        if(restoreCombat&&hand!=null)foreach(var c in Player.PlayerCombatState!.Hand.Cards){var node=NCard.Create(c);if(node!=null)hand.Add(node);}
    }
    public async Task Switch(PlayerChoiceContext ctx,CardModel? switchingCard=null){
        if(!ContractActive||Switching||Combat==null)return;
        Switching=true;
        try{
            NPlayerHand.Instance?.CancelAllCardPlay();
            var previous=Current;Capture(previous);IsSaber=!IsSaber;Restore(Current);
            if(!Current.Entered){
                Current.Entered=true;
                foreach(var c in Player.Deck.Cards){var clone=Combat.CloneCard(c);clone.DeckVersion=c;CardOwners[clone]=(this,Current);Player.PlayerCombatState!.DrawPile.AddInternal(clone);}
                Player.PlayerCombatState!.DrawPile.RandomizeOrderInternal(Player,Player.RunState.Rng.Shuffle,Combat);
                foreach(var c in Player.PlayerCombatState.DrawPile.Cards.Where(c=>c.Keywords.Contains(CardKeyword.Innate)).ToArray())Player.PlayerCombatState.DrawPile.MoveToTopInternal(c);
            }
            if(Current.LastBaseDrawTurn!=ActualPlayerTurn){
                Current.LastBaseDrawTurn=ActualPlayerTurn;
                decimal draw=Hook.ModifyHandDraw(Combat,Player,5,out var modifiers);
                await Hook.AfterModifyingHandDraw(Combat,modifiers);
                await CardPileCmd.Draw(ctx,draw,Player,fromHandDraw:true);
            }
            // The switching card finishes into its original fighter's pile without activating that fighter.
            if(switchingCard!=null&&previous.Piles[PileType.Play].Cards.Contains(switchingCard)){
                previous.Piles[PileType.Play].RemoveInternal(switchingCard,true);previous.Piles[PileType.Discard].AddInternal(switchingCard,silent:true);
            }
            Save();
        }finally{Switching=false;}
    }
    public async Task ExchangeHp(PlayerChoiceContext ctx,CardModel source){
        var f=Current;f.Hp=Player.Creature.CurrentHp;f.MaxHp=Player.Creature.MaxHp;
        int a=f.Hp,b=Other.Hp;var incoming=Rules.ReceiveLife(b,f.MaxHp);var outgoing=Rules.ReceiveLife(a,Other.MaxHp);
        Other.Hp=outgoing.hp;Other.TemporaryHp+=outgoing.temporary;
        f.TemporaryHp+=incoming.temporary;await CreatureCmd.SetCurrentHp(Player.Creature,incoming.hp);f.Hp=incoming.hp;
        Art.RefreshFighter(this);
    }
    public void RemoveLinked(){
        if(!MegaCrit.Sts2.Core.TestSupport.TestMode.IsOn&&NPlayerHand.Instance is {} hand&&Player.PlayerCombatState!=null)
            foreach(var c in Player.PlayerCombatState.Hand.Cards.Where(Rules.Linked).ToArray())hand.Remove(c);
        foreach(var c in Player.Deck.Cards.Where(Rules.Linked).ToArray())Player.Deck.RemoveInternal(c);
        foreach(var f in new[]{Master,Saber})foreach(var pile in f.Piles.Values.Append(f.Deck))foreach(var c in pile.Cards.Where(Rules.Linked).ToArray())pile.RemoveInternal(c,true);
        if(Player.PlayerCombatState!=null)foreach(var pile in Player.PlayerCombatState.AllPiles)foreach(var c in pile.Cards.Where(Rules.Linked).ToArray())pile.RemoveInternal(c);
        Save();
    }
    public void NaturalTurn(){ActualPlayerTurn++;Current.LastBaseDrawTurn=ActualPlayerTurn;Current.Turns++;BetweenTurns=false;Art.RefreshFighter(this);}
    public void Finish(){
        if(Combat==null)return;
        if(IsSaber){Capture(Saber);IsSaber=false;Master.Powers.Clear();Master.Block=0;Restore(Master,false);}
        else{Master.Hp=Player.Creature.CurrentHp;Master.MaxHp=Player.Creature.MaxHp;}
        foreach(var f in new[]{Master,Saber}){f.Powers.Clear();f.TemporaryHp=0;f.Block=0;foreach(var pile in f.Piles.Values)pile.Clear(true);}
        if(Player.PlayerCombatState!=null)foreach(var pile in Player.PlayerCombatState.AllPiles)pile.Clear(true);
        Combat=null;Save();
        var permanent=Player.Deck.Cards.Concat(Saber.Deck.Cards).ToHashSet();
        foreach(var c in CardOwners.Where(p=>p.Value.duo==this&&!permanent.Contains(p.Key)).Select(p=>p.Key).ToArray())CardOwners.Remove(c);
    }
    public async Task UseSeal(int option,PlayerChoiceContext ctx){
        if(Combat==null||Seal.Charges<=0||Seal.UsedThisCombat||Switching)return;
        Seal.Charges--;Seal.UsedThisCombat=true;
        if(option==0)await PlayerCmd.GainEnergy(5,Player);
        if(option==1){await Switch(ctx);await CreatureCmd.GainBlock(Player.Creature,Player.Creature.CurrentHp,ValueProp.Unpowered,null);await CardPileCmd.Draw(ctx,4,Player);}
        if(option==2){
            Seal.Released=true;Seal.EscapeRewardsPending=true;RemoveLinked();
            if(IsSaber){Capture(Saber);IsSaber=false;Restore(Master);}
            Saber.Deck.Clear(true);Saber.Relics.Clear();Saber.Powers.Clear();Saber.Hp=0;Escaping=true;Save();
            foreach(var enemy in Combat.HittableEnemies.ToList())await CreatureCmd.Escape(enemy);
            await CombatManager.Instance.CheckWinCondition();
        }
        if(Seal.Charges==0)RemoveLinked();Save();Art.RefreshFighter(this);
    }
}
