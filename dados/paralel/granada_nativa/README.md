# Granada nativa — candidato offline, NÃO publicado

Base SHA256 `2F1C74D6BB205FA5610957A9B126720731CFA34DF4775329B2DDA7A82101F956`.
Montar: `python dados/paralel/granada_nativa/montar.py`.
Mocks: `PYTHONPATH=D:/tools/pylibs python dados/paralel/granada_nativa/test_granada.py`.

Substitui granada mesh/arco manual/shell de dano próprio por BPGrenadeW deferred,
FuseTimer da row real ANTES FinishSpawning, solver CustomArc e ProjectileMovement.
Não agenda strikes, ApplyDamage, logi.blast ou FX artificiais de explosão. Morteiro
continua abstrato e explicitamente separado como dívida. Cooldown/contador/animação
só confirmam após ator finalizado e acompanhamento aceito; falhas limpam apenas
ator criado pelo próprio fluxo e liberam reserva. `fire` continua tiro normal se
granada for recusada, em vez de perder a ação silenciosamente.

## Dependência a integrar pelo principal

- `rts.nativeAcquire()` → bool, reserva uma pendência e ancora ServerSettings fresca.
- `rts.nativeRelease()` desfaz reserva em falha, restaura somente contexto próprio.
- `rts.nativeTrack(actor)` → bool, transfere reserva para acompanhamento por nome/classe.
- Tick/clear/reset do principal devem manter contexto enquanto granadas estiverem
  vivas, não escrever em cache de UObject morto; restore original somente se a GI
  ainda apontar para settings própria. Este candidato NÃO implementa outro lifetime.
- MyController fraco não é escrito: binding/atribuição de instigador permanecem
  gate. Owner m.pawn é passado pelo parâmetro nativo já provado com playerPawn;
  isso não prova equipe correta contra soldados nem concessão de killcredit.

## Batch vivo posterior — ainda pendente

1. Integrar helpers de lifetime e candidato junto do restante do lote, sem lançar
   laboratório só para este helper. Validar uma única publicação/reinicialização.
2. Arremesso real a partir de soldado, aliados/inimigos, cobertura, alcance curto/
   longo. Não substituir solver recusado por teleporte/arco manual.
3. Registrar timer4s, trajetória/colisão/bounce e HP nativo de alvos; confirmar
   dano/efeito nativo também no soldado, morte/cleanup/animação via fluxo existente.
4. Confirmar equipe/friendlyfire/Owner/MyController/killcredit; contador `gdmg`
   antigo não mede dano nativo automaticamente e NÃO certifica ausência de dano.
5. Reset/saída/morte do lançador com projétil em voo, várias granadas simultâneas,
   falha de spawn/solver/Finish e contexto externo trocado enquanto lease ativa.
6. Validar GIsettings restaurada só quando todas pendências terminarem, sem crash;
   fechar somente PID laboratório após batch. Sem mouse/teclado automatizado.

Mocks17PASS provam decisões/limpeza, não Unreal. Evidência viva anterior prova
somente oracle isolado de lançamento, não este `throwGrenade` integrado.
