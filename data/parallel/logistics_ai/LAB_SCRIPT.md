# IA_LOGISTICA (logistics AI) lab script (for the LABORATORIO agent)

This script was **prepared and not run**. CLAUDE_IA_LOGISTICA did not open the game nor use the channel or the
botloop. The lab owner runs it, after the coordinator integrates the batch in the order
ESTABILIDADE → ECONOMIA → IA_LOGISTICA (see `REPORT.md` §5). Each row is approved or failed with
evidence (log, channel output, capture). Record the hash of the published `main.lua` on each row.

## Batch rules
- Before launching: Steam open and logged in, copy at `D:\FoxholeLab\Foxhole`, no `botloop.sh` running
  (`Get-CimInstance Win32_Process`). Publish with `bash D:/tools/foxhole-lab/restart.sh`. Do not use Ctrl+R.
- Do not use the channel with the bot on. Read-only probe: copy `t_logistics_ai.lua` from this folder to
  `D:/tools/foxhole-lab/` and run `sh D:/tools/foxhole-lab/run.sh t_logistics_ai.lua`. It only reads state.
- No keyboard or mouse injection. The match keys (Shift+F6, Ctrl+F6, Alt+F6) belong to the user or to
  equivalent channel commands the lab already uses. IA_LOGISTICA brings no new key.
- Region: the same where the player's chain was validated (CallumsCapeHex, batch 17), with Alt+L already accepted.
  HomeRegionW is only a test bench.
- When validation ends, close only the copy's PID. Steam and the firewall stay as they are.

## Technical matrix (short, with the channel)

| ID | Step | Approval |
|---|---|---|
| L1 | New match with logistics. Run the probe right at the start. | `auditoria=true (razão fechado)`, `ativo=true`, front m2 c10, bmat 240, free fleet 2. HUD with "INIMIGO: frente equipa 10". No Lua error in `UE4SS.log`. |
| L2 | Wait for the 1st convoy (20 s after the waves start, plus whatever cargo is missing). | Event "comboio 1 saiu: N cx". The BPTruckC actor exists, `ator_ativo=true` and the cargo shows in the probe. The rear dropped exactly the cargo's crates. Alert "COMBOIO INIMIGO ... (carga)". |
| L3 | Let the convoy arrive without interfering. | A single "entregou na frente"; the front rises by `units` (shirt crate = 10). Run the probe 3x in a row: no second delivery. The truck returns and vanishes, and the free fleet goes back to 2. `auditoria=true`. |
| L4 | Ambush: our soldiers within 15 m of the loaded convoy (real move order by the user, or an existing position). | "comboio N perdido (destruído): -X munição, -Y camisas" **once**. Alert "COMBOIO INIMIGO DESTRUÍDO (+25): a frente perde ...". The front does not change. "reconstruindo 1". `auditoria=true`. |
| L5 | Mortar (Ctrl+5) on a loaded convoy. | The same as L4. A mortar on an already destroyed truck does not record a second loss. |
| L6 | Wait 30 s or more after the loss. | "caminhão de comboio reconstruído (-100 bmat)" only when bmat ≥ 100. The factory stays idle if there is no free truck and a rebuild is due. |
| L7 | Waves with the front full and then empty. Compare `#enemies` right after each spawn with the wave record. | `enviados` = soldiers that actually spawned. With the front empty: "faltou suprimento ao inimigo: a onda vem com N a menos (falta camisas/munição; K por comboios destruídos)". Real wave at the floor of 3, no extra soldier. |
| L8 | Enemy point with reinforcement (`ai.tick`) and a dry front, then supplied. | Without material, no "REFORÇO INIMIGO". With material, reinforcement of 2-3 and the front debited by the number that **spawned**. |
| L9 | Save/continue with a convoy on the road: wait for a save (30 s), close and continue (Ctrl+F6). | Event "cadeia inimiga restaurada do save (reenviar ...)". The pending amount equals the cargo that was on the road. `auditoria=true`. The next convoy carries the pending amount. Continuing twice duplicates nothing (compare initial+produced). |
| L10 | Invalid convoy actor: through the channel, `logi.foes[1].pawn:K2_DestroyActor()` (only this line, separate and recorded probe). | On the next frame: "perdido (ator do caminhão inválido)", no delivery and `auditoria=true`. No crash or native error. |
| L11 | Assault (Alt+F6). | No convoy, front intact, no consumption (`ativo=false`). |
| L12 | Shift+F6 several times and F11 in the middle of the match. | No convoy left in the world (count active `BPTruckC_C`); new `logi.en`; no error. |

## Long regression matrix (combat and balance, with the bot)

The usual bot: `sh D:/tools/foxhole-lab/botloop.sh` in the background, waiting with
`until grep -q "auto<TAB>false" botrun.log`. With the bot on, do not use the channel. Read the probe **after**
each match. Minimum: 3 matches per cell at normal difficulty and 1 at easy and 1 at hard, if time allows.

| Cell | Build | Interdiction | Record |
|---|---|---|---|
| B0 | main **without** IA_LOGISTICA (only ESTABILIDADE+ECONOMIA) | the bot's (if it does not attack convoys, note it) | victory/defeat, final wave, kills/losses, duration, convoys/destroyed |
| B1 | with IA_LOGISTICA | the bot's | the same as B0 + `logi.eReport()` at the end (waves: requested/sent/missing/byCut) + `auditoria` |
| B2 | with IA_LOGISTICA | forced: the user or the bot's order keeps the squad on the convoy route | the same as B1; compare the size of waves 4-10 with B1 |
| B3 | with IA_LOGISTICA, `CFG.ECHAIN.free` = 5 (through the channel **before** turning on the bot) | like B2 | the same; used to calibrate the floor |

Technical approval (applies to B1-B3): `auditoria=true` at the end of **every** match; no Lua error or UE4SS
crash in 30 min or more; number of active BPTruckC ≤ 2 (fleet) in any sample. For frame time, a
`LoopInGameThreadWithDelay(100)` sampler writing to `_G` (not through the channel), comparing B0 and B1.

Traceable effect approval: in B2, the recorded loss (`perdido` in the ledger) > 0, there are waves with `byCut` > 0,
and waves 4-10 of B2 are smaller than those of B1 at the same index. After the interdiction stops, some wave
goes back to `faltaram 0`.

Balance (it is the user's decision, the script only measures): the B1 result should stay close to the B0 history
(batch 12: victory in 10 waves, 111/24; batch 13: defeat at wave 10, 83/38). If B2 becomes trivial (waves stuck
at the floor early on), calibrate `free`, `front0`, `want`, `trip` or `minLoad` and repeat only the affected cell.

## Outside this script
- The convoy's road route depends on the ESTRADAS (roads) driver, which does not exist yet; today it drives straight
  and without collision, as before.
- HUD/panel readability and real input (ambush by click) are validated by the user.
