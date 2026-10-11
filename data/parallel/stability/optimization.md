# Contorno — custo e opções sem perder aparência

## Estado verificado informado pelo coordenador (PID4436)

PASS curto: criação de 28 cópias, desseleção/reseleção, morte/reap com referências removidas,
recriação e CollectGarbage confirmado por metadados; reseleção aos 89s. Teste de 6 selecionados/168 cópias
em andamento quando este relatório foi escrito. Causa das quedas originais não isolada; não é certificado
prolongado nem resultado de seleção grande. Não apliquei mudanças de otimização.

## Contagem estática, não benchmark

Por soldado atual selecionado (7 peças x 4): update consulta câmera 1 vez, transforma fontes 3 x 7,
escreve clones 3 x 28 = 84 UFunctions. Total update: 106 chamadas refletidas por quadro, além de guards,
leituras de propriedades e CustomDepth/stencil. Para 6 soldados: 636 chamadas update/quadro.
`outlineDepth(true)` acrescenta 2 por componente descoberto, inclusive peças sem clone.
Não selecionados e olho continuam SetRenderCustomDepth(false) por componente/quadro: nativo reativa
esse estado, conforme rastro real. Número de cópias não demonstra tempo de GPU nem custo de callback.

## Medir antes de escolher

Usar profile() já disponível: janelas equivalentes de 60s com 0/1/3/6/10 selecionados, mesmas unidades,
mesmo mapa/câmera/zoom, parados; repetir em movimento. Cada chamada zera acumuladores. Salvar frames,
stratTick ms/quadro e total, clones reais e câmera, sem callback extra. Calcular:

    custo adicional aproximado/cópia = (stratTick_N - stratTick_0)/(28*N)

Isso mistura CPU de depth/guards/transformações e não mede GPU; anotar essa limitação. Relatar média
por janela e repetição, não inventar p95 a partir da média. Comparar 6 unidades não selecionadas com
as mesmas 6 selecionadas; aumentar unidades e seleção juntos confundiria o custo.

## Ordem de otimização proposta

1. **Câmera consultada uma vez por stratTick**, passada como parâmetro opcional de updateOutline.
   Economiza N-1 leituras/quadro, mantém geometria integral; custo pequeno, testar antes de aplicar.
   Caller direto updateOutline deve continuar funcionando; snapshot só do mesmo quadro, nunca cache eterno.
2. **Rotation/scale das cópias só quando transformação calculada mudar.** Comparar valores numéricos
   por peça com último transform, não identidade da tabela. Cópias continuam usando pose MasterPose;
   fontes e câmera devem ser consultadas a cada quadro. Caso parado pode evitar 56 escritas/soldado/quadro.
   Risco: engine também muda transform via attachment; pular location sem medir o efeito perde a homotetia.
   Portanto primeira experiência só escala/rotação, não posição; invalidar cache em limpeza/recriação.
   Verificar fonte girando, câmera movendo, equip substituído, zoom alto e várias posições da tela.
3. **Um MID emissivo por conjunto**, aplicado imediatamente às cópias como raiz de engine.
   Mesma cor, nenhuma aparência diferente; reduz criação de 28 MIDs/soldado para 1, mas não custo contínuo
   demonstrado. Só útil se medir pico da seleção/GC. Não manter MID apenas em userdata Lua.
4. **Evitar reescrever stencil quando já é 1**, somente se leitura refletida segura/contrato confirmado.
   Não remover writes CustomDepth: rastro mostra reativação nativa em amigos/olho.

Sem LOD por retirar peças/cópias e sem atualizar contorno a 10Hz: essas opções reduzem fidelidade ou
seguimento e não atendem aparência aprovada. Não criar novo scheduler/callback por clone.

## Alternativas nativas de fato descobertas

`M_OccludedOutline` é material nativo PostProcess já rastreado e ancorado no volume; fornece preenchimento
encoberto, não borda de partes visíveis. Assim não substitui sozinho as 28 cópias.
`SetMasterPoseComponent`, attachment KeepWorld e CustomDepth/stencil foram usados e rastreados; nenhum
shader nativo geral de borda foi demonstrado nos dados atuais. Shader cooked é alternativa de pesquisa,
não asset pronto nem solução comprovada. Não tentar leitura MasterPoseComponent/AnimClass (crash registrado).

