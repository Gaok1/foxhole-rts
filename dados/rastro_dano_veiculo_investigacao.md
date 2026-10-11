# Investigação offline: dano nativo de veículo (2026-10-10)

Escopo: leitura de evidências locais; nenhum comando ao jogo, nenhuma chamada RPC,
nenhuma edição de `main.lua`. Aplicados Como retomar, universal-modder (kb search
foxhole), reverse-engineering/oráculos, playbook Unreal e ponytail.

## O que existe de verdade

- `dados/esquema_combate_nativo.txt:70–77`: `/Script/War.SimVehicle.Health` é
  IntProperty; `OnRep_Health` não é RPC e não tem parâmetros. Isso autoriza investigar
  a notificação local, não pressupõe que a morte seja segura ou que seja o aplicador de dano.
- `D:/tools/foxhole-lab/data_dump.txt:930`: TruckW tem MaxHealth900, TankArmour0,
  MinorDamagePercent0.1875 e MajorDamagePercent≈0.7. São dados extraídos da tabela
  BPVehicleDynamicData, não fórmulas recriadas.
- `re-agent/props_SimDamageType.txt`: classe nativa SimDamageType tem Type,
  bCanPenetrateArmour, bApplyTankArmourMechanics, bApplyTankArmourAngleRangeBonuses,
  bCanDisableSubsystems, bDisableVehicleCollisionsIfKilledBy, bCanCauseLeaks etc.
  A identificação de um asset não prova seus valores em CDO nem comportamento.

### Correspondência de munição e DamageType comprovada no dump

Fonte `D:/tools/foxhole-lab/data_dump.txt`, seção BPAmmoDynamicData:

| Linha | Munição | Damage | DamageType |
|---|---|---:|---|
|1082|RifleAmmo|45|BPLightKineticDamageType_C|
|1083|MGAmmo|55|BPHeavyKineticDamageType_C|
|1086|ATRifleAmmo|150|BPAntiTankKineticDamageType_C|
|1091|SMGAmmo|27|BPLightKineticDamageType_C|
|1065|MortarAmmo|300|BPHighExplosiveDamageType_C|
|1074|HEGrenade|240|BPExplosiveDamageType_C|
|1077|RpgAmmo|550|BPExplosivePenetratingDamageType_C|

Assets correspondentes listados em `pak_files.txt:1739,1754,1762,1765,1773`.
Exemplo de caminho candidato verificável:
`/Game/Blueprints/DamageTypes/BPLightKineticDamageType.BPLightKineticDamageType_C`.
Usar a classe real obtida/carregada, nunca assumir que nome basta.

## Diferença para o mod atual

- `logi.hit` subtrai diretamente `tr.hp` e oculta o pawn quando chega a zero;
  NÃO consulta nem debita SimVehicle.Health. Explosão visual e contador de corte
  também são próprios. Esse é o sistema reinventado, a substituir após oracle.
- `logi.blast` faz distância e multiplicador fixo x2, igualmente próprios.
- O combate de personagens já usa GameplayStatics.ApplyDamage, porém passa nil
  em DamageType; isso é mecanismo Engine nativo com decisão/tiro simulado do mod,
  não comprova disparo nativo Foxhole nem contrato de mitigação veicular.
- ReceiveAnyDamage/ReceivePointDamage/ReceiveRadialDamage são callbacks refletidos:
  não chamar como se fossem substitutos de TakeDamage. AllFire sem parâmetros pode
  ser efeito/notificação; metadata sozinha não prova disparo físico.
- `ServerFire` e métodos Multicast/Server/Client estão fora do escopo pedido.

## Oracle mínimo para o agente responsável pelo laboratório

1. Ator TruckW isolado vivo, não destruindo, fora dos caminhões contábeis; registrar
   Health, bCanBeDamaged, classe, posição e autoridade. Nada de modificar `tr.hp`.
2. Confirmar schema GameplayStatics.ApplyDamage (preflight já preparado externamente),
   carregar a classe de DamageType e ler seu CDO Type/flags seguros.
3. Aplicar UM pulso baixo com tipo de munição correto, atirador e causer vivos.
   Registrar retorno, Health antes/depois, flag de destruição imediatamente e após
   pequeno atraso. Não exigir que diferença seja igual ao número recebido.
4. A/B Engine genérico versus LightKinetic versus HeavyKinetic pode separar contrato
   Foxhole de simples callback, sem envolver rede. Se não houver diferença de Health,
   seguir rastro nativo; não substituir por escrita de HP.
5. Só depois validar impacto/ponto/radial e morte/subsistemas. Não repetir zeroHP num
   ator com caches vivos. A segurança de OnRep_Health no personagem não transfere
   automaticamente ao veículo.

Faltam prova dinâmica de redução real, classificação/mitigação, impacto, destruição
nativa, integração contábil sem débito duplo e origem nativa do disparo. Este relatório
NÃO certifica nenhum deles.

## Localização para investigação nativa posterior

`re-agent/class_natives.txt:5895`: SimVehicle size0x12f0, StaticClass0x141248990.
OnRep_Health wrapper0x1412499a0. `native_tables.txt:2683` registra exec wrapper
0x141248100; não confundir os dois com TakeDamage virtual.
`strings_all.txt` tem `Vehicle DamageDebug` em0x36362b0 e formato de PenChance
em0x3636390. `DecompStrRefs.java` pode procurar essas strings e seus callers;
nenhuma decompilação existente pesquisada provou esse fluxo nesta investigação.
Manter toda decompilação fora do repositório conforme skill reverse-engineering.

## Avanço estático posterior: fluxo de dano localizado

