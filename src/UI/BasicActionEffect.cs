using MegaCrit.Sts2.Core.Nodes;
using MegaCrit.Sts2.Core.Nodes.Rooms;
namespace RinArcherCore;
public sealed partial class BasicActionEffect:Node2D
{
    public static int LiveCount;public static BasicActionEffect? Latest;
    public readonly string Kind;public float Age,HitAge=-1;public bool SettlementObserved;
    readonly ContractPresentationBody body;readonly Creature target;readonly CanvasItem targetNode;readonly int hp,block;
    Vector2 hand,aim,muzzle;public float Cue=>Kind=="bow"?.38f:.22f;public bool Released=>Age>=Cue;
    public BasicActionEffect(string kind,ContractPresentationBody actor,Creature victim,CanvasItem node)
    {
        Kind=kind;body=actor;target=victim;targetNode=node;hp=target.CurrentHp;block=target.Block;Name="BasicAction-"+kind;
        Draw+=Render;Ready+=()=>{LiveCount++;Latest=this;GetTree().ProcessFrame+=Tick;};
        TreeExiting+=()=>{GetTree().ProcessFrame-=Tick;LiveCount--;};
    }
    void Tick()
    {
        Age+=(float)GetProcessDeltaTime();
        if(!GodotObject.IsInstanceValid(body)||!body.IsInsideTree()||!GodotObject.IsInstanceValid(targetNode)||!targetNode.IsInsideTree()){GetParent().QueueFree();return;}
        hand=body.Actor!.GetGlobalTransformWithCanvas()*body.Actor.Call("emitter_position").AsVector2();
        aim=targetNode.GetGlobalTransformWithCanvas().Origin+new Vector2(0,-105);
        if(Kind=="bow"&&Age<.285f)muzzle=hand;
        if(HitAge<0&&Age>=Cue&&(target.CurrentHp!=hp||target.Block!=block)){SettlementObserved=true;HitAge=Age;}
        if(Age>=.82f){GetParent().QueueFree();return;}QueueRedraw();
    }
    void Glow(Vector2 a,Vector2 b,Color c,float w,float opacity)
    {DrawLine(a,b,new(c.R,c.G,c.B,opacity*.09f),w*6,true);DrawLine(a,b,new(c.R,c.G,c.B,opacity*.25f),w*2.7f,true);DrawLine(a,b,new(c.R,c.G,c.B,opacity),w,true);}
    void Render()
    {
        float fade=Mathf.Clamp((.82f-Age)/.3f,0,1);
        var c=Kind=="reinforce"?new Color("e94067"):new Color("aacfe6");
        if(Kind=="bow")
        {
            if(Age>=.285f&&HitAge<0)
            {float f=Mathf.Clamp((Age-.285f)/.095f,0,1);var head=muzzle.Lerp(aim,f);var dir=(aim-muzzle).Normalized();Glow(head-dir*125,head,c,3.4f,1);DrawPolyline([head-dir*15+dir.Orthogonal()*5,head,head-dir*15-dir.Orthogonal()*5],Colors.White,2,true);}
            if(HitAge>=0){float t=Age-HitAge;float a=Mathf.Clamp(1-t/.28f,0,1);for(int i=0;i<12;i++){var v=Vector2.FromAngle(i*2.4f);Glow(aim+v*(10+t*160),aim+v*(28+t*210),c,1.7f,a);}DrawArc(aim,8+t*90,0,Mathf.Tau,48,new(c.R,c.G,c.B,a*.6f),2,true);}
            return;
        }
        if(Kind=="reinforce"||Kind=="deflect")
        {
            Vector2 center=aim+new Vector2(35,-25);float r=42+Mathf.SmoothStep(0,1,Age/.22f)*17;
            DrawArc(center,r,-1.25f,1.3f,48,new(c.R,c.G,c.B,fade*.16f),14,true);
            DrawArc(center,r,-1.25f,1.3f,48,new(c.R,c.G,c.B,fade*.85f),2.2f,true);
            if(Kind=="reinforce")for(int i=0;i<5;i++){var v=Vector2.FromAngle(-1.2f+i*.6f);var p=center+v*r;DrawPolyline([p-v*8+v.Orthogonal()*4,p+v*5,p-v*8-v.Orthogonal()*4],new(c.R,c.G,c.B,fade),1.8f,true);}
            if(HitAge>=0){float t=Age-HitAge;float a=Mathf.Clamp(1-t/.22f,0,1);Glow(center+new Vector2(-28,35),center+new Vector2(32,-36),PresentationTheme.Paper,3,a);}
        }
        else
        {DrawArc(hand,12+Age*22,0,Mathf.Tau,32,new(c.R,c.G,c.B,fade*.55f),1.7f,true);}
    }
    public static async Task Play(ContractRuntime d,StarterCard card,ContractPresentationBody body,string kind)
    {
        var room=NCombatRoom.Instance!;var target=kind=="bow"?d.PlayTarget(card):d.Member(card.OwnerCharacterId).Creature;
        target??=d.Member(card.OwnerCharacterId).Creature;var node=room.GetCreatureNode(target);if(node==null)return;
        body.Cast(kind);var layer=new Node2D{Name="ContractBasicActionLayer",Transform=room.GetGlobalTransformWithCanvas().AffineInverse()};room.AddChild(layer);
        var fx=new BasicActionEffect(kind,body,target,node);layer.AddChild(fx);
        while(GodotObject.IsInstanceValid(fx)&&fx.IsInsideTree()&&!fx.Released)await NGame.Instance!.ToSignal(NGame.Instance.GetTree(),SceneTree.SignalName.ProcessFrame);
    }
}
