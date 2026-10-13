"""
Ouvido do JARVIS: transforma a tua voz em texto com o Whisper (offline).

O modelo descarrega-se sozinho na primeira utilização.
Tamanho escolhido em config.py (MODELO_WHISPER):
    "base"  ~150 MB  rápido, erra mais
    "small" ~480 MB  bom equilíbrio para português (recomendado)

Teste isolado:
    python3 ouvido.py      # grava 4 segundos e mostra o que percebeu
"""

import numpy as np

from config import MODELO_WHISPER

TAXA = 16000  # o Whisper trabalha a 16 kHz

_modelo = None


def preparar() -> None:
    """Carrega o modelo no arranque (pode demorar alguns segundos)."""
    global _modelo
    if _modelo is None:
        from faster_whisper import WhisperModel
        print(f"  A carregar o Whisper '{MODELO_WHISPER}' (da 1ª vez descarrega-o)...")
        _modelo = WhisperModel(MODELO_WHISPER, device="cpu", compute_type="int8")
        print("  Whisper pronto.")


def transcrever(audio: np.ndarray) -> str:
    """audio: float32 mono a 16 kHz, valores entre -1 e 1."""
    preparar()
    if audio.size < TAXA * 0.3:  # menos de 0,3 s não vale a pena
        return ""
    segmentos, _ = _modelo.transcribe(
        audio.astype(np.float32),
        language="pt",
        beam_size=1,
        vad_filter=True,           # corta silêncios e ruído
        condition_on_previous_text=False,
    )
    return " ".join(s.text.strip() for s in segmentos).strip()


if __name__ == "__main__":
    import sounddevice as sd
    preparar()
    print("Fala agora (4 segundos)...")
    gravacao = sd.rec(int(4 * TAXA), samplerate=TAXA, channels=1, dtype="float32")
    sd.wait()
    print("Percebi:", repr(transcrever(gravacao[:, 0])))
