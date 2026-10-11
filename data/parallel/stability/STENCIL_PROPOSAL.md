# Residual fill — isolated proposal, not applied

The user reported yellow blinks on a non-selected unit when switching groups.
The current source turns CustomDepth off but only writes the stencil when on=true, keeping 1
on the deselected component. The game reactivates native CustomDepth (earlier trace).
That combination is a hypothesis for the residual fill; it does not prove timing/material yet.

Minimal candidate change in rts.outlineDepth:

```lua
if c.CustomDepthStencilValue ~= (on and 1 or 0) then
    c:SetCustomDepthStencilValue(on and 1 or 0)
end
```

test_stencil_clear.py extracts the real helper: the baseline keeps 1 after turning off and
a simulated reactivation; the proposal clears to 0, keeps reselection at 1, does not repeat writes and
refuses a pawn being destroyed. It tests Lua state, NOT the shader or flicker in the engine.

Before integrating: finish the isolated rehearsal of the key bridge. Then, a clean load
with only the stencil change, observe the real value per frame and a soldier hidden by a vehicle.
Confirm stencil 0 without fill and no native rewrite to 1 between callbacks.
If it rewrites, trace the writer/frame order before inventing another timer.
Do not mix with the crash hypothesis.
