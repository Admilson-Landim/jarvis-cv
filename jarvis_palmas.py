#!/usr/bin/env python3
"""
JARVIS - Fase 1: duas palmas -> abre o ambiente de trabalho e cumprimenta.

Instalação no Fedora:
    sudo dnf install portaudio speech-dispatcher espeak-ng
    pip install --user -r requirements.txt
    python3 -m piper.download_voices pt_BR-faber-medium --data-dir vozes

Uso:
    python3 jarvis_palmas.py --calibrar   # mostra o volume para afinar o LIMIAR
    python3 jarvis_palmas.py              # modo normal
"""

import argparse
import queue
import shutil
import subprocess
import time

import numpy as np
import sounddevice as sd

import voz
from config import ASSISTENTE, NOME
from voz import falar

# --- Afinação ---------------------------------------------------------------
TAXA = 48000          # amostras por segundo (igual no jarvis.py, para a calibração valer lá)
BLOCO = 1024          # ~21 ms por bloco
LIMIAR = 0.45         # pico mínimo para contar como palma (calibrado: palmas ~0.56-0.61, voz <0.10)
INTERVALO_MIN = 0.15  # s; picos mais próximos que isto = a mesma palma
INTERVALO_MAX = 0.80  # s; distância máxima entre a 1ª e a 2ª palma
PAUSA = 3.0           # s; tempo de espera depois de disparar

# --- Ações ------------------------------------------------------------------

def abrir(*cmd: str) -> None:
    if shutil.which(cmd[0]):
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        print(f"  (não encontrei '{cmd[0]}', ignorado)")


def abrir_terminal() -> None:
    # Fedora recente usa o Ptyxis; versões antigas usam o gnome-terminal
    for cmd in (["ptyxis", "--new-window"], ["kgx"], ["gnome-terminal"], ["konsole"]):
        if shutil.which(cmd[0]):
            abrir(*cmd)
            return
    print("  (não encontrei nenhum terminal conhecido)")


def modo_trabalho() -> None:
    hora = time.localtime().tm_hour
    saudacao = "Bom dia" if hora < 12 else "Boa tarde" if hora < 19 else "Boa noite"
    falar(f"{saudacao}, {NOME}. A preparar o ambiente de trabalho.")
    abrir("code")
    abrir_terminal()
    abrir("xdg-open", "https://github.com/Admilson-Landim")


# --- Deteção ----------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--calibrar", action="store_true",
                        help="mostra o nível de som para escolher o LIMIAR")
    args = parser.parse_args()

    eventos: "queue.Queue[str]" = queue.Queue()
    estado = {"ultimo_pico": 0.0, "palmas": [], "bloqueado_ate": 0.0,
              "maximo": 0.0, "ultimo_registo": 0.0}

    def callback(indata, frames, time_info, status):
        pico = float(np.max(np.abs(indata)))

        if args.calibrar:
            agora = time.monotonic()
            estado["maximo"] = max(estado["maximo"], pico)
            # Sons fortes (palmas) ficam registados numa linha própria
            if pico >= 0.10 and agora - estado["ultimo_registo"] > 0.3:
                estado["ultimo_registo"] = agora
                marca = "  <- acima do LIMIAR" if pico >= LIMIAR else ""
                print(f"\rSOM FORTE: {pico:0.2f}{marca}" + " " * 40)
            barra = "#" * int(pico * 50)
            print(f"\ragora {pico:0.2f} | máx {estado['maximo']:0.2f} | {barra:<50}",
                  end="", flush=True)
            return

        agora = time.monotonic()
        if voz.a_falar.is_set():
            estado["bloqueado_ate"] = agora + 0.5  # ignora o eco da própria voz
            return
        if agora < estado["bloqueado_ate"] or pico < LIMIAR:
            return
        if agora - estado["ultimo_pico"] < INTERVALO_MIN:
            return  # ainda é a mesma palma
        estado["ultimo_pico"] = agora

        palmas = [t for t in estado["palmas"] if agora - t <= INTERVALO_MAX]
        palmas.append(agora)
        estado["palmas"] = palmas

        if len(palmas) >= 2:
            estado["palmas"] = []
            estado["bloqueado_ate"] = agora + PAUSA
            eventos.put("duas_palmas")

    if args.calibrar:
        print("MODO CALIBRAÇÃO: bate palmas algumas vezes, depois fala normalmente.")
        print("Os sons fortes ficam registados. Ctrl+C para terminar.\n")
    else:
        voz.preparar()
        print(f"{ASSISTENTE} à escuta... (Ctrl+C para sair)")
    try:
        with sd.InputStream(samplerate=TAXA, blocksize=BLOCO, channels=1, callback=callback):
            while True:
                evento = eventos.get()
                if evento == "duas_palmas":
                    print("👏👏 detetadas!")
                    modo_trabalho()
    except KeyboardInterrupt:
        pass  # o microfone já foi fechado ao sair do "with"

    if args.calibrar:
        print(f"\n\nSom mais forte registado: {estado['maximo']:0.2f}")
        print(f"LIMIAR atual: {LIMIAR}")
    print(f"\nAté já, {NOME}.")


if __name__ == "__main__":
    main()
