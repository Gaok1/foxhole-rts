# Investigação de disparo nativo — 2026-10-10

Somente estudo offline e metadados; não alterou main.lua, não chamou RPC, não manipulou inventário nem controlou o jogo.

## Evidência existente e descoberta
- `dados/esquema_combate_nativo.txt`: `Character_C.PlayerFire` é ParticleSystemComponent, não arma. `SimCharacter.ServerSyncLastWeaponInvoke` é caminho com nome RPC, não solução local aprovada.
- `D:/tools/foxhole-lab/re-agent/class_natives.txt` e `props_HitScanWeaponComponent.txt`: classe nativa **HitScanWeaponComponent** (SC 1411e0fd0); também existem ItemComponent, ProjectileItemComponent, HeavyMachineGunItemComponent. Rifle não exige necessariamente actor de projétil: existe pipeline hitscan.
- Campos de HitScan: ShotSoundCue/MuzzleFlashPS/WeaponFireFXClass, SimulatedHitNotify, BurstFiringRate. `dados/esquema_classes_disparo.txt` recém produzido pelo agente raiz confirma classe/HitNotify na reflexão viva.
- Dump antigo + leitura estática Capstone do executável do laboratório: vtable candidata HitScan `1434fd998`. Wrapper refletido `1411e2d50` (ServerStartInvoke) valida slot508 e chama slot510=`140a65fa0`; este encaminha a slot518=`140a68dd0`. Isto é descoberta estática, **não autorização para chamar RPC ou offset bruto**.
- Decompilação já disponível `D:/tools/foxhole-lab/re-agent/d5/140a68dd0.c`: verifica proprietário SimCharacter, encontra entrada associada ao componente via `140a55860`, exige campo short+1A não zero, rejeita timer ativo, chama atividade, agenda burst quando cabível e chama `140a691f0`.
- `.../d7/140a691f0.c`: verifica proprietário vivo/estado; decrementa aquele short; obtém parâmetros da arma; constrói dados do tiro em `1409d5ca0`; chama `1409e9860`; converte resultado com `140a5cb90` e preenche SimulatedHitNotify+9A8; invoca efeitos `140a69dd0` em uma condição de modo. Chamada subsequente `140aec820` muda estado do personagem (sem nome semântico provado).
- `.../d7/140a55860.c` encontra entrada cujo ponteiro do componente coincide no armazenamento do owner: não basta criar componente sem vínculo válido. Não implementar inventário à mão.

## O que NÃO foi provado
- Nome/contrato C++ exato de `140a68dd0` e `140a691f0`; decompilador mostra argumentos parcialmente e pode perder registradores.
- Contexto que originalmente constrói os componentes, define owner/equip/muzzle e fornece WeaponInvoke; objeto vivo equipado com munição.
- `1409e9860` como dano final ou somente trace: segue investigação, não atribuir nome ainda. Nenhuma prova dinâmica de disparo→impacto→HP veículo obtida nesta investigação.
- OnRep_SimulatedHitNotify não é prova de dano: poderia apenas tocar efeito. TotalShotsFired byte não é contagem dinâmica validada.
- GhidraMCP127.0.0.1:8089 recusou conexão; nenhuma GUI iniciada. Projeto/decompilação antigos foram reutilizados, não reaberto.

## Próximo oráculo mínimo
Rastrear chamadas locais e contexto legítimo do componente antes de uma tentativa. Correlacionar um disparo autorizado no laboratório offline com consumo nativo, HitNotify e saúde de veículo; comparar alvo livre/ocluído. Não anunciar integração enquanto houver apenas nome/reflexão/decompilação.

Sonda auxiliar externa `D:/tools/foxhole-lab/t_disparo_classes_metadata.lua` fez apenas FindAllOf(Class/ScriptStruct) filtrado e retornou zero na execução do agente raiz; enumeração inadequada, **não ausência de classes**. StaticFindObject pelo nome comprovado funcionou na sonda do agente raiz.

