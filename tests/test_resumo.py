import io
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import resumo  # noqa: E402
import tempo  # noqa: E402
from comandos import interpretar  # noqa: E402

TEMPO_FALSO = {"cidade": "Praia", "agora": 27, "sensacao": 29, "ceu": "parcialmente nublado",
               "vento": 18, "maxima": 29, "minima": 24, "chuva": 40}


def test_frases_ativam_o_resumo():
    for frase in ["Bom dia, JARVIS", "Boa noite", "Faz o resumo do dia"]:
        assert interpretar(frase).nome == "bom_dia"


def test_saudacao_pela_hora():
    assert resumo.saudacao(8) == "Bom dia"
    assert resumo.saudacao(15) == "Boa tarde"
    assert resumo.saudacao(22) == "Boa noite"


def test_dados_do_dia_formata_data(monkeypatch):
    monkeypatch.setattr(tempo, "obter", lambda: None)
    d = resumo.dados_do_dia(time.strptime("2026-10-13 08:05", "%Y-%m-%d %H:%M"))
    assert d["data"] == "terça-feira, 13 de outubro"
    assert d["hora"] == "8 e 05"
    assert d["saudacao"] == "Bom dia"


def test_resumo_sem_ia_usa_texto_fixo(monkeypatch):
    monkeypatch.setattr(tempo, "obter", lambda: TEMPO_FALSO)
    texto = resumo.gerar(None)
    assert "Landim" in texto and "27 graus" in texto and "40 por cento" in texto


def test_resumo_com_ia_passa_os_dados(monkeypatch):
    monkeypatch.setattr(tempo, "obter", lambda: TEMPO_FALSO)

    class CerebroFalso:
        pedido = ""

        def escrever(self, pedido):
            CerebroFalso.pedido = pedido
            return "Bom dia, Landim. Resumo da IA."

    assert resumo.gerar(CerebroFalso()) == "Bom dia, Landim. Resumo da IA."
    assert "27 graus" in CerebroFalso.pedido and "sem inventar" in CerebroFalso.pedido


def test_resumo_com_ia_em_falha_volta_ao_fixo(monkeypatch):
    monkeypatch.setattr(tempo, "obter", lambda: None)

    class CerebroEmBaixo:
        def escrever(self, pedido):
            return ""

    assert resumo.gerar(CerebroEmBaixo()).startswith(("Bom dia", "Boa tarde", "Boa noite"))


def test_tempo_le_resposta_do_open_meteo(monkeypatch):
    resposta = {
        "current": {"temperature_2m": 26.6, "apparent_temperature": 28.2,
                    "weather_code": 2, "wind_speed_10m": 17.9},
        "daily": {"temperature_2m_max": [28.9], "temperature_2m_min": [23.6],
                  "precipitation_probability_max": [10]},
    }

    class Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(tempo.urllib.request, "urlopen",
                        lambda url, timeout: Resp(json.dumps(resposta).encode()))
    t = tempo.obter()
    assert t["agora"] == 27 and t["ceu"] == "parcialmente nublado" and t["maxima"] == 29
    assert "probabilidade" not in tempo.frase(t)  # 10% de chuva não vale a pena dizer
