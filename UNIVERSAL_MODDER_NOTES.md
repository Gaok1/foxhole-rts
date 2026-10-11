# Universal Modder — uso e avaliação no Foxhole RTS

Registro de 2026-10-07. Toolkit: `D:\GitHub\universal-modder`.
Separar resultado desta rodada, evidência histórica do MODLOG e hipótese.
Scanner e decompilação não substituem teste no jogo.

## Como usar neste Windows

Em PowerShell, execute o toolkit dentro de seu repositório:

```powershell
Set-Location D:\GitHub\universal-modder
$env:UM_HOME = 'D:\tools\um-home'
$env:PYTHONIOENCODING = 'utf-8'
python -m um kb search foxhole
python -m um scan 'Foxhole' --json
python -m um backup create "$env:LOCALAPPDATA\Foxhole" --name foxhole-config
python -m um backup list foxhole-config
python -m um win ps
python -m um win shot --title '^War' --scale 0.5 D:\tools\foxhole-lab\check.png
python -m um publish check D:\GitHub\foxhole-rts\mod --game D:\SteamLibrary\steamapps\common\Foxhole
```

Não execute a lista cegamente: captura exige jogo aberto; backup deve preceder
alteração de configuração/lançamento. Use o mesmo `UM_HOME` para criar e consultar
snapshots. Para recuperar, consulte `python -m um backup restore --help` e prefira
restaurar primeiro para uma pasta separada com `--to`.

`python -m um <grupo> --help` mostra a interface local realmente instalada.
Não foi necessário instalar outra cópia nem usar WSL para chamar a CLI.

**Falha reproduzida nesta continuação:** `kb search inventory` abortou ao imprimir
uma seta Unicode usando stdout cp1252 (`UnicodeEncodeError`). Reexecutar com
`$env:PYTHONIOENCODING='utf-8'` terminou com código 0 e exibiu todas as notas.
É configuração da saída Python; não exige editar a KB nem instalar dependência.
Saída parcial antes do traceback não deve ser tomada como busca concluída.

### Skills utilizadas

- `mod-any-game`: reconhecimento, laboratório, fatia funcional e prova em jogo.
- `reverse-engineering`: código/reflexão antes de adivinhar RPCs; decompilações fora do repo.
- `game-automation`: captura GPU, processo por PID e teste repetível.
- Playbook `mod-any-game/references/engines/unreal.md`: UE4SS/PAK e limites.

## O que funciona bem / o que não resolve

| Recurso | Evidência | Bom para | Limite observado |
|---|---|---|---|
| `kb search foxhole` | Rodada atual | Recuperar receitas e tentativas fracassadas | Nota é experiência, não certificação; pode ficar desatualizada |
| `scan` | Recon histórico | Instalação, engine e rotas possíveis | Sugestão UE4SS genérica não prova suporte ou autorização |
| `backup` | Histórico no launcher | Preservar config compartilhada | Não isola rede nem separa perfis automaticamente |
| `win shot --title '^War'` | Capturas históricas | Captura GPU da janela certa | `--exe` já capturou console UE4SS; conferir a imagem |
| `win drive --title` | Alteração local anterior | Input dirigido à janela correta | Toma mouse/teclado: pedir antes, checar idle/foco |
| `win kill PID` | Reinícios históricos | Encerrar processo identificado | Conferir caminho; nunca matar por padrão de nome |
| `publish check` | Rodada atual | Lint de pacote | Não prova estabilidade, isolamento ou direitos de distribuição |
| Ghidra + reflexão UE4SS | Histórico | Entender classes/RPCs | Complementares ao toolkit; hipótese estática precisa de teste |

## Próxima execução: procedimento e critério de sucesso

1. Conferir instalação oficial limpa e cópia com `tools/lab.ps1 check` no repo do mod.
2. Confirmar bloqueio de rede do executável exato da cópia. Nesta rodada,
   `Get-NetFirewallRule -DisplayName '*Foxhole*'` retornou **acesso negado**.
   Não prova ausência nem presença da regra. Não houve novo lançamento.
3. Executar os testes offline:

   ```powershell
   Set-Location D:\GitHub\foxhole-rts
   $env:PYTHONPATH = 'D:\tools\pylibs'
   python tools\test_orders.py
   ```

   Usa `lupa` 2.8 já disponível. Exercita funções reais com APIs simuladas;
   não verifica física Unreal, RPCs, tecla real ou renderização.
