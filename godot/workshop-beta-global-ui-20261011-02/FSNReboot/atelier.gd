extends Node2D
var rin: Node2D
var archer: Node2D
func _ready():
	rin=load("res://FSNReboot/actor.tscn").instantiate()
	rin.position=Vector2(510,660)
	rin.scale=Vector2.ONE*1.5
	add_child(rin)
	archer=load("res://FSNReboot/actor.tscn").instantiate()
	archer.is_rin=false
	archer.position=Vector2(1030,660)
	archer.scale=Vector2.ONE*1.5
	add_child(archer)
	var label:=Label.new()
	label.text="FATE / stay night     ·     CONTRACT ACTION ATELIER\nSPACE: Rin Gand Shot     /     ENTER: Archer Projection & Dual Blades\nAnimation / materials / timing source: FSNReboot/actor.gd"
	label.position=Vector2(70,50)
	label.add_theme_font_size_override("font_size",26)
	add_child(label)
	var controls:=HBoxContainer.new()
	controls.position=Vector2(70,800)
	controls.add_theme_constant_override("separation",20)
	add_child(controls)
	for item in [["Replay Rin · SPACE",rin,"gandr"],["Replay Archer · ENTER",archer,"weapon"]]:
		var button:=Button.new()
		button.text=item[0]
		button.custom_minimum_size=Vector2(280,48)
		button.pressed.connect(item[1].perform.bind(item[2]))
		controls.add_child(button)
	if "--capture" in OS.get_cmdline_args():
		await get_tree().process_frame
		await get_tree().process_frame
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("res://atelier-idle.png")
		rin.perform("gandr")
		archer.perform("weapon")
		await get_tree().create_timer(1.42).timeout
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("res://atelier-action.png")
		get_tree().quit()
func _unhandled_key_input(event):
	if event is InputEventKey and event.pressed:
		if event.keycode==KEY_SPACE:rin.perform("gandr")
		if event.keycode==KEY_ENTER:archer.perform("weapon")
