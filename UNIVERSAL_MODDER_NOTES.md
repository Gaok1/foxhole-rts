# Universal Modder — use and evaluation in Foxhole RTS

Record of 2026-10-07. Toolkit: `D:\GitHub\universal-modder` (https://github.com/rehan-remade/universal-modder).
Separate this round's results, historical evidence from the MODLOG and hypotheses.
Scanner and decompilation do not replace an in-game test.

## How to use it on this Windows machine

In PowerShell, run the toolkit inside its repository:

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

Do not run the list blindly: a screenshot needs the game open; a backup must come before
changing the configuration/launching. Use the same `UM_HOME` to create and look up
snapshots. To recover, see `python -m um backup restore --help` and prefer
restoring first to a separate folder with `--to`.

`python -m um <group> --help` shows the locally installed interface.
It was not necessary to install another copy or use WSL to call the CLI.

**Failure reproduced in this continuation:** `kb search inventory` aborted while printing
a Unicode arrow through a cp1252 stdout (`UnicodeEncodeError`). Running again with
`$env:PYTHONIOENCODING='utf-8'` finished with code 0 and showed all notes.
It is a Python output setting; it does not require editing the KB or installing a dependency.
Partial output before the traceback must not be taken as a finished search.

### Skills used

- `mod-any-game`: recon, lab, vertical slice and in-game proof.
- `reverse-engineering`: code/reflection before guessing RPCs; decompilations outside the repo.
- `game-automation`: GPU capture, process by PID and repeatable test.
- Playbook `mod-any-game/references/engines/unreal.md`: UE4SS/PAK and limits.

## What works well / what it does not solve

| Feature | Evidence | Good for | Observed limit |
|---|---|---|---|
| `kb search foxhole` | Current round | Recovering recipes and failed attempts | A note is experience, not certification; it can go stale |
| `scan` | Historical recon | Installation, engine and possible routes | The generic UE4SS suggestion does not prove support or authorization |
| `backup` | History in the launcher | Preserving shared config | Does not isolate the network nor separate profiles automatically |
| `win shot --title '^War'` | Historical screenshots | GPU capture of the right window | `--exe` once captured the UE4SS console; check the image |
| `win drive --title` | Earlier local change | Input directed at the correct window | Takes mouse/keyboard: ask first, check idle/focus |
| `win kill PID` | Historical restarts | Ending an identified process | Check the path; never kill by name pattern |
| `publish check` | Current round | Package lint | Does not prove stability, isolation or distribution rights |
| Ghidra + UE4SS reflection | History | Understanding classes/RPCs | Complementary to the toolkit; a static hypothesis needs a test |

## Next run: procedure and success criterion

1. Check the clean official installation and the copy with `tools/lab.ps1 check` in the mod repo.
2. Confirm the network block of the copy's exact executable. In this round,
   `Get-NetFirewallRule -DisplayName '*Foxhole*'` returned **access denied**.
   It proves neither absence nor presence of the rule. There was no new launch.
3. Run the offline tests:

   ```powershell
   Set-Location D:\GitHub\foxhole-rts
   $env:PYTHONPATH = 'D:\tools\pylibs'
   python tools\test_orders.py
   ```

   Uses `lupa` 2.8, already available. Exercises real functions with simulated APIs;
   does not check Unreal physics, RPCs, real keys or rendering.
4. Backup and controlled restart of the copy; do not use Ctrl+R. The restart helper
   (now `tools/lab/restart.sh`) does not check isolation.
   Loading once took ~95 s; `Responding=False` alone does not prove a deadlock.
5. F6, group 1, move order, H: group 1 must stop without sliding; group 2 keeps
   the previous order. A new order must make group 1 walk. Repeat with all
   selected and enemies (automatic fire must continue).
6. Keep the log and a GPU screenshot, open and check the image. Only then mark
   v0.3.1 as validated in game.

## Attempts that must not become false solutions

- `ServerTakePickup` without error does not mean the item was acquired: the inventory stayed empty.
  Temporarily changing `bIsLocalPlayerController` did not solve it.
- Nulling the nested RPC argument avoided a crash, but may interrupt the path
  needed for the inventory. Real rifles are still under investigation.
- `CreatePlayer` pulled extra UI and crashed; `AIController` lost the pawn.
  `HeadlessPlayerController` is the route validated earlier for soldiers.
- The earlier black screen was a camera fade; changing show flags did not solve it.
- Lint is not a functional test, and mocks do not prove it works in the game.

No publishing, PR, commit or loader installation in this round.

### Rifle RE: additional lesson

Following the `reverse-engineering` skill, checking constructors/assembly avoided
trusting a base vtable as if it were PlayerCharacter's final one. The helper
`D:\tools\foxhole-lab\re-agent\pe.py` is complementary, **not part of the um CLI**,
and has that limitation. Details in `RIFLES_INVESTIGATION.md`.
The next probe measures preconditions before repeating RPCs; tests with mocks in
`tools/test_inventory_probe.py` cover unavailable fields, invalid pawn and locks.

### Final result of this round's checks

- `publish check`: **PASS**, 3 files, 0 failures, 0 warnings after adding a README.
- `kb check --index`: **FAIL**, 60 notes checked; index `knowledge/INDEX.md`
  out of date. The Foxhole search worked, but the global validation did not pass.
  The toolkit suggests `python -m um kb index` to regenerate; I did not change the shared
  index in this round. This is not a failure of the mod's code.

## Isolation: alternative query and required action

In the continuation, **read-only** queries with `netsh` worked even when
`Get-NetFirewallRule` failed:

```powershell
netsh advfirewall show allprofiles state
netsh advfirewall firewall show rule name=all verbose |
    Select-String -Pattern 'Foxhole|War-Win64' -Context 8,12
```

Result: three profiles on; only inbound rules allowing
`D:\SteamLibrary\steamapps\common\Foxhole\War.exe` were found. No specific
block rule for the copy was found. This does not rule out other generic policies,
but it does not give the required evidence of isolation. The game stayed closed.

**Manual action requested from the user**, in PowerShell as administrator, if there is
no equivalent rule already installed (not run by the agent):

```powershell
New-NetFirewallRule -DisplayName 'FoxholeRTS Lab - Block Outbound' `
  -Direction Outbound -Action Block -Enabled True -Profile Any `
  -Program 'D:\FoxholeLab\Foxhole\War\Binaries\Win64\War-Win64-Shipping.exe'
```

Then tell the agent to check the rule with:

```powershell
netsh advfirewall firewall show rule name="FoxholeRTS Lab - Block Outbound" verbose
```

Check the exact path, outbound, block, enabled and all profiles. The rule is for
the copy's executable, not the official client. Do not disable the firewall.
This is a network barrier; it does not certify the absence of all indirect traffic nor
guarantee account safety. The other lab precautions are still required.
