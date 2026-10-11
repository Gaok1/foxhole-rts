# Primeiros passos — Foxhole RTS

Este é um plano de investigação, não uma confirmação de que o mod já é tecnicamente viável.

## 1. Reconhecimento após a instalação

- [x] Confirmar com o usuário que a instalação terminou.
- [x] Confirmar a modalidade desejada: solo contra IA, controle por esquadrão.
- [x] Localizar a instalação e registrar loja, versão/build e executáveis.
- [x] Executar o scanner do toolkit em modo somente leitura.
- [x] Identificar engine, proteções, configurações, logs e eventuais saves locais. Config/logs/saves só existem após o primeiro lançamento.
- [x] Atualizar a pesquisa sobre ferramentas da comunidade e regras oficiais.
- [x] Registrar evidências e dúvidas em `MODLOG.md` e a rota proposta em `MODDING_PLAN.md`.

## 2. Marco decisivo: controle da simulação

- [x] Investigar se existe uma rota autorizada para carregar uma cena isolada e controlar sua simulação. Resultado desta rodada: não encontrada; detalhes em `RECON_AMBIENTE.md`.
- [x] Verificar o que depende do servidor e o que pode ser modificado localmente. Estático: o único bloqueio do host é o perfil em `PostLogin`; ver `COMO_FAZER_O_MOD.md`. Falta confirmar em execução (T2).
- [x] Não assumir que alterar câmera ou texturas permite criar e comandar unidades. Provado em execução em 2026-10-07 (soldados criados e comandados).
- [ ] Se nenhuma rota utilizável for encontrada, documentar o bloqueio e discutir com o usuário antes de mudar o escopo.

## 3. Preparar o laboratório — somente com rota demonstrada

- [x] Apresentar alterações necessárias e pedir autorização para instalar qualquer loader. Autorizado (UE4SS só na cópia).
- [x] Fazer backup dos arquivos/configurações afetados e registrar como restaurar: `tools/lab.ps1` faz `um backup` da config antes de cada `run`; a instalação Steam não é alterada.
- [x] Separar ambiente de testes de partidas oficiais: cópia em `D:\FoxholeLab\Foxhole`, com trava que recusa loader na instalação Steam.
- [x] Preparar logs e um teste repetível: `D:	oolsoxhole-labestart.sh` + canal `cmd.lua` + `um win shot`.

## 4. Primeira prova jogável

- [x] Carregar uma cena no ambiente isolado (`HomeRegionW` em listen).
- [x] Criar ou disponibilizar uma unidade controlável (`HeadlessPlayerController`).
- [x] Selecionar um esquadrão e dar uma ordem de movimento por clique (todos os membros se movem).
- [x] Verificar execução real por logs e captura de tela.

Critério de sucesso: uma unidade executa uma ordem RTS em uma simulação sob nosso controle. Câmera livre, mockup ou vídeo conceitual não contam como essa prova.

## 5. Expandir apenas após a prova

1. Seleção múltipla, câmera RTS e ordens básicas. *(câmera e ordens por esquadrão feitas; seleção múltipla não)*
2. Navegação, combate e IA simples. *(v0.3: combate com dano simulado e efeitos do jogo, IA de ondas, desvio de obstáculo simples; arma real pendente)*
3. Batalha pequena: dois grupos de infantaria, um tanque e um objetivo.
4. Produção, transporte e abastecimento.
5. Construção, trincheiras e persistência, conforme a rota permitir.

## Encerramento de cada sessão

- Atualizar o diário com resultados, falhas, evidências e próximo passo.
- Distinguir claramente o que foi testado do que é hipótese.
- Quando houver descobertas úteis, preparar uma nota para a base de conhecimento; publicar somente com autorização.