Disassembly offline via ferramentas existentes `re-agent/pe.py` (PE/Capstone), sem
processo do jogo nem injeção. Evidência externa `D:/tools/foxhole-lab/damage-native-static.txt`.
Não é decompilação publicável nem autoriza chamadas nativas por endereço.

1. execApplyDamage0x142a52670 chama0x142550100, que constrói FDamageEvent e
   chama virtual do alvo no offset0x570 (slot174).
2. Constructor real SimVehicle0x140d5be40 instala vtable0x1436290f8;
   slot0x570 aponta0x140d96d80, candidato TakeDamage demonstrado pelo caller.
3. Este converte evento com0x140a104b0 e despacha a interface EMBUTIDA em
   this+0x8f8, vtable0x1435fb920, método+0x10→0x140d81a00. Não é UObject
   componente: não procurar FindAllOf pelo endereço.
4. Dispatch verifica Health(original this+0xb08)>0 e resolve tipo em0x140a257b0.
   A resolução exige CDO IsA SimDamageType, confirmado classdb.json para
   StaticClass0x1411c8be0. Dano com EngineDamageType genérico pode ser recusado.
5. Guard virtual original this+0x688→0x140d94b00→0x140dc0cb0→0x142781620.
   O último exige byteRole+0xf0>=3, bCanBeDamaged bit+0x5a&1, dmg diferente
   de zero e ponteiro World(vtable+0x150)+0x128 não nulo. Esse ponteiro é
   candidato AuthGameMode, ainda requer confirmação refletida; falta dele é
   hipótese concreta de rejeição, não impossibilidade de dano offline.
6. Guard War exige this+0x808==0 OU byteCDO+0x48!=0. Corresponde provavelmente
   a proteção de spawn e bypass, mas o significado exato não está provado.
   NÃO alterar offsets diretamente; confirmar nomes refletidos primeiro.

Próxima sonda segura é SOMENTE observação: Role/GetLocalRole/HasAuthority, World
e AuthGameMode refletidos, propriedade invulnerável refletida se existir, CDO real
SimDamageType e Type. Não repetir dezenas de ApplyDamage antes desses guards.

Oracle do responsável pelo lab: ApplyDamage45 com LightKinetic/HeavyKinetic/Explosive
retornou0, TruckW manteve900HP; ApplyRadialDamage75 retornoutrue, mas Health900.
Fontes `dados/rastro_dano_veiculo_nativo.txt` e `dados/rastro_dano_veiculo_radial.txt`.
Retorno true radial NÃO prova dano; Team255 permaneceu255, portanto não foi A/B
entre equipes. Nenhuma integração nativa entregue nesta investigação.

## Continuação offline: guards delimitados (2026-10-10)

- Oracle posterior confirmou Role3/HasAuthoritytrue/SimGameMode válido, TeamId0
  e, após12s, HP900/dano0. CDOs vivos Type1/2/7/3/8/18 confirmados, todos bypassfalse.
  Portanto autoridade e nome de DamageType já não explicam sozinhos o resultado.
- Setter UHT de `bBypassesSpawnInvulnerability` comprovado por parâmetro nativo
  em0x1436e9e50: SetBit0x1405efab0 faz `CDO+0x48=1`. Não é inferência por nome.
- Actor+0x808 NÃO é UProperty exposta no dump WarCharacter (10 propriedades).
  Constructor WarCharacter0x140d9f5b0 zera a flag. Setter local0x140dc3d80
  recebe duração float positiva, seta808=1, registra timerhandle800 com callback
  0x140dac120; callback zera808 e limpa timer. O único caller direto localizado
  está em helper de spawn0x140b95100, call0x140b951fb. Não há prova de flag ativa
  no truck12s depois nem autorização para alterar offsets/manualmente cancelar timer.
- `DamageAttributes` constructor0x140a104b0 copia Damage recebido direto em+0;
  guarda FDamageEvent em+0x20. NÃO possui ramo de ID0 que zere dano. Resolvedor
  0x140a257b0 lê DamageEvent+8 (DamageTypeClass), CDO e IsA SimDamageType;
  também serve ao evento genérico. Não declarar genérico intrinsecamente incapaz.
- **Guard distinto ainda não observado:** damageinterface0x140d81ae0 chama
  `world → SimGameMode → WarGameInstance → ServerSettings`; retorno nulo em
  0x140d81afb salta à saída zero0x140d82719 ANTES de mitigação. Contexto é
  resolvido por0x14113e570→0x141192be0→0x140b61090→0x1411409c0.
  O último lê `WarGameInstance+0x3d0`; extração UHT comprova nome `ServerSettings`
  ObjectProperty e classe ServerSettings. SimGameMode válido não prova essa
  propriedade não nula. Evidência externa `damage-gameinstance-props.txt:14`.
- Isso é descoberta estática de requisito de contexto local, **não proposta de
  implementar servidor, RPC, configurar rede ou perseguir sistemas online**.
  Limite desta investigação: observar propriedade JÁ existente, sem fabricar
  objeto/configuração para passar guard. Se nula, causa concreta da recusa;
  a decisão de reaproveitamento nativo exige respeitar escopo offline do usuário.

Próximo mínimo oracle recomendado: registrar GameInstance classe e ServerSettings
IsValid, sem aplicar dano. Se válido, rastrear resultado de guard/profiler local
antes de um novo oracle com impacto. Nenhum PointDamage com HitInfo inventado.

Disassembly/extrações ficam externos: `war808-refs.txt`, `damage-waractor-props.txt`,
`damage-gameinstance-props.txt` e `damage-native-static.txt`. Nenhum processo do jogo,
canal, offset write, RPC ou alteração de `main.lua` nesta continuação.
