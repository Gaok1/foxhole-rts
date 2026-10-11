# Contexto local nativo do dano — evidências estáticas

2026-10-11. Usuário autorizou reutilizar configuração nativa LOCAL, sem rede.
Somente leitura offline; sem jogo/canal, RPC, inventário, escrita de offset ou edição
de main.lua. Steam ausente impede oracle vivo; não iniciar/login pelo usuário.

## Objeto e inicialização

`/Script/War.ServerSettings` é um **SaveGame passivo**, não serviço de rede.
Classe nativa size0x7f8, StaticClass0x14121e6b0; super thunk0x1406f1560 aponta
Engine.SaveGame0x142b1e920. Wrapperctor0x14121f380 chama0x14099d6b0.
Constructor inicializa campos e chama constructor WarTweakables0x14099bff0 em+0x118.
WarTweakables: struct0x5a0,340propriedades; o exportador antigo limitava80 e omitira
este schema, não ausência no cliente.

Auditoria do corpo0x14099d6b0–0x14099da89: chamadas baseSaveGame/UObject,
FText vazio/limpeza de referência e data/calendário NextWarTime; nenhuma chamada
RPC/socket/request/servidor. Constructor WarTweakables termina0x14099cc23 e não
tem CALL algum: escreve defaults compilados e inicializa containers.
WarServerSettings não tem UFunctions próprias. Não há necessidade comprovada
de chamar initializer de GameInstance ou rede para inicializar esses defaults.
Isto demonstra constructor passivo; comportamento global posterior à associação
em GI precisa ser observado, não presumido.

## Campos efetivamente consumidos no dano SimVehicle

Damageinterface0x140d81a00 obtém ponteiro WarTweakables via0x14113e570.
Decomp externa `rifle-decomp/140d81a00.c`, confirmado com disassembly:

|Campo WarTweakables|Offset|Default nativo|Uso estático|
|---|---|---|---|
|MinTankArmourMultiplier|0x218|1.0|limite inferior de desgaste de blindagem|
|BallisticPenetrationMaxDistance|0x29c|4000.0|distância de penetração quando não há override|
|BallisticPenetrationDistanceExponent|0x2a0|1.5|expoente do fator de distância|
|BallisticPenetrationMaxAngleBonus|0x2a4|≈0.4|bônus de ângulo|
|BallisticPenetrationMaxRangeBonus|0x2a8|≈0.4|bônus de alcance|

Defaults comprovados em0x14099c421/55b/565/56f/579 (bits3f800000,
457a0000,3fc00000,3ecccccd,3ecccccd). NÃO copiar esses números para uma fórmula
Lua: são evidência de que criar instância nativa entrega os valores.
ServerSettings.SpawnInvulnerabilityTime também tem default nativo3.0 (+f4).
Nenhum custo/economia próprio aparece nessa lista do cálculo de impacto.

## Perfil de dano já no cliente

Getter0x1408f8e80 carrega e guarda classe
`/Game/Blueprints/Data/BPDamageProfiles.BPDamageProfiles_C`, devolve CDO.
DamageProfiles.DataTable é ObjectProperty+0x218, aponta ao perfil tabelado;
DTDamageProfiles e BPDamageProfiles estão no pak, linhas1785/1786.
`DamageProfile` struct0x58 tem LightVehicle(+8), Tier1Tank(+c), Tier2Tank(+10),
estruturas/navios etc. Lookup0x1409066d0 escolhe row pelo enumDamageType e
cache0x140912da0; aplicação0x140914060 escolhe coluna ArmourType.
Os valores das células AINDA não foram exportados/validados; presença dos assets
e consumo nativo estão comprovados, valores não devem ser adivinhados.

Ordem de guards observada: Health>0 → CDO SimDamageType válido → actor autoridade/
bCanBeDamaged/mundo+proteção temporária → regra de friendly team/contexto →
ServerSettings/WarTweakables não nulo → aplicação Engine/callbacks → perfil
DamageType/ArmourType → blindagem/penetração/subsistemas → débito de Health/morte.
ServerSettings não nulo não certifica sozinho os demais contratos.

## Oracle futuro mínimo (não executado)