## Continuação: trace/ponte
- `.../d8/1409e9860.c` inicializa saída com padrão HitResult (Time=1), resolve world, executa consultas (`1409f4e30` e `142408380`) e devolve flag/resultado. **Evidência estática sugere consulta/trace, não aplicação direta de dano.** Seguir o consumidor do HitResult antes de declarar dano provado.
- `.../d8/1409d5ca0.c` preenche estrutura de consulta e chama `1409e1cf0` para geometria; assinatura decompilada tem 12 parâmetros apesar de chamada anterior resumida em4. Isto demonstra que assinaturas inferidas pelo decompilador não bastam para invoke seguro.
- Sonda somente instancia/owner preparada em `D:/tools/foxhole-lab/t_disparo_instancias_owner.lua`: FindAllOf(HitScanWeaponComponent), nome e GetOwner via pcall; não lê inventário/struct instance nem dispara. Agente raiz é único dono do canal.
- Pesquisa pontual não achou helper Frida em foxhole-lab nem import disponível (`PYTHONPATH=D:/tools/pylibs`, find_spec(frida)=None). UE4SS Mods presentes são Lua usuais; não encontrada ponte C++ específica para invoke local. `D:/tools/ue4ss` tem arquivos ZIP, não é ponte instalada. Nenhuma instalação iniciada.

## Resultado vivo do agente raiz / encerramento
`dados/rastro_instancias_armas_nativas.txt` confirmou zero instâncias de HitScanWeaponComponent/ProjectileItemComponent/HMG neste HomeRegionW. Classes existem, mas não há objeto de arma armado vivo para observar nesta cena. Não executar sonda owner redundante. Próximo passo continua localizar contexto nativo legítimo que cria/associa componente ao pawn, sem perseguir inventário/RPC. Não integrar disparo por offsets até reconstruir ABI e comprovar fluxo dinâmico completo. A análise de 1409e9860 sugere consultas; argumentos extras mal inferidos tornam especialmente prematuro concluir que ela aplique ou não dano.

## Avanço estático: aplicação de impacto localizada (segunda investigação)

Ghidra headless existente rodou `-readOnly -noanalysis`, sem GUI/instalação; duas execuções concluíram com exit0. Decomp mantida exclusivamente em `D:/tools/foxhole-lab/disparo-decomp`, logs disparo-headless[2].log.

### Correção de escopo — NÃO generalizar rifle
A função autoritativa encontrada é **140a68710 de HeavyMachineGunItemComponent**, pointer1434fcb40 na vtable1434fc608+538. Não é a140a691f0 de HitScanWeaponComponent. A classe HMG também faz hitscan, mas isso não prova integração de rifles ou de toda arma.

### Cadeia nativa estática
-140a68710 exige owner SimCharacter, não morto/estado apto e dois guards de uma interface embutida; obtém orientação/muzzle/atributos do componente e constrói consulta1409d5ca0.
-1409e9860 produz HitResult; o ramo seguinte exige **Role do owner=3 (Authority)** e HitActor válido. Helper142405420 lê owner+F0 diretamente, **não GetNetMode**. Não confundir Role3 com NetMode3.
- O ramo obtém dados via virtuais4F8 e528, combina atributos e chama **1409dcd30** em140a68c68.
-1409dcd30 calcula variação/falloff/contexto e resolve interface **DamageableActor**, StaticClass1411c8220 (nome extraído da própria registration table). Para alvo com interface, constrói atributos com140a104b0 e chama a interfacevirtual+10 em1409dd31a.
- Alvo sem essa interface vai por fallback **142550460** em1409dd33c: monta evento de point damage e chama **TakeDamage virtual570** em142550588. Este slot é o mesmo apontado pelo estudo de SimVehicle; no caminhão nativo o caminho com interface evita passar primeiro por GenericApplyDamage.
- Em seguida a arma consome entrada de munição, grava HitNotify incluindo dano retornado e toca efeitos. Animar/OnRepHitNotify isolado não substitui aplicação nativa.

