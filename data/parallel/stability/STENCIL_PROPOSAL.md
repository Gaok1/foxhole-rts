# Preenchimento residual — proposta isolada, não aplicada

Usuário relatou piscadas amarelas em unidade não selecionada na troca de grupos.
A fonte atual desliga CustomDepth mas só grava stencil quando on=true, retendo1
no componente desmarcado. O jogo reativa CustomDepth nativo (rastro anterior).
Essa combinação é hipótese de fill residual; ainda não comprova timing/material.

Mudança mínima candidata em rts.outlineDepth:

```lua
if c.CustomDepthStencilValue ~= (on and 1 or 0) then
    c:SetCustomDepthStencilValue(on and 1 or 0)
end
```

test_stencil_clear.py extrai helper real: baseline retém1 após desligamento e
reativação simulada; proposta limpa0, preserva reseleção1, não repete writes e
recusa pawn em destruição. Testa estado Lua, NÃO shader ou flicker no engine.

Antes de integrar: concluir ensaio isolado da ponte de teclas. Depois, carga limpa
com mudança única de stencil, observar valor real/frame e soldado oculto por veículo.
Confirmar stencil0sem fill e ausência de reescrita nativa1 entre callbacks.
Se reescrever, rastrear escritor/ordem de quadro antes de inventar outro timer.
Não misturar com hipótese do crash.
