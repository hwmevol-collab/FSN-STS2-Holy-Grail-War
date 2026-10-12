extends Node2D
func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed:
		if event.keycode == KEY_SPACE: $Rin.cast()
		if event.keycode == KEY_ESCAPE: get_tree().quit()
