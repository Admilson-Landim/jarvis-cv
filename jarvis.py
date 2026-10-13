#!/usr/bin/env python3
"""
JARVIS - Fase 2: duas palmas -> "Sim, Landim?" -> ouve a ordem -> executa.

Uso:
    python3 jarvis.py              # modo normal (palmas + voz)
    python3 jarvis.py --escrever   # escreves os comandos no teclado (para testar)

Calibração das palmas: python3 jarvis_palmas.py --calibrar
"""

import argparse
import queue
import time

import numpy as np
import sounddevice as sd

import cerebro
import ouvido
import voz
from comandos import executar_acao, interpretar, precisa_do_cerebro
from config import DURACAO_MAX, ESPERA_MAX, IA, LIMIAR_VOZ, NOME, SILENCIO_FIM
from jarvis_palmas import INTERVALO_MAX, INTERVALO_MIN, LIMIAR

TAXA = ouvido.TAXA   # 16 kHz serve para as palmas e para o Whisper
BLOCO = 512          # ~32 ms

CEREBRO = cerebro.Cerebro() if cerebro.disponivel() else None


def tratar(texto: str) -> bool:
    """Interpreta e executa. Devolve False se for para sair."""
    cmd = interpretar(texto)

    if CEREBRO and precisa_do_cerebro(texto, cmd):
        print("  -> 🧠 a pensar...")
        resultado = CEREBRO.pensar(texto)
        sair = False
        for acao in resultado["acoes"]:
            print(f"     ação: {acao}")
            if acao["tipo"] == "sair":
                sair = True
            else:
                executar_acao(acao)
        if resultado["resposta"]:
            print(f"  JARVIS: {resultado['resposta']}")
            voz.falar(resultado["resposta"], esperar=True)
        return not sair

    print(f"  -> {cmd.nome}")
    cmd.executar()
    if cmd.resposta:
        voz.falar(cmd.resposta, esperar=True)
    return not cmd.sair


def estado_cerebro() -> None:
    if CEREBRO:
        print(f"  Cérebro: {IA} ✅")
    else:
        print("  Cérebro: desligado (falta a chave no .env) — só comandos simples")


def modo_escrever() -> None:
    voz.preparar()
    estado_cerebro()
    print("Escreve um comando (ex.: 'abre o youtube'). 'adeus' para sair.")
    while True:
        try:
            texto = input("> ")
        except (EOFError, KeyboardInterrupt):
            break
        if not tratar(texto):
            break


def modo_voz() -> None:
    voz.preparar()
    ouvido.preparar()
    estado_cerebro()

    eventos: "queue.Queue[tuple]" = queue.Queue()
    estado = {
        "modo": "palmas",          # palmas | gravar | ocupado
        "ultimo_pico": 0.0, "palmas": [], "bloqueado_ate": 0.0,
        "blocos": [], "inicio": 0.0, "falou": False, "ultimo_som": 0.0,
    }

    def callback(indata, frames, time_info, status):
        agora = time.monotonic()
        pico = float(np.max(np.abs(indata)))

        if voz.a_falar.is_set():
            estado["bloqueado_ate"] = agora + 0.5
            return

        if estado["modo"] == "gravar":
            estado["blocos"].append(indata[:, 0].copy())
            if pico >= LIMIAR_VOZ:
                estado["falou"] = True
                estado["ultimo_som"] = agora
            duracao = agora - estado["inicio"]
            fim = (
                (estado["falou"] and agora - estado["ultimo_som"] > SILENCIO_FIM)
                or (not estado["falou"] and duracao > ESPERA_MAX)
                or duracao > DURACAO_MAX
            )
            if fim:
                estado["modo"] = "ocupado"
                audio = np.concatenate(estado["blocos"]) if estado["falou"] else np.zeros(0)
                eventos.put(("audio", audio))
            return

        if estado["modo"] != "palmas":
            return
        if agora < estado["bloqueado_ate"] or pico < LIMIAR:
            return
        if agora - estado["ultimo_pico"] < INTERVALO_MIN:
            return
        estado["ultimo_pico"] = agora
        palmas = [t for t in estado["palmas"] if agora - t <= INTERVALO_MAX]
        palmas.append(agora)
        estado["palmas"] = palmas
        if len(palmas) >= 2:
            estado["palmas"] = []
            estado["modo"] = "ocupado"
            eventos.put(("palmas", None))

    def voltar_as_palmas():
        estado["palmas"] = []
        estado["bloqueado_ate"] = time.monotonic() + 1.0
        estado["modo"] = "palmas"

    print(f"JARVIS à escuta, {NOME}. Duas palmas para chamar. (Ctrl+C para sair)")
    try:
        with sd.InputStream(samplerate=TAXA, blocksize=BLOCO, channels=1,
                            dtype="float32", callback=callback):
            while True:
                tipo, dados = eventos.get()

                if tipo == "palmas":
                    print("👏👏")
                    voz.falar(f"Sim, {NOME}?", esperar=True)
                    voz.bip()  # podes falar a partir daqui
                    estado.update(blocos=[], falou=False, inicio=time.monotonic(),
                                  ultimo_som=time.monotonic())
                    estado["modo"] = "gravar"
                    print("  🔊 bip — a ouvir...")

                elif tipo == "audio":
                    texto = ouvido.transcrever(dados) if dados.size else ""
                    print(f"  ouvi: {texto!r}")
                    if not tratar(texto):
                        return  # o JARVIS já se despediu
                    voltar_as_palmas()
    except KeyboardInterrupt:
        print(f"\nAté já, {NOME}.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--escrever", action="store_true",
                        help="escrever os comandos em vez de falar")
    args = parser.parse_args()
    if args.escrever:
        modo_escrever()
    else:
        modo_voz()


if __name__ == "__main__":
    main()
