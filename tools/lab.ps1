<#
Foxhole RTS - laboratorio isolado (Windows PowerShell 5.1).

  .\tools\lab.ps1 check                      # travas de seguranca: instalacao Steam limpa, copia presente
  .\tools\lab.ps1 prepare                    # steam_appid.txt na copia + backup da config
  .\tools\lab.ps1 lab-ini                   # Engine.ini do usuario: sem Steam game server/VAC, sem splitscreen (run ja faz)
  .\tools\lab.ps1 run [-Map HomeRegionW] [-NoListen] [-ExtraArgs "..."]   # lanca a COPIA com -log
  .\tools\lab.ps1 ue4ss-install -Ue4ssDir D:\tools\ue4ss\pkg               # UE4SS so na copia
  .\tools\lab.ps1 ue4ss-remove
  .\tools\lab.ps1 log                        # ultimas linhas uteis do War.log

Regras (HOW_TO_MAKE_THE_MOD.md, secao 5): UE4SS nunca na instalacao Steam; a copia nunca
conecta em servidor oficial; backup antes de cada sessao modificada.
#>
param(
    [Parameter(Position = 0)][string]$Cmd = "check",
    [string]$Map = "HomeRegionW",
    [switch]$NoListen,
    [string]$ExtraArgs = "",
    [string]$Ue4ssDir = "D:\tools\ue4ss\pkg",
    [string]$SteamGame = "D:\SteamLibrary\steamapps\common\Foxhole",
    [string]$LabGame = "D:\FoxholeLab\Foxhole",
    [string]$Toolkit = "D:\GitHub\universal-modder"
)
$ErrorActionPreference = "Stop"
$BinRel = "War\Binaries\Win64"
$Exe = "War-Win64-Shipping.exe"
$ConfigDir = Join-Path $env:LOCALAPPDATA "Foxhole"   # confirmado no 1o lancamento (nao "War")
# Arquivos que identificam um loader (proxy dll do UE4SS e afins)
$LoaderMarkers = @("dwmapi.dll", "xinput1_3.dll", "UE4SS.dll", "UE4SS-settings.ini", "ue4ss")

function Find-Loader([string]$game) {
    $bin = Join-Path $game $BinRel
    $LoaderMarkers | ForEach-Object { Join-Path $bin $_ } | Where-Object { Test-Path $_ }
}

function Assert-SteamClean {
    $found = @(Find-Loader $SteamGame)
    if ($found.Count -gt 0) {
        throw "PERIGO: loader na instalacao Steam (risco de VAC online): $($found -join ', '). Remova antes de continuar."
    }
    Write-Host "OK  instalacao Steam sem loader: $SteamGame"
}

function Assert-Lab {
    if (-not (Test-Path (Join-Path $LabGame "$BinRel\$Exe"))) { throw "Copia de laboratorio ausente: $LabGame" }
    if ((Resolve-Path $LabGame).Path -eq (Resolve-Path $SteamGame).Path) { throw "LabGame aponta para a instalacao Steam." }
    Write-Host "OK  copia de laboratorio: $LabGame"
}

function Backup-Config {
    # Estado do toolkit (backups, ferramentas baixadas) em D:, nao no perfil em C:
    $env:UM_HOME = "D:\tools\um-home"
    if (Test-Path $ConfigDir) {
        Push-Location $Toolkit
        try { python -m um backup create $ConfigDir --name foxhole-config } finally { Pop-Location }
    } else {
        Write-Host "--  sem config ainda ($ConfigDir); nada a salvar"
    }
}

# Ajustes do laboratorio no Engine.ini do usuario (inofensivos para o jogo online):
# - [OnlineSubsystemSteam] bInitServerOnClient=False: num cliente, o Steam game server so sobe com
#   esta chave (ou a cvar OSS.SteamInitServerOnClient); assim nenhum servidor VAC e criado.
# - [OnlineSubsystemSteam] bVACEnabled=False: garantia extra; o init (VA 0x1405f78e0) usa
#   eServerMode = 2 + bVACEnabled, e o BaseEngine.ini embutido traz bVACEnabled=1.
# - [/Script/EngineSettings.GameMapsSettings] bUseSplitscreen=False: soldados serao jogadores
#   locais extras; sem isto a tela seria dividida.
$LabIni = @(
    @("OnlineSubsystemSteam", "bInitServerOnClient", "False"),
    @("OnlineSubsystemSteam", "bVACEnabled", "False"),
    @("/Script/EngineSettings.GameMapsSettings", "bUseSplitscreen", "False")
)

function Set-IniKey([string]$ini, [string]$section, [string]$key, [string]$value) {
    $lines = @()
    if (Test-Path $ini) { $lines = @(Get-Content -Path $ini) }
    $out = New-Object System.Collections.Generic.List[string]
    $header = "[" + $section + "]"
    $entry = $key + "=" + $value
    $inSection = $false; $sectionSeen = $false; $keyWritten = $false
    foreach ($line in $lines) {
        if ($line -match '^\s*\[') {
            if ($inSection -and -not $keyWritten) { $out.Add($entry); $keyWritten = $true }
            $inSection = ($line.Trim() -eq $header)
            if ($inSection) { $sectionSeen = $true }
            $out.Add($line); continue
        }
        if ($inSection -and $line -match ('^\s*' + [regex]::Escape($key) + '\s*=')) {
            if (-not $keyWritten) { $out.Add($entry); $keyWritten = $true }
            continue
        }
        $out.Add($line)
    }
    if ($inSection -and -not $keyWritten) { $out.Add($entry); $keyWritten = $true }
    if (-not $sectionSeen) { $out.Add(""); $out.Add($header); $out.Add($entry) }
    Set-Content -Path $ini -Value $out -Encoding ascii
}