### ABI / contratos ainda não seguros
-1409dcd30 tem argumentos além dos quatro registradores. No caller: RCX=owner pawn; RDX=owner+258 (candidato controller, sem nova prova refletida); R8D=inteiro combinado de atributos; XMM3=float combinado. Stack+20 contém float convertido de atributo; +28 ponteiro classe/tipo; +30 HitResult; +38 contexto auxiliar; +40 configuração adicional. **Não executar esta assinatura por aproximação.**
- Decomp infere9args mas declara param4 undefined8 apesar de XMM3 float no caller; registro/stack prevalecem sobre protótipo automático.
-140a5cb90 é conversão HitResult→HitNotify (Damage vindo do parâmetro float), não execução de dano.
- Schema vivo existente confirma CharacterInvokeInfo: ImpactPoint, RenderTimestamp, MuzzleOffset, AimYawPitch e flags bHasMuzzleOffset/bHasAimYawPitch. DamageAttributes não foi enumerada naquele schema; nome por si não é layout/ABI comprovado.
- Ainda falta caminho autoritativo equivalente de HitScanWeaponComponent/rifle e objeto armado nativo legítimo. Não fabricar inventário nem chamar RPC para preencher lacuna. Próxima prova inclui contexto de DamageableActor/ServerSettings identificado em paralelo pelo agente de dano, depois oráculo vivo devidamente isolado.

## Rifle específico — entrada local encontrada, consumidor ainda em estudo (2026-10-11)
- Constructor real HitScanWeaponComponent140a43a30 instala vtable primária1434fd998 e **interface embutida+ B0, vtable1434fdef8**. Não é UObject separado.
- Interfacevirtual10→140a60640 valida ownerSimCharacter; chama virtualprimária518→140a68dd0 local; após sucesso chama1411e13c0, wrapperProcessEvent. Portanto **não usar essa entrada como invoke puramente local**: envolve evento com encaminhamento potencialRPC. Nenhuma chamada executada.
- VirtualinterfaceE0→140a6b860 produz estrutura de parâmetros do tiro: consulta dados da arma, observa munição de entrada associada e preenche owner/origem/alvo; termina1409ff620. Isso não é aplicação de dano provada.
- Virtuais primárias4D0/4D8/4E0/488 tratam encaminhamento de setup/dados, retorno de atributos, escrita em entrada de munição e guardburst; nada nelas provou impacto→dano. Nomes semânticos C++ completos ainda não conhecidos.
- Decompilação headless readOnly/noanalysis dos métodos terminou, resultados externos em D:/tools/foxhole-lab/rifle-decomp (rifle-headless[2].log). Sem mudanças no projeto/main/settings nem controle do jogo.
- `1409dc010` (helper nativo de dano em área/contexto) tem caller140a764a3. Consumidor local próximo às armas em investigação; não rotular rifle antes de vínculo de classe/owner provado.

### Resultado do consumidor / limite de prova do rifle
- Terceiro job headless terminal **exit0**, logrifle-headless3.log e três funções externas gravadas. Nenhum processo nativo do jogo aberto.
-1409ff620 completa parâmetros de mira/cone/origem e consulta contexto do personagem. Não mostrou aplicação de dano ao alvo; ser chamada do rifle não torna todo helper posterior automaticamente disparo autoritativo.
- Candidatecaller140a764a3 pertence à função140a76290. Seu ramo exigeRoleAuthority e dois valores positivos do contexto, resolve tipo de dano e chama1409dc010 (helper de área/contexto). **Não foi encontrado vínculo de vtable/owner/classe HitScanWeaponComponent**; portanto esse candidato NÃO é evidência de rifle causando dano.
-1409dc010 prepara consultas e encaminha1409dc270 com múltiplos parâmetros de contexto; pode servir outras armas/explosões. Não substituir rifle por aplicação radial para declarar sucesso.
- A entrada local de HitScan140a60640 permanece acoplada ao wrapperProcessEvent1411e13c0 depois da validação local. Não executada, nenhuma perseguição de RPC/inventário.
- **Rifle nativo offline ainda não integrado nem demonstrado.** Prova existente é estrutura/entry/contexto/consumo/trace/efeito; dano estático completo certificado apenas no ramoHMG descrito acima. Precisam ser identificados executor local autoritativo e criação legítima do componente/equip/owner, depois oráculo dinâmico. Steam ausente e cena sem arma real impedem oráculo vivo agora, não tornam o resultado negativo uma prova de impossibilidade.

