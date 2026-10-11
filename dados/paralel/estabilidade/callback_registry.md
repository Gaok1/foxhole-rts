# Auditoria de callbacks/Registry após crash PID4408

## Evidência comparada (não diagnóstico)

`crashes_comparados.json` foi extraído de três CrashContext.runtime-xml reais.
- DF9A… lote17: leitura0xffffffff.
- 97D8… lote17: XML registra leitura0x08 (corrige a descrição genérica no rastro antigo).
- 18BCE… PID4408: leitura0x63,SecondsSinceStart111.
Todos trazem PCallStackHash6341FC051FB0F3E558B68187F705D55824D754E0, mas cabeçalhos de pilha
DIFERENTES; hash igual sozinho não prova mesma instrução/causa. Offsets Lua/UE4SS repetidos são comuns:
b985c4,b9d34c,c6cfde,c6c1e0,c77cab,c6b9a9,c6c733,c6bff4,c640ac,c7c9a1.
Cauda engine igual:+5220da,+52847c,+5284fa,+53265b,+32ae58e. Sem símbolos/PDB não nomear esses offsets.
Pilha nova e97D8 compartilham estrutura muito semelhante após o cabeçalho; primeiro DF9A também passa
pela sequência repetida. Isso justifica investigar ponte Lua/callbacks comum às variantes, não inocenta
contorno nem atribui MasterPose/GC/input.

Timeline informada pelo coordenador:wheel18:20:01,Registry Ref was not function18:20:03,
selecionados6 logs18:20:04/06. Essas entradas posteriores mostram que erro Registry não é instante
de término do processo. Nenhuma entrada foi injetada pelo agente; evento wheel não demonstra causa.

## Fluxos registrados na fonte atual

- `onGame(f)` cria closure de keybind; cada execução cria NOVA closure passada a ExecuteInGameThread.
  Closure interna captura f; registro keybind e fila engine precisam reter referência Lua corretamente.
  Fonte não remove callback, chama luaL_unref nem manipula Registry diretamente.
- `plain(f)` captura f e consulta teclas modificadoras DENTRO da closure enfileirada; não precisa manter
  userdata do playerController entre agendamento e execução. Controller é buscado no momento da execução.
- Roda do mouse não usa RegisterKeyBind/onGame: `cameraTick` chama `rts.wheel`, leitura poll por frame.
  Seleção por clique/arrasto também vem do frame/mouseTick, não necessariamente wrapper keybind.
  Portanto logs wheel/seleção não identificam qual callback Registry falhou.
- Animação: RegisterHook uma vez por ABP, callback função estável `anim.onUpdate` armazenada em tabela anim.
  onUpdate pega AnimInstance ctx vivo e m por endereço. Todos caminhos de morte auditados removem anim cache
  antes OnRep_Health; troca de AnimInstance com unidade viva não é revalidada automaticamente.
- `anim.track`: atribui anim.hooked=true MESMO se pcall(RegisterHook) falhar. Defeito lógico comprovável:
  uma falha inicial suprime todas tentativas seguintes. Não explica diretamente Registry inválido em hook
  já registrado. Proposta separada mínima: somente set hooked=true se hk==true; não aplicar sem teste.
- IDs de hook não são guardados, não há unregister no fluxo. Isso não prova coleta indevida: retenção deve
  ser garantida pela API nativa. Anchoring adicional em Lua seria hipótese/experiência, não root cause.
- Loop principal AfterFrames tem closure persistente; canal/autostart Delay1000 tem outra closure;
  respawn pre/post hooks e ServerTakePickup hooks também callbacks. Stack sem símbolo não distingue esses.
- Sondas executadas foram chamadas diretas pelo canal; não acrescentaram callback/hotpatch. Isso reduz
  contaminação recente, mas não elimina ponte de keybind/anim/loops já existente.

## Próxima investigação recomendada sem reiniciar aqui

1. Preservar UE4SS.log e crash XML/dump e hashes binário/mod. Resolver offsets com PDB exatamente correspondente
   se já disponível; não baixar build e trocar loader em meio ao diagnóstico. Verificar versão/hash antes.