## Gate para qualquer proposta

Teste real das funções, contador refletido mocks antes/depois, mesma fórmula projetada existente;
integração pelo coordenador, carga limpa, captura comparação e medição. Lifetime antes de performance.


## Medição recebida e conferida (PID4436)

`D:/tools/foxhole-lab/stability-group-live.txt`: 32,30255s / 1400 quadros; 6x28 cópias;
stratTick 16,72ms/quadro, mod 17,70ms/quadro. 94,46% do tempo medido do mod nessa etapa.
É gargalo real. 16,72/168 = 0,09952ms/cópia como razão BRUTA, não custo incremental sem baseline.

Prioridade revisada: medir controle mesmas 6 sem seleção; então experimentar combinação de transformação
numa UFunction em vez de 3 por clone. Procurar `K2_SetActorTransform` nos metadados carregados antes de
chamar: se refletida e contrato confirmado, construir FTransform corretamente (quaternion, não Rotator
inventado) e comparar com os três setters. Pode reduzir 84→28 escritas/soldado/quadro sem sacrificar
geometria. Nenhum registro dessa função em data/tools/mod atuais foi encontrado; não é ainda contrato
local demonstrado. Se faltar, testar setters existentes com comparação numérica de escala/rotação.
Não retirar validação de vida útil nem depth só para reduzir tempo.

Alternativa arquitetural sem corte visual: um único proxy contendo 7 peças e 4 deslocamentos renderizados
num shader cooked; elimina atores extras e setters por cópia. Exige asset próprio UE4.24 e prova de pose,
outline e oclusão, portanto não é mudança imediata segura. Só iniciar cook depois de varrer materiais
locais e confirmar que não há shader de borda disponível. Sem downloads/instalações nesta análise.


## Sonda de schema preparada (não executada)

`D:/tools/foxhole-lab/t_outline_transform_schema.lua` enumera parâmetros de K2_SetActorTransform,
campos Transform/Quat/Rotator e funções KismetMathLibrary filtradas por Quat/Rotator, MakeTransform,
BreakTransform. Só metadados; nenhuma alteração de ator, chamada setter/conversor ou callback novo.
Usa ForEachProperty/GetStruct já demonstrados em t_sigs.lua/t_findfn2.lua. Depois da confirmação:

1. Confirmar ordem/tipos dos parâmetros e layout Rotation/Translation/Scale3D pelo output real.
2. Confirmar conversor nativo Rotator→Quat (ou MakeTransform) antes de formar FTransform.
3. Num clone de sonda isolado e saudável, aplicar setters atuais para p/rot/scale conhecidos e ler resultado.
4. Aplicar setter único com mesma transformação e comparar location/rotation/scale; incluir yaw77,
   pitch-60/roll13, escala não uniforme e posições negativas. Quaternion roundtrip pode trocar representação;
   comparar resultado em rotator efetivo/projeção, não somente bytes/quaternion sign.
5. Só integrar depois de confirmar attachment/KeepWorld e movimento/câmera em quadro real. Converter uma vez
   por peça, não por cópia; MakeTransform+setter por cópia pode reduzir 3→2, não3→1, se não reutilizar.


## Entrega transformação consolidada

Oráculos nativos do coordenador PASS: outline-transform-oracle-live.txt e
outline-transform-packed-live.txt (tabela copiada; erro caso3 7,63e-06).
`transform.before.lua`/`transform.after.lua` substituem updateOutline inteiro: MakeTransform uma vez
por peça, quaternion copiado em tabela Lua, escala projetada uma vez/peça e Translation por cópia.
Sem matemática manual de quaternion, sem alterar appearance/cópias/guards. Contagem update:
1camera +21reads +7MakeTransform +28setter =57/soldado (antes106); redução46,23% de calls da função,
mas nenhum ganho temporal alegado até nova medição. Cache mathlib no rts, sem local top-level.
`test_transform.py` PASS: 8cópias/2peças/3câmeras, mesma geometria/rotação/escala; setters72→24,
6conversões. Mock usa codificação marcador, não implementa quaternion: native oracle é a prova dessa etapa.
`orders_transform.before.txt`/after.txt adaptam mocks do teste existente em dois blocos; não alterei
arquivo real. Integrador aplica e executa test_orders com a função integrada.