4. Backup e reinício controlado da cópia; não usar Ctrl+R. O helper histórico
   `D:\tools\foxhole-lab\restart.sh` fica fora do repo e não verifica isolamento.
   Carregamento já levou ~95 s; `Responding=False` sozinho não prova deadlock.
5. F6, grupo 1, ordem de mover, H: grupo 1 deve parar sem deslizar; grupo 2 mantém
   a ordem anterior. Nova ordem deve fazer o grupo 1 andar. Repetir com todos
   selecionados e inimigos (tiro automático deve continuar).
6. Guardar log e screenshot GPU, abrir e conferir a imagem. Só então marcar
   v0.3.1 como validada em jogo.

## Tentativas que não devem virar falsas soluções

- `ServerTakePickup` sem erro não significa item adquirido: inventário ficou vazio.
  Alterar temporariamente `bIsLocalPlayerController` não resolveu.
- Anular argumento da RPC aninhada evitou crash, mas pode interromper o caminho
  necessário ao inventário. Rifles reais continuam em investigação.
- `CreatePlayer` puxou UI extra e crashou; `AIController` perdeu o pawn.
  `HeadlessPlayerController` é a rota validada anteriormente para soldados.
- Tela preta anterior era fade da câmera; alterar show flags não solucionou.
- Lint não é teste funcional, e mocks não provam funcionamento no jogo.

Nenhuma publicação, PR, commit ou instalação de loader nesta rodada.

### RE de rifles: lição adicional

Seguindo a skill `reverse-engineering`, conferir construtores/assembly evitou
confiar numa vtable base como se fosse a final de PlayerCharacter. O helper
`D:\tools\foxhole-lab\re-agent\pe.py` é complementar, **não faz parte da CLI um**,
e tem essa limitação. Detalhes em `RIFLES_INVESTIGATION.md`.
O próximo probe mede pré-condições antes de repetir RPCs; testes com mocks em
`tools/test_inventory_probe.py` cobrem campos indisponíveis, pawn inválido e travas.

### Resultado final dos checks desta rodada

- `publish check`: **PASS**, 3 arquivos, 0 falhas, 0 avisos após adicionar README.
- `kb check --index`: **FAIL**, 60 notas verificadas; índice `knowledge/INDEX.md`
  desatualizado. A busca Foxhole funcionou, mas a validação global não passou.
  O toolkit sugere `python -m um kb index` para regenerar; não alterei o índice
  compartilhado nesta rodada. Isso não é falha do código do mod.

## Isolamento: consulta alternativa e ação necessária

Na continuação, consultas **somente leitura** com `netsh` funcionaram mesmo quando
`Get-NetFirewallRule` falhou:

```powershell
netsh advfirewall show allprofiles state
netsh advfirewall firewall show rule name=all verbose |
    Select-String -Pattern 'Foxhole|War-Win64' -Context 8,12
```

Resultado: três perfis ligados; encontradas apenas regras de entrada permitindo
`D:\SteamLibrary\steamapps\common\Foxhole\War.exe`. Nenhuma regra específica
de bloqueio da cópia foi encontrada. Isso não descarta outras políticas genéricas,
mas não fornece a evidência de isolamento exigida. O jogo permaneceu fechado.

**Ação manual solicitada ao usuário**, em PowerShell como administrador, se não
houver outra regra equivalente já instalada (não executada pelo agente):

```powershell
New-NetFirewallRule -DisplayName 'FoxholeRTS Lab - Block Outbound' `
  -Direction Outbound -Action Block -Enabled True -Profile Any `
  -Program 'D:\FoxholeLab\Foxhole\War\Binaries\Win64\War-Win64-Shipping.exe'
```

Depois, avisar o agente para conferir a regra com:

```powershell
netsh advfirewall firewall show rule name="FoxholeRTS Lab - Block Outbound" verbose
```

Conferir caminho exato, saída, bloqueio, habilitada e todos os perfis. A regra é
do executável da cópia, não do cliente oficial. Não desabilitar o firewall.
Isso é uma barreira de rede; não certifica ausência de todo tráfego indireto nem
garante segurança de conta. Os demais cuidados do laboratório continuam exigidos.
