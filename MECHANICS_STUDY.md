# Estudo das mecânicas do Foxhole (fase 2 do roteiro)

Fonte: o próprio cliente do laboratório (2026-10-09). Nada aqui vem do servidor nem da internet.

## Combate nativo — contexto observado em 10/10

O ramo de dano de SimVehicle exige `WarGameInstance.ServerSettings` existente. Em
HomeRegionW offline essa referência foi nula, embora Role3/HasAuthority e SimGameMode
fossem válidos; a guarda nativa explica retorno0/HP900 nos oráculos anteriores.
Não concluir impossibilidade de dano nativo nem fabricar servidor/alterar guard.
Preflight reproduzível: `tools/preflight_native_damage.lua` (somente leitura).
CDOs: `tools/export_damage_types.lua`; ambos executados via canal de comandos.
Evidência: `data/trace_context_damage_native.txt`, `data/trace_export_types_damage.txt`.

Fluxo autoritativo estático encontrado é da **HeavyMachineGunItemComponent**, não de
todas as armas: trace -> autoridade -> DamageAttributes -> DamageableActor -> dano.
Rifle/ABI/instância equipada/prova dinâmica ainda faltam. Relatórios em
`data/trace_firing_investigation.md` e `data/trace_damage_vehicle_investigation.md`.

## Como os dados foram lidos
- **Lista de arquivos:** o índice do `War-WindowsNoEditor.pak` (versão 8) não é criptografado; os 24.352 caminhos
  `.uasset/.umap` estão em `data/pak_files.txt` (extraídos por expressão regular sobre o índice).
- **Tabelas:** `LoadAsset("/Game/Blueprints/Data/<tabela>.<tabela>")` e `DataTable:ForEachRow` pelo canal de
  comandos. Colunas pela `RowStruct` (`ForEachProperty`); receitas usam `ProductionResource {ItemCodeName, Quantity}`;
  custos de estruturas/veículos usam `ResourceAmounts {Resource, OtherResources[]}`, com elementos
  `CodeNameSmallQuantity {CodeName, Quantity}`. Resultado em `data/game_costs.txt`.
  **Correção do lote 16:** a sonda antiga confundia esses schemas e engolia o erro, deixando custos vazios.
  Exportador reproduzível `tools/export_costs.lua`, teste offline `tools/test_costs.py`; erro agora interrompe,
  não vira custo zero. As receitas de caixa não mudaram.
- **Cuidado:** um dump genérico (ler toda propriedade de toda linha) derrubou o jogo na tabela
  `BPAirDynamicData`. Ler só colunas conhecidas e com tipo simples.

