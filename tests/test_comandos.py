import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from comandos import interpretar, normalizar  # noqa: E402


def test_normalizar():
    assert normalizar("Abre o YouTube!") == "abre o youtube"
    assert normalizar("  Que horas são?  ") == "que horas sao"
    assert normalizar("Bloqueia o ecrã.") == "bloqueia o ecra"


@pytest.mark.parametrize("frase, esperado", [
    ("Abre o YouTube.", "abrir_youtube"),
    ("abra o github", "abrir_github"),
    ("Abre o VS Code", "abrir_vscode"),
    ("abre o terminal", "abrir_terminal"),
    ("Abre o navegador", "abrir_browser"),
    ("Aumenta o volume.", "volume_mais"),
    ("Baixa o som", "volume_menos"),
    ("Silêncio!", "mudo"),
    ("Bloqueia o ecrã", "bloquear"),
    ("Bloqueia a tela", "bloquear"),
    ("Que horas são?", "horas"),
    ("Que dia é hoje?", "data"),
    ("Pesquisa por receitas de cachupa", "pesquisar"),
    ("Modo trabalho", "modo_trabalho"),
    ("Obrigado, JARVIS", "obrigado"),
    ("Desliga.", "sair"),
    ("Faz-me um café", "desconhecido"),
    ("", "vazio"),
])
def test_interpretar(frase, esperado):
    assert interpretar(frase).nome == esperado


def test_pesquisa_guarda_o_termo():
    cmd = interpretar("Procura sobre praias da Boa Vista")
    assert "praias da boa vista" in cmd.resposta


def test_sair_marca_saida():
    assert interpretar("Adeus").sair
