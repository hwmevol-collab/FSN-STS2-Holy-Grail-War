using MegaCrit.Sts2.Core.Nodes;
using MegaCrit.Sts2.Core.Nodes.Combat;
namespace RinArcherCore;

// Visual-only adapter. The native action still owns payment, targeting and damage.
public sealed partial class RinGandrRuntimeEffect:Node2D
{
    public const float HitCue=.375f;
    public static int LiveCount,StartedCount,FinishedCount;
    public static RinGandrRuntimeEffect? Latest;
    public float Age{get;private set;}
    public float HitAge{get;private set;}=-1;
    public Vector2 Finger{get;private set;}
    public Vector2 Aim{get;private set;}
    public bool DamageObserved{get;private set;}
    public Creature Target=>target;
    public bool Released=>Age>=HitCue;
    readonly ContractPresentationBody body;
    readonly Creature target;
    readonly NCreature targetNode;
    readonly int hp,block;
    readonly bool boosted;
    Node2D? art;bool shotSound;
    public RinGandrRuntimeEffect(ContractPresentationBody source,Creature victim,NCreature node,bool boost)
    {
        body=source;target=victim;targetNode=node;hp=target.CurrentHp;block=target.Block;boosted=boost;
        Name="RinGandrRuntime";Ready+=Initialize;
    }
    void Initialize()
    {
        art=ResourceLoader.Load<PackedScene>("res://Rin2D/scenes/gandr_fx.tscn").Instantiate<Node2D>();AddChild(art);
        art.Set("tick_callback",Callable.From<double>(Tick));
        Latest=this;LiveCount++;StartedCount++;
        TreeExiting+=()=>{LiveCount--;FinishedCount++;};
    }
    void Tick(double delta)
    {
        Age+=(float)delta;
        // Room exit/death never leaves a detached overlay in the next screen.
        if(!GodotObject.IsInstanceValid(body)||!body.IsInsideTree()||!GodotObject.IsInstanceValid(targetNode)||!targetNode.IsInsideTree()) {GetParent().QueueFree();return;}
        var caster=body.Actor;
        Finger=caster!=null?caster.GetGlobalTransformWithCanvas()*caster.Call("emitter_position").AsVector2():body.Emitter;
        var center=FindCenter(targetNode);
        Aim=center!=null?center.GetGlobalTransformWithCanvas().Origin:targetNode.GetGlobalTransformWithCanvas().Origin+new Vector2(0,-90);
        if(!shotSound&&Age>=.285f){shotSound=true;Sound("gandr");}
        // Observe the native resolved HP/block change, not a simulated enemy flash.
        if(HitAge<0&&Age>=HitCue&&(target.CurrentHp!=hp||target.Block!=block))
        {DamageObserved=true;HitAge=Age;Sound("impact");}
        // Damage can be prevented; the spell still ends visually on its target.
        if(HitAge<0&&Age>=HitCue+.1f){HitAge=Age;Sound("impact");}
        art?.Call("update_at",Age,Finger,Aim,HitAge,boosted);
        if(Age>=.94f)GetParent().QueueFree();
    }
    static CanvasItem? FindCenter(Node n)
    {
        if(n.Name=="CenterPos"&&n is CanvasItem item)return item;
        foreach(var c in n.GetChildren())if(FindCenter(c) is {} center)return center;
        return null;
    }
    void Sound(string name)
    {
        var p=Path.Combine(Path.GetDirectoryName(typeof(RinGandrRuntimeEffect).Assembly.Location)!,"Presentation","Assets",name+".wav");
        if(!File.Exists(p))return;
        var player=new AudioStreamPlayer{Stream=AudioStreamWav.LoadFromFile(p),VolumeDb=-15};AddChild(player);player.Play();
    }
}