## O que o cliente tem
- **Mapas:** as 54 regiões do mundo (`Maps/Master/*Hex.umap`: Callahan's Passage, Deadlands, Westgate...) e as
  duas regiões de casa (`HomeRegionW`, `HomeRegionC`).
- **Veículos:** caminhões (carga, recurso, combustível), caminhão-plataforma, colheitadeira, ambulância, ônibus,
  blindados, tanques leve/médio/de batalha/super, meia-lagarta, artilharia de campo, motos e bicicletas, trens
  (locomotiva, vagões de carga, hospital, artilharia), barcaça, cargueiro, lancha, canhoneiras, navios grandes,
  navio de desembarque, submarino/minador e aviões (caça, bombardeiro, mergulho, torpedeiro, paraquedista).
- **Estruturas:** refinarias, fábricas (armas leves, munição, aviões, veículos), minas, campos de recurso,
  depósito, porto, hospital, base avançada, guarnições, bunkers, trincheiras, arame, sacos de areia.

## Nomes internos de material
| Interno | No jogo |
|---|---|
| Metal | Sucata (salvage) |
| Cloth | Material básico (bmat) |
| Wood | Material refinado (rmat) |
| Explosive / HeavyExplosive | Pó explosivo / pó explosivo pesado |
| Components, Sulfur | Componentes, enxofre |

## Custos de caixa (fábrica)
| Caixa | Custo | Quantidade | Tempo (s) |
|---|---|---|---|
| Fuzil (RifleW) | 100 bmat | 20 | 70 |
| Munição de fuzil | 80 bmat | 40 | 50 |
| Metralhadora (MGW) | 25 rmat | 5 | 100 |
| Munição de MG | 100 bmat | 20 | 70 |
| Granada (GrenadeW) | 100 bmat + 40 explosivo | 20 | 100 |
| Bandagem | 80 bmat | 50 | 40 |
| Kit de primeiros socorros | 60 bmat | 10 | 35 |
| Suprimento de soldado (camisas) | 80 bmat | 10 | 80 |
| Morteiro / munição de morteiro | 100 bmat + 25 rmat / 60 bmat + 70 explosivo | 5 / 15 | 50 / 100 |
| Arame / sacos de areia (materiais) | 15 bmat | 5 | 15 |
| Suprimento de bunker | 75 bmat | 150 | 190 |

Munição (`BPAmmoDynamicData`): fuzil 45 de dano, MG 55, SMG 27, granada 200 (raio 5,5 m), morteiro 300 (5 m),
artilharia leve 400 (11 m).

## Custos de construção conferidos (lote 16)
Fábrica urbana (`Factory`): 400 bmat, 2000 HP; refinaria (`Refinery`): 400 bmat, 2700 HP;
caminhão Warden (`TruckW`): 100 bmat, 900 HP. Facilities têm linhas/custos próprios na tabela;
não herdam o custo nem as receitas da fábrica urbana. Esses números são do cliente instalado.
O custo não demonstra, sozinho, um fluxo de construção funcional offline.

## Veículos (`BPVehicleDynamicData`)
| Veículo | Vida | Combustível | Consumo/s | Carga |
|---|---|---|---|---|
| Caminhão (TruckW) | 900 | 100 | 0,025 | 15 |
| Caminhão de recurso | 1000 | 120 | 0,038 | 20 |
| Colheitadeira | 1250 | 200 | 0,150 | 15 |
| Ambulância | 750 | 100 | 0,025 | 9 |
| Blindado (ArmoredCarW) | 1150 | 150 | 0,050 | 1 |
| Tanque leve / médio | 1950 / 3100 | 300 / 325 | 0,19 / 0,23 | 1 / 3 |

## Bancada de logística: HomeRegionW (não é região da guerra)
HomeRegionW é a ilha de treinamento/embarque dos Wardens. Os atores abaixo servem ao protótipo;
suas coordenadas, quantidade e acesso por estrada não representam outras regiões. Os mapas `*Hex`
precisam de inventário ao carregar; a presença dos arquivos no cliente não garante os atores de uma guerra offline.
Contagem de atores no mapa de teste (coordenadas aproximadas, cm):
- Campos: sucata ×3 (22525, −34725), componentes (−5468, 9810), enxofre (−5067, 14459), petróleo (3419, −37440);
  minas de sucata/componente/enxofre perto de (−7500, 12000).
- Refinarias `BPRefinery_C` ×2 (10785, 11096); fábrica `BPFactory_C` (15643, 11428); base avançada
  (19557, 12293); fábrica de veículos (12484, −20098); instalações (refinaria, transferência) perto de (10000, −37500).
- Caminhões `BPTruckW_C` ×7 e plataforma ×3 estacionados.
- A base do mod (onde o comandante nasce) fica perto de (10789, −24935): o mapa tem cerca de 500 × 300 m.

## Próximo passo: logística v1 (lote 12)
Cadeia do mod, offline e com sistemas próprios, usando os prédios do mapa como lugares:
1. **Sucata:** campo de sucata produz enquanto há um caminhão de recurso carregando (20 por viagem).
2. **Refinaria** (`BPRefinery_C`): sucata vira bmat.
3. **Fábrica** (`BPFactory_C`): bmat vira caixas com os custos e tempos da tabela acima (fila de produção).
4. **Caminhão** (15 caixas): leva caixas da fábrica para um depósito (base ou ponto nosso), pela estrada, e pode
   ser atacado.
5. **Consumo:** recrutar gasta camisas e a arma do depósito onde o soldado nasce; recarregar munição gasta caixas
   de munição do depósito do ponto. A IA inimiga tem a mesma cadeia, mais simples.

## Regiões reais: primeiro inventário offline (2026-10-09)
Rastro: `data/trace_regions.txt`; sonda reproduzível em `tools/inspect_region.lua`.
Deadlands e CallumsCape abriram como sessões locais. CallumsCape tem campo de sucata ativo e instalações
em ruínas nos locais do mapa; precisam de reconstrução antes de uma cadeia operacional. A contagem dos
atores ativos é diferente da do lobby. O lote 17 acrescentou implantação própria explícita e veículos reais
do cenário, com orçamento e rollback; acesso por estrada ainda pendente.
Imagem não é inventário: estruturas podem sumir por ângulo/oclusão, veículos por LOS. Pesquisar classes
derivadas e ruínas; um zero numa classe descreve somente o estado local carregado, não o estado do servidor.

**Sondas de reconstrução (lote 16):** `data/trace_rebuild.txt`. Classes ativas de fábrica/refinaria
nasceram nas transformações das ruínas, com HP/classe-base conferidos; foram sondas temporárias, não uma
mecânica entregue. Canteiro criado diretamente veio sem alvo/custo configurados. Caminhão colocado por
trace vertical pode nascer em telhado ou retornar já em destruição. A próxima implementação precisa de
orçamento explícito, estacionamento validado e rollback; não basta ocultar a ruína ou retornar IsValid.

**Implantação entregue (lote 17):** `data/trace_deployment.txt`. Alt+L debita a carteira do cenário somente
após validar todas as instalações/caminhões; falha restaura as ruínas e preserva soldados. CallumsCapeHex
produziu três caixas em 65,21 s e entregou duas de munição/dez camisas à base, com três caminhões íntegros.
Teste sem ondas e com estoque inicial zerado: não valida equilíbrio nem estrada, construção nativa de
canteiro ou facilities. Caminhões ainda transportados em reta pelo sistema próprio do mod.
