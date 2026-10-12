extends Node2D
## Four independently editable VFX layers; shared deterministic animation time.
@export_enum("Ground", "Charge", "Beam", "Impact", "Debris") var layer := "Charge"
var action_time := -1.0
var finger := Vector2(490,482)
var muzzle := Vector2(562,500)
var aim := Vector2(1398,670)
const FIRE := 0.285
const HIT := 0.375

func update_at(t: float, hand: Vector2) -> void:
	action_time = t
	finger = hand
	if layer == "Beam" and has_node("ProjectileArt"):
		var sprite: Sprite2D = $ProjectileArt
		sprite.visible = t >= FIRE and t <= HIT+0.065
		if sprite.visible:
			var travel: float = clampf((t-FIRE)/(HIT-FIRE),0.0,1.0)
			var head := muzzle.lerp(aim,travel)
			var span: float = minf((head-muzzle).length()+28.0,360.0)
			sprite.position = head
			sprite.rotation = (aim-muzzle).angle()
			sprite.scale = Vector2(span/1927.0,0.13)
			sprite.modulate.a = 1.0-clampf((t-HIT)/0.065,0.0,1.0)
	if layer == "Impact" and has_node("ImpactArt"):
		var sprite: Sprite2D = $ImpactArt
		sprite.visible = t >= HIT and t <= HIT+0.235
		if sprite.visible:
			var f: float = (t-HIT)/0.235
			sprite.position = aim
			sprite.scale = Vector2(0.105+f*0.09,0.080+f*0.035)
			sprite.modulate.a = pow(1.0-f,1.5)
	queue_redraw()

func _draw() -> void:
	var t: float = action_time
	if layer == "Ground":
		draw_set_transform(Vector2(476,730),0.0,Vector2(1.0,0.13))
		for i in 5:
			draw_circle(Vector2.ZERO,64.0-i*7.0,Color(0.012,0.015,0.014,0.035))
		draw_set_transform(Vector2.ZERO)
		return
	if t < 0.0: return
	match layer:
		"Charge": draw_charge(t)
		"Beam": pass
		"Impact": pass
		"Debris": draw_debris(t)

func draw_charge(t: float) -> void:
	if t < 0.095 or t > 0.335: return
	var f: float = clampf((t-0.095)/0.19,0.0,1.0)
	var fade: float = 1.0-clampf((t-FIRE)/0.05,0.0,1.0)
	var red := Color(1.0,0.08,0.22,fade)
	# Fleeting broken circuits and converging motes, close to the fingertip.
	for i in 3:
		var radius: float = (15.0+i*4.0)*(1.0-f*0.38)
		var angle: float = t*11.0+i*2.1
		draw_arc(finger,radius,angle,angle+1.4,12,Color(0.95,0.06,0.2,fade*f*0.58),1.15,true)
	for i in 12:
		var angle: float = float(i)*2.39996
		var distance: float = 30.0*(1.0-f)+4.0+float(i%3)*3.0
		var q := finger+Vector2(cos(angle),sin(angle))*distance
		draw_line(q,q+Vector2(cos(angle),sin(angle))*4.0,Color(1.0,0.2,0.34,fade*f),1.5,true)
	# Short knot of dark-red magic, bright pinprick at the very centre.
	draw_circle(finger,3.0+f*3.0,Color(0.23,0.003,0.035,fade*f))
	draw_arc(finger,3.0+f*3.0,0,TAU,18,red,1.8,true)
	draw_circle(finger,1.2+f*1.0,Color(1.0,0.82,0.84,fade*f))
	if t >= FIRE:
		var a: float = 1.0-(t-FIRE)/0.05
		for i in 5:
			var dir := Vector2.from_angle(float(i)*1.22-0.2)
			draw_line(finger+dir*3.0,finger+dir*(11.0+8.0*a),Color(1.0,0.31,0.4,a),1.8,true)

func draw_debris(t: float) -> void:
	if t < HIT or t > HIT+0.46: return
	var f: float = (t-HIT)/0.46
	var a: float = pow(1.0-f,1.65)
	for i in 22:
		var angle: float = float(i)*2.39996
		var velocity := Vector2(cos(angle)*float(45+i%6*17)+23.0,sin(angle)*float(23+i%5*12))
		var p := aim+velocity*f+Vector2(0,40.0*f*f)
		var dir := velocity.normalized()
		var normal := Vector2(-dir.y,dir.x)
		var length: float = float(3+i%4)*(1.0-f*0.5)
		draw_colored_polygon(PackedVector2Array([p+dir*length,p+normal*1.2,p-dir*length,p-normal*1.2]),Color(1.0,0.13+float(i%3)*0.12,0.32,a))
		if i%3 == 0: draw_line(p,p-dir*length,Color(1.0,0.73,0.76,a*0.8),0.8,true)