function Set-LabIni {
    $iniDir = Join-Path $ConfigDir "Saved\Config\WindowsNoEditor"
    $ini = Join-Path $iniDir "Engine.ini"
    if (-not (Test-Path $iniDir)) { New-Item -ItemType Directory -Force $iniDir | Out-Null }
    foreach ($kv in $LabIni) {
        Set-IniKey $ini $kv[0] $kv[1] $kv[2]
        Write-Host ("OK  [" + $kv[0] + "] " + $kv[1] + "=" + $kv[2])
    }
    Write-Host "    em $ini"
}

switch ($Cmd) {
    "lab-ini" { Set-LabIni }
    "check" {
        Assert-SteamClean
        Assert-Lab
        $l = @(Find-Loader $LabGame)
        if ($l.Count -gt 0) { Write-Host "--  loader na copia: $($l -join ', ')" } else { Write-Host "--  copia sem loader" }
        $appid = Join-Path $LabGame "$BinRel\steam_appid.txt"
        Write-Host ("--  steam_appid.txt na copia: " + (Test-Path $appid))
    }
    "prepare" {
        Assert-SteamClean; Assert-Lab
        Set-Content -Path (Join-Path $LabGame "$BinRel\steam_appid.txt") -Value "505460" -Encoding ascii
        Write-Host "OK  steam_appid.txt escrito na copia"
        Backup-Config
    }
    "run" {
        Assert-SteamClean; Assert-Lab
        # Sem o cliente Steam aberto e logado, SteamAPI_Init falha ("conditions not met") e o jogo
        # roda sem verificacao de posse; sem steam_appid.txt o Steam relanca a instalacao oficial.
        if (-not (Get-Process steam -ErrorAction SilentlyContinue)) { throw "Abra o Steam e faca login antes de lancar a copia." }
        $activeUser = (Get-ItemProperty HKCU:\Software\Valve\Steam\ActiveProcess -ErrorAction SilentlyContinue).ActiveUser
        if (-not $activeUser) { throw "Steam aberto mas sem usuario logado." }
        if (-not (Test-Path (Join-Path $LabGame "$BinRel\steam_appid.txt"))) { throw "Falta steam_appid.txt na copia (rode: lab.ps1 prepare)." }
        Backup-Config
        Set-LabIni
        $url = "/Game/Maps/$Map"
        if ($Map -like "*Hex" -or $Map -eq "MarbanHollow") { $url = "/Game/Maps/Master/$Map" }
        if (-not $NoListen) { $url += "?listen" }
        $argList = @($url, "-log") + ($ExtraArgs -split " " | Where-Object { $_ })
        $exePath = Join-Path $LabGame "$BinRel\$Exe"
        Write-Host "RUN $exePath $($argList -join ' ')"
        $p = Start-Process -FilePath $exePath -ArgumentList $argList -WorkingDirectory (Join-Path $LabGame $BinRel) -PassThru
        Write-Host "PID $($p.Id)  (encerrar com: python -m um win kill $($p.Id))"
    }
    "ue4ss-install" {
        Assert-SteamClean; Assert-Lab
        if (-not (Test-Path $Ue4ssDir)) { throw "UE4SS nao encontrado em $Ue4ssDir" }
        Copy-Item -Path (Join-Path $Ue4ssDir "*") -Destination (Join-Path $LabGame $BinRel) -Recurse -Force
        $modSrc = Join-Path $PSScriptRoot "..\mod\FoxholeRTS"
        if (Test-Path $modSrc) {
            $modsDir = Join-Path $LabGame "$BinRel\ue4ss\Mods"
            if (-not (Test-Path $modsDir)) { $modsDir = Join-Path $LabGame "$BinRel\Mods" }
            Copy-Item -Path $modSrc -Destination $modsDir -Recurse -Force
            Write-Host "OK  mod FoxholeRTS copiado para $modsDir (enabled.txt ativa o carregamento)"
        }
        Write-Host "OK  UE4SS instalado SOMENTE na copia"
        Assert-SteamClean
    }
    "ue4ss-remove" {
        Assert-Lab
        $bin = Join-Path $LabGame $BinRel
        foreach ($m in $LoaderMarkers) {
            $p = Join-Path $bin $m
            if (Test-Path $p) { Remove-Item -Path $p -Recurse -Force -Confirm:$false; Write-Host "removido $p" }
        }
    }
    "log" {
        $log = Join-Path $ConfigDir "Saved\Logs\War.log"
        if (-not (Test-Path $log)) { throw "Sem log em $log" }
        Select-String -Path $log -Pattern "LoadMap|Listen|NetDriver|Steam|VAC|Auth|WarService|Profile|Travel|Error|Fatal|SimGameMode" |
            Select-Object -Last 80 | ForEach-Object { $_.Line }
    }
    default { throw "Comando desconhecido: $Cmd (use check|prepare|lab-ini|run|ue4ss-install|ue4ss-remove|log)" }
}
