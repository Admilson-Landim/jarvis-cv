import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cerebro  # noqa: E402
import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def estado_temporario(tmp_path, monkeypatch):
    monkeypatch.setattr(cerebro, "ESTADO", tmp_path / "estado.json")
    monkeypatch.setattr(cerebro, "ultimo_modelo", "")
import comandos  # noqa: E402
from comandos import interpretar, precisa_do_cerebro  # noqa: E402


def test_analisar_resposta_normal():
    bruto = json.dumps({
        "resposta": "A abrir o YouTube, Landim.",
        "acoes": [{"tipo": "abrir_site", "url": "https://www.youtube.com"},
                  {"tipo": "pesquisar_youtube", "termo": "IA para programadores"}],
    })
    r = cerebro.analisar(bruto)
    assert r["resposta"] == "A abrir o YouTube, Landim."
    assert [a["tipo"] for a in r["acoes"]] == ["abrir_site", "pesquisar_youtube"]


def test_analisar_bloqueia_acoes_desconhecidas_e_urls_estranhas():
    bruto = json.dumps({
        "resposta": "ok",
        "acoes": [{"tipo": "executar_comando", "cmd": "rm -rf ~"},
                  {"tipo": "abrir_site", "url": "file:///etc/passwd"},
                  "lixo",
                  {"tipo": "bloquear_ecra"}],
    })
    assert [a["tipo"] for a in cerebro.analisar(bruto)["acoes"]] == ["bloquear_ecra"]


def test_analisar_aceita_bloco_de_codigo_e_texto_simples():
    assert cerebro.analisar('```json\n{"resposta": "Olá", "acoes": []}\n```')["resposta"] == "Olá"
    assert cerebro.analisar("Olá, Landim!") == {"resposta": "Olá, Landim!", "acoes": []}


def test_encaminhamento():
    simples = "Abre o YouTube"
    composto = "Abre o YouTube e pesquisa algo interessante sobre IA"
    livre = "Conta-me uma curiosidade sobre Cabo Verde"
    assert not precisa_do_cerebro(simples, interpretar(simples))
    assert precisa_do_cerebro(composto, interpretar(composto))
    assert precisa_do_cerebro(livre, interpretar(livre))
    assert not precisa_do_cerebro("Desliga", interpretar("Desliga"))


def test_executar_acoes(monkeypatch):
    chamadas = []
    monkeypatch.setattr(comandos, "_correr", lambda *c: chamadas.append(c))
    monkeypatch.setattr(comandos, "NAVEGADOR", None)
    comandos.executar_acao({"tipo": "pesquisar_youtube", "termo": "cachupa rica"})
    comandos.executar_acao({"tipo": "volume", "direcao": "mais"})
    comandos.executar_acao({"tipo": "abrir_app", "app": "rm"})  # app inválida: ignora
    assert chamadas[0] == ("xdg-open", "https://www.youtube.com/results?search_query=cachupa%20rica")
    assert chamadas[1][0] == "wpctl"
    assert len(chamadas) == 2


def test_gemini_formato_do_pedido(monkeypatch):
    enviado = {}

    def falso_post(url, cabecalhos, corpo, timeout=30):
        enviado.update(url=url, cabecalhos=cabecalhos, corpo=corpo)
        return {"candidates": [{"content": {"parts": [{"text": '{"resposta": "Olá", "acoes": []}'}]}}]}

    monkeypatch.setattr(cerebro, "_post", falso_post)
    monkeypatch.setattr(cerebro, "IA", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "teste")
    c = cerebro.Cerebro()
    assert c.pensar("olá")["resposta"] == "Olá"
    assert ":generateContent" in enviado["url"]
    assert enviado["cabecalhos"]["x-goog-api-key"] == "teste"
    assert enviado["corpo"]["contents"][0]["role"] == "user"
    # a segunda pergunta leva o histórico
    c.pensar("e tu?")
    assert [m["role"] for m in enviado["corpo"]["contents"]] == ["user", "model", "user"]


def test_ler_env_limpa_invisiveis_e_ignora_exemplo(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text(
        'GEMINI_API_KEY=cola_aqui_a_tua_chave\nexport GEMINI_API_KEY = "AQ.abc 123​"\n',
        encoding="utf-8")
    monkeypatch.setattr(cerebro, "PASTA", tmp_path)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    cerebro._carregar_env()
    import os
    assert os.environ["GEMINI_API_KEY"] == "AQ.abc123"


def test_gemini_tenta_outro_modelo_quando_ocupado(monkeypatch):
    import io
    import urllib.error
    tentados = []

    def falso_post(url, cabecalhos, corpo, timeout=30):
        modelo = url.split("/models/")[1].split(":")[0]
        tentados.append(modelo)
        if len(tentados) < 3:
            codigo = 503 if len(tentados) == 1 else 404
            raise urllib.error.HTTPError(url, codigo, "x", {}, io.BytesIO(b"{}"))
        return {"candidates": [{"content": {"parts": [{"text": '{"resposta": "ok", "acoes": []}'}]}}]}

    monkeypatch.setattr(cerebro, "_post", falso_post)
    monkeypatch.setattr(cerebro, "IA", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "teste")
    assert cerebro.Cerebro().pensar("olá")["resposta"] == "ok"
    assert len(tentados) == 3 and cerebro.ultimo_modelo == tentados[2]


def test_gemini_chave_invalida_nao_insiste(monkeypatch):
    import io
    import urllib.error
    tentados = []

    def falso_post(url, cabecalhos, corpo, timeout=30):
        tentados.append(url)
        raise urllib.error.HTTPError(url, 400, "x", {}, io.BytesIO(b"API key not valid"))

    monkeypatch.setattr(cerebro, "_post", falso_post)
    monkeypatch.setattr(cerebro, "IA", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "teste")
    assert "recusou" in cerebro.Cerebro().pensar("olá")["resposta"]
    assert len(tentados) == 1


def test_gemini_comeca_pelo_ultimo_modelo_que_funcionou(monkeypatch):
    tentados = []

    def falso_post(url, cabecalhos, corpo, timeout=30):
        tentados.append(url.split("/models/")[1].split(":")[0])
        return {"candidates": [{"content": {"parts": [{"text": '{"resposta": "ok", "acoes": []}'}]}}]}

    monkeypatch.setattr(cerebro, "_post", falso_post)
    monkeypatch.setattr(cerebro, "IA", "gemini")
    monkeypatch.setattr(cerebro, "ultimo_modelo", "gemini-3.1-flash-lite")
    monkeypatch.setenv("GEMINI_API_KEY", "teste")
    cerebro.Cerebro().pensar("olá")
    assert tentados == ["gemini-3.1-flash-lite"]


def test_modelo_que_funcionou_fica_gravado(monkeypatch):
    def falso_post(url, cabecalhos, corpo, timeout=30):
        return {"candidates": [{"content": {"parts": [{"text": '{"resposta": "ok", "acoes": []}'}]}}]}

    monkeypatch.setattr(cerebro, "_post", falso_post)
    monkeypatch.setattr(cerebro, "IA", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "teste")
    cerebro.Cerebro().pensar("olá")
    assert cerebro._ler_estado()["modelo"] == cerebro.MODELO_IA