2. Buscar primeira emissão Registry no log e todos contextos anterior/posterior; marcar limites das sondas.
   Não presumir origem pelo último log Lua antes da mensagem.
3. Experimentos em cargas limpas distintas: seis soldados SEM seleção com animação; depois com seleção;
   repetir sem entrada real solicitando usuário não tocar (agente nunca injeta). Controle precisa durar
   pelo menos a janela que falhou111s e repetir; sobrevivência isolada não certifica.
4. Variante experimental apenas para isolamento mantém refs dos callbacks enfileirados até execução,
   sem mudar lógica; comparar registro+ExecInGameThread com loopframe/canal. Não tratar retenção Lua como
   correção antes de reproduzir erro/desaparecimento. Nunca reusar userdata ctx fora hook.
5. Instrumentação por contadores `_G` no começo/fim de callbacks preexistentes, não novos callbacks.
   Registro rotulado de enqueue/start/end keybind e updateanim start/end, engine logs mantidos.
   Logging por frame deve ser amostrado/contagem para não alterar timing excessivamente.
6. Não desligar contorno como solução final nem retornar aparência a discos; variantes sem clone só controle.
   Não remover proteções Steam/firewall, não chamar RPC nativo para gerar reprodução.

## Conclusão

Crash persiste após guards e otimizações. Há evidência forte de caminho UE4SS/Lua recorrente,
mas nenhum símbolo/reprodução identifica função culpada. Performance e estabilidade continuam gates
independentes. Não declarei lote estável; nenhum main.lua ou processo foi alterado por esta auditoria.


### Atualização: reduzir callbacks efêmeros sem alegar causa

MODLOG.md:1320 registra crash v0.2 com LoopAsync33ms+ExecuteInGameThread; migração para loops
GameThread persistentes. Fonte atual mantém ExecuteInGameThread no wrapper de teclas. Esse histórico
justifica experiência isolada com fila Lua drenada no loop persistente, mas situações não são equivalentes:
anterior era33ms contínuo, atual por evento de tecla, Registry sem origem confirmada.

Fila mínima proposta: onGame(f) retorna closure que só insere f numa tabela S; frame persistente drena
antes do earlyreturn de isLocalAuthority (F9/session e F10 devem funcionar no menu), por snapshot/troca
de fila para eventos novos não mutarem iteração; preserva pcall/log e ordem FIFO. Todo f é executado no
GameThread do loop existente, nenhum ExecuteInGameThread efêmero. Eventos normais continuam explicitamente
atrás do plain() que deve consultar modificadores no momento de execução como hoje.

Cuidados: sincronização entre callback keybind thread e Lua frame depende garantia UE4SS; não presumir
thread-safe só por ser tabela Lua. Limitar drenagem por quadro evita travamento se fonte de evento
inundar, mas NÃO descartar ordens silenciosamente. Não criar timer/novo callback para drenar; não alterar
seleção/roda polling. Executar teste offline FIFO/reentrância/erro antes e depois e gate input real usuário.
Primeiro medir se erro Registry aparece sem keypress: se sim, wrapper pode não explicar crash observado.

Consulta de *.pdb em D:/tools/ue4ss não retornou arquivo. Sem símbolo correspondente não mapeei offsets;
nenhum download ou relançamento feito.


## Entregas separadas (não aplicadas)

- anim_hook.before.lua/after.lua + test_anim_hook.py PASS: falha inicial RegisterHook mantém cache42
  mas hooked=false, retry seguinte registra exatamente1vez e chamadas seguintes não duplicam hook.
  Defeito independente, não causa atribuída do crash.
- queue_experiment.before.txt/after.txt + test_queue_experiment.py: dois blocos, wrapper e início do
  frame. CFG.KEYBIND_QUEUE=false preserva caminho anterior; true evita ExecuteInGameThread efêmero.
  Drena antes earlyreturn/menu, troca fila antes iterar (enqueues reentrantes ficam próximo quadro),
  pcall/log por evento conserva FIFO e continuidade após erro. Sem manipular RPC/pollingwheel.
  Teste não prova sincronização thread nativa, exige variante limpa isolada e input real usuário.
  Não integrar junto com anim_hook em experimento que queira inferir causa: um fator por carga.
