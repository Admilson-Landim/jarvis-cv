#!/usr/bin/env python3
"""
Truta (jarvis-cv): duas palmas -> "Sim, Landim?" -> ouve a ordem -> executa.

Uso:
    python3 jarvis.py              # modo normal (palmas + voz)
    python3 jarvis.py --escrever   # escreves os comandos no teclado (para testar)

Calibração das palmas: python3 jarvis_palmas.py --calibrar
"""

import argparse
import fcntl
import queue
import shutil
import subprocess
import threading
import time
from pathlib import Path

import numpy as np
import sounddevice as sd

import cerebro
import ouvido
import resumo
import voz
from comandos import executar_acao, interpretar, precisa_do_cerebro
from config import ASSISTENTE, DURACAO_MAX, ESPERA_MAX, IA, LIMIAR_VOZ, NOME, SILENCIO_FIM
from jarvis_palmas import INTERVALO_MAX, INTERVALO_MIN, LIMIAR, TAXA as TAXA_MIC

TAXA = TAXA_MIC      # o microfone é lido em alta qualidade (as palmas precisam)
BLOCO = 1536         # ~32 ms a 48 kHz

CEREBRO = cerebro.Cerebro() if cerebro.disponivel() else None


AVISO_APOS = 4.0  # s: se a IA demorar mais do que isto, o assistente avisa que está a pensar


def com_aviso(funcao, *args):
    """Corre funcao(*args); se demorar, diz "Um momento" para não ficar em silêncio."""
    aviso = threading.Timer(AVISO_APOS, voz.falar, args=(f"Um momento, {NOME}.",))
    aviso.daemon = True
    aviso.start()
    try:
        return funcao(*args)
    finally:
        aviso.cancel()
        while voz.a_falar.is_set():  # não falar por cima do "um momento"
            time.sleep(0.05)


def executar_resultado(resultado: dict) -> bool:
    sair = False
    for acao in resultado["acoes"]:
        print(f"     ação: {acao}")
        if acao["tipo"] == "sair":
            sair = True
        else:
            executar_acao(acao)
    if resultado["resposta"]:
        print(f"  {ASSISTENTE}: {resultado['resposta']}")
        voz.falar(resultado["resposta"], esperar=True)
    return not sair


def tratar(texto: str) -> bool:
    """Interpreta e executa. Devolve False se for para sair."""
    cmd = interpretar(texto)

    if cmd.nome == "bom_dia":
        print("  -> ☀️ resumo do dia")
        texto_resumo = com_aviso(resumo.gerar, CEREBRO)
        print(f"  {ASSISTENTE}: {texto_resumo}")
        voz.falar(texto_resumo, esperar=True)
        return True

    if CEREBRO and precisa_do_cerebro(texto, cmd):
        print("  -> 🧠 a pensar...")
        resultado = com_aviso(CEREBRO.pensar, texto)
        if resultado.get("falhou") and cmd.nome != "desconhecido":
            print(f"  (IA em baixo; faço o que sei sem ela: {cmd.nome})")
        else:
            return executar_resultado(resultado)

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


_trinco = None  # mantém o ficheiro de trinco aberto enquanto o programa corre


def so_uma_instancia() -> bool:
    """Evita dois Trutas a ouvir o mesmo microfone (ex.: serviço + terminal)."""
    global _trinco
    _trinco = open(Path(__file__).parent / ".truta.lock", "w")
    try:
        fcntl.flock(_trinco, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


def notificar(texto: str) -> None:
    if shutil.which("notify-send"):
        subprocess.Popen(["notify-send", "-a", ASSISTENTE, "-i", "audio-input-microphone",
                          ASSISTENTE, texto])


def modo_voz() -> None:
    if not so_uma_instancia():
        print(f"O {ASSISTENTE} já está a correr noutro sítio (provavelmente o serviço).")
        print("Para o parar:  ./arranque.sh parar")
        return
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

    print(f"{ASSISTENTE} à escuta, {NOME}. Duas palmas para chamar. (Ctrl+C para sair)")
    notificar(f"À escuta, {NOME}. Duas palmas para chamar.")
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
                    texto = ouvido.transcrever(ouvido.para_16k(dados, TAXA)) if dados.size else ""
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
