"""
Comandos de voz do JARVIS.

`interpretar(texto)` transforma o que o Whisper ouviu num Comando.
`Comando.executar()` faz a ação no Fedora.

Para acrescentar um comando: cria uma função `_cmd_...` e junta-a a REGRAS.
"""

import re
import shutil
import subprocess
import time
import unicodedata
import urllib.parse
from dataclasses import dataclass, field
from typing import Callable, Optional

from config import NOME


@dataclass
class Comando:
    nome: str
    resposta: str
    acao: Optional[Callable[[], None]] = field(default=None, repr=False)
    sair: bool = False

    def executar(self) -> None:
        if self.acao:
            self.acao()


# --- Utilitários -------------------------------------------------------------
def normalizar(texto: str) -> str:
    """minúsculas, sem acentos nem pontuação: 'Abre o YouTube!' -> 'abre o youtube'"""
    texto = unicodedata.normalize("NFD", texto.lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    texto = re.sub(r"[^a-z0-9 ]", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _correr(*cmd: str) -> None:
    if shutil.which(cmd[0]):
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        print(f"  (não encontrei '{cmd[0]}')")


def _abrir_url(url: str) -> Callable[[], None]:
    return lambda: _correr("xdg-open", url)


def _abrir_terminal() -> None:
    for cmd in (["ptyxis", "--new-window"], ["kgx"], ["gnome-terminal"], ["konsole"]):
        if shutil.which(cmd[0]):
            _correr(*cmd)
            return


def _volume(passo: str) -> Callable[[], None]:
    # wpctl vem com o PipeWire, o sistema de som do Fedora
    return lambda: _correr("wpctl", "set-volume", "-l", "1.0", "@DEFAULT_AUDIO_SINK@", passo)


VERBOS_ABRIR = ("abre", "abrir", "abra", "abri", "mostra", "poe", "liga", "inicia")
SITES = {
    "youtube": "https://www.youtube.com",
    "github": "https://github.com/Admilson-Landim",
    "gmail": "https://mail.google.com",
    "email": "https://mail.google.com",
    "whatsapp": "https://web.whatsapp.com",
    "google": "https://www.google.com",
    "chatgpt": "https://chatgpt.com",
    "claude": "https://claude.ai",
}


def _tem(texto: str, *palavras: str) -> bool:
    return any(re.search(rf"\b{re.escape(p)}\b", texto) for p in palavras)


# --- Regras (a ordem importa: a primeira que reconhecer ganha) ---------------
def _cmd_sair(t: str) -> Optional[Comando]:
    if _tem(t, "desliga", "desligar", "adeus", "tchau", "encerra", "encerrar"):
        return Comando("sair", f"Até já, {NOME}.", sair=True)
    return None


def _cmd_pesquisar(t: str) -> Optional[Comando]:
    m = re.search(r"\b(?:pesquisa|pesquisar|procura|procurar|busca|buscar)\b(?: por| sobre)? (.+)", t)
    if m:
        termo = m.group(1).strip()
        url = "https://www.google.com/search?q=" + urllib.parse.quote(termo)
        return Comando("pesquisar", f"A pesquisar por {termo}.", _abrir_url(url))
    return None


def _cmd_volume(t: str) -> Optional[Comando]:
    if _tem(t, "silencio", "mudo", "muta", "cala"):
        return Comando("mudo", "", lambda: _correr("wpctl", "set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"))
    if _tem(t, "volume", "som"):
        if _tem(t, "aumenta", "aumentar", "sobe", "subir", "mais", "alto"):
            return Comando("volume_mais", "Volume aumentado.", _volume("10%+"))
        if _tem(t, "diminui", "diminuir", "baixa", "baixar", "menos"):
            return Comando("volume_menos", "Volume diminuído.", _volume("10%-"))
    return None


def _cmd_bloquear(t: str) -> Optional[Comando]:
    if _tem(t, "bloqueia", "bloquear", "tranca", "trancar") and _tem(t, "ecra", "tela", "computador", "pc"):
        return Comando("bloquear", "A bloquear o ecrã.", lambda: _correr("loginctl", "lock-session"))
    return None


def _cmd_horas(t: str) -> Optional[Comando]:
    if _tem(t, "horas", "hora"):
        agora = time.localtime()
        return Comando("horas", f"São {agora.tm_hour} e {agora.tm_min:02d}.")
    if _tem(t, "dia", "data") and _tem(t, "hoje", "que"):
        meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
                 "agosto", "setembro", "outubro", "novembro", "dezembro"]
        agora = time.localtime()
        return Comando("data", f"Hoje é dia {agora.tm_mday} de {meses[agora.tm_mon - 1]}.")
    return None


def _cmd_trabalho(t: str) -> Optional[Comando]:
    if _tem(t, "trabalho", "trabalhar"):
        def acao():
            _correr("code")
            _abrir_terminal()
            _correr("xdg-open", SITES["github"])
        return Comando("modo_trabalho", "A preparar o ambiente de trabalho.", acao)
    return None


def _cmd_abrir(t: str) -> Optional[Comando]:
    if not _tem(t, *VERBOS_ABRIR):
        return None
    for site, url in SITES.items():
        if _tem(t, site):
            return Comando(f"abrir_{site}", f"A abrir o {site}.", _abrir_url(url))
    if _tem(t, "code", "vscode", "editor"):
        return Comando("abrir_vscode", "A abrir o VS Code.", lambda: _correr("code"))
    if _tem(t, "terminal", "consola"):
        return Comando("abrir_terminal", "A abrir o terminal.", _abrir_terminal)
    if _tem(t, "browser", "navegador", "firefox"):
        return Comando("abrir_browser", "A abrir o navegador.", lambda: _correr("firefox"))
    if _tem(t, "ficheiros", "arquivos", "pastas"):
        return Comando("abrir_ficheiros", "A abrir os ficheiros.", lambda: _correr("nautilus"))
    return None


def _cmd_conversa(t: str) -> Optional[Comando]:
    if _tem(t, "obrigado", "obrigada", "valeu"):
        return Comando("obrigado", f"Sempre às ordens, {NOME}.")
    if _tem(t, "quem es", "quem e voce", "quem e tu", "como te chamas"):
        return Comando("quem", "Eu sou o JARVIS, o teu assistente pessoal.")
    return None


REGRAS = [_cmd_sair, _cmd_pesquisar, _cmd_volume, _cmd_bloquear, _cmd_horas,
          _cmd_trabalho, _cmd_abrir, _cmd_conversa]


def interpretar(texto: str) -> Comando:
    t = normalizar(texto)
    if not t:
        return Comando("vazio", "Não ouvi nada.")
    for regra in REGRAS:
        cmd = regra(t)
        if cmd:
            return cmd
    return Comando("desconhecido", "Desculpa, ainda não sei fazer isso.")
