# Camera-relative modelview (FREELANCER_PRECISE_RENDER)

Not in the original game. Build flag `FreelancerPreciseRender` (client and `x86math.dll`),
switched at run time by `port.ini`:

```ini
[Render]
precise_view = 1
```

## The problem

Every renderer builds an object's modelview as `I3DMathEngine::MulTransform(View, World)`.
`View`'s translation is `-R^T * CameraPos`, `World`'s is the object's position. Far from the
system centre both are huge floats (a float has about 6 cm of resolution at 1,000,000) and their
sum, the small distance from the camera to the object, keeps only the rounding noise of the two.
That noise changes with every turn of the camera, so ships, stations and the player's own ship
shake by centimetres to decimetres.

## The fix

`FSpaceCamera::GetViewTransform` registers its view and its world position with `x86math.dll`
(`PortRegisterView`, `include/port_precise_view.h`) whenever it rebuilds the view.
`MulTransform` recognises that view as the left operand (bit for bit, so copies count too) and
returns `R = Rv * Rw`, `T = Rv * (Tw - CameraPos)`. The subtraction of two nearby floats is
exact, so the result is as precise as the positions themselves.

Physics, the server and the stored positions are unchanged.

## Not covered (yet)

Effects whose vertices are written in world coordinates (particles, beams, trails) are drawn
with the bare view as the modelview and still carry the world-size rounding of their vertices.

## During camera shake

While the hit / jump shake amplitude (`G_CameraShakeAmount`, `GetCameraShakeAmount`) is
non-zero, `GetViewTransform` clears the registered views instead of registering its own, so
every modelview takes the ordinary path for those frames and the shake reaches the scene
unfiltered. The precise path resumes on the first still frame.