## Retomada após gate de dano nativo PASS — sem extrapolar para rifle
- Raiz comprovou aplicação nativa com configuração local válida. Isso resolve guard do contexto de dano, **não prova disparo autoritativo de rifle**.
- Comparação precisa: HitScanvirtual510=140a65fa0→virtual518=140a68dd0→140a691f0; HMGvirtual510=140a65fc0→virtual540 (não o mesmo caminho), virtual518 é retorno trivial. Não intercambiar classes/slots.
- HitScan herda ItemComponent: helperSuper140937f50 é thunk paraStaticClass1411e5cc0, confirmado no executável. Registro nativo contém somente OnRep_IsEquipped, OnRep_SimulatedHitNotify, ServerStartInvoke; ItemComponent contém somente ClientSyncAmmo. **Nenhum executor de tiro puramente local refletido nesses registros**. Esta evidência restringe estas classes, não todo jogo.
- Cinco funções extras decompiladas em jobrifle-headless4.log, terminalexit0. CallersStaticClass140a55fc0/140a56260 registram replicação de bIsEquipped/SimulatedHitNotify: NÃO são fábrica/attach/equip local.140a27ed0 encontra equippedcomponent e escreveHitNotify; não encontrou aplicação de dano ao alvo nem validação de spawn/equip.
-140a6b470 é caminho alternativo de construção de query (encaminha140a905c0 ou140a6b860), não demonstra execução de impacto.1409f3520 processa geometria/contexto de mira/query, não mostrou ligação direta aos helpersDamageAttributes/TakeDamage buscados.
- **Owner/equip sem inventário não provado**: GetOwner/ctor/interface não bastam; funções atuais exigem vínculo a entrada nativa associada ao componente. Não escrever arrays/munição por offset para fabricar esse estado.
- Próxima investigação deve ligar a atividade de disparo nativa/pedido de tiro à fase autoritativa que consome dados do rifle (pode ser pipeline separado do trace visual). Até lá, não trocar DPSinventado por ApplyDamage por segundo e chamar isso de arma real; nem usar RPC ou repetir sondas já negativas.

