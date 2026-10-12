extends Node2D
## Actual battle-space coordinates are supplied each rendered frame by C#.
const FIRE := 0.285
const HIT := 0.375
var age := -1.0
var impact_age := -1.0
var finger := Vector2.ZERO
var muzzle := Vector2.ZERO
var aim := Vector2.ZERO
var projectile: Sprite2D
var impact: Sprite2D
var boosted := false
var tick_callback: Callable
var launched := false

func _ready() -> void:
	process_priority = 2
	projectile = Sprite2D.new()
	projectile.name = "PaintedProjectile"
	projectile.texture = load("res://Rin2D/art/FX/gandr-projectile.png")
	projectile.centered = false
	projectile.offset = Vector2(-1980,-381)
	projectile.visible = false
	add_child(projectile)
	impact = Sprite2D.new()
	impact.name = "PaintedImpact"
	impact.texture = load("res://Rin2D/art/FX/gandr-impact.png")
	impact.centered = false
	impact.offset = Vector2(-540,-686)
	impact.visible = false
	add_child(impact)

func _process(delta: float) -> void:
	if tick_callback.is_valid(): tick_callback.call(delta)

func update_at(t: float, hand: Vector2, target: Vector2, hit_t: float, boost: bool) -> void:
	age = t
	finger = hand
	aim = target
	impact_age = t-hit_t if hit_t >= 0.0 else -1.0
	boosted = boost
	# Charge follows the hand; the travelling spell detaches at release.
	if not launched and t >= FIRE:
		launched = true
		muzzle = hand
	var travel: float = clampf((t-FIRE)/(HIT-FIRE),0.0,1.0)
	var head := muzzle.lerp(aim,travel)
	projectile.visible = t >= FIRE and (hit_t < 0.0 or impact_age < 0.06)
	if projectile.visible:
		var span: float = minf((head-muzzle).length()+22.0,410.0)
		projectile.position = head
		projectile.rotation = (aim-muzzle).angle()
		projectile.scale = Vector2(span/1927.0,0.14 if boost else 0.12)
		projectile.modulate.a = 1.0-clampf(impact_age/0.06,0.0,1.0)
	impact.visible = impact_age >= 0.0 and impact_age < 0.235
	if impact.visible:
		var f: float = impact_age/0.235
		impact.position = aim
		impact.rotation = (aim-muzzle).angle()*0.35
		impact.scale = Vector2(0.105+f*0.09,0.080+f*0.035)*(1.12 if boost else 1.0)
		impact.modulate.a = pow(1.0-f,1.5)
	queue_redraw()

func _draw() -> void:
	if age < 0.0: return
	if age >= 0.095 and age <= 0.335:
		var f: float = clampf((age-0.095)/0.19,0.0,1.0)
		var fade: float = 1.0-clampf((age-FIRE)/0.05,0.0,1.0)
		for i in 3:
			var radius: float = (15.0+i*4.0)*(1.0-f*0.38)
			var a: float = age*11.0+i*2.1
			draw_arc(finger,radius,a,a+1.4,12,Color(0.95,0.06,0.2,fade*f*0.58),1.15,true)
		for i in 12:
			var a: float = float(i)*2.39996
			var d: float = 30.0*(1.0-f)+4.0+float(i%3)*3.0
			var direction := Vector2(cos(a),sin(a))
			var p := finger+direction*d
			draw_line(p,p+direction*4.0,Color(1.0,0.2,0.34,fade*f),1.5,true)
		draw_circle(finger,3.0+f*3.0,Color(0.23,0.003,0.035,fade*f))
		draw_arc(finger,3.0+f*3.0,0,TAU,18,Color(1,0.08,0.22,fade),1.8,true)
		draw_circle(finger,1.2+f*1.0,Color(1,0.82,0.84,fade*f))
	# A continuous luminous tether behind the painted moving core crosses Archer
	# in one foreground pass. It disappears promptly after impact.
	if projectile.visible:
		var f: float = clampf((age-FIRE)/(HIT-FIRE),0.0,1.0)
		var end := muzzle.lerp(aim,f)
		var alpha: float = 1.0-clampf(impact_age/0.055,0.0,1.0)
		draw_line(muzzle,end,Color(0.55,0.008,0.07,alpha*0.14),12.0,true)
		draw_line(muzzle,end,Color(0.96,0.07,0.2,alpha*0.32),4.0,true)
		draw_line(muzzle,end,Color(1.0,0.52,0.62,alpha*0.7),1.4,true)
	if impact_age >= 0.0 and impact_age < 0.46:
		var f: float = impact_age/0.46
		var alpha: float = pow(1.0-f,1.65)
		for i in 22:
			var a: float = float(i)*2.39996
			var velocity := Vector2(cos(a)*float(45+i%6*17)+23.0,sin(a)*float(23+i%5*12))
			var p := aim+velocity*f+Vector2(0,40*f*f)
			var direction := velocity.normalized()
			var normal := Vector2(-direction.y,direction.x)
			var length: float = float(3+i%4)*(1.0-f*0.5)
			draw_colored_polygon(PackedVector2Array([p+direction*length,p+normal*1.2,p-direction*length,p-normal*1.2]),Color(1,0.13+float(i%3)*0.12,0.32,alpha))
