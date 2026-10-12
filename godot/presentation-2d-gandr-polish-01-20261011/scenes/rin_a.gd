extends Node2D
## Redrawn cels only; constant placement and scale, no skeletal deformation.
@onready var player: AnimationPlayer = $AnimationPlayer

func _ready() -> void:
	player.animation_finished.connect(func(clip: StringName):
		if clip == &"gandr":
			player.speed_scale = 1.0
			player.play("idle"))

func cast() -> void:
	player.stop()
	player.play("gandr")

func pose_at(t: float) -> void:
	player.play("gandr")
	player.seek(t, true)
	player.pause()