## Fechamento do consumer visual e contrato pendente (2026-10-11)
- Jobs rifle-headless5 e rifle-headless6 terminaram exit0, readOnly/noanalysis. Decomp protegida permanece externa em D:/tools/foxhole-lab/rifle-decomp; nenhum endereço executado.
- Slot primário510=140a65fa0 tem apenas chamada indireta ao518 e retorno: não contém aplicação de dano nem encaminhamentoRPC próprio.518=140a68dd0 inicia ActivityFiring3, exige entrada associada com munição e encaminha140a691f0. Não há dano oculto distinto em510.
- Activity start140b10150→140b0fc30 aciona transições de estado/timer e funções de apresentação condicionadas ao cliente. SimCharacter update140b110c0 obtém query da interface da arma+E0 e grava cache+1534; os consumidores examinados desse cache não demonstraram DamageableActor. Isso é limite de pesquisa, não ausência universal de caminho autoritativo.
- WeaponFireFX: helper1409fe9b0 cria ator de efeito, orienta movimento e emite som/partícula. OnProjectileStop refletido14127c5a0 encaminha140dec880; este consumer trata overlap/ignoreactors, clone de efeito em personagem contextual, parada de componentes e término de vida. Não houve chamada direta aos helpers de dano conhecidos nesse consumer. Não usar essa classe como substituta de projétil nativo autoritativo.
- SimCharacter local140b0b9f0 copia CharacterInvokeInfo de40bytes, atualiza aim/timestamp e chama interface+250 quando necessário. Não demonstrou impacto→TakeDamage.
- Pré-condições observadas para eventual ponte local: objeto HitScan construído legitimamente (inclui interface embutida+B0); owner SimCharacter vivo e estado apto; atributos/configuração nativos resolvidos; associação real componente↔entrada no holder e munição; CharacterInvokeInfo finito/origem/mira válidos; estado/timers de atividade e contexto de dano autoritativo. GetOwner/SpawnComponent não estabelecem esses contratos por si.
- A entrada interface+10=140a60640 segue518 com wrapperProcessEvent1411e13c0. Não executá-la como entrada offline pura. Não escrever holder/munição por offset para fabricar equip.
- **Integração rifle continua pendente:** dano nativo genérico passou no oráculo da raiz, mas não é prova de rifle. Falta identificar executor autoritativo local e init/equip legítimo fora inventário; ABI exata e ponte só depois disso. HMG continua o único ramo hitscan cujo trace→DamageableActor foi ligado estaticamente nesta investigação. Nenhuma mudança em main.lua ou contexto vivo.

## Retomada — mapa completo de referências diretas e callbacks (11/10)

Quatro jobs headless readOnly/noanalysis concluíram exit0. Script de referências
sem corte de quantidade, externo ListNativeRefs.java. Decomp protegida só em
D:/tools/foxhole-lab/rifle-authority-decomp; logs rifle-{native-refs-all,
authority-consumers,authority-timers,authority-mode-effects}.log.

- No projeto analisado, 1409dcd30 tem dois callers diretos: 1409a71f0 e
  140a68710(HMG), além de duas referências DATA. Não surgiu caller direto do
  rifle140a691f0. Isso NÃO enumera chamadas indiretas nem prova ausência universal.
- 1409e9860 tem oito callers diretos: 140a68710,140a67e40,140a691f0,140a8cd40,
  140d06c80,140d007c0,140d50940,140d51250; três referências DATA. Os mesmos oito
  usam1409d5ca0, com uma referência DATA adicional. Evitar investigar só os
  primeiros seis retornados por um helper de decompilação limitada.
- 140d06c80 identifica consulta FighterWeaponTrace; 140d007c0 usa AirTargetingTrace.
  Portanto não promover esses consumidores de geometria a executor do rifle.
- 140d51250 identifica HitScanMount; não confundir mount com HitScanWeaponComponent.
  140a8cd40 usa associação140a55860, HitNotify, WeaponFireFX e estado, sem ligação
  direta aos helpers de dano conhecidos nesta função.
- 140a67e40 e140d50940 registram callbacks140a4ae70/140d39eb0 após comparação
  de142407030 com3. Seguidos os callbacks: encaminham140a6d600/140d57430,
  que gerenciam objeto criado por142575160 e posição142477180; não chamam os
  helpers de dano conhecidos nesses corpos. Nomes C++ desses helpers ainda não
  vinculados; tratar como apresentação candidata, não impacto autoritativo.
- **Guard distinto:**142407030 resolve contexto do owner/world e encaminha
  1426b9a80, cujo ramo devolve3 ou1/2 conforme virtual350/global. Não é a leitura
  de Role em owner+F0 feita por142405420. Não chamar timer de "Authority3" só pelo
  literal3; interpretação como NetMode/presentation é consistente, sem nova prova
  dinâmica. Nenhum guard alterado nem endereço chamado.

Próximo recorte: localizar produtor/consumidor autoritativo dos dados de tiro além
do trace/HitNotify visual e vincular classe/owner/init reais. Não repetir oráculos
de FX, não executar offsets/ABI inferidos, não buscar RPC/inventário e não usar
ApplyDamage por tempo como substituto. Laboratório continuou fechado.
