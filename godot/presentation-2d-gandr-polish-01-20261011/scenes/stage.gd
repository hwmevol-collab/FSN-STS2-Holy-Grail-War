extends Node2D
## Near-game OFFLINE composition. Native screenshot UI stays static.
var action_time := -1.0
var elapsed := 0.0
var casts := 0
var next_cast := 0.65
var movie := false
var still := false
var still_time := 0.315
var slow := false
var badge: Label
var background_material: ShaderMaterial
var layers: Array[Node2D] = []
@onready var actor = $Rin
@onready var cue: AnimationPlayer = $AnimationPlayer

func _ready() -> void:
	# Read animated poses/cues after AnimationPlayers update, without bypassing end signals.
	process_priority = 1
	var args := OS.get_cmdline_user_args()
	movie = "--movie" in args
	still = "--still" in args
	if "--prepare" in args: still_time = 0.19
	if "--beam" in args: still_time = 0.338
	if "--impact" in args: still_time = 0.405
	if "--recover" in args: still_time = 0.66
	if "--idle" in args: still_time = 0.90
	var bg := Sprite2D.new()
	bg.texture = load("res://art/battle-original.png")
	bg.centered = false
	background_material = ShaderMaterial.new()
	background_material.shader = load("res://shaders/enemy_response.gdshader")
	bg.material = background_material
	$Background.add_child(bg)
	# Use the previous clean plate ONLY where the old Rin stood; preserve native UI.
	var plate := Sprite2D.new()
	var atlas := AtlasTexture.new()
	atlas.atlas = load("res://art/cleanplate-generated.png")
	atlas.region = Rect2(380.0*1672/1920,450.0*941/1080,195.0*1672/1920,292.0*941/1080)
	atlas.filter_clip = true
	plate.texture = atlas
	plate.centered = false
	plate.position = Vector2(380,450)
	plate.scale = Vector2(1920.0/1672,1080.0/941)
	var plate_material := ShaderMaterial.new()
	plate_material.shader = load("res://shaders/plate.gdshader")
	plate.material = plate_material
	$Background.add_child(plate)
	# Original reserve pixels act as a foreground occluder for the projectile.
	var mask := Polygon2D.new()
	mask.texture = bg.texture
	mask.polygon = PackedVector2Array([Vector2(659,427),Vector2(683,429),Vector2(693,456),Vector2(706,474),Vector2(720,540),Vector2(708,571),Vector2(706,641),Vector2(716,696),Vector2(729,730),Vector2(638,733),Vector2(648,696),Vector2(632,671),Vector2(634,602),Vector2(636,533),Vector2(638,475),Vector2(650,456)])
	mask.uv = mask.polygon
	$ReserveOccluder.add_child(mask)
	layers = [$GroundShadow,$Charge,$ProjectileTrail,$Impact,$ForegroundSparks]
	cue.animation_finished.connect(func(clip: StringName):
		if clip == &"gandr": action_time = -1.0)
	badge = Label.new()
	badge.position = Vector2(1470,250)
	badge.add_theme_font_size_override("font_size",18)
	badge.add_theme_color_override("font_color",Color(0.78,0.78,0.72,0.85))
	badge.text = "本地合成预览 · 正常速度"
	add_child(badge)
	var replay_button := Button.new()
	replay_button.text = "重播甘德  [空格]    半速 [S]"
	replay_button.position = Vector2(1480,296)
	replay_button.size = Vector2(340,40)
	replay_button.pressed.connect(func(): replay(false))
	add_child(replay_button)
	if movie or still: replay_button.hide()
	if still:
		actor.pose_at(still_time)
		action_time = still_time
		update_effects()
		capture_image()
	print("POLISH_READY redrawn cels; offline screenshot composition; no gameplay integration")

func finger_at(t: float) -> Vector2:
	var source := Vector2(700,710)
	if t >= 0.035 and t < 0.105: source = Vector2(638,304)
	elif t >= 0.105 and t < 0.215: source = Vector2(620,182)
	elif t >= 0.215 and t < 0.25: source = Vector2(850,115)
	elif t >= 0.25 and t < 0.285: source = Vector2(948,243)
	elif t >= 0.285: source = Vector2(998,270)
	return Vector2(480,730)+(source-Vector2(570,1470))*0.192

func replay(half_speed: bool) -> void:
	slow = half_speed
	actor.player.speed_scale = 0.5 if slow else 1.0
	cue.speed_scale = actor.player.speed_scale
	actor.cast()
	cue.stop()
	cue.play("gandr")
	badge.text = "本地合成预览 · 半速回看" if slow else "本地合成预览 · 正常速度"

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_SPACE: replay(false)
		if event.keycode == KEY_S: replay(true)
		if event.keycode == KEY_ESCAPE: get_tree().quit()

func _process(delta: float) -> void:
	elapsed += delta
	if not still and elapsed >= next_cast and casts < 3:
		replay(casts == 2)
		casts += 1
		next_cast = 2.35 if casts == 1 else 4.30
	update_effects()
	if movie and elapsed >= 7.90:
		var settled: bool = action_time < 0.0 and actor.player.current_animation == &"idle" and float($HitGlow.material.get_shader_parameter("strength")) == 0.0 and float(background_material.get_shader_parameter("impulse")) == 0.0
		print("POLISH_MOVIE_END FX_OFF_IDLE_RESTORED=",settled)
		print("END_STATE time=",action_time," pose=",actor.player.current_animation)
		if not settled: push_error("Polish export did not settle")
		get_tree().quit(0 if settled else 1)

func update_effects() -> void:
	var hand := finger_at(action_time)
	for layer in layers: layer.update_at(action_time,hand)
	var charge := 0.0
	if action_time >= 0.095 and action_time < 0.285:
		charge = pow(clampf((action_time-0.095)/0.19,0,1),0.65)*0.75
	elif action_time >= 0.285 and action_time < 0.335:
		charge = (1.0-(action_time-0.285)/0.05)*1.45
	$CastingLight.position = hand-Vector2(52,52)
	$CastingLight.material.set_shader_parameter("strength",charge)
	actor.get_node("Sprite").material.set_shader_parameter("red_light",charge*0.25)
	var glow := 0.0
	var impulse := 0.0
	var flash := 0.0
	if action_time >= 0.375 and action_time < 0.63:
		var f: float = (action_time-0.375)/0.255
		glow = pow(1.0-f,2.0)*1.5
		impulse = sin(f*PI*2.6)*exp(-f*4.0)*11.0
		flash = maxf(0.0,1.0-f*4.0)
	$HitGlow.material.set_shader_parameter("strength",glow)
	background_material.set_shader_parameter("impulse",impulse)
	background_material.set_shader_parameter("flash",flash)

func capture_image() -> void:
	await get_tree().process_frame
	update_effects()
	await RenderingServer.frame_post_draw
	var name := "battle-release.png"
	if "--prepare" in OS.get_cmdline_user_args(): name = "battle-prepare.png"
	if "--beam" in OS.get_cmdline_user_args(): name = "battle-beam.png"
	if "--impact" in OS.get_cmdline_user_args(): name = "battle-impact.png"
	if "--recover" in OS.get_cmdline_user_args(): name = "battle-recover.png"
	if "--idle" in OS.get_cmdline_user_args(): name = "battle-idle.png"
	var error: int = get_viewport().get_texture().get_image().save_png(ProjectSettings.globalize_path("res://../media/"+name))
	print("POLISH_CAPTURE ",name," error=",error)
	get_tree().quit(error)
