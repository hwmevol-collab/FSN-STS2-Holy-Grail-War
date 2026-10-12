namespace FateStayNight;

// This DLL is loaded dynamically, without Godot's script source generator.
// Bind native signals explicitly instead of relying on virtual script dispatch.
public static class NativeAnimation
{
    public static void Start(Node owner,Action<double> tick,Action? draw=null){
        if(draw!=null&&owner is CanvasItem canvas)canvas.Draw+=draw;
        ulong last=Time.GetTicksUsec();
        var timer=new Godot.Timer{WaitTime=1.0/60,Autostart=true};owner.AddChild(timer);
        timer.Timeout+=()=>{ulong now=Time.GetTicksUsec();double dt=Math.Min(.1,(now-last)/1000000.0);last=now;tick(dt);};
    }
}

// Decorative nodes never consume input, alter game state, or use the game's RNG.
public partial class ContractAtmosphere : Node2D
{
    public bool Selection;
    public bool Saber;
    float clock;
    public void Start()=>NativeAnimation.Start(this,_Process,_Draw);
    public override void _Process(double delta){clock+=(float)delta;QueueRedraw();}
    public override void _Draw(){
        Color c=new(Saber?"8dccff":"66e5c1");
        if(Selection){
            for(int i=0;i<38;i++){
                float x=900+(i*137%1180),y=1050-((clock*(14+i%7)+i*89)%1050);
                float a=.12f+.24f*Mathf.Pow(Mathf.Sin(clock*.5f+i),2);
                DrawCircle(new(x,y),i%3==0?2.3f:1.2f,new Color(i%3==0?new Color("edcd8b"):c,a));
            }
        }else{
            var center=new Vector2(0,4);float pulse=.55f+.08f*Mathf.Sin(clock*1.7f);
            for(int r=0;r<2;r++){
                var points=new Vector2[81];
                for(int i=0;i<=80;i++){float a=i*Mathf.Tau/80;points[i]=center+new Vector2(Mathf.Cos(a)*(88+r*12),Mathf.Sin(a)*(18+r*3));}
                DrawPolyline(points,new Color(c,pulse*(r==0?.45f:.2f)),1.3f,true);
            }
            for(int i=0;i<12;i++){float a=i*Mathf.Tau/12+clock*.14f;var p=new Vector2(Mathf.Cos(a)*99,Mathf.Sin(a)*21);DrawLine(p,p+new Vector2(Mathf.Cos(a)*7,Mathf.Sin(a)*2),new Color(c,.4f),1,true);}
        }
    }
}

public partial class FighterMotion : Node
{
    public Sprite2D Sprite=null!;
    float clock,impulse;
    public void Start()=>NativeAnimation.Start(this,_Process);
    public void Strike(){impulse=1;}
    public override void _Process(double delta){
        if(!GodotObject.IsInstanceValid(Sprite))return;
        clock+=(float)delta;impulse=Mathf.Max(0,impulse-(float)delta*3.5f);
        Sprite.Position=new Vector2(Mathf.Sin(impulse*Mathf.Pi)*24,-173+Mathf.Sin(clock*1.8f)*1.4f);
        Sprite.Rotation=-Mathf.Sin(impulse*Mathf.Pi)*.045f;
    }
}
