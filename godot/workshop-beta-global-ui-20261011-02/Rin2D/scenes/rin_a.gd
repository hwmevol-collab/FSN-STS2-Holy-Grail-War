extends Node2D
## A-route painted cels. Small mesh offsets add counterweight without moving feet.
@onready var player: AnimationPlayer = $AnimationPlayer
@onready var sprite: Sprite2D = $Sprite
var recoil := 0.0
var settle := 0.0
var action := "idle"
var phase := "idle"
var age := -1.0

func _ready() -> void:
	process_priority = 1
	sprite.material = sprite.material.duplicate()
	player.animation_finished.connect(func(clip: StringName):
		if clip == &"gandr" or clip == &"reinforce":
			action = "idle"
			age = -1.0
			phase = "idle"
			player.speed_scale = 1.0
			player.play("idle"))

func cast() -> void:
	action = "gandr"
	age = 0.0
	player.stop()
	player.play("gandr")
	player.advance(0.0)

func perform(kind: String) -> void:
	if kind == "gandr": cast()
	else:
		action = "reinforce"
		age = 0.0
		player.stop()
		player.play("reinforce")
		player.advance(0.0)

func _process(_delta: float) -> void:
	age = player.current_animation_position if action != "idle" else -1.0
	phase = "prepare" if age < 0.285 else "release" if age < 0.425 else "recover"
	if age < 0.0: phase = "idle"
	recoil = sample_curve(age, [0.0,0.105,0.215,0.285,0.315,0.365,0.425,0.555,0.735,0.855,0.94], [0.0,-0.12,-0.35,-0.25,1.0,0.7,0.2,-0.1,0.04,0.0,0.0]) if age >= 0.0 else 0.0
	settle = sample_curve(age, [0.0,0.105,0.215,0.285,0.335,0.425,0.635,0.855,0.94], [0.0,0.1,0.2,-0.15,0.7,0.3,-0.1,0.0,0.0]) if age >= 0.0 else 0.0
	sprite.material.set_shader_parameter("recoil", recoil)
	sprite.material.set_shader_parameter("settle", settle)
	var light: float = smoothstep(0.095,0.25,age)*(1.0-smoothstep(0.30,0.43,age)) if age >= 0.0 else 0.0
	sprite.material.set_shader_parameter("red_light", light*0.6)
	queue_redraw()

func sample_curve(t: float, times: Array, values: Array) -> float:
	for i in range(times.size()-1):
		if t <= float(times[i+1]):
			var f: float = clampf((t-float(times[i]))/(float(times[i+1])-float(times[i])),0.0,1.0)
			return lerpf(float(values[i]),float(values[i+1]),smoothstep(0.0,1.0,f))
	return float(values.back())

func source_finger() -> Vector2:
	# Texture identity, rather than predicted time, keeps the cue on the visible cel.
	var file: String = sprite.texture.resource_path.get_file()
	match file:
		"01-raise.png": return Vector2(638,304)
		"02-prepare.png": return Vector2(620,182)
		"03-windup.png": return Vector2(850,115)
		"04-extend.png": return Vector2(948,243)
		"05-release.png": return Vector2(998,270)
		_: return Vector2(700,710)

func vertex_offset(p: Vector2) -> Vector2:
	var upper: float = 1.0-smoothstep(620.0,1370.0,p.y)
	var head: float = 1.0-smoothstep(290.0,530.0,p.y)
	return Vector2((-13.0*upper-5.0*head)*recoil, 4.0*upper*settle+2.0*head*recoil)

func emitter_position() -> Vector2:
	var p := source_finger()
	return sprite.transform*(p+vertex_offset(p))

func _draw() -> void:
	draw_set_transform(Vector2(0,-22),0.0,Vector2(1.0,0.13))
	for i in 4: draw_circle(Vector2.ZERO,345.0-i*35.0,Color(0.008,0.01,0.009,0.075))
	draw_set_transform(Vector2.ZERO)

func pose_at(t: float) -> void:
	player.play("gandr")
	player.seek(t, true)
	player.pause()
