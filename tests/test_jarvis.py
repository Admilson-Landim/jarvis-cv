"""Testes do encaminhamento no jarvis.py, com som e IA falsos."""
import sys
import time
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.modules.setdefault("sounddevice", types.SimpleNamespace(play=lambda *a, **k: None,
                                                            wait=lambda: None, InputStream=None))

import comandos  # noqa: E402
import jarvis  # noqa: E402
import voz  # noqa: E402


@pytest.fixture
def ambiente(monkeypatch):
    ditos, corridos = [], []
    monkeypatch.setattr(voz, "falar", lambda texto, esperar=False: ditos.append(texto))
    monkeypatch.setattr(comandos, "_correr", lambda *c: corridos.append(c))
    monkeypatch.setattr(comandos, "NAVEGADOR", None)
    return ditos, corridos


class CerebroEmBaixo:
    def pensar(self, texto):
        return {"resposta": "Os servidores da IA estão ocupados agora.", "acoes": [], "falhou": True}


def test_ia_em_baixo_faz_o_comando_local(monkeypatch, ambiente):
    ditos, corridos = ambiente
    monkeypatch.setattr(jarvis, "CEREBRO", CerebroEmBaixo())
    jarvis.tratar("Pesquisa por praias de Santiago e depois diz-me qual é a melhor")
    assert corridos and "google.com/search" in corridos[0][1]
    assert ditos and ditos[-1].startswith("A pesquisar")


def test_ia_em_baixo_e_pedido_desconhecido_avisa(monkeypatch, ambiente):
    ditos, corridos = ambiente
    monkeypatch.setattr(jarvis, "CEREBRO", CerebroEmBaixo())
    jarvis.tratar("Conta-me uma anedota sobre programadores")
    assert not corridos and "ocupados" in ditos[-1]


def test_aviso_um_momento_quando_demora(monkeypatch, ambiente):
    ditos, _ = ambiente
    monkeypatch.setattr(jarvis, "AVISO_APOS", 0.05)

    class CerebroLento:
        def pensar(self, texto):
            time.sleep(0.2)
            return {"resposta": "Pronto.", "acoes": []}

    monkeypatch.setattr(jarvis, "CEREBRO", CerebroLento())
    jarvis.tratar("Conta-me uma curiosidade sobre Cabo Verde")
    assert ditos[0].startswith("Um momento") and ditos[-1] == "Pronto."


def test_resposta_rapida_sem_aviso(monkeypatch, ambiente):
    ditos, _ = ambiente

    class CerebroRapido:
        def pensar(self, texto):
            return {"resposta": "Pronto.", "acoes": []}

    monkeypatch.setattr(jarvis, "CEREBRO", CerebroRapido())
    jarvis.tratar("Conta-me uma curiosidade sobre Cabo Verde")
    assert ditos == ["Pronto."]