1. Steam já aberto/logado pelo usuário; lab exclusivamente offline.
2. Confirmar GI.ServerSettings continua nulo; conservar valor original exato.
3. Construir **instância própria** da classe nativa com OuterGI (não CDO), pelo
   StaticConstructObject nativo suportado pela versão UE4SS; ler classe/IsValid,
   campos acima e SpawnInvulnerabilityTime. Gate: defaults íntegros e não NaN.
4. Associar temporariamente GI.ServerSettings à instância. Não alterar campos de
   rede, CDO, bypass de spawn, fórmulas, nem chamar initializer online.
5. Truck exclusivo com HP900/contexto correto, uma aplicação de dano tipo real;
   ler HP antes/depois e retorno. Não escrever HP ou creditar destruição manualmente.
6. Garantir restauração do valor original GI.ServerSettings em sucesso OU erro,
   remover somente o ator exclusivo e referências locais; conferir restauração.

Não implementado no mod e nenhum resultado vivo certificado. Fontes protegidas
fora do repo: `damage-settings-native-ctor.txt`, `damage-settings-props.txt`,
`damage-tweakables-props.txt`, `damage-profile-props.txt`, `rifle-decomp/140d81a00.c`,
todos em `D:/tools/foxhole-lab/`. Relatório anterior conserva diagnóstico dos guards.

## Crash do primeiro oracle: ramo debug e lifetime pendente

PID24924: gate vivo de constructor/nested structs passou. Oracle seguinte caiu
nativamente; buffer perdido impede atribuir com certeza o último comando concluído.
Stack CrashContext `UE4CC-Windows-608B38A24B507F2999BD40955C73B6EF_0000`:
b5d5bc → b64277 → d613df → d82713 → d96e1c →2550198→2a527dc.

Ramo estático identificado: fim do dano0x140d81a00 chama lambda0x140d61310;
ela lê `WarTweakables.bEnableDamageDebug` e chama helperSimGameMode0x140b68780
→0x140b641f0→lookup0x140b5d530. Lookup procura chave string num TMap privado
ServerSettings+0x80. Crash0x140b5d5bc lê elemento de mapa, não efeito físico/RPC.
UHT setter141272610 comprova flagDebug+0x428; constructor14099c8b0 a defineTRUE.
Não desativar debug para esconder a causa; não alterar mapa privado/offsets.

Constructor inicializa TMap vazio coerente: this+0x80 ponteiro0, +0x88 num/cap0,
+0xa0/+0xa8 zero, +0xb0 freeindex=-1, +0xb4 freecount0, +0xc0 hashptr0,
+0xc8 hashsize0. Lookup compara map+8 contra map+0x34; num0==freecount0 sai
ANTES da busca. Constructor fresco não explica sozinho um índice enorme.

Leitura do minidump padrão, sem executar processo: R14map=0x2552cacc0a0,
RCXelems=0x25509a002d8, RBXíndice=0x2b84f1c0. RDI=0x1051daa80 e acesso
inválido0x25d328d56e0. O heap do mapa não está capturado, portanto NÃO prova
causa exata; mostra dados/índice incoerentes com mapa vazio inicial.

Hipótese forte de lifetime: sonda criou settings, manteve apenas `_G` Lua enquanto
GI.ServerSettings permanecia nulo por12s, depois associou. Lua não é raiz do GC de
UObject, armadilha já documentada para MID; IsValid pode continuartrue ou endereço
ser reaproveitado. Nenhuma classe/endereço foi conferida imediatamente antes da
associação. Isso é hipótese, não resultado confirmado nem prova de corrupção nativa.

Próximo oracle mínimo preparado pelo raiz: spawn SOMENTE truck → esperar12s →
baseline semsettings → criar instânciaNOVA no MESMO chunk do ensaio configurado →
conferir classe/defaults/endereço e associar IMEDIATAMENTE à UPROPERTYGI → uma
chamada → restauraroriginal em sucesso/erro e removerator exclusivo. Pré-carregar
assets antes de criarsettings. Não manter settings solta Lua_G durante espera.
Checkpoints antes/depois de cada fase, pois pcall NÃO captura crash nativo.
Nada disso foi executado nesta investigação offline; sem claim de dano aprovado.
