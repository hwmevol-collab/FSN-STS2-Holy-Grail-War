extends Node
## Honest comparisons of unretouched source cels and Godot battle compositions.
var views: Array[SubViewport] = []

func title(root: Node, text: String, p: Vector2, size: int, color: Color) -> void:
	var label := Label.new()
	label.text = text
	label.position = p
	label.add_theme_font_size_override("font_size",size)
	label.add_theme_color_override("font_color",color)
	root.add_child(label)

func canvas(size: Vector2i) -> SubViewport:
	var view := SubViewport.new()
	view.size = size
	view.world_2d = World2D.new()
	view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(view)
	views.append(view)
	var background := ColorRect.new()
	background.size = Vector2(size)
	background.color = Color(0.047,0.052,0.063,1)
	view.add_child(background)
	return view

func cel(root: Node, path: String, position: Vector2) -> void:
	var sprite := Sprite2D.new()
	sprite.texture = load(path)
	sprite.centered = false
	sprite.position = position-Vector2(570,1470)*0.62
	sprite.scale = Vector2(0.62,0.62)
	var material := ShaderMaterial.new()
	material.shader = load("res://shaders/character.gdshader")
	material.set_shader_parameter("ambient",Vector3.ONE)
	sprite.material = material
	root.add_child(sprite)

func screenshot(root: Node, path: String, x: float) -> void:
	var sprite := Sprite2D.new()
	sprite.texture = ImageTexture.create_from_image(Image.load_from_file(path))
	sprite.centered = false
	sprite.position = Vector2(x,0)
	root.add_child(sprite)

func _ready() -> void:
	var keys := canvas(Vector2i(3840,2160))
	title(keys,"A 新绘关键帧 · 同倍率原画对比",Vector2(50,20),44,Color(0.92,0.88,0.79))
	title(keys,"上一轮 PoC",Vector2(50,93),31,Color(0.70,0.72,0.75))
	title(keys,"本轮 Polish 01",Vector2(50,1120),31,Color(1.0,0.35,0.43))
	var old_paths := ["00-idle","02-prepare","04-release"]
	var new_paths := ["00-idle","02-prepare","05-release"]
	var names := ["待机 / 站姿","聚能 / 脸与手","释放 / 扭转与轮廓"]
	for i in 3:
		var x: float = 600.0+float(i)*1260.0
		cel(keys,"res://art/PoC/"+old_paths[i]+".png",Vector2(x,1050))
		cel(keys,"res://art/A/"+new_paths[i]+".png",Vector2(x,2070))
		title(keys,names[i],Vector2(x-190,1065),29,Color(0.75,0.75,0.71))
		var guide := ColorRect.new()
		guide.position = Vector2(x-330,2071)
		guide.size = Vector2(670,1)
		guide.color = Color(0.65,0.33,0.38,0.4)
		keys.add_child(guide)
	title(keys,"原画均为 1024×1536；统一 0.62 倍率，没有逐帧缩放补偿。",Vector2(50,2110),28,Color(0.66,0.69,0.70))
	var battle := canvas(Vector2i(3840,1080))
	screenshot(battle,ProjectSettings.globalize_path("res://art/PoC/battle-impact.png"),0)
	screenshot(battle,ProjectSettings.globalize_path("res://../media/battle-impact.png"),1920)
	title(battle,"上一轮 PoC · 离线合成",Vector2(1470,300),24,Color(1,0.82,0.76))
	title(battle,"本轮 Polish 01 · 离线合成",Vector2(3390,300),24,Color(1,0.82,0.76))
	await get_tree().process_frame
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var error_keys: int = keys.get_texture().get_image().save_png(ProjectSettings.globalize_path("res://../media/keyframes-before-after.png"))
	var error_battle: int = battle.get_texture().get_image().save_png(ProjectSettings.globalize_path("res://../media/battle-before-after.png"))
	print("POLISH_COMPARISONS errors=",error_keys,",",error_battle)
	get_tree().quit(error_keys+error_battle)
