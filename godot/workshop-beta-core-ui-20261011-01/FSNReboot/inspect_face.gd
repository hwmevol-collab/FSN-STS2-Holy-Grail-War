extends Node2D
func _ready():
	var a=load("res://FSNReboot/actor.tscn").instantiate()
	a.position=Vector2(480,480)
	a.scale=Vector2.ONE*1.4
	add_child(a)
	a.set_process(false)
	a.camera.size=0.4
	a.camera.position=Vector3(0,1.48,4)
	a.camera.look_at(Vector3(0,1.48,0))
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("res://raw-rin-test.png")
	get_tree().quit()