## Regressão de custo pós-transições — não alegar ganho sustentável

Log `stability-optimized-after-gc-profile.txt`: 95,4164s desde grupo;1873 quadros,
stratTick16,40ms/quadro, mod17,46ms/quadro, ainda28cópias por6soldados. Primeira janela otimizada7,91ms
não representa ganho sustentável. Geometria/setter corretos não provam custo estável.

Hipóteses, NÃO causas:
- Perfil mede apenas trecho Lua/UFunctions de stratTick, não tick nativo geral/GPU. Mais atores velhos podem
  atrasar engine/chamadas, mas requisito MasterPose/tick acumulado não é dedutível de média.
- `clearOutline` apaga refs mesmo quando DestroyActor falha via pcall. Cópias vivas sem referência podem
  acumular. IsValid true de destruídos é esperado até GC; contar ambos separadamente.
- Listas de componentes podem se expandir/trocar:28clones não informa quantidade de fontes/depth de pawn.
- Coleta/reseleção cria pico de spawn/MID; perfil inclui trabalho de criação em stratTick. Média mistura
  pico e steady-state se não houver reset depois da transição.
- `profile()` zera acumuladores, mas timestamps externos nem sempre acompanham reset.1873frames não
  comprovam duração95s da janela; TIME é desde grupo, não último reset.

Sonda preparada `D:/tools/foxhole-lab/t_outline_phase.lua` (não executada): sem callback/hotpatch;
comando fecha perfil da janela anterior, conta selected/tracked, FindAllOf SkeletalMeshActor ativo/em
retirada/inválido e vivo não rastreado, depois abre novo timestamp. Primeira janela descartada.
Contagem não rastreada inclui possíveis atores nativos: comparar baseline, não chamar todos vazamento.

Protocolo comparável:
1. Carga limpa,6unidades paradas,não selecionadas; iniciar sonda,aguardar60s,sonda (controle).
2. Selecionar6; aguardar5s assentamento;sonda descarta pico; aguardar60s;sonda (janela S1).
3. Sem transição,mais60s;sonda(S2);mais60s;sonda(S3). Isso distingue degradação pelo tempo.
4. Desselecionar/reselecionar uma única vez;aguardar5s;sonda descarta pico;60s;sonda(R1).
5. Mais60s sem transição;sonda(R2). Se vivos não rastreados crescerem, conferir DestroyActor retorno/log.
6. GC confirmado em fase separada,aguardar5s,reset por sonda;60s;sonda(G1);mais60s;sonda(G2).
7. Só depois morte/recriação6;mesmo protocolo. Repetir ordem invertida em carga limpa para separar ordem.

Registrar hash,PID,mapa,frame count e duration real de cada janela. Não capturar a tela nem executar
buscas amplas durante janela. Não repetir profilagem via callback temporário nem esconder picos:
pico reportado à parte,steady-state em janela separada. Não tocar MasterPoseComponent/AnimClass.


## ComponentToWorld — proposta seguinte, ainda não integrada

Fase S1 informada pelo coordenador:61,86s/2447frames/stratTick15,72ms;207atores/168rastreados/39nativos,
sem aumento de contagem. Isso enfraquece acúmulo de atores nessa janela, não exclui outros custos.
`K2_GetComponentToWorld` retorna FTransform segundo metadados reais de SceneComponent descobertos
na task ESTRADAS. Oráculo preparado (não executado aqui) compara 3getters+MakeTransform com esse retorno;
quaternion alinhado por sinal. Artefatos component_transform.before.lua/after.lua propõem substituir4reads/
conversão por1read/peça, sem mudanças geométricas/guards.36calls/soldado em vez57 update/quadro,
redução36,84% relativa de calls, sem alegar ms. test_component_transform.py PASS decisões Lua/geometria.
orders_component.before.txt/after.txt adaptam mocks compartilhados em2blocos, sem editar teste real.
