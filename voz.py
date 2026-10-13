"""
Voz do JARVIS.

Usa o Piper (voz neural, offline) quando a voz está descarregada em ./vozes,
senão recorre ao spd-say/espeak (robótico, mas funciona sempre).

Descarregar a voz brasileira (uma vez):
    python3 -m piper.download_voices pt_BR-faber-medium --data-dir vozes
"""

import shutil
import subprocess
import threading
from pathlib import Path

import numpy as np
import sounddevice as sd

from config import ASSISTENTE, NOME

PASTA_VOZES = Path(__file__).parent / "vozes"
VOZ = "pt_BR-faber-medium"   # troca aqui para experimentar outra voz

# Fica "ligado" enquanto o JARVIS fala, para o microfone não confundir a voz com palmas
a_falar = threading.Event()

_voz_piper = None
_carregada = False


def _carregar_piper():
    global _voz_piper, _carregada
    if _carregada:
        return _voz_piper
    _carregada = True
    modelo = PASTA_VOZES / f"{VOZ}.onnx"
    if not modelo.exists():
        print(f"  A descarregar a voz '{VOZ}' (só da primeira vez, ~60 MB)...")
        try:
            from piper.download_voices import download_voice
            PASTA_VOZES.mkdir(exist_ok=True)
            download_voice(VOZ, PASTA_VOZES)
        except Exception as erro:
            print(f"  (não consegui descarregar a voz: {erro}; a usar espeak)")
            return None
    try:
        from piper import PiperVoice
        _voz_piper = PiperVoice.load(str(modelo))
        print(f"  Voz carregada: {VOZ}")
    except Exception as erro:  # piper não instalado ou modelo inválido
        print(f"  (não consegui carregar o Piper: {erro}; a usar espeak)")
    return _voz_piper


def preparar() -> None:
    """Carrega a voz logo no arranque, para a primeira frase não demorar."""
    _carregar_piper()


def _falar_agora(texto: str) -> None:
    a_falar.set()
    try:
        voz = _carregar_piper()
        if voz is not None:
            blocos = [c.audio_float_array for c in voz.synthesize(texto)]
            if blocos:
                taxa = voz.config.sample_rate
                sd.play(np.concatenate(blocos), taxa)
                sd.wait()
            return
        if shutil.which("spd-say"):
            subprocess.run(["spd-say", "-w", "-l", "pt-BR", texto])
        elif shutil.which("espeak-ng"):
            subprocess.run(["espeak-ng", "-v", "pt-br", texto])
        else:
            print(f"[{ASSISTENTE}] {texto}")
    finally:
        a_falar.clear()


def bip() -> None:
    """Bip curto: sinal de que o JARVIS está a ouvir."""
    taxa = 22050
    t = np.linspace(0, 0.15, int(taxa * 0.15), endpoint=False)
    som = 0.3 * np.sin(2 * np.pi * 880 * t) * np.hanning(t.size)
    a_falar.set()
    try:
        sd.play(som.astype(np.float32), taxa)
        sd.wait()
    finally:
        a_falar.clear()


def falar(texto: str, esperar: bool = False) -> None:
    """Diz o texto em voz alta. Por defeito não bloqueia o resto do programa."""
    if esperar:
        _falar_agora(texto)
    else:
        threading.Thread(target=_falar_agora, args=(texto,), daemon=True).start()


if __name__ == "__main__":
    import sys
    frase = " ".join(sys.argv[1:]) or f"Olá, {NOME}. Eu sou o {ASSISTENTE}. Todos os sistemas estão operacionais."
    falar(frase, esperar=True)
